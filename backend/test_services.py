#!/usr/bin/env python3
"""
Test script for SAR drone backend services
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import our services
from app.services.area_calculator import (
    AreaCalculator, DroneCapabilities, EnvironmentalFactors,
    TerrainType, WeatherCondition
)
from app.services.mission_planner import (
    MissionPlannerService, MissionType, MissionPriority,
    SearchArea, Coordinates
)
from app.services.drone_manager import (
    DroneManager, DroneInfo, DroneType, DroneStatus,
    DroneCapabilities as DroneManagerCapabilities,
    TelemetryData
)
from app.services.notification_service import (
    NotificationService, NotificationRecipient, NotificationType,
    NotificationPriority, NotificationChannel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_area_calculator():
    """Test the AreaCalculator service"""
    logger.info("Testing AreaCalculator service...")
    
    calculator = AreaCalculator()
    
    # Test drone capabilities
    drone_capabilities = DroneCapabilities(
        max_flight_time_minutes=30.0,
        max_speed_kmh=50.0,
        max_range_km=10.0,
        camera_resolution=(1920, 1080),
        camera_fov_degrees=90.0,
        optimal_altitude_m=50.0,
        max_altitude_m=120.0,
        wind_resistance_kmh=20.0,
        battery_capacity_mah=5000,
        power_consumption_w=100.0
    )
    
    # Test environmental factors
    environmental_factors = EnvironmentalFactors(
        terrain_type=TerrainType.FOREST,
        weather_condition=WeatherCondition.CLEAR,
        wind_speed_kmh=10.0,
        visibility_km=8.0,
        temperature_c=20.0,
        altitude_m=500.0,
        obstacles_density=0.3
    )
    
    # Calculate searchable area
    coverage = await calculator.calculate_searchable_area(
        drone_count=3,
        drone_capabilities=drone_capabilities,
        environmental_factors=environmental_factors,
        battery_levels=[0.9, 0.8, 0.85],
        travel_distance_km=2.0,
        mission_time_limit_minutes=120
    )
    
    logger.info(f"Coverage analysis: {coverage.total_searchable_area_km2:.2f} km²")
    logger.info(f"Confidence: {coverage.coverage_confidence:.1%}")
    logger.info(f"Recommended drones: {coverage.recommended_drone_count}")
    
    # Test environmental impact calculation
    impacts = await calculator.calculate_environmental_impact(
        environmental_factors, drone_capabilities
    )
    logger.info(f"Environmental impacts: {impacts}")
    
    logger.info("AreaCalculator test completed ✓")


async def test_mission_planner():
    """Test the MissionPlannerService"""
    logger.info("Testing MissionPlannerService...")
    
    # Create area calculator dependency
    area_calculator = AreaCalculator()
    planner = MissionPlannerService(area_calculator)
    
    # Define search area
    search_area = SearchArea(
        center=Coordinates(34.0522, -118.2437),  # Los Angeles
        boundaries=[
            Coordinates(34.0622, -118.2537),
            Coordinates(34.0622, -118.2337),
            Coordinates(34.0422, -118.2337),
            Coordinates(34.0422, -118.2537)
        ],
        area_km2=4.0,
        terrain_type="urban",
        elevation_min_m=50.0,
        elevation_max_m=200.0
    )
    
    # Available drones
    available_drones = [
        {
            "id": "drone_001",
            "name": "SAR Drone 1",
            "max_flight_time": 30,
            "max_speed_kmh": 50,
            "max_range_km": 10,
            "battery_level": 0.9
        },
        {
            "id": "drone_002", 
            "name": "SAR Drone 2",
            "max_flight_time": 35,
            "max_speed_kmh": 45,
            "max_range_km": 12,
            "battery_level": 0.8
        }
    ]
    
    # Environmental conditions
    environmental_conditions = EnvironmentalFactors(
        terrain_type=TerrainType.URBAN,
        weather_condition=WeatherCondition.CLEAR,
        wind_speed_kmh=15.0,
        visibility_km=10.0,
        temperature_c=22.0,
        altitude_m=100.0,
        obstacles_density=0.4
    )
    
    # Mission requirements
    mission_requirements = {
        "travel_distance_km": 3.0,
        "time_limit_minutes": 90,
        "command_center": Coordinates(34.0522, -118.2437)
    }
    
    # Create mission plan
    mission_plan = await planner.create_mission_plan(
        mission_type=MissionType.MISSING_PERSON,
        priority=MissionPriority.HIGH,
        search_area=search_area,
        available_drones=available_drones,
        environmental_conditions=environmental_conditions,
        mission_requirements=mission_requirements,
        created_by="test_operator"
    )
    
    logger.info(f"Mission plan created: {mission_plan.mission_id}")
    logger.info(f"Drone assignments: {len(mission_plan.drone_assignments)}")
    logger.info(f"Estimated duration: {mission_plan.timeline.total_duration}")
    logger.info(f"Success probability: {mission_plan.success_probability:.1%}")
    
    # Validate mission plan
    validation = await planner.validate_mission_plan(mission_plan)
    logger.info(f"Mission validation: {validation}")
    
    logger.info("MissionPlannerService test completed ✓")


async def test_drone_manager():
    """Test the DroneManager service"""
    logger.info("Testing DroneManager service...")
    
    manager = DroneManager()
    
    # Test drone discovery
    discovered_drones = await manager.discover_drones("network_scan", 10.0)
    logger.info(f"Discovered {len(discovered_drones)} drones")
    
    # Register drones
    for drone_info in discovered_drones:
        success = await manager.register_drone(drone_info)
        logger.info(f"Registered drone {drone_info.drone_id}: {success}")
    
    # Test telemetry processing
    if discovered_drones:
        test_drone = discovered_drones[0]
        
        telemetry = TelemetryData(
            timestamp=datetime.now(),
            drone_id=test_drone.drone_id,
            latitude=34.0522,
            longitude=-118.2437,
            altitude_m=50.0,
            heading_degrees=90.0,
            speed_kmh=25.0,
            vertical_speed_ms=0.5,
            acceleration_ms2=(0.1, 0.2, -9.8),
            battery_percentage=75.0,
            battery_voltage=12.6,
            battery_current_a=5.2,
            battery_temperature_c=25.0,
            flight_mode="AUTO",
            armed=True,
            gps_satellites=8,
            gps_hdop=1.2
        )
        
        success = await manager.process_telemetry(test_drone.drone_id, telemetry)
        logger.info(f"Telemetry processed: {success}")
        
        # Perform health check
        health = await manager.perform_health_check(test_drone.drone_id)
        logger.info(f"Health check: {health.overall_status.value}")
        logger.info(f"Active issues: {len(health.active_issues)}")
        
        # Update performance metrics
        mission_data = {
            "flight_time": timedelta(minutes=25),
            "distance_km": 8.5,
            "successful": True,
            "battery_efficiency": 0.9,
            "positioning_accuracy": 1.8
        }
        
        performance = await manager.update_performance_metrics(
            test_drone.drone_id, mission_data
        )
        logger.info(f"Performance updated: {performance.successful_missions} successful missions")
    
    # Get fleet summary
    summary = await manager.get_fleet_summary()
    logger.info(f"Fleet summary: {summary}")
    
    logger.info("DroneManager test completed ✓")


async def test_notification_service():
    """Test the NotificationService"""
    logger.info("Testing NotificationService...")
    
    service = NotificationService()
    
    # Wait for background tasks to start
    await asyncio.sleep(1)
    
    # Register recipients
    recipient = NotificationRecipient(
        user_id="operator_001",
        name="Test Operator",
        channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
        contact_info={"email": "operator@example.com", "phone": "+1234567890"}
    )
    
    await service.register_recipient(recipient)
    logger.info(f"Registered recipient: {recipient.user_id}")
    
    # Test notification creation
    notification = await service.create_notification(
        title="Test Discovery Alert",
        message="Object of interest discovered during search mission",
        notification_type=NotificationType.DISCOVERY,
        priority=NotificationPriority.HIGH,
        data={"latitude": 34.0522, "longitude": -118.2437, "drone_id": "drone_001"}
    )
    
    logger.info(f"Created notification: {notification.notification_id}")
    
    # Test template-based notification
    template_notification = await service.create_from_template(
        template_id="discovery_found",
        data={
            "latitude": 34.0522,
            "longitude": -118.2437,
            "drone_id": "drone_002"
        }
    )
    
    logger.info(f"Created template notification: {template_notification.notification_id}")
    
    # Wait for delivery
    await asyncio.sleep(2)
    
    # Get user notifications
    user_notifications = await service.get_notifications_for_user(
        "operator_001", include_history=True
    )
    logger.info(f"User notifications: {len(user_notifications)}")
    
    # Test acknowledgment
    if user_notifications:
        ack_success = await service.acknowledge_notification(
            user_notifications[0].notification_id, "operator_001"
        )
        logger.info(f"Notification acknowledged: {ack_success}")
    
    # Get statistics
    stats = await service.get_notification_stats()
    logger.info(f"Notification stats: {stats}")
    
    logger.info("NotificationService test completed ✓")


async def test_integration():
    """Test service integration"""
    logger.info("Testing service integration...")
    
    # Initialize services
    area_calculator = AreaCalculator()
    mission_planner = MissionPlannerService(area_calculator)
    drone_manager = DroneManager()
    notification_service = NotificationService()
    
    # Wait for services to initialize
    await asyncio.sleep(1)
    
    # Register notification recipient
    recipient = NotificationRecipient(
        user_id="mission_commander",
        name="Mission Commander",
        channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH]
    )
    await notification_service.register_recipient(recipient)
    
    # Discover and register drones
    drones = await drone_manager.discover_drones("network_scan", 5.0)
    for drone in drones:
        await drone_manager.register_drone(drone)
        
        # Send discovery notification
        await notification_service.create_from_template(
            "discovery_new_drone",
            {"drone_id": drone.drone_id, "drone_name": drone.name}
        )
    
    logger.info(f"Integration test: {len(drones)} drones discovered and registered")
    
    # Create a mission plan using discovered drones
    if drones:
        search_area = SearchArea(
            center=Coordinates(34.0522, -118.2437),
            boundaries=[
                Coordinates(34.0622, -118.2537),
                Coordinates(34.0622, -118.2337),
                Coordinates(34.0422, -118.2337),
                Coordinates(34.0422, -118.2537)
            ],
            area_km2=4.0,
            terrain_type="urban",
            elevation_min_m=50.0,
            elevation_max_m=200.0
        )
        
        available_drones = [
            {
                "id": drone.drone_id,
                "name": drone.name,
                "max_flight_time": 30,
                "max_speed_kmh": 50,
                "max_range_km": 10,
                "battery_level": 0.9
            }
            for drone in drones[:2]  # Use first 2 drones
        ]
        
        environmental_conditions = EnvironmentalFactors(
            terrain_type=TerrainType.URBAN,
            weather_condition=WeatherCondition.CLEAR,
            wind_speed_kmh=10.0,
            visibility_km=10.0,
            temperature_c=20.0,
            altitude_m=100.0,
            obstacles_density=0.3
        )
        
        mission_plan = await mission_planner.create_mission_plan(
            mission_type=MissionType.MISSING_PERSON,
            priority=MissionPriority.HIGH,
            search_area=search_area,
            available_drones=available_drones,
            environmental_conditions=environmental_conditions,
            mission_requirements={"travel_distance_km": 2.0},
            created_by="mission_commander"
        )
        
        # Send mission start notification
        await notification_service.create_from_template(
            "mission_started",
            {
                "mission_id": mission_plan.mission_id,
                "mission_name": f"Missing Person Search {mission_plan.mission_id[:8]}",
                "drone_count": len(mission_plan.drone_assignments)
            }
        )
        
        logger.info(f"Integration test: Mission {mission_plan.mission_id} created")
    
    # Wait for notifications to be processed
    await asyncio.sleep(2)
    
    # Get final stats
    fleet_summary = await drone_manager.get_fleet_summary()
    notification_stats = await notification_service.get_notification_stats()
    
    logger.info(f"Final fleet summary: {fleet_summary}")
    logger.info(f"Final notification stats: {notification_stats}")
    
    logger.info("Integration test completed ✓")


async def main():
    """Run all tests"""
    logger.info("Starting SAR drone backend services tests...")
    
    try:
        await test_area_calculator()
        await test_mission_planner()
        await test_drone_manager()
        await test_notification_service()
        await test_integration()
        
        logger.info("All tests completed successfully! ✅")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)