"""
Battery Monitor Agent
Monitors drone battery levels and manages power-related decisions
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.database import db_service

logger = logging.getLogger(__name__)

class BatteryMonitorAgent(BaseAgent):
    """Monitors drone battery levels and manages power decisions"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("battery_monitor", redis_service, websocket_manager)
        self.drone_batteries: Dict[int, Dict[str, Any]] = {}
        self.battery_alerts: Dict[int, str] = {}
        self.charging_stations: List[Dict[str, Any]] = []
    
    async def start_agent(self) -> None:
        """Start the battery monitor"""
        await self.subscribe_to_channel("drone.telemetry")
        await self.subscribe_to_channel("drone.status_update")
        await self.subscribe_to_channel("mission.battery_check")
        await self.subscribe_to_channel("charging.station_update")
        logger.info("Battery Monitor Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the battery monitor"""
        logger.info("Battery Monitor Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "drone.telemetry":
                await self._handle_telemetry_update(message)
            elif channel == "drone.status_update":
                await self._handle_status_update(message)
            elif channel == "mission.battery_check":
                await self._handle_battery_check(message)
            elif channel == "charging.station_update":
                await self._handle_charging_station_update(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_telemetry_update(self, message: Dict[str, Any]) -> None:
        """Handle drone telemetry update"""
        drone_id = message.get("drone_id")
        telemetry = message.get("telemetry", {})
        
        if not drone_id or "battery_percent" not in telemetry:
            return
        
        battery_percent = telemetry["battery_percent"]
        
        # Update battery tracking
        self.drone_batteries[drone_id] = {
            "battery_percent": battery_percent,
            "last_update": asyncio.get_event_loop().time(),
            "status": telemetry.get("status", "unknown"),
            "mission_id": telemetry.get("mission_id"),
            "position": {
                "lat": telemetry.get("lat"),
                "lng": telemetry.get("lng"),
                "alt": telemetry.get("alt")
            }
        }
        
        # Check battery levels and take action
        await self._check_battery_levels(drone_id, battery_percent)
    
    async def _handle_status_update(self, message: Dict[str, Any]) -> None:
        """Handle drone status update"""
        drone_id = message.get("drone_id")
        status = message.get("status")
        
        if drone_id in self.drone_batteries:
            self.drone_batteries[drone_id]["status"] = status
    
    async def _handle_battery_check(self, message: Dict[str, Any]) -> None:
        """Handle battery check request"""
        mission_id = message.get("mission_id")
        
        # Check all drones in the mission
        mission_drones = [
            drone_id for drone_id, data in self.drone_batteries.items()
            if data.get("mission_id") == mission_id
        ]
        
        battery_report = await self._generate_battery_report(mission_drones)
        
        # Publish battery report
        await self.publish_message("battery.report", {
            "mission_id": mission_id,
            "report": battery_report
        })
    
    async def _handle_charging_station_update(self, message: Dict[str, Any]) -> None:
        """Handle charging station update"""
        station_data = message.get("station_data", {})
        self.charging_stations.append(station_data)
        logger.info(f"Updated charging station: {station_data.get('id', 'unknown')}")
    
    async def _check_battery_levels(self, drone_id: int, battery_percent: int) -> None:
        """Check battery levels and take appropriate action"""
        if battery_percent <= 0:
            await self._handle_critical_battery(drone_id, battery_percent)
        elif battery_percent <= 10:
            await self._handle_emergency_battery(drone_id, battery_percent)
        elif battery_percent <= 20:
            await self._handle_low_battery(drone_id, battery_percent)
        elif battery_percent <= 30:
            await self._handle_warning_battery(drone_id, battery_percent)
        else:
            # Clear any existing alerts
            if drone_id in self.battery_alerts:
                del self.battery_alerts[drone_id]
    
    async def _handle_critical_battery(self, drone_id: int, battery_percent: int) -> None:
        """Handle critical battery level (0% or below)"""
        logger.critical(f"CRITICAL: Drone {drone_id} battery at {battery_percent}%")
        
        # Emergency land immediately
        await self.publish_message("drone.emergency_land", {
            "drone_id": drone_id,
            "reason": "critical_battery",
            "battery_percent": battery_percent
        })
        
        # Update drone status
        await db_service.update_drone_status(drone_id, "emergency_landing")
        
        # Send alert
        await self._send_battery_alert(drone_id, "critical", f"Battery critical at {battery_percent}% - Emergency landing")
        
        self.battery_alerts[drone_id] = "critical"
    
    async def _handle_emergency_battery(self, drone_id: int, battery_percent: int) -> None:
        """Handle emergency battery level (10% or below)"""
        logger.warning(f"EMERGENCY: Drone {drone_id} battery at {battery_percent}%")
        
        # Return to base immediately
        await self.publish_message("drone.return_to_base", {
            "drone_id": drone_id,
            "reason": "emergency_battery",
            "battery_percent": battery_percent,
            "priority": "critical"
        })
        
        # Update drone status
        await db_service.update_drone_status(drone_id, "returning_to_base")
        
        # Send alert
        await self._send_battery_alert(drone_id, "emergency", f"Battery emergency at {battery_percent}% - Returning to base")
        
        self.battery_alerts[drone_id] = "emergency"
    
    async def _handle_low_battery(self, drone_id: int, battery_percent: int) -> None:
        """Handle low battery level (20% or below)"""
        logger.warning(f"LOW: Drone {drone_id} battery at {battery_percent}%")
        
        # Plan return to base
        await self.publish_message("drone.plan_return", {
            "drone_id": drone_id,
            "reason": "low_battery",
            "battery_percent": battery_percent,
            "priority": "high"
        })
        
        # Send alert
        await self._send_battery_alert(drone_id, "low", f"Battery low at {battery_percent}% - Planning return to base")
        
        self.battery_alerts[drone_id] = "low"
    
    async def _handle_warning_battery(self, drone_id: int, battery_percent: int) -> None:
        """Handle warning battery level (30% or below)"""
        logger.info(f"WARNING: Drone {drone_id} battery at {battery_percent}%")
        
        # Send warning
        await self._send_battery_alert(drone_id, "warning", f"Battery warning at {battery_percent}% - Monitor closely")
        
        self.battery_alerts[drone_id] = "warning"
    
    async def _send_battery_alert(self, drone_id: int, level: str, message: str) -> None:
        """Send battery alert"""
        alert_data = {
            "drone_id": drone_id,
            "level": level,
            "message": message,
            "battery_percent": self.drone_batteries.get(drone_id, {}).get("battery_percent", 0),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send via WebSocket
        await self.send_websocket_message("battery_alert", alert_data)
        
        # Publish to Redis
        await self.publish_message("battery.alert", alert_data)
    
    async def _generate_battery_report(self, drone_ids: List[int]) -> Dict[str, Any]:
        """Generate battery report for specified drones"""
        report = {
            "timestamp": asyncio.get_event_loop().time(),
            "drones": [],
            "summary": {
                "total_drones": len(drone_ids),
                "critical": 0,
                "emergency": 0,
                "low": 0,
                "warning": 0,
                "normal": 0
            }
        }
        
        for drone_id in drone_ids:
            if drone_id not in self.drone_batteries:
                continue
            
            battery_data = self.drone_batteries[drone_id]
            battery_percent = battery_data["battery_percent"]
            
            # Categorize battery level
            if battery_percent <= 0:
                level = "critical"
            elif battery_percent <= 10:
                level = "emergency"
            elif battery_percent <= 20:
                level = "low"
            elif battery_percent <= 30:
                level = "warning"
            else:
                level = "normal"
            
            drone_report = {
                "drone_id": drone_id,
                "battery_percent": battery_percent,
                "level": level,
                "status": battery_data["status"],
                "last_update": battery_data["last_update"],
                "position": battery_data["position"]
            }
            
            report["drones"].append(drone_report)
            report["summary"][level] += 1
        
        return report
    
    async def calculate_flight_time_remaining(self, drone_id: int) -> Optional[float]:
        """Calculate estimated flight time remaining for drone"""
        if drone_id not in self.drone_batteries:
            return None
        
        battery_data = self.drone_batteries[drone_id]
        battery_percent = battery_data["battery_percent"]
        
        # Get drone specifications
        try:
            drones = await db_service.get_all_drones()
            drone = next((d for d in drones if d.id == drone_id), None)
            
            if not drone:
                return None
            
            # Calculate based on battery capacity and current level
            battery_capacity = drone.battery_capacity  # mAh
            current_battery = (battery_percent / 100) * battery_capacity
            
            # Estimate consumption rate (simplified)
            # Typical drone consumes ~1000mAh per hour
            consumption_rate = 1000  # mAh per hour
            
            # Calculate remaining time
            remaining_battery = current_battery - (battery_capacity * 0.1)  # Reserve 10%
            if remaining_battery <= 0:
                return 0
            
            remaining_hours = remaining_battery / consumption_rate
            return remaining_hours * 3600  # Convert to seconds
        
        except Exception as e:
            logger.error(f"Error calculating flight time for drone {drone_id}: {e}")
            return None
    
    async def get_optimal_charging_station(self, drone_id: int) -> Optional[Dict[str, Any]]:
        """Get optimal charging station for drone"""
        if drone_id not in self.drone_batteries:
            return None
        
        drone_position = self.drone_batteries[drone_id]["position"]
        if not drone_position or not drone_position.get("lat"):
            return None
        
        # Find nearest available charging station
        nearest_station = None
        min_distance = float('inf')
        
        for station in self.charging_stations:
            if not station.get("available", False):
                continue
            
            station_pos = station.get("position", {})
            if not station_pos.get("lat"):
                continue
            
            # Calculate distance (simplified)
            distance = self._calculate_distance(
                drone_position["lat"], drone_position["lng"],
                station_pos["lat"], station_pos["lng"]
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        import math
        
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
    
    async def schedule_charging(self, drone_id: int) -> bool:
        """Schedule drone for charging"""
        if drone_id not in self.drone_batteries:
            return False
        
        # Find optimal charging station
        charging_station = await self.get_optimal_charging_station(drone_id)
        
        if not charging_station:
            logger.warning(f"No available charging station for drone {drone_id}")
            return False
        
        # Send charging request
        await self.publish_message("charging.schedule", {
            "drone_id": drone_id,
            "station_id": charging_station["id"],
            "priority": "high" if self.drone_batteries[drone_id]["battery_percent"] <= 20 else "medium"
        })
        
        logger.info(f"Scheduled drone {drone_id} for charging at station {charging_station['id']}")
        return True
    
    def get_battery_status(self, drone_id: int) -> Optional[Dict[str, Any]]:
        """Get battery status for specific drone"""
        return self.drone_batteries.get(drone_id)
    
    def get_all_battery_status(self) -> Dict[int, Dict[str, Any]]:
        """Get battery status for all drones"""
        return self.drone_batteries.copy()
    
    def get_battery_alerts(self) -> Dict[int, str]:
        """Get current battery alerts"""
        return self.battery_alerts.copy()