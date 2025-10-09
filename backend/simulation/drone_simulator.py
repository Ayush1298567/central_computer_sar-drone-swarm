"""
Drone Simulator
Simulates realistic drone behavior for SAR operations
"""

import asyncio
import json
import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from ..services.redis_service import RedisService
from ..services.websocket_manager import WebSocketManager
from ..services.database import db_service

logger = logging.getLogger(__name__)

class DroneSimulator:
    """Simulates realistic drone behavior"""
    
    def __init__(self, redis_service: RedisService, websocket_manager: WebSocketManager):
        self.redis_service = redis_service
        self.websocket_manager = websocket_manager
        self.active_drones: Dict[int, Dict[str, Any]] = {}
        self.drone_tasks: Dict[int, asyncio.Task] = {}
        self._running = False
        self.base_position = {"lat": 37.7749, "lng": -122.4194, "alt": 0}  # San Francisco base
    
    async def start(self) -> None:
        """Start the drone simulator"""
        self._running = True
        logger.info("Drone simulator started")
    
    async def stop(self) -> None:
        """Stop the drone simulator"""
        self._running = False
        
        # Cancel all drone tasks
        for task in self.drone_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.drone_tasks:
            await asyncio.gather(*self.drone_tasks.values(), return_exceptions=True)
        
        self.drone_tasks.clear()
        self.active_drones.clear()
        logger.info("Drone simulator stopped")
    
    def is_running(self) -> bool:
        """Check if simulator is running"""
        return self._running
    
    async def add_drone(self, drone_id: int, name: str, capabilities: Dict[str, Any], 
                       battery_capacity: int = 5000) -> None:
        """Add a new drone to simulation"""
        if drone_id in self.active_drones:
            logger.warning(f"Drone {drone_id} already exists")
            return
        
        # Initialize drone state
        self.active_drones[drone_id] = {
            "id": drone_id,
            "name": name,
            "capabilities": capabilities,
            "battery_capacity": battery_capacity,
            "battery_percent": 100,
            "position": self.base_position.copy(),
            "target_position": self.base_position.copy(),
            "heading": 0,
            "speed": 0,
            "max_speed": 15,  # m/s
            "status": "idle",
            "mission_id": None,
            "assignment": None,
            "waypoints": [],
            "current_waypoint": 0,
            "coverage_progress": 0.0,
            "last_telemetry": asyncio.get_event_loop().time(),
            "discoveries": [],
            "flight_time": 0,
            "total_distance": 0.0
        }
        
        # Start drone simulation task
        self.drone_tasks[drone_id] = asyncio.create_task(
            self._simulate_drone(drone_id)
        )
        
        logger.info(f"Added drone {drone_id} ({name}) to simulation")
    
    async def remove_drone(self, drone_id: int) -> None:
        """Remove drone from simulation"""
        if drone_id not in self.active_drones:
            return
        
        # Cancel drone task
        if drone_id in self.drone_tasks:
            self.drone_tasks[drone_id].cancel()
            try:
                await self.drone_tasks[drone_id]
            except asyncio.CancelledError:
                pass
            del self.drone_tasks[drone_id]
        
        # Remove from active drones
        del self.active_drones[drone_id]
        
        logger.info(f"Removed drone {drone_id} from simulation")
    
    async def assign_mission(self, drone_id: int, assignment: Dict[str, Any]) -> None:
        """Assign mission to drone"""
        if drone_id not in self.active_drones:
            logger.error(f"Drone {drone_id} not found")
            return
        
        drone = self.active_drones[drone_id]
        drone["assignment"] = assignment
        drone["mission_id"] = assignment.get("mission_id")
        drone["waypoints"] = assignment.get("waypoints", [])
        drone["current_waypoint"] = 0
        drone["coverage_progress"] = 0.0
        drone["status"] = "assigned"
        
        logger.info(f"Assigned mission to drone {drone_id}")
    
    async def start_mission(self, drone_id: int) -> None:
        """Start mission for drone"""
        if drone_id not in self.active_drones:
            return
        
        drone = self.active_drones[drone_id]
        if not drone["assignment"]:
            logger.warning(f"No assignment for drone {drone_id}")
            return
        
        drone["status"] = "active"
        drone["flight_time"] = 0
        
        # Set first waypoint as target
        if drone["waypoints"]:
            drone["target_position"] = {
                "lat": drone["waypoints"][0]["lat"],
                "lng": drone["waypoints"][0]["lng"],
                "alt": drone["waypoints"][0]["alt"]
            }
        
        logger.info(f"Started mission for drone {drone_id}")
    
    async def pause_mission(self, drone_id: int) -> None:
        """Pause mission for drone"""
        if drone_id not in self.active_drones:
            return
        
        drone = self.active_drones[drone_id]
        if drone["status"] == "active":
            drone["status"] = "paused"
            logger.info(f"Paused mission for drone {drone_id}")
    
    async def resume_mission(self, drone_id: int) -> None:
        """Resume mission for drone"""
        if drone_id not in self.active_drones:
            return
        
        drone = self.active_drones[drone_id]
        if drone["status"] == "paused":
            drone["status"] = "active"
            logger.info(f"Resumed mission for drone {drone_id}")
    
    async def return_to_base(self, drone_id: int) -> None:
        """Return drone to base"""
        if drone_id not in self.active_drones:
            return
        
        drone = self.active_drones[drone_id]
        drone["status"] = "returning_to_base"
        drone["target_position"] = self.base_position.copy()
        drone["waypoints"] = []
        drone["current_waypoint"] = 0
        
        logger.info(f"Drone {drone_id} returning to base")
    
    async def emergency_land(self, drone_id: int) -> None:
        """Emergency land drone"""
        if drone_id not in self.active_drones:
            return
        
        drone = self.active_drones[drone_id]
        drone["status"] = "emergency_landing"
        drone["target_position"]["alt"] = 0
        drone["speed"] = 0
        
        logger.critical(f"Emergency landing drone {drone_id}")
    
    async def _simulate_drone(self, drone_id: int) -> None:
        """Main drone simulation loop"""
        try:
            while self._running and drone_id in self.active_drones:
                drone = self.active_drones[drone_id]
                
                # Update drone state
                await self._update_drone_state(drone)
                
                # Send telemetry
                await self._send_telemetry(drone)
                
                # Check for discoveries
                await self._check_discoveries(drone)
                
                # Wait before next update
                await asyncio.sleep(2)  # 2 second update interval
        
        except asyncio.CancelledError:
            logger.info(f"Drone {drone_id} simulation cancelled")
        except Exception as e:
            logger.error(f"Error simulating drone {drone_id}: {e}")
        finally:
            if drone_id in self.drone_tasks:
                del self.drone_tasks[drone_id]
    
    async def _update_drone_state(self, drone: Dict[str, Any]) -> None:
        """Update drone state based on current status"""
        if drone["status"] == "idle":
            return
        
        # Update battery
        await self._update_battery(drone)
        
        # Update position
        await self._update_position(drone)
        
        # Update mission progress
        await self._update_mission_progress(drone)
        
        # Update flight time
        drone["flight_time"] += 2  # 2 seconds per update
    
    async def _update_battery(self, drone: Dict[str, Any]) -> None:
        """Update drone battery level"""
        # Battery drain based on activity
        if drone["status"] == "active":
            drain_rate = 0.1  # 0.1% per 2 seconds
        elif drone["status"] == "returning_to_base":
            drain_rate = 0.15  # Higher drain when returning
        elif drone["status"] == "emergency_landing":
            drain_rate = 0.2  # Highest drain during emergency
        else:
            drain_rate = 0.05  # Lower drain when idle/paused
        
        # Apply battery drain
        drone["battery_percent"] = max(0, drone["battery_percent"] - drain_rate)
        
        # Handle low battery
        if drone["battery_percent"] <= 0:
            drone["status"] = "battery_critical"
        elif drone["battery_percent"] <= 10 and drone["status"] == "active":
            # Auto-return to base
            await self.return_to_base(drone["id"])
    
    async def _update_position(self, drone: Dict[str, Any]) -> None:
        """Update drone position"""
        if drone["status"] in ["idle", "paused"]:
            return
        
        current_pos = drone["position"]
        target_pos = drone["target_position"]
        
        # Calculate distance to target
        distance = self._calculate_distance(
            current_pos["lat"], current_pos["lng"],
            target_pos["lat"], target_pos["lng"]
        )
        
        # If close to target, move to next waypoint
        if distance < 5.0:  # 5 meter threshold
            await self._move_to_next_waypoint(drone)
            return
        
        # Calculate movement vector
        lat_diff = target_pos["lat"] - current_pos["lat"]
        lng_diff = target_pos["lng"] - current_pos["lng"]
        
        # Normalize and scale by speed
        if distance > 0:
            lat_step = (lat_diff / distance) * (drone["speed"] / 111000)  # Rough conversion to degrees
            lng_step = (lng_diff / distance) * (drone["speed"] / 111000)
            
            # Update position
            drone["position"]["lat"] += lat_step
            drone["position"]["lng"] += lng_step
            
            # Update altitude
            alt_diff = target_pos["alt"] - current_pos["alt"]
            if abs(alt_diff) > 1:
                alt_step = 1 if alt_diff > 0 else -1
                drone["position"]["alt"] += alt_step
            
            # Update heading
            drone["heading"] = math.degrees(math.atan2(lng_diff, lat_diff))
            
            # Update total distance
            drone["total_distance"] += self._calculate_distance(
                current_pos["lat"] - lat_step, current_pos["lng"] - lng_step,
                current_pos["lat"], current_pos["lng"]
            )
    
    async def _move_to_next_waypoint(self, drone: Dict[str, Any]) -> None:
        """Move to next waypoint in mission"""
        if not drone["waypoints"]:
            return
        
        # Move to next waypoint
        drone["current_waypoint"] += 1
        
        if drone["current_waypoint"] >= len(drone["waypoints"]):
            # Mission complete
            drone["status"] = "completed"
            drone["coverage_progress"] = 100.0
            await self._notify_mission_complete(drone)
            return
        
        # Set next waypoint as target
        next_waypoint = drone["waypoints"][drone["current_waypoint"]]
        drone["target_position"] = {
            "lat": next_waypoint["lat"],
            "lng": next_waypoint["lng"],
            "alt": next_waypoint["alt"]
        }
        
        # Update coverage progress
        drone["coverage_progress"] = (drone["current_waypoint"] / len(drone["waypoints"])) * 100
    
    async def _update_mission_progress(self, drone: Dict[str, Any]) -> None:
        """Update mission progress"""
        if not drone["assignment"]:
            return
        
        # Calculate progress based on waypoints completed
        if drone["waypoints"]:
            progress = (drone["current_waypoint"] / len(drone["waypoints"])) * 100
            drone["coverage_progress"] = min(100.0, progress)
    
    async def _check_discoveries(self, drone: Dict[str, Any]) -> None:
        """Check for discoveries during flight"""
        if drone["status"] != "active":
            return
        
        # Random chance of discovery (simplified)
        discovery_chance = 0.001  # 0.1% chance per update
        
        if random.random() < discovery_chance:
            await self._create_discovery(drone)
    
    async def _create_discovery(self, drone: Dict[str, Any]) -> None:
        """Create a discovery"""
        discovery = {
            "type": random.choice(["survivor", "hazard", "obstacle"]),
            "confidence": random.randint(60, 95),
            "position": drone["position"].copy(),
            "description": f"Possible {random.choice(['person', 'structure', 'debris'])} detected",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        drone["discoveries"].append(discovery)
        
        # Send discovery alert
        await self._send_discovery_alert(drone, discovery)
        
        logger.info(f"Drone {drone['id']} made discovery: {discovery['type']}")
    
    async def _send_telemetry(self, drone: Dict[str, Any]) -> None:
        """Send drone telemetry"""
        telemetry = {
            "drone_id": drone["id"],
            "mission_id": drone["mission_id"],
            "timestamp": asyncio.get_event_loop().time(),
            "lat": drone["position"]["lat"],
            "lng": drone["position"]["lng"],
            "alt": drone["position"]["alt"],
            "battery_percent": drone["battery_percent"],
            "status": drone["status"],
            "heading": drone["heading"],
            "speed": drone["speed"],
            "coverage_progress": drone["coverage_progress"],
            "current_waypoint": drone["current_waypoint"],
            "total_waypoints": len(drone["waypoints"]),
            "flight_time": drone["flight_time"],
            "total_distance": drone["total_distance"]
        }
        
        # Save to database
        try:
            await db_service.save_telemetry(
                drone_id=drone["id"],
                mission_id=drone["mission_id"],
                lat=telemetry["lat"],
                lng=telemetry["lng"],
                alt=telemetry["alt"],
                battery_percent=telemetry["battery_percent"],
                status=telemetry["status"],
                heading=telemetry["heading"],
                speed=telemetry["speed"],
                coverage_progress=telemetry["coverage_progress"]
            )
        except Exception as e:
            logger.error(f"Error saving telemetry: {e}")
        
        # Send via Redis
        await self.redis_service.publish("telemetry", telemetry)
        
        # Send via WebSocket
        await self.websocket_manager.send_telemetry(str(drone["id"]), telemetry)
    
    async def _send_discovery_alert(self, drone: Dict[str, Any], discovery: Dict[str, Any]) -> None:
        """Send discovery alert"""
        discovery_data = {
            "drone_id": drone["id"],
            "mission_id": drone["mission_id"],
            "discovery": discovery,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Save to database
        try:
            await db_service.create_discovery(
                mission_id=drone["mission_id"],
                drone_id=drone["id"],
                lat=discovery["position"]["lat"],
                lng=discovery["position"]["lng"],
                discovery_type=discovery["type"],
                confidence=discovery["confidence"],
                description=discovery["description"]
            )
        except Exception as e:
            logger.error(f"Error saving discovery: {e}")
        
        # Send via Redis
        await self.redis_service.publish("discovery", discovery_data)
        
        # Send via WebSocket
        await self.websocket_manager.send_discovery(discovery_data)
    
    async def _notify_mission_complete(self, drone: Dict[str, Any]) -> None:
        """Notify mission completion"""
        completion_data = {
            "drone_id": drone["id"],
            "mission_id": drone["mission_id"],
            "assignment_id": drone["assignment"].get("assignment_id") if drone["assignment"] else None,
            "completion_time": asyncio.get_event_loop().time(),
            "total_distance": drone["total_distance"],
            "flight_time": drone["flight_time"],
            "discoveries_count": len(drone["discoveries"])
        }
        
        # Send via Redis
        await self.redis_service.publish("drone.assignment_completed", completion_data)
        
        # Send via WebSocket
        await self.websocket_manager.broadcast({
            "type": "mission_completed",
            "data": completion_data
        })
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_drone_status(self, drone_id: int) -> Optional[Dict[str, Any]]:
        """Get status of specific drone"""
        return self.active_drones.get(drone_id)
    
    def get_all_drone_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all drones"""
        return self.active_drones.copy()
    
    def get_active_drones(self) -> List[int]:
        """Get list of active drone IDs"""
        return [drone_id for drone_id, drone in self.active_drones.items() 
                if drone["status"] in ["active", "assigned"]]
    
    def get_mission_drones(self, mission_id: int) -> List[int]:
        """Get drones assigned to specific mission"""
        return [drone_id for drone_id, drone in self.active_drones.items() 
                if drone["mission_id"] == mission_id]