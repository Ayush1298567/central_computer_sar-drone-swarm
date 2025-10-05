"""
Drone Registry for SAR Mission Commander
Manages drone discovery, registration, and connection status
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class DroneConnectionType(Enum):
    """Types of drone connections"""
    WIFI = "wifi"
    LORA = "lora"
    MAVLINK = "mavlink"
    WEBSOCKET = "websocket"
    BLUETOOTH = "bluetooth"

class DroneStatus(Enum):
    """Drone operational status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IDLE = "idle"
    FLYING = "flying"
    RETURNING = "returning"
    LANDING = "landing"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    OFFLINE = "offline"

@dataclass
class DroneCapabilities:
    """Drone hardware and software capabilities"""
    max_flight_time: int  # minutes
    max_speed: float  # m/s
    max_altitude: float  # meters
    payload_capacity: float  # kg
    camera_resolution: str  # e.g., "4K", "1080p"
    has_thermal_camera: bool
    has_gimbal: bool
    has_rtk_gps: bool
    has_collision_avoidance: bool
    has_return_to_home: bool
    communication_range: float  # meters
    battery_capacity: float  # mAh
    supported_commands: List[str]

@dataclass
class DroneInfo:
    """Complete drone information"""
    drone_id: str
    name: str
    model: str
    manufacturer: str
    firmware_version: str
    serial_number: str
    capabilities: DroneCapabilities
    connection_type: DroneConnectionType
    connection_params: Dict
    status: DroneStatus
    last_seen: datetime
    battery_level: float
    position: Dict[str, float]  # lat, lon, alt
    heading: float
    speed: float
    signal_strength: float
    current_mission_id: Optional[str] = None
    assigned_operator: Optional[str] = None
    maintenance_due: Optional[datetime] = None

class DroneRegistry:
    """Central registry for all drones in the system"""
    
    def __init__(self):
        self.drones: Dict[str, DroneInfo] = {}
        self.connection_handlers: Dict[DroneConnectionType, List[str]] = {
            connection_type: [] for connection_type in DroneConnectionType
        }
        self.discovery_active = False
        self._discovery_tasks: Set[asyncio.Task] = set()
        
    async def start_discovery(self):
        """Start drone discovery across all communication protocols"""
        self.discovery_active = True
        logger.info("Starting drone discovery...")
        
        # Start discovery for each connection type
        for connection_type in DroneConnectionType:
            task = asyncio.create_task(self._discover_drones(connection_type))
            self._discovery_tasks.add(task)
            task.add_done_callback(self._discovery_tasks.discard)
    
    async def stop_discovery(self):
        """Stop drone discovery"""
        self.discovery_active = False
        
        # Cancel all discovery tasks
        for task in list(self._discovery_tasks):
            task.cancel()
        
        # Wait for tasks to complete
        if self._discovery_tasks:
            await asyncio.gather(*self._discovery_tasks, return_exceptions=True)
        
        logger.info("Drone discovery stopped")
    
    async def _discover_drones(self, connection_type: DroneConnectionType):
        """Discover drones using specific connection type"""
        while self.discovery_active:
            try:
                if connection_type == DroneConnectionType.WIFI:
                    await self._discover_wifi_drones()
                elif connection_type == DroneConnectionType.LORA:
                    await self._discover_lora_drones()
                elif connection_type == DroneConnectionType.MAVLINK:
                    await self._discover_mavlink_drones()
                elif connection_type == DroneConnectionType.WEBSOCKET:
                    await self._discover_websocket_drones()
                elif connection_type == DroneConnectionType.BLUETOOTH:
                    await self._discover_bluetooth_drones()
                
                # Wait before next discovery cycle
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {connection_type.value} discovery: {e}")
                await asyncio.sleep(5)
    
    async def _discover_wifi_drones(self):
        """Discover drones via WiFi network scanning"""
        # Scan for devices with drone-specific identifiers
        drone_identifiers = [
            "drone-", "quadcopter-", "uas-", "sar-drone-",
            "pixhawk-", "ardupilot-", "px4-"
        ]
        
        # This would integrate with network scanning tools
        # For now, simulate discovery
        pass
    
    async def _discover_lora_drones(self):
        """Discover drones via LoRa communication"""
        # Scan LoRa channels for drone beacons
        lora_channels = [868.1, 868.3, 868.5, 915.0, 915.2, 915.4]
        
        # This would integrate with LoRa radio modules
        # For now, simulate discovery
        pass
    
    async def _discover_mavlink_drones(self):
        """Discover drones via MAVLink protocol"""
        # Scan serial ports and network interfaces for MAVLink connections
        # This would integrate with pymavlink library
        pass
    
    async def _discover_websocket_drones(self):
        """Discover drones via WebSocket connections"""
        # Look for WebSocket servers on common drone ports
        common_ports = [8080, 8081, 9090, 9091, 8888, 8889]
        
        # This would attempt WebSocket connections to discover drones
        pass
    
    async def _discover_bluetooth_drones(self):
        """Discover drones via Bluetooth"""
        # Scan for Bluetooth devices with drone identifiers
        # This would integrate with bluetooth libraries
        pass
    
    def register_drone(self, drone_info: DroneInfo) -> bool:
        """Register a new drone in the registry"""
        try:
            # Validate drone info
            if not self._validate_drone_info(drone_info):
                logger.error(f"Invalid drone info for {drone_info.drone_id}")
                return False
            
            # Add to registry
            self.drones[drone_info.drone_id] = drone_info
            self.connection_handlers[drone_info.connection_type].append(drone_info.drone_id)
            
            logger.info(f"Registered drone: {drone_info.name} ({drone_info.drone_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register drone {drone_info.drone_id}: {e}")
            return False
    
    def unregister_drone(self, drone_id: str) -> bool:
        """Unregister a drone from the registry"""
        try:
            if drone_id in self.drones:
                drone_info = self.drones[drone_id]
                connection_type = drone_info.connection_type
                
                # Remove from connection handlers
                if drone_id in self.connection_handlers[connection_type]:
                    self.connection_handlers[connection_type].remove(drone_id)
                
                # Remove from main registry
                del self.drones[drone_id]
                
                logger.info(f"Unregistered drone: {drone_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister drone {drone_id}: {e}")
            return False
    
    def update_drone_status(self, drone_id: str, status: DroneStatus, 
                          position: Optional[Dict] = None,
                          battery_level: Optional[float] = None,
                          signal_strength: Optional[float] = None) -> bool:
        """Update drone status and telemetry"""
        try:
            if drone_id not in self.drones:
                logger.warning(f"Attempted to update unknown drone: {drone_id}")
                return False
            
            drone_info = self.drones[drone_id]
            drone_info.status = status
            drone_info.last_seen = datetime.utcnow()
            
            if position:
                drone_info.position.update(position)
            
            if battery_level is not None:
                drone_info.battery_level = battery_level
            
            if signal_strength is not None:
                drone_info.signal_strength = signal_strength
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update drone status {drone_id}: {e}")
            return False
    
    def get_drone(self, drone_id: str) -> Optional[DroneInfo]:
        """Get drone information by ID"""
        return self.drones.get(drone_id)
    
    def get_all_drones(self) -> List[DroneInfo]:
        """Get all registered drones"""
        return list(self.drones.values())
    
    def get_drones_by_status(self, status: DroneStatus) -> List[DroneInfo]:
        """Get drones with specific status"""
        return [drone for drone in self.drones.values() if drone.status == status]
    
    def get_drones_by_connection_type(self, connection_type: DroneConnectionType) -> List[DroneInfo]:
        """Get drones using specific connection type"""
        return [drone for drone in self.drones.values() if drone.connection_type == connection_type]
    
    def get_available_drones(self) -> List[DroneInfo]:
        """Get drones available for mission assignment"""
        available_statuses = [DroneStatus.CONNECTED, DroneStatus.IDLE]
        return [drone for drone in self.drones.values() if drone.status in available_statuses]
    
    def assign_mission(self, drone_id: str, mission_id: str) -> bool:
        """Assign a mission to a drone"""
        try:
            if drone_id not in self.drones:
                return False
            
            drone_info = self.drones[drone_id]
            if drone_info.status not in [DroneStatus.CONNECTED, DroneStatus.IDLE]:
                return False
            
            drone_info.current_mission_id = mission_id
            drone_info.status = DroneStatus.FLYING
            drone_info.last_seen = datetime.utcnow()
            
            logger.info(f"Assigned mission {mission_id} to drone {drone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign mission {mission_id} to drone {drone_id}: {e}")
            return False
    
    def unassign_mission(self, drone_id: str) -> bool:
        """Unassign mission from a drone"""
        try:
            if drone_id not in self.drones:
                return False
            
            drone_info = self.drones[drone_id]
            drone_info.current_mission_id = None
            
            if drone_info.status == DroneStatus.FLYING:
                drone_info.status = DroneStatus.IDLE
            
            logger.info(f"Unassigned mission from drone {drone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unassign mission from drone {drone_id}: {e}")
            return False
    
    def get_connection_statistics(self) -> Dict:
        """Get connection statistics"""
        stats = {
            "total_drones": len(self.drones),
            "by_status": {},
            "by_connection_type": {},
            "discovery_active": self.discovery_active
        }
        
        # Count by status
        for status in DroneStatus:
            count = len(self.get_drones_by_status(status))
            stats["by_status"][status.value] = count
        
        # Count by connection type
        for connection_type in DroneConnectionType:
            count = len(self.get_drones_by_connection_type(connection_type))
            stats["by_connection_type"][connection_type.value] = count
        
        return stats
    
    def _validate_drone_info(self, drone_info: DroneInfo) -> bool:
        """Validate drone information"""
        required_fields = [
            'drone_id', 'name', 'model', 'manufacturer',
            'capabilities', 'connection_type', 'connection_params'
        ]
        
        for field in required_fields:
            if not hasattr(drone_info, field) or getattr(drone_info, field) is None:
                return False
        
        # Validate capabilities
        if not drone_info.capabilities:
            return False
        
        # Validate connection parameters
        if not drone_info.connection_params:
            return False
        
        return True

# Global drone registry instance
drone_registry = DroneRegistry()
