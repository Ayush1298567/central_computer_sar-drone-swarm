#!/usr/bin/env python3
"""
Test script for Advanced Backend Services (Session 11).

Tests the four main services implemented in Session 11:
1. HybridCoordinationEngine
2. MissionAnalyticsEngine
3. EmergencyResponseSystem
4. BackgroundTaskSystem

This script demonstrates the functionality of each service with realistic scenarios.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Import services directly
from app.services.coordination_engine import HybridCoordinationEngine, CoordinationCommand, CommandType, Priority
from app.services.analytics_engine import MissionAnalyticsEngine, EventType
from app.services.emergency_service import EmergencyResponseManager, EmergencyType, EmergencySeverity, GeofenceZone
from app.services.task_manager import BackgroundTaskManager, TaskType, TaskPriority

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_hybrid_coordination_engine():
    """Test the HybridCoordinationEngine with simulated drone scenarios."""
    logger.info("=== Testing HybridCoordinationEngine ===")

    # Initialize coordination engine
    coordination_engine = HybridCoordinationEngine()

    # Initialize the engine
    await coordination_engine.initialize()

    # Test scenario: Multiple drones with various conditions
    mission_state = {
        "mission_id": "test_mission_001",
        "status": "active",
        "drones": [
            {
                "id": "drone_001",
                "battery_level": 15,  # Low battery
                "signal_strength": 85,
                "area_progress": 95,
                "current_position": {"lat": 40.7128, "lng": -74.0060, "alt": 30}
            },
            {
                "id": "drone_002",
                "battery_level": 75,
                "signal_strength": 25,  # Weak signal
                "area_progress": 60,
                "current_position": {"lat": 40.7130, "lng": -74.0058, "alt": 25}
            },
            {
                "id": "drone_003",
                "battery_level": 90,
                "signal_strength": 95,
                "area_progress": 30,
                "current_position": {"lat": 40.7125, "lng": -74.0062, "alt": 35}
            }
        ],
        "discoveries": [
            {
                "id": "disc_001",
                "object_type": "person",
                "confidence_score": 0.85,
                "latitude": 40.7129,
                "longitude": -74.0061
            }
        ],
        "weather": {
            "wind_speed": 12,  # Moderate wind
            "temperature": 22,
            "visibility": 8
        },
        "emergency_situation": False
    }

    # Generate coordination commands
    commands = await coordination_engine.coordinate_drones(mission_state)

    logger.info(f"Generated {len(commands)} coordination commands:")

    for command in commands:
        logger.info(f"  - {command.drone_id}: {command.command_type.value} (Priority: {command.priority.value}) - {command.reason}")

    # Test command execution tracking
    if commands:
        first_command = commands[0]
        coordination_engine.mark_command_executed(first_command.drone_id, first_command.command_type)

    # Get system status
    status = coordination_engine.get_system_status()
    logger.info(f"Coordination engine status: {status}")

    return len(commands) > 0

async def test_mission_analytics_engine():
    """Test the MissionAnalyticsEngine with sample mission data."""
    logger.info("=== Testing MissionAnalyticsEngine ===")

    # Initialize analytics engine
    analytics_engine = MissionAnalyticsEngine()

    # Create sample mission data
    mission_id = "test_mission_analytics_001"

    # Log various mission events
    events_data = [
        (EventType.MISSION_START, None, {"description": "Mission started"}),
        (EventType.DRONE_ASSIGNMENT, "drone_001", {"area_id": "area_001"}),
        (EventType.DRONE_TAKEOFF, "drone_001", {"altitude": 30}),
        (EventType.DISCOVERY, "drone_001", {"object_type": "person", "confidence": 0.85}),
        (EventType.INVESTIGATION_START, "drone_001", {"investigation_id": "inv_001"}),
        (EventType.INVESTIGATION_END, "drone_001", {"investigation_id": "inv_001", "outcome": "successful"}),
        (EventType.DRONE_LANDING, "drone_001", {"flight_time": 45}),
        (EventType.MISSION_END, None, {"total_duration": 60})
    ]

    for event_type, drone_id, event_data in events_data:
        analytics_engine.log_mission_event(
            event_type=event_type,
            mission_id=mission_id,
            drone_id=drone_id,
            event_data=event_data
        )

    # Store mission summary
    analytics_engine.database.store_mission_summary(mission_id, {
        "estimated_duration": 50,
        "search_area": {
            "type": "polygon",
            "coordinates": [
                [40.7120, -74.0070],
                [40.7140, -74.0070],
                [40.7140, -74.0050],
                [40.7120, -74.0050],
                [40.7120, -74.0070]
            ]
        }
    })

    # Analyze mission performance
    try:
        analysis = analytics_engine.analyze_mission_performance(mission_id)

        logger.info(f"Mission Analysis Results:")
        logger.info(f"  Overall Score: {analysis.overall_score:.2f}")
        logger.info(f"  Duration Efficiency: {analysis.duration_analysis.get('duration_efficiency', 0):.1f}%")
        logger.info(f"  Coverage Efficiency: {analysis.coverage_efficiency.get('coverage_percentage', 0):.1f}%")
        logger.info(f"  Discovery Effectiveness: {analysis.discovery_effectiveness.get('investigation_success_rate', 0):.1f}%")
        logger.info(f"  Resource Efficiency: {analysis.resource_utilization.get('resource_efficiency', 0):.2f}")
        logger.info(f"  Decision Quality: {analysis.decision_quality.get('decision_success_rate', 0):.1f}%")

        # Test recommendations
        recommendations = analysis.recommendations
        logger.info(f"Generated {len(recommendations)} recommendations:")
        for rec in recommendations[:3]:  # Show first 3
            logger.info(f"  - {rec}")

        # Test mission replay
        replay = analytics_engine.create_mission_replay(mission_id)
        logger.info(f"Mission replay contains {len(replay.get('mission_timeline', []))} timeline events")

        return True

    except Exception as e:
        logger.error(f"Analytics test failed: {e}")
        return False

async def test_emergency_response_system():
    """Test the EmergencyResponseSystem with simulated emergency scenarios."""
    logger.info("=== Testing EmergencyResponseSystem ===")

    # Initialize emergency manager
    emergency_manager = EmergencyResponseManager()

    # Add a geofence zone
    geofence = GeofenceZone(
        zone_id="test_no_fly_zone",
        name="Test No-Fly Zone",
        zone_type="no_fly",
        coordinates=[
            (40.7100, -74.0100),
            (40.7150, -74.0100),
            (40.7150, -74.0000),
            (40.7100, -74.0000)
        ],
        restrictions=["No drone operations allowed"]
    )
    emergency_manager.add_geofence_zone(geofence)

    # Test 1: Battery critical emergency
    logger.info("Testing battery critical emergency...")
    emergency_event = await emergency_manager.declare_emergency(
        emergency_type=EmergencyType.BATTERY_CRITICAL,
        description="Drone battery level critically low at 8%",
        affected_drones=["drone_001"],
        location={"lat": 40.7128, "lng": -74.0060, "alt": 30}
    )

    logger.info(f"Emergency declared: {emergency_event.event_id}")
    logger.info(f"Severity: {emergency_event.severity.value}")
    logger.info(f"Protocols applied: {len(emergency_event.protocols_applied)}")

    # Test 2: Geofence violation detection
    logger.info("Testing geofence violation detection...")
    drone_positions = {
        "drone_001": {"lat": 40.7125, "lng": -74.0050, "alt": 30},  # Inside no-fly zone
        "drone_002": {"lat": 40.7200, "lng": -74.0060, "alt": 25}   # Outside zone
    }

    violations = emergency_manager.check_geofence_violations(drone_positions)
    logger.info(f"Found {len(violations)} geofence violations")

    for violation in violations:
        logger.info(f"  - {violation['drone_id']}: {violation['zone_type']} zone violation")

    # Test 3: Mission safety validation
    logger.info("Testing mission safety validation...")
    mission_plan = {
        "weather_conditions": {
            "wind_speed": 18,  # High wind
            "visibility": 0.5   # Low visibility
        },
        "search_area": {
            "coordinates": [
                [40.7100, -74.0100],
                [40.7200, -74.0100],
                [40.7200, -74.0000],
                [40.7100, -74.0000]
            ]
        },
        "drone_assignments": [
            {
                "drone_id": "drone_001",
                "assigned_area": {
                    "coordinates": [
                        [40.7110, -74.0080],
                        [40.7130, -74.0080],
                        [40.7130, -74.0060],
                        [40.7110, -74.0060]
                    ]
                }
            }
        ]
    }

    safety_result = emergency_manager.validate_mission_safety(mission_plan)
    logger.info(f"Mission safety status: {safety_result['overall_status']}")
    logger.info(f"Issues found: {len(safety_result['issues'])}")
    logger.info(f"Warnings: {len(safety_result['warnings'])}")

    for issue in safety_result['issues']:
        logger.info(f"  - Issue: {issue}")

    for warning in safety_result['warnings']:
        logger.info(f"  - Warning: {warning}")

    # Test 4: Emergency resolution
    logger.info("Testing emergency resolution...")
    emergency_manager.resolve_emergency(
        emergency_event.event_id,
        "Battery replaced, drone returned to service"
    )

    # Get system status
    status = emergency_manager.get_emergency_status()
    logger.info(f"Emergency system status: {status}")

    return len(violations) > 0 or len(safety_result['issues']) > 0

async def test_background_task_system():
    """Test the BackgroundTaskSystem with various task scenarios."""
    logger.info("=== Testing BackgroundTaskSystem ===")

    # Initialize task manager
    task_manager = BackgroundTaskManager()

    # Start the task manager
    task_manager.start()

    try:
        # Test 1: Schedule default recurring tasks
        logger.info("Scheduling default recurring tasks...")
        scheduled_tasks = task_manager.schedule_default_tasks()
        logger.info(f"Scheduled {len(scheduled_tasks)} recurring tasks")

        # Wait a moment for tasks to be processed
        await asyncio.sleep(2)

        # Test 2: Schedule a custom immediate task
        logger.info("Scheduling immediate health check...")
        task_id = task_manager.force_task_execution(
            TaskType.HEALTH_CHECK
        )
        logger.info(f"Scheduled immediate task: {task_id}")

        # Test 3: Schedule a delayed task
        logger.info("Scheduling delayed data cleanup...")
        delayed_task_id = task_manager.schedule_task(
            task_type=TaskType.DATA_CLEANUP,
            name="Test Data Cleanup",
            description="Test cleanup operation",
            scheduled_time=datetime.utcnow() + timedelta(minutes=1),
            priority=TaskPriority.LOW
        )
        logger.info(f"Scheduled delayed task: {delayed_task_id}")

        # Test 4: Get queue status
        queue_status = task_manager.get_queue_status()
        logger.info(f"Queue status: {queue_status}")

        # Test 5: Get task status
        task_status = task_manager.get_task_status(task_id)
        if task_status:
            logger.info(f"Task {task_id} status: {task_status['status']}")

        # Test 6: Cancel a task
        logger.info("Testing task cancellation...")
        cancelled = task_manager.cancel_task(delayed_task_id)
        logger.info(f"Task cancellation {'successful' if cancelled else 'failed'}")

        # Wait for some tasks to complete
        await asyncio.sleep(5)

        # Test 7: Cleanup old tasks
        logger.info("Testing task cleanup...")
        cleaned_count = task_manager.cleanup_completed_tasks(max_age_hours=1)
        logger.info(f"Cleaned up {cleaned_count} old tasks")

        # Get final system status
        system_status = task_manager.get_system_status()
        logger.info(f"Final system status: {system_status}")

        return True

    finally:
        # Stop the task manager
        task_manager.stop()

async def run_all_tests():
    """Run all service tests."""
    logger.info("Starting Advanced Backend Services Test Suite")
    logger.info("=" * 60)

    test_results = []

    try:
        # Test each service
        test_results.append(await test_hybrid_coordination_engine())
        test_results.append(await test_mission_analytics_engine())
        test_results.append(await test_emergency_response_system())
        test_results.append(await test_background_task_system())

        # Summary
        passed = sum(test_results)
        total = len(test_results)

        logger.info("=" * 60)
        logger.info(f"Test Results: {passed}/{total} services passed")

        if passed == total:
            logger.info("✅ All services functioning correctly!")
            return True
        else:
            logger.error("❌ Some services failed testing")
            return False

    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        return False

async def main():
    """Main test function."""
    success = await run_all_tests()

    if success:
        logger.info("🎉 All advanced backend services tests completed successfully!")
        return 0
    else:
        logger.error("💥 Some tests failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    # Run the tests
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)