"""
Drone Manager Service for SAR Mission Commander
Handles real-time drone connections, telemetry, and status management
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.database import SessionLocal
from ..models.drone import Drone, DroneStatus
from ..models.mission import Mission
from ..utils.logging import get_logger

logger = get_logger(__name__)

class DroneCommandType(Enum):
    START_MISSION = "start_mission"
    RETURN_HOME = "return_home"
    LAND = "land"
    EMERGENCY_STOP = "emergency_stop"
    UPDATE_ALTITUDE = "update_altitude"
    CHANGE_HEADING = "change_heading"
    ENABLE_AUTONOMOUS = "enable_autonomous"
    DISABLE_AUTONOMOUS = "disable_autonomous"

@dataclass
class DroneCommand:
    drone_id: str
    command_type: DroneCommandType
    parameters: Optional[Dict] = None
    timestamp: Optional[datetime] = None
    priority: int = 1  # 1=normal, 2=high, 3=emergency

@dataclass
class TelemetryData:
    drone_id: str
    timestamp: datetime
    position: Dict[str, float]  # lat, lon, alt
    battery_level: float
    speed: float
    heading: float
    signal_strength: float
    gps_accuracy: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None

class DroneManager:
    """Manages drone fleet operations and real-time telemetry"""
    
    def __init__(self):
        self.connected_drones: Dict[str, Dict] = {}
        self.telemetry_history: Dict[str, List[TelemetryData]] = {}
        self.command_queue: List[DroneCommand] = []
        self.mission_assignments: Dict[str, str] = {}  # drone_id -> mission_id
        self._running = False
        
    async def start(self):
        """Start the drone manager service"""
        self._running = True
        logger.info("Drone Manager service started")
        
        # Start background tasks
        asyncio.create_task(self._process_command_queue())
        asyncio.create_task(self._monitor_drone_health())
        asyncio.create_task(self._cleanup_old_telemetry())
        
    async def stop(self):
        """Stop the drone manager service"""
        self._running = False
        logger.info("Drone Manager service stopped")
        
    async def register_drone(self, drone_id: str, capabilities: Dict) -> bool:
        """Register a new drone connection"""
        try:
            drone_data = {
                "id": drone_id,
                "capabilities": capabilities,
                "status": DroneStatus.IDLE,
                "last_heartbeat": datetime.utcnow(),
                "connected": True,
                "current_mission": None,
                "battery_level": 100.0,
                "position": {"latitude": 0.0, "longitude": 0.0, "altitude": 0.0}
            }
            
            self.connected_drones[drone_id] = drone_data
            self.telemetry_history[drone_id] = []
            
            logger.info(f"Drone {drone_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register drone {drone_id}: {e}")
            return False
    
    async def unregister_drone(self, drone_id: str) -> bool:
        """Unregister a drone connection"""
        try:
            if drone_id in self.connected_drones:
                # Return drone home if on mission
                if self.connected_drones[drone_id]["current_mission"]:
                    await self.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.RETURN_HOME,
                        priority=2
                    ))
                
                del self.connected_drones[drone_id]
                
            if drone_id in self.telemetry_history:
                del self.telemetry_history[drone_id]
                
            if drone_id in self.mission_assignments:
                del self.mission_assignments[drone_id]
                
            logger.info(f"Drone {drone_id} unregistered")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister drone {drone_id}: {e}")
            return False
    
    async def update_telemetry(self, drone_id: str, telemetry: TelemetryData) -> bool:
        """Update drone telemetry data"""
        try:
            if drone_id not in self.connected_drones:
                logger.warning(f"Received telemetry from unregistered drone {drone_id}")
                return False
                
            # Update drone data
            drone_data = self.connected_drones[drone_id]
            drone_data.update({
                "last_heartbeat": datetime.utcnow(),
                "battery_level": telemetry.battery_level,
                "position": telemetry.position,
                "speed": telemetry.speed,
                "heading": telemetry.heading
            })
            
            # Store telemetry history
            self.telemetry_history[drone_id].append(telemetry)
            
            # Keep only last 100 telemetry entries
            if len(self.telemetry_history[drone_id]) > 100:
                self.telemetry_history[drone_id] = self.telemetry_history[drone_id][-100:]
                
            # Check for low battery
            if telemetry.battery_level < 20:
                await self._handle_low_battery(drone_id, telemetry.battery_level)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to update telemetry for drone {drone_id}: {e}")
            return False
    
    async def send_command(self, command: DroneCommand) -> bool:
        """Send command to drone"""
        try:
            if command.drone_id not in self.connected_drones:
                logger.warning(f"Command sent to unregistered drone {command.drone_id}")
                return False
                
            # Add timestamp if not provided
            if not command.timestamp:
                command.timestamp = datetime.utcnow()
                
            # Add to command queue (sorted by priority)
            self.command_queue.append(command)
            self.command_queue.sort(key=lambda x: x.priority, reverse=True)
            
            logger.info(f"Command {command.command_type.value} queued for drone {command.drone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue command for drone {command.drone_id}: {e}")
            return False
    
    async def assign_mission(self, drone_id: str, mission_id: str) -> bool:
        """Assign drone to a mission"""
        try:
            if drone_id not in self.connected_drones:
                logger.warning(f"Cannot assign mission to unregistered drone {drone_id}")
                return False
                
            # Check if drone is available
            drone_status = self.connected_drones[drone_id]["status"]
            if drone_status not in [DroneStatus.IDLE, DroneStatus.CHARGING]:
                logger.warning(f"Drone {drone_id} is not available for mission assignment")
                return False
                
            self.mission_assignments[drone_id] = mission_id
            self.connected_drones[drone_id]["current_mission"] = mission_id
            self.connected_drones[drone_id]["status"] = DroneStatus.MISSION
            
            logger.info(f"Drone {drone_id} assigned to mission {mission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign mission to drone {drone_id}: {e}")
            return False
    
    async def unassign_mission(self, drone_id: str) -> bool:
        """Unassign drone from current mission"""
        try:
            if drone_id in self.mission_assignments:
                mission_id = self.mission_assignments[drone_id]
                del self.mission_assignments[drone_id]
                
            if drone_id in self.connected_drones:
                self.connected_drones[drone_id]["current_mission"] = None
                self.connected_drones[drone_id]["status"] = DroneStatus.IDLE
                
            logger.info(f"Drone {drone_id} unassigned from mission")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unassign mission from drone {drone_id}: {e}")
            return False
    
    def get_drone_status(self, drone_id: str) -> Optional[Dict]:
        """Get current status of a drone"""
        return self.connected_drones.get(drone_id)
    
    def get_all_drones(self) -> List[Dict]:
        """Get status of all connected drones"""
        return list(self.connected_drones.values())
    
    def get_mission_drones(self, mission_id: str) -> List[Dict]:
        """Get all drones assigned to a mission"""
        return [
            drone for drone_id, drone in self.connected_drones.items()
            if drone.get("current_mission") == mission_id
        ]
    
    def get_available_drones(self) -> List[Dict]:
        """Get all available drones for mission assignment"""
        return [
            drone for drone in self.connected_drones.values()
            if drone["status"] in [DroneStatus.IDLE, DroneStatus.CHARGING]
        ]
    
    async def emergency_stop_all(self) -> bool:
        """Emergency stop all drones"""
        try:
            emergency_commands = []
            for drone_id in self.connected_drones.keys():
                emergency_commands.append(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.EMERGENCY_STOP,
                    priority=3  # Highest priority
                ))
            
            # Add all emergency commands to queue
            self.command_queue.extend(emergency_commands)
            self.command_queue.sort(key=lambda x: x.priority, reverse=True)
            
            logger.warning("Emergency stop command sent to all drones")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send emergency stop to all drones: {e}")
            return False
    
    async def _process_command_queue(self):
        """Background task to process command queue"""
        while self._running:
            try:
                if self.command_queue:
                    command = self.command_queue.pop(0)
                    await self._execute_command(command)
                    
                await asyncio.sleep(0.1)  # Process commands every 100ms
                
            except Exception as e:
                logger.error(f"Error processing command queue: {e}")
                await asyncio.sleep(1)
    
    async def _execute_command(self, command: DroneCommand):
        """Execute a drone command"""
        try:
            drone_id = command.drone_id
            
            # In a real implementation, this would send the command to the actual drone
            # For now, we'll simulate the command execution
            logger.info(f"Executing command {command.command_type.value} for drone {drone_id}")
            
            # Update drone status based on command
            if command.command_type == DroneCommandType.START_MISSION:
                self.connected_drones[drone_id]["status"] = DroneStatus.MISSION
            elif command.command_type == DroneCommandType.RETURN_HOME:
                self.connected_drones[drone_id]["status"] = DroneStatus.RETURNING
            elif command.command_type == DroneCommandType.LAND:
                self.connected_drones[drone_id]["status"] = DroneStatus.IDLE
            elif command.command_type == DroneCommandType.EMERGENCY_STOP:
                self.connected_drones[drone_id]["status"] = DroneStatus.ERROR
                
        except Exception as e:
            logger.error(f"Failed to execute command {command.command_type.value} for drone {command.drone_id}: {e}")
    
    async def _monitor_drone_health(self):
        """Background task to monitor drone health"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                for drone_id, drone_data in self.connected_drones.items():
                    last_heartbeat = drone_data.get("last_heartbeat")
                    if last_heartbeat and (current_time - last_heartbeat).seconds > 30:
                        # Drone hasn't sent heartbeat in 30 seconds
                        drone_data["status"] = DroneStatus.ERROR
                        logger.warning(f"Drone {drone_id} appears to be offline")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring drone health: {e}")
                await asyncio.sleep(10)
    
    async def _handle_low_battery(self, drone_id: str, battery_level: float):
        """Handle low battery warning"""
        try:
            # Return drone home if battery is critically low
            if battery_level < 10:
                await self.send_command(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.RETURN_HOME,
                    priority=2
                ))
                logger.warning(f"Critical battery level for drone {drone_id}: {battery_level}% - returning home")
            else:
                logger.warning(f"Low battery warning for drone {drone_id}: {battery_level}%")
                
        except Exception as e:
            logger.error(f"Failed to handle low battery for drone {drone_id}: {e}")
    
    async def _cleanup_old_telemetry(self):
        """Background task to clean up old telemetry data"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                for drone_id, telemetry_list in self.telemetry_history.items():
                    # Remove telemetry older than 24 hours
                    self.telemetry_history[drone_id] = [
                        t for t in telemetry_list 
                        if t.timestamp > cutoff_time
                    ]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error cleaning up telemetry data: {e}")
                await asyncio.sleep(3600)

# Global drone manager instance
drone_manager = DroneManager()