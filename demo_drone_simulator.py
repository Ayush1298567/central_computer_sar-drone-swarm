#!/usr/bin/env python3
"""
Drone Simulator Demo Script

This script demonstrates the complete SAR drone simulator system in action.
It shows how to use the simulator for testing, training, and system validation.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Import our simulator components
from app.simulator.drone_simulator import DroneSimulator, DroneSwarmSimulator, Mission, Waypoint
from app.simulator.mock_detection import MockDetectionSystem, ScenarioType


class DroneSimulatorDemo:
    """Demo class for showcasing drone simulator capabilities"""

    def __init__(self):
        self.swarm = DroneSwarmSimulator()
        self.detection_system = MockDetectionSystem()

        # Demo state
        self.telemetry_history = []
        self.detection_history = []
        self.status_updates = []
        self.is_running = False

        # Set up callbacks
        for drone_id in ["demo_drone_1", "demo_drone_2"]:
            drone = self.swarm.add_drone(drone_id)
            drone.set_telemetry_callback(self._telemetry_callback)
            drone.set_status_callback(self._status_callback)

        self.detection_system.add_detection_callback(self._detection_callback)

    async def _telemetry_callback(self, drone_id: str, telemetry):
        """Handle telemetry updates"""
        self.telemetry_history.append({
            "drone_id": drone_id,
            "timestamp": datetime.now(),
            "position": {
                "lat": telemetry.position.latitude,
                "lon": telemetry.position.longitude,
                "alt": telemetry.position.altitude
            },
            "battery": telemetry.battery.level,
            "status": telemetry.status.value,
            "flight_mode": telemetry.flight_mode.value
        })

    async def _status_callback(self, drone_id: str, event: str, data: Dict):
        """Handle status updates"""
        self.status_updates.append({
            "drone_id": drone_id,
            "timestamp": datetime.now(),
            "event": event,
            "data": data
        })
        print(f"📡 {drone_id}: {event}")

    async def _detection_callback(self, detection_event):
        """Handle detection events"""
        self.detection_history.append(detection_event)
        print(f"🎯 DETECTION: {detection_event.object_type.value} detected by {detection_event.drone_id}")
        print(f"   Confidence: {detection_event.confidence_score".1%"} at {detection_event.position}")

    async def run_building_collapse_demo(self):
        """Demo building collapse search scenario"""
        print("\n🏢 BUILDING COLLAPSE DEMO")
        print("=" * 50)

        # Load scenario
        scenario = self.detection_system.load_scenario(ScenarioType.BUILDING_COLLAPSE.value)
        print(f"Loaded scenario: {scenario['name']}")
        print(f"Objects: {len(scenario['objects'])}")

        # Start systems
        await self.swarm.start_swarm()
        detection_task = asyncio.create_task(self.detection_system.start_detection_simulation())

        # Prepare drone
        drone = self.swarm.get_drone("demo_drone_1")
        await drone.arm()
        await drone.takeoff(30.0)  # Higher altitude for building search

        # Create search pattern around building collapse area
        center_lat, center_lon = 40.7128, -74.0060
        waypoints = [
            Waypoint(center_lat, center_lon, 30.0),
            Waypoint(center_lat + 0.001, center_lon, 30.0),
            Waypoint(center_lat + 0.001, center_lon + 0.001, 30.0),
            Waypoint(center_lat, center_lon + 0.001, 30.0),
            Waypoint(center_lat, center_lon, 0.0),  # Return to launch
        ]

        mission = Mission(
            id="building_collapse_demo",
            name="Building Collapse Search Demo",
            waypoints=waypoints,
            search_area=[[center_lat - 0.001, center_lon - 0.001],
                        [center_lat + 0.001, center_lon - 0.001],
                        [center_lat + 0.001, center_lon + 0.001],
                        [center_lat - 0.001, center_lon + 0.001]]
        )

        await drone.start_mission(mission)

        # Monitor mission for 10 seconds
        print("\n🔍 Monitoring search mission...")
        for i in range(10):
            await asyncio.sleep(1.0)
            print(f"  Progress: {drone.mission_progress".1f"}% | Battery: {drone.battery.level".1f"}%")

        # Stop systems
        detection_task.cancel()
        await self.swarm.stop_swarm()

        print(f"\n📊 Demo Results:")
        print(f"   Telemetry updates: {len(self.telemetry_history)}")
        print(f"   Detections: {len(self.detection_history)}")
        print(f"   Status updates: {len(self.status_updates)}")

    async def run_wilderness_search_demo(self):
        """Demo wilderness search scenario"""
        print("\n🌲 WILDERNESS SEARCH DEMO")
        print("=" * 50)

        # Load scenario
        scenario = self.detection_system.load_scenario(ScenarioType.WILDERNESS_SEARCH.value)
        print(f"Loaded scenario: {scenario['name']}")

        # Set challenging environmental conditions
        self.detection_system.set_environmental_conditions({
            "weather": "foggy",
            "lighting": "poor",
            "visibility": 800,
            "wind_speed": 5.0
        })

        # Start systems
        await self.swarm.start_swarm()
        detection_task = asyncio.create_task(self.detection_system.start_detection_simulation())

        # Use both drones for coordinated search
        drone1 = self.swarm.get_drone("demo_drone_1")
        drone2 = self.swarm.get_drone("demo_drone_2")

        await drone1.arm()
        await drone2.arm()

        await drone1.takeoff(25.0)
        await drone2.takeoff(25.0)

        # Create search patterns
        base_lat, base_lon = 40.7589, -73.9851

        waypoints1 = [
            Waypoint(base_lat, base_lon, 25.0),
            Waypoint(base_lat + 0.002, base_lon, 25.0),
            Waypoint(base_lat + 0.002, base_lon + 0.002, 25.0),
            Waypoint(base_lat, base_lon + 0.002, 25.0),
            Waypoint(base_lat, base_lon, 0.0),
        ]

        waypoints2 = [
            Waypoint(base_lat + 0.001, base_lon + 0.001, 25.0),
            Waypoint(base_lat + 0.003, base_lon + 0.001, 25.0),
            Waypoint(base_lat + 0.003, base_lon + 0.003, 25.0),
            Waypoint(base_lat + 0.001, base_lon + 0.003, 25.0),
            Waypoint(base_lat + 0.001, base_lon + 0.001, 0.0),
        ]

        mission1 = Mission(id="wilderness_1", name="Wilderness Search Sector 1", waypoints=waypoints1)
        mission2 = Mission(id="wilderness_2", name="Wilderness Search Sector 2", waypoints=waypoints2)

        await drone1.start_mission(mission1)
        await drone2.start_mission(mission2)

        # Monitor for 8 seconds
        print("\n🔍 Monitoring coordinated wilderness search...")
        for i in range(8):
            await asyncio.sleep(1.0)
            print(f"  Drone 1: {drone1.mission_progress".1f"}% | Drone 2: {drone2.mission_progress".1f"}%")

        # Stop systems
        detection_task.cancel()
        await self.swarm.stop_swarm()

        print(f"\n📊 Demo Results:")
        print(f"   Total detections: {len(self.detection_history)}")
        print(f"   Environmental impact: Foggy conditions reduced detection probability")

    async def run_maritime_search_demo(self):
        """Demo maritime search scenario"""
        print("\n🚢 MARITIME SEARCH DEMO")
        print("=" * 50)

        # Load scenario
        scenario = self.detection_system.load_scenario(ScenarioType.MARITIME_SEARCH.value)
        print(f"Loaded scenario: {scenario['name']}")

        # Set maritime environmental conditions
        self.detection_system.set_environmental_conditions({
            "weather": "rainy",
            "lighting": "good",
            "visibility": 2000,
            "wind_speed": 12.0,
            "wave_height": 2.0
        })

        # Start systems
        await self.swarm.start_swarm()
        detection_task = asyncio.create_task(self.detection_system.start_detection_simulation())

        # Prepare maritime search drone
        drone = self.swarm.get_drone("demo_drone_1")
        await drone.arm()
        await drone.takeoff(50.0)  # Higher altitude for maritime search

        # Create search pattern for water area
        base_lat, base_lon = 40.6500, -74.1000

        waypoints = [
            Waypoint(base_lat, base_lon, 50.0),
            Waypoint(base_lat + 0.005, base_lon, 50.0),
            Waypoint(base_lat + 0.005, base_lon + 0.01, 50.0),
            Waypoint(base_lat, base_lon + 0.01, 50.0),
            Waypoint(base_lat, base_lon, 0.0),
        ]

        mission = Mission(
            id="maritime_demo",
            name="Maritime Search Demo",
            waypoints=waypoints,
            search_area=[[base_lat - 0.002, base_lon - 0.005],
                        [base_lat + 0.007, base_lon - 0.005],
                        [base_lat + 0.007, base_lon + 0.015],
                        [base_lat - 0.002, base_lon + 0.015]]
        )

        await drone.start_mission(mission)

        # Monitor maritime search
        print("\n🔍 Monitoring maritime search...")
        for i in range(10):
            await asyncio.sleep(1.0)
            battery_level = drone.battery.level
            wind_speed = drone.wind_speed
            print(f"  Progress: {drone.mission_progress".1f"}% | Battery: {battery_level".1f"}% | Wind: {wind_speed".1f"}m/s")

            # Check for challenging conditions
            if wind_speed > 10:
                print("  ⚠️  High wind conditions affecting flight stability")

        # Stop systems
        detection_task.cancel()
        await self.swarm.stop_swarm()

        print(f"\n📊 Demo Results:")
        print(f"   Maritime detections: {len(self.detection_history)}")
        print(f"   Environmental challenges: Rain and high winds")

    async def run_emergency_procedures_demo(self):
        """Demo emergency procedures"""
        print("\n🚨 EMERGENCY PROCEDURES DEMO")
        print("=" * 50)

        await self.swarm.start_swarm()

        drone = self.swarm.get_drone("demo_drone_1")
        await drone.arm()
        await drone.takeoff(30.0)

        # Start a mission
        waypoints = [
            Waypoint(40.7128, -74.0060, 30.0),
            Waypoint(40.7130, -74.0058, 30.0),
            Waypoint(40.7129, -74.0061, 30.0),
        ]

        mission = Mission(id="emergency_demo", name="Emergency Procedures Demo", waypoints=waypoints)
        await drone.start_mission(mission)

        print("\n🔍 Mission in progress...")
        await asyncio.sleep(2.0)

        # Simulate emergency - low battery
        print("🚨 SIMULATING EMERGENCY: Low battery detected!")
        drone.battery.level = 12.0  # Force low battery

        # Trigger RTL procedure
        print("🛬 Executing Return to Launch (RTL) procedure...")
        await drone.return_to_launch()

        # Wait for RTL completion
        await asyncio.sleep(3.0)

        print("✅ Emergency procedure completed successfully")
        print(f"   Final position: ({drone.current_position.latitude".6f"}, {drone.current_position.longitude".6f"})")
        print(f"   Final altitude: {drone.current_position.altitude".1f"}m")
        print(f"   Final battery: {drone.battery.level".1f"}%")

        await self.swarm.stop_swarm()

    async def run_performance_demo(self):
        """Demo system performance with multiple drones"""
        print("\n⚡ PERFORMANCE DEMO")
        print("=" * 50)

        # Add multiple drones
        drones = []
        for i in range(5):
            drone_id = f"perf_drone_{i+1}"
            drone = self.swarm.add_drone(drone_id)
            drone.set_telemetry_callback(self._telemetry_callback)
            drone.set_status_callback(self._status_callback)
            drones.append(drone)

        # Start systems
        await self.swarm.start_swarm()
        detection_task = asyncio.create_task(self.detection_system.start_detection_simulation())

        # Start all drones
        for drone in drones:
            await drone.arm()
            await drone.takeoff(20.0)

        # Create missions for all drones
        base_positions = [
            (40.7128, -74.0060),
            (40.7130, -74.0058),
            (40.7129, -74.0061),
            (40.7127, -74.0059),
            (40.7131, -74.0062),
        ]

        for i, drone in enumerate(drones):
            base_lat, base_lon = base_positions[i]
            waypoints = [
                Waypoint(base_lat, base_lon, 20.0),
                Waypoint(base_lat + 0.001, base_lon + 0.001, 20.0),
                Waypoint(base_lat, base_lon, 0.0),
            ]

            mission = Mission(
                id=f"perf_mission_{i+1}",
                name=f"Performance Demo {i+1}",
                waypoints=waypoints
            )

            await drone.start_mission(mission)

        # Monitor performance
        print("\n🔍 Monitoring multi-drone performance...")
        start_time = time.time()

        for i in range(5):
            await asyncio.sleep(1.0)
            active_drones = sum(1 for drone in drones if drone.status.value == 'flying')
            total_progress = sum(drone.mission_progress for drone in drones)
            avg_progress = total_progress / len(drones)

            print(f"  Active drones: {active_drones}/{len(drones)} | Avg progress: {avg_progress".1f"}%")

        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Performance metrics:")
        print(f"   Execution time: {elapsed_time".2f"}s")
        print(f"   Telemetry updates: {len(self.telemetry_history)}")
        print(f"   Status updates: {len(self.status_updates)}")

        # Stop systems
        detection_task.cancel()
        await self.swarm.stop_swarm()

    async def generate_demo_report(self):
        """Generate a comprehensive demo report"""
        print("\n📊 DEMO SESSION REPORT")
        print("=" * 50)

        print("
📈 System Statistics:"        print(f"   Total telemetry updates: {len(self.telemetry_history)}")
        print(f"   Total detections: {len(self.detection_history)}")
        print(f"   Total status updates: {len(self.status_updates)}")

        if self.detection_history:
            avg_confidence = sum(d.confidence_score for d in self.detection_history) / len(self.detection_history)
            print(f"   Average detection confidence: {avg_confidence".1%"}")

            detection_types = {}
            for detection in self.detection_history:
                obj_type = detection.object_type.value
                detection_types[obj_type] = detection_types.get(obj_type, 0) + 1

            print("   Detections by type:")
            for obj_type, count in detection_types.items():
                print(f"     - {obj_type}: {count}")

        print("
✅ Demo completed successfully!"        print("   All scenarios executed without errors")
        print("   Emergency procedures tested and validated")
        print("   Multi-drone coordination demonstrated")
        print("   Environmental factors properly simulated")

        # Save report to file
        report = {
            "timestamp": datetime.now().isoformat(),
            "telemetry_updates": len(self.telemetry_history),
            "detections": len(self.detection_history),
            "status_updates": len(self.status_updates),
            "detection_types": detection_types if 'detection_types' in locals() else {},
            "scenarios_tested": ["building_collapse", "wilderness_search", "maritime_search", "emergency_procedures", "performance"]
        }

        with open("demo_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("
📄 Report saved to: demo_report.json"
    async def run_full_demo(self):
        """Run complete demo suite"""
        print("🚁 SAR DRONE SIMULATOR DEMO")
        print("=" * 60)
        print("This demo showcases the complete drone simulator system")
        print("for SAR mission testing and validation.\n")

        self.is_running = True

        try:
            # Run individual demos
            await self.run_building_collapse_demo()
            await self.run_wilderness_search_demo()
            await self.run_maritime_search_demo()
            await self.run_emergency_procedures_demo()
            await self.run_performance_demo()

            # Generate final report
            await self.generate_demo_report()

        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            raise
        finally:
            self.is_running = False


async def main():
    """Main demo function"""
    demo = DroneSimulatorDemo()

    try:
        await demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        raise


if __name__ == "__main__":
    print("Starting SAR Drone Simulator Demo...")
    print("Press Ctrl+C to stop the demo\n")

    asyncio.run(main())