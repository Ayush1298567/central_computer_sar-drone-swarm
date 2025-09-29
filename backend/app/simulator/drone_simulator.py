"""
Drone simulator for testing and development.
"""

import asyncio
import logging
import math
import random
import time
from typing import Dict, List, Optional
from datetime import datetime
from ..models import Drone, Mission
from ..services import drone_manager, notification_service

logger = logging.getLogger(__name__)


class DroneSimulator:
    """Simulates drone behavior for testing and development."""

    def __init__(self):
        self.simulated_drones: Dict[int, Dict] = {}
        self.simulation_active = False
        self.simulation_speed = 1.0  # 1x real-time

    def start_simulation(self, mission: Mission, drones: List[Drone]):
        """Start simulating a mission with the given drones."""
        self.simulation_active = True

        logger.info(f"Starting drone simulation for mission: {mission.name}")

        # Initialize simulated drones
        for drone in drones:
            self.simulated_drones[drone.id] = {
                "drone": drone,
                "mission": mission,
                "current_position": {
                    "lat": drone.current_lat or mission.center_lat,
                    "lng": drone.current_lng or mission.center_lng,
                    "altitude": 0.0
                },
                "target_position": None,
                "flight_path": [],
                "status": "ready",
                "battery_level": 100.0,
                "speed": 0.0,
                "heading": 0.0
            }

        # Start simulation loop
        asyncio.create_task(self._simulation_loop())

    def stop_simulation(self):
        """Stop the current simulation."""
        self.simulation_active = False
        self.simulated_drones.clear()
        logger.info("Drone simulation stopped")

    async def _simulation_loop(self):
        """Main simulation loop running drone behaviors."""
        while self.simulation_active and self.simulated_drones:
            try:
                # Update each simulated drone
                for drone_id, sim_data in self.simulated_drones.items():
                    await self._update_drone_simulation(drone_id, sim_data)

                # Broadcast updates via WebSocket
                await self._broadcast_simulation_updates()

                # Wait before next update
                await asyncio.sleep(1.0 / self.simulation_speed)

            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                break

        self.simulation_active = False

    async def _update_drone_simulation(self, drone_id: int, sim_data: Dict):
        """Update a single drone's simulation state."""
        drone = sim_data["drone"]
        mission = sim_data["mission"]

        # Update battery level
        sim_data["battery_level"] = max(0, sim_data["battery_level"] - 0.1)

        # Update position if flying
        if sim_data["status"] == "flying":
            await self._simulate_flight(drone_id, sim_data)

        # Check for discoveries
        await self._simulate_discovery_detection(drone_id, sim_data)

        # Update drone manager with current state
        telemetry = {
            "position": sim_data["current_position"],
            "attitude": {
                "heading": sim_data["heading"],
                "speed": sim_data["speed"]
            },
            "battery": {
                "level": sim_data["battery_level"]
            },
            "status": sim_data["status"]
        }

        drone_manager.update_drone_telemetry(drone_id, telemetry)

    async def _simulate_flight(self, drone_id: int, sim_data: Dict):
        """Simulate drone flight physics."""
        current_pos = sim_data["current_position"]
        target_pos = sim_data["target_position"]

        if not target_pos:
            # Generate a random waypoint within mission area
            mission = sim_data["mission"]
            target_pos = {
                "lat": mission.center_lat + (random.random() - 0.5) * 0.01,
                "lng": mission.center_lng + (random.random() - 0.5) * 0.01,
                "altitude": mission.search_altitude + (random.random() - 0.5) * 10
            }
            sim_data["target_position"] = target_pos

        # Calculate movement toward target
        lat_diff = target_pos["lat"] - current_pos["lat"]
        lng_diff = target_pos["lng"] - current_pos["lng"]
        alt_diff = target_pos["altitude"] - current_pos["altitude"]

        # Simple movement simulation
        move_speed = 0.0001  # Degrees per second
        sim_data["speed"] = min(15.0, math.sqrt(lat_diff**2 + lng_diff**2) * 1000)

        # Update position
        if abs(lat_diff) > 0.00001:
            current_pos["lat"] += lat_diff * 0.1
        if abs(lng_diff) > 0.00001:
            current_pos["lng"] += lng_diff * 0.1
        if abs(alt_diff) > 1:
            current_pos["altitude"] += alt_diff * 0.1

        # Check if target reached
        distance_to_target = math.sqrt(lat_diff**2 + lng_diff**2 + (alt_diff/100)**2)
        if distance_to_target < 0.0001:
            sim_data["target_position"] = None

    async def _simulate_discovery_detection(self, drone_id: int, sim_data: Dict):
        """Simulate AI discovery detection."""
        # 1% chance per second to detect something
        if random.random() < 0.01:
            mission = sim_data["mission"]
            current_pos = sim_data["current_position"]

            # Generate random discovery type
            discovery_types = ["person", "vehicle", "debris", "structure"]
            discovery_type = random.choice(discovery_types)

            # Create discovery alert
            discovery_data = {
                "mission_id": mission.id,
                "drone_id": drone_id,
                "lat": current_pos["lat"],
                "lng": current_pos["lng"],
                "altitude": current_pos["altitude"],
                "discovery_type": discovery_type,
                "confidence": round(random.uniform(0.6, 0.95), 2),
                "description": f"Simulated {discovery_type} detection",
                "category": "human" if discovery_type == "person" else "other",
                "status": "new",
                "priority": random.choice(["low", "normal", "high"]),
                "response_required": discovery_type == "person"
            }

            # Send discovery alert via notification service
            notification_service.discovery_alert(
                discovery_type=discovery_type,
                location=f"{current_pos['lat']:.4f}, {current_pos['lng']:.4f}",
                priority=discovery_data["priority"],
                mission_id=mission.id
            )

            logger.info(f"Simulated discovery detected: {discovery_type} at mission {mission.name}")

    async def _broadcast_simulation_updates(self):
        """Broadcast simulation updates to connected clients."""
        # This would integrate with the WebSocket service to send real-time updates
        # For now, just log the updates
        for drone_id, sim_data in self.simulated_drones.items():
            current_pos = sim_data["current_position"]
            logger.debug(f"Drone {drone_id} position: {current_pos['lat']:.4f}, {current_pos['lng']:.4f}, alt: {current_pos['altitude']:.1f}m")

    def get_simulation_status(self) -> Dict:
        """Get current simulation status."""
        return {
            "active": self.simulation_active,
            "simulated_drones": len(self.simulated_drones),
            "simulation_speed": self.simulation_speed,
            "drones": [
                {
                    "id": drone_id,
                    "name": sim_data["drone"].name,
                    "position": sim_data["current_position"],
                    "status": sim_data["status"],
                    "battery": sim_data["battery_level"]
                }
                for drone_id, sim_data in self.simulated_drones.items()
            ]
        }


# Global instance
drone_simulator = DroneSimulator()