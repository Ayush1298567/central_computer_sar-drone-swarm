"""
Collision Avoidance Agent
Monitors drone positions and prevents collisions
"""

import asyncio
import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from ...services.database import db_service

logger = logging.getLogger(__name__)

class CollisionAvoidanceAgent(BaseAgent):
    """Monitors drone positions and prevents collisions"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("collision_avoidance", redis_service, websocket_manager)
        self.drone_positions: Dict[int, Dict[str, Any]] = {}
        self.collision_zones: Dict[int, List[Dict[str, Any]]] = {}
        self.safety_distance = 50.0  # meters
        self.altitude_separation = 10.0  # meters
        self.collision_warnings: Dict[Tuple[int, int], Dict[str, Any]] = {}
    
    async def start_agent(self) -> None:
        """Start the collision avoidance agent"""
        await self.subscribe_to_channel("drone.telemetry")
        await self.subscribe_to_channel("drone.status_update")
        await self.subscribe_to_channel("mission.zone_update")
        await self.subscribe_to_channel("obstacle.detected")
        logger.info("Collision Avoidance Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the collision avoidance agent"""
        logger.info("Collision Avoidance Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "drone.telemetry":
                await self._handle_telemetry_update(message)
            elif channel == "drone.status_update":
                await self._handle_status_update(message)
            elif channel == "mission.zone_update":
                await self._handle_zone_update(message)
            elif channel == "obstacle.detected":
                await self._handle_obstacle_detected(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_telemetry_update(self, message: Dict[str, Any]) -> None:
        """Handle drone telemetry update"""
        drone_id = message.get("drone_id")
        telemetry = message.get("telemetry", {})
        
        if not drone_id or "lat" not in telemetry or "lng" not in telemetry:
            return
        
        # Update drone position
        self.drone_positions[drone_id] = {
            "lat": telemetry["lat"],
            "lng": telemetry["lng"],
            "alt": telemetry.get("alt", 50),
            "heading": telemetry.get("heading", 0),
            "speed": telemetry.get("speed", 0),
            "status": telemetry.get("status", "unknown"),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Check for collisions
        await self._check_collisions(drone_id)
    
    async def _handle_status_update(self, message: Dict[str, Any]) -> None:
        """Handle drone status update"""
        drone_id = message.get("drone_id")
        status = message.get("status")
        
        if drone_id in self.drone_positions:
            self.drone_positions[drone_id]["status"] = status
    
    async def _handle_zone_update(self, message: Dict[str, Any]) -> None:
        """Handle mission zone update"""
        zone_data = message.get("zone_data", {})
        mission_id = message.get("mission_id")
        
        # Update collision zones for mission
        if mission_id:
            self.collision_zones[mission_id] = zone_data.get("zones", [])
    
    async def _handle_obstacle_detected(self, message: Dict[str, Any]) -> None:
        """Handle obstacle detection"""
        obstacle = message.get("obstacle", {})
        drone_id = message.get("drone_id")
        
        logger.info(f"Obstacle detected by drone {drone_id}: {obstacle}")
        
        # Add obstacle to collision zones
        obstacle_zone = {
            "type": "obstacle",
            "position": {
                "lat": obstacle.get("lat"),
                "lng": obstacle.get("lng"),
                "alt": obstacle.get("alt", 0)
            },
            "radius": obstacle.get("radius", 20),
            "height": obstacle.get("height", 100),
            "drone_id": drone_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add to all mission zones
        for mission_id in self.collision_zones:
            self.collision_zones[mission_id].append(obstacle_zone)
    
    async def _check_collisions(self, drone_id: int) -> None:
        """Check for potential collisions with other drones"""
        if drone_id not in self.drone_positions:
            return
        
        current_drone = self.drone_positions[drone_id]
        
        # Check against other drones
        for other_drone_id, other_drone in self.drone_positions.items():
            if other_drone_id == drone_id:
                continue
            
            # Skip if either drone is not active
            if (current_drone["status"] not in ["active", "searching"] or 
                other_drone["status"] not in ["active", "searching"]):
                continue
            
            # Calculate distance
            distance = self._calculate_distance(
                current_drone["lat"], current_drone["lng"],
                other_drone["lat"], other_drone["lng"]
            )
            
            # Check altitude separation
            alt_diff = abs(current_drone["alt"] - other_drone["alt"])
            
            # Check if collision risk exists
            if distance < self.safety_distance and alt_diff < self.altitude_separation:
                await self._handle_collision_risk(drone_id, other_drone_id, distance, alt_diff)
            else:
                # Clear any existing warning
                warning_key = tuple(sorted([drone_id, other_drone_id]))
                if warning_key in self.collision_warnings:
                    del self.collision_warnings[warning_key]
        
        # Check against obstacles
        await self._check_obstacle_collisions(drone_id)
    
    async def _check_obstacle_collisions(self, drone_id: int) -> None:
        """Check for potential collisions with obstacles"""
        if drone_id not in self.drone_positions:
            return
        
        current_drone = self.drone_positions[drone_id]
        
        # Check all collision zones
        for mission_id, zones in self.collision_zones.items():
            for zone in zones:
                if zone["type"] == "obstacle":
                    obstacle_pos = zone["position"]
                    distance = self._calculate_distance(
                        current_drone["lat"], current_drone["lng"],
                        obstacle_pos["lat"], obstacle_pos["lng"]
                    )
                    
                    # Check if drone is within obstacle radius
                    if distance < zone["radius"]:
                        # Check altitude
                        alt_diff = abs(current_drone["alt"] - obstacle_pos["alt"])
                        if alt_diff < zone["height"]:
                            await self._handle_obstacle_collision_risk(drone_id, zone, distance)
    
    async def _handle_collision_risk(self, drone1_id: int, drone2_id: int, distance: float, alt_diff: float) -> None:
        """Handle collision risk between two drones"""
        warning_key = tuple(sorted([drone1_id, drone2_id]))
        
        # Check if warning already exists
        if warning_key in self.collision_warnings:
            existing_warning = self.collision_warnings[warning_key]
            # Update warning if distance is getting smaller
            if distance < existing_warning["distance"]:
                existing_warning["distance"] = distance
                existing_warning["severity"] = self._calculate_severity(distance)
                existing_warning["timestamp"] = asyncio.get_event_loop().time()
        else:
            # Create new warning
            warning = {
                "drone1_id": drone1_id,
                "drone2_id": drone2_id,
                "distance": distance,
                "altitude_diff": alt_diff,
                "severity": self._calculate_severity(distance),
                "timestamp": asyncio.get_event_loop().time()
            }
            self.collision_warnings[warning_key] = warning
        
        # Take evasive action based on severity
        severity = self.collision_warnings[warning_key]["severity"]
        
        if severity == "critical":
            await self._execute_emergency_avoidance(drone1_id, drone2_id)
        elif severity == "high":
            await self._execute_immediate_avoidance(drone1_id, drone2_id)
        elif severity == "medium":
            await self._execute_preventive_avoidance(drone1_id, drone2_id)
        else:
            await self._send_collision_warning(drone1_id, drone2_id, distance)
    
    async def _handle_obstacle_collision_risk(self, drone_id: int, obstacle: Dict[str, Any], distance: float) -> None:
        """Handle collision risk with obstacle"""
        logger.warning(f"Drone {drone_id} collision risk with obstacle at distance {distance:.1f}m")
        
        # Calculate avoidance vector
        avoidance_vector = await self._calculate_avoidance_vector(drone_id, obstacle)
        
        if avoidance_vector:
            # Send avoidance command
            await self.publish_message("drone.avoid_obstacle", {
                "drone_id": drone_id,
                "obstacle": obstacle,
                "avoidance_vector": avoidance_vector,
                "priority": "high"
            })
            
            # Send warning
            await self._send_obstacle_warning(drone_id, obstacle, distance)
    
    def _calculate_severity(self, distance: float) -> str:
        """Calculate collision severity based on distance"""
        if distance < 10:
            return "critical"
        elif distance < 20:
            return "high"
        elif distance < 30:
            return "medium"
        else:
            return "low"
    
    async def _execute_emergency_avoidance(self, drone1_id: int, drone2_id: int) -> None:
        """Execute emergency collision avoidance"""
        logger.critical(f"EMERGENCY: Collision avoidance for drones {drone1_id} and {drone2_id}")
        
        # Emergency stop both drones
        for drone_id in [drone1_id, drone2_id]:
            await self.publish_message("drone.emergency_stop", {
                "drone_id": drone_id,
                "reason": "collision_avoidance",
                "priority": "critical"
            })
        
        # Send emergency alert
        await self._send_emergency_alert(drone1_id, drone2_id)
    
    async def _execute_immediate_avoidance(self, drone1_id: int, drone2_id: int) -> None:
        """Execute immediate collision avoidance"""
        logger.warning(f"IMMEDIATE: Collision avoidance for drones {drone1_id} and {drone2_id}")
        
        # Calculate avoidance maneuvers
        avoidance1 = await self._calculate_drone_avoidance(drone1_id, drone2_id)
        avoidance2 = await self._calculate_drone_avoidance(drone2_id, drone1_id)
        
        # Execute avoidance maneuvers
        if avoidance1:
            await self.publish_message("drone.avoid_collision", {
                "drone_id": drone1_id,
                "avoidance": avoidance1,
                "priority": "high"
            })
        
        if avoidance2:
            await self.publish_message("drone.avoid_collision", {
                "drone_id": drone2_id,
                "avoidance": avoidance2,
                "priority": "high"
            })
    
    async def _execute_preventive_avoidance(self, drone1_id: int, drone2_id: int) -> None:
        """Execute preventive collision avoidance"""
        logger.info(f"PREVENTIVE: Collision avoidance for drones {drone1_id} and {drone2_id}")
        
        # Adjust altitude or speed to avoid collision
        await self.publish_message("drone.adjust_trajectory", {
            "drone1_id": drone1_id,
            "drone2_id": drone2_id,
            "action": "preventive_avoidance",
            "priority": "medium"
        })
    
    async def _calculate_drone_avoidance(self, drone_id: int, other_drone_id: int) -> Optional[Dict[str, Any]]:
        """Calculate avoidance maneuver for drone"""
        if drone_id not in self.drone_positions or other_drone_id not in self.drone_positions:
            return None
        
        drone = self.drone_positions[drone_id]
        other_drone = self.drone_positions[other_drone_id]
        
        # Calculate relative position
        lat_diff = other_drone["lat"] - drone["lat"]
        lng_diff = other_drone["lng"] - drone["lng"]
        
        # Calculate avoidance direction (perpendicular to collision vector)
        avoidance_heading = (drone["heading"] + 90) % 360  # Turn 90 degrees
        
        # Calculate altitude adjustment
        alt_adjustment = 10 if drone["alt"] <= other_drone["alt"] else -10
        
        return {
            "heading": avoidance_heading,
            "altitude_change": alt_adjustment,
            "speed_reduction": 0.5  # Reduce speed by 50%
        }
    
    async def _calculate_avoidance_vector(self, drone_id: int, obstacle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calculate avoidance vector for obstacle"""
        if drone_id not in self.drone_positions:
            return None
        
        drone = self.drone_positions[drone_id]
        obstacle_pos = obstacle["position"]
        
        # Calculate vector from drone to obstacle
        lat_diff = obstacle_pos["lat"] - drone["lat"]
        lng_diff = obstacle_pos["lng"] - drone["lng"]
        
        # Calculate perpendicular avoidance direction
        avoidance_heading = (drone["heading"] + 90) % 360
        
        # Calculate safe distance
        safe_distance = obstacle["radius"] + 20  # 20m buffer
        
        return {
            "heading": avoidance_heading,
            "distance": safe_distance,
            "altitude_change": 10  # Climb to avoid obstacle
        }
    
    async def _send_collision_warning(self, drone1_id: int, drone2_id: int, distance: float) -> None:
        """Send collision warning"""
        warning_data = {
            "drone1_id": drone1_id,
            "drone2_id": drone2_id,
            "distance": distance,
            "severity": "low",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send via WebSocket
        await self.send_websocket_message("collision_warning", warning_data)
        
        # Publish to Redis
        await self.publish_message("collision.warning", warning_data)
    
    async def _send_obstacle_warning(self, drone_id: int, obstacle: Dict[str, Any], distance: float) -> None:
        """Send obstacle collision warning"""
        warning_data = {
            "drone_id": drone_id,
            "obstacle": obstacle,
            "distance": distance,
            "severity": "high",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send via WebSocket
        await self.send_websocket_message("obstacle_warning", warning_data)
        
        # Publish to Redis
        await self.publish_message("obstacle.warning", warning_data)
    
    async def _send_emergency_alert(self, drone1_id: int, drone2_id: int) -> None:
        """Send emergency collision alert"""
        alert_data = {
            "drone1_id": drone1_id,
            "drone2_id": drone2_id,
            "severity": "critical",
            "action": "emergency_stop",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send via WebSocket
        await self.send_websocket_message("collision_emergency", alert_data)
        
        # Publish to Redis
        await self.publish_message("collision.emergency", alert_data)
    
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
    
    def get_collision_status(self) -> Dict[str, Any]:
        """Get current collision status"""
        return {
            "active_drones": len([d for d in self.drone_positions.values() if d["status"] in ["active", "searching"]]),
            "collision_warnings": len(self.collision_warnings),
            "safety_distance": self.safety_distance,
            "altitude_separation": self.altitude_separation
        }
    
    def get_drone_positions(self) -> Dict[int, Dict[str, Any]]:
        """Get current drone positions"""
        return self.drone_positions.copy()
    
    def get_collision_warnings(self) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Get current collision warnings"""
        return self.collision_warnings.copy()