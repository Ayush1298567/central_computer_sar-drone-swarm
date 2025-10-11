"""
Emergency MAVLink Handler for SAR Mission Commander

This module provides emergency MAVLink communication capabilities for direct
drone control in critical situations. It's designed to be lazy-loaded only
when needed, allowing the system to run without hardware dependencies.

Author: SAR Drone Swarm System
References:
    - MAVLink Protocol: https://mavlink.io/en/
    - ArduPilot MAVLink: https://ardupilot.org/dev/docs/mavlink-basics.html
    - PX4 MAVLink: https://docs.px4.io/main/en/middleware/mavlink.html
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import threading

# Lazy import - only load when actually needed
_pymavlink_module = None
_mavutil = None

logger = logging.getLogger(__name__)


def _lazy_import_mavlink():
    """Lazy import of pymavlink to avoid requiring hardware dependencies at startup."""
    global _pymavlink_module, _mavutil
    if _mavutil is None:
        try:
            from pymavlink import mavutil
            _mavutil = mavutil
            _pymavlink_module = True
            logger.info("pymavlink loaded successfully")
        except ImportError as e:
            logger.warning(f"pymavlink not available: {e}. Emergency MAVLink features disabled.")
            _pymavlink_module = False
    return _mavutil is not None


class EmergencyCommand(Enum):
    """Emergency commands that can be sent via MAVLink"""
    RETURN_TO_LAUNCH = "RTL"
    LAND_NOW = "LAND"
    EMERGENCY_STOP = "ESTOP"
    PAUSE_MISSION = "PAUSE"
    RESUME_MISSION = "RESUME"
    CHANGE_ALTITUDE = "ALTITUDE"
    CHANGE_SPEED = "SPEED"


@dataclass
class EmergencyResponse:
    """Response from emergency command execution"""
    success: bool
    command: str
    drone_id: str
    timestamp: datetime
    message: str
    telemetry: Optional[Dict[str, Any]] = None


class EmergencyMAVLinkConnection:
    """
    Emergency MAVLink connection for direct drone communication.
    
    This class provides a minimal, reliable interface for emergency
    situations where standard communication channels may be compromised.
    
    Usage:
        connection = EmergencyMAVLinkConnection(connection_string="udp:127.0.0.1:14550")
        await connection.connect()
        response = await connection.send_emergency_command(EmergencyCommand.RETURN_TO_LAUNCH, drone_id="drone_001")
    """
    
    def __init__(self, connection_string: str, system_id: int = 255, component_id: int = 190):
        """
        Initialize emergency MAVLink connection.
        
        Args:
            connection_string: MAVLink connection string (e.g., "udp:127.0.0.1:14550", "/dev/ttyUSB0:57600")
            system_id: Ground control system ID (default: 255)
            component_id: Ground control component ID (default: 190)
        """
        self.connection_string = connection_string
        self.system_id = system_id
        self.component_id = component_id
        self.mav = None
        self._connected = False
        self._running = False
        self._message_thread: Optional[threading.Thread] = None
        self._last_heartbeat: Dict[int, datetime] = {}
        self._telemetry_cache: Dict[int, Dict] = {}
        self._callbacks: Dict[str, list] = {"telemetry": [], "status": [], "heartbeat": []}
        self._lock = asyncio.Lock()
        
    async def connect(self, timeout: float = 10.0) -> bool:
        """
        Establish emergency MAVLink connection.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection established, False otherwise
        """
        try:
            if not _lazy_import_mavlink():
                logger.error("Cannot connect: pymavlink not available")
                return False
            
            async with self._lock:
                logger.info(f"Establishing emergency MAVLink connection: {self.connection_string}")
                
                # Create MAVLink connection
                self.mav = _mavutil.mavlink_connection(
                    self.connection_string,
                    source_system=self.system_id,
                    source_component=self.component_id,
                    dialect='ardupilotmega'
                )
                
                # Wait for first heartbeat with timeout
                start_time = datetime.now()
                while (datetime.now() - start_time).total_seconds() < timeout:
                    heartbeat = self.mav.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
                    if heartbeat:
                        system_id = heartbeat.get_srcSystem()
                        self._last_heartbeat[system_id] = datetime.now()
                        logger.info(f"Emergency MAVLink connected to system {system_id}")
                        self._connected = True
                        
                        # Start message processing thread
                        self._running = True
                        self._message_thread = threading.Thread(
                            target=self._process_messages,
                            daemon=True,
                            name="EmergencyMAVLink_MessageProcessor"
                        )
                        self._message_thread.start()
                        
                        return True
                
                logger.error(f"Emergency MAVLink connection timeout after {timeout}s")
                return False
                
        except Exception as e:
            logger.error(f"Emergency MAVLink connection failed: {e}", exc_info=True)
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect emergency MAVLink connection."""
        async with self._lock:
            self._running = False
            self._connected = False
            
            if self._message_thread and self._message_thread.is_alive():
                self._message_thread.join(timeout=2.0)
            
            if self.mav:
                try:
                    self.mav.close()
                except Exception as e:
                    logger.error(f"Error closing MAVLink connection: {e}")
                self.mav = None
            
            logger.info("Emergency MAVLink connection closed")
    
    def _process_messages(self) -> None:
        """Background thread to process incoming MAVLink messages."""
        logger.info("Emergency MAVLink message processor started")
        
        while self._running and self.mav:
            try:
                msg = self.mav.recv_match(blocking=True, timeout=1.0)
                if msg:
                    msg_type = msg.get_type()
                    system_id = msg.get_srcSystem()
                    
                    # Update heartbeat tracking
                    if msg_type == 'HEARTBEAT':
                        self._last_heartbeat[system_id] = datetime.now()
                        self._notify_callbacks("heartbeat", {"system_id": system_id, "timestamp": datetime.now()})
                    
                    # Cache telemetry data
                    elif msg_type == 'GLOBAL_POSITION_INT':
                        telemetry = {
                            "system_id": system_id,
                            "lat": msg.lat / 1e7,
                            "lon": msg.lon / 1e7,
                            "alt": msg.alt / 1000.0,
                            "relative_alt": msg.relative_alt / 1000.0,
                            "heading": msg.hdg / 100.0,
                            "ground_speed": (msg.vx**2 + msg.vy**2)**0.5 / 100.0,
                            "timestamp": datetime.now()
                        }
                        self._telemetry_cache[system_id] = telemetry
                        self._notify_callbacks("telemetry", telemetry)
                    
                    # Cache system status
                    elif msg_type == 'SYS_STATUS':
                        status = {
                            "system_id": system_id,
                            "battery_voltage": msg.voltage_battery / 1000.0,
                            "battery_remaining": msg.battery_remaining,
                            "battery_current": msg.current_battery / 100.0,
                            "timestamp": datetime.now()
                        }
                        if system_id not in self._telemetry_cache:
                            self._telemetry_cache[system_id] = {}
                        self._telemetry_cache[system_id].update(status)
                        self._notify_callbacks("status", status)
                        
            except Exception as e:
                if self._running:
                    logger.error(f"Error processing MAVLink message: {e}")
        
        logger.info("Emergency MAVLink message processor stopped")
    
    def _notify_callbacks(self, callback_type: str, data: Dict) -> None:
        """Notify registered callbacks."""
        for callback in self._callbacks.get(callback_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in {callback_type} callback: {e}")
    
    def register_callback(self, callback_type: str, callback: Callable) -> None:
        """
        Register a callback for specific message types.
        
        Args:
            callback_type: Type of callback ("telemetry", "status", "heartbeat")
            callback: Callback function
        """
        if callback_type in self._callbacks:
            self._callbacks[callback_type].append(callback)
        else:
            logger.warning(f"Unknown callback type: {callback_type}")
    
    async def send_emergency_command(
        self,
        command: EmergencyCommand,
        drone_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> EmergencyResponse:
        """
        Send emergency command to drone.
        
        Args:
            command: Emergency command to execute
            drone_id: Target drone identifier
            parameters: Command-specific parameters
            
        Returns:
            EmergencyResponse with execution result
        """
        if not self._connected or not self.mav:
            return EmergencyResponse(
                success=False,
                command=command.value,
                drone_id=drone_id,
                timestamp=datetime.now(),
                message="Not connected to MAVLink"
            )
        
        try:
            # Extract system ID from drone_id (assuming format like "drone_001" -> system 1)
            # In production, you'd have a proper mapping
            system_id = self._parse_system_id(drone_id)
            parameters = parameters or {}
            
            # Map emergency commands to MAVLink commands
            # Reference: https://mavlink.io/en/messages/common.html#MAV_CMD
            if command == EmergencyCommand.RETURN_TO_LAUNCH:
                # MAV_CMD_NAV_RETURN_TO_LAUNCH (20)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    20,  # MAV_CMD_NAV_RETURN_TO_LAUNCH
                    0,   # confirmation
                    0, 0, 0, 0, 0, 0, 0  # param1-7 (unused for RTL)
                )
                message = "Return to launch command sent"
                
            elif command == EmergencyCommand.LAND_NOW:
                # MAV_CMD_NAV_LAND (21)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    21,  # MAV_CMD_NAV_LAND
                    0,
                    parameters.get("abort_alt", 0),  # Abort altitude
                    parameters.get("land_mode", 0),   # Land mode
                    0, 0,
                    parameters.get("lat", 0),  # Latitude
                    parameters.get("lon", 0),  # Longitude
                    parameters.get("alt", 0)   # Altitude
                )
                message = "Emergency land command sent"
                
            elif command == EmergencyCommand.EMERGENCY_STOP:
                # Set mode to STABILIZE and throttle to zero
                # This is a custom emergency procedure
                self.mav.mav.set_mode_send(
                    system_id,
                    1,   # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
                    0    # STABILIZE mode for ArduPilot
                )
                message = "Emergency stop command sent (STABILIZE mode)"
                
            elif command == EmergencyCommand.PAUSE_MISSION:
                # MAV_CMD_DO_PAUSE_CONTINUE (193)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    193,  # MAV_CMD_DO_PAUSE_CONTINUE
                    0,
                    0,  # 0 = pause
                    0, 0, 0, 0, 0, 0
                )
                message = "Mission pause command sent"
                
            elif command == EmergencyCommand.RESUME_MISSION:
                # MAV_CMD_DO_PAUSE_CONTINUE (193)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    193,  # MAV_CMD_DO_PAUSE_CONTINUE
                    0,
                    1,  # 1 = resume
                    0, 0, 0, 0, 0, 0
                )
                message = "Mission resume command sent"
                
            elif command == EmergencyCommand.CHANGE_ALTITUDE:
                # MAV_CMD_NAV_CONTINUE_AND_CHANGE_ALT (30)
                altitude = parameters.get("altitude", 0)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    30,  # MAV_CMD_NAV_CONTINUE_AND_CHANGE_ALT
                    0,
                    0,  # Continue on current course
                    altitude,
                    0, 0, 0, 0, 0
                )
                message = f"Altitude change to {altitude}m command sent"
                
            elif command == EmergencyCommand.CHANGE_SPEED:
                # MAV_CMD_DO_CHANGE_SPEED (178)
                speed = parameters.get("speed", 0)
                self.mav.mav.command_long_send(
                    system_id,
                    self.mav.target_component,
                    178,  # MAV_CMD_DO_CHANGE_SPEED
                    0,
                    1,  # Speed type: 1 = ground speed
                    speed,
                    -1,  # Throttle: -1 = no change
                    0, 0, 0, 0
                )
                message = f"Speed change to {speed} m/s command sent"
            
            else:
                return EmergencyResponse(
                    success=False,
                    command=command.value,
                    drone_id=drone_id,
                    timestamp=datetime.now(),
                    message=f"Unknown command: {command.value}"
                )
            
            # Get current telemetry if available
            telemetry = self._telemetry_cache.get(system_id)
            
            logger.info(f"Emergency command sent: {command.value} to drone {drone_id} (system {system_id})")
            
            return EmergencyResponse(
                success=True,
                command=command.value,
                drone_id=drone_id,
                timestamp=datetime.now(),
                message=message,
                telemetry=telemetry
            )
            
        except Exception as e:
            logger.error(f"Failed to send emergency command: {e}", exc_info=True)
            return EmergencyResponse(
                success=False,
                command=command.value,
                drone_id=drone_id,
                timestamp=datetime.now(),
                message=f"Command execution failed: {str(e)}"
            )
    
    def _parse_system_id(self, drone_id: str) -> int:
        """
        Parse MAVLink system ID from drone identifier.
        
        This is a simplified implementation. In production, maintain a proper
        mapping between drone IDs and MAVLink system IDs.
        """
        try:
            # Try to extract numeric part from drone_id (e.g., "drone_001" -> 1)
            import re
            match = re.search(r'(\d+)', drone_id)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.warning(f"Could not parse system ID from {drone_id}: {e}")
        
        # Default to system 1
        return 1
    
    def is_connected(self) -> bool:
        """Check if emergency connection is active."""
        return self._connected
    
    def get_last_heartbeat(self, system_id: int) -> Optional[datetime]:
        """Get timestamp of last heartbeat from specific system."""
        return self._last_heartbeat.get(system_id)
    
    def get_telemetry(self, system_id: int) -> Optional[Dict]:
        """Get cached telemetry data for specific system."""
        return self._telemetry_cache.get(system_id)
    
    def get_all_systems(self) -> list:
        """Get list of all detected system IDs."""
        return list(self._last_heartbeat.keys())


# Global emergency connection instance (lazy-initialized)
_emergency_connection: Optional[EmergencyMAVLinkConnection] = None


async def get_emergency_connection(connection_string: str = "udp:127.0.0.1:14550") -> Optional[EmergencyMAVLinkConnection]:
    """
    Get or create global emergency MAVLink connection.
    
    Args:
        connection_string: MAVLink connection string
        
    Returns:
        EmergencyMAVLinkConnection instance or None if unavailable
    """
    global _emergency_connection
    
    if _emergency_connection is None:
        if not _lazy_import_mavlink():
            logger.error("Cannot create emergency connection: pymavlink not available")
            return None
        
        _emergency_connection = EmergencyMAVLinkConnection(connection_string)
        if not await _emergency_connection.connect():
            _emergency_connection = None
            return None
    
    return _emergency_connection


async def send_emergency_rtl(drone_id: str, connection_string: str = "udp:127.0.0.1:14550") -> EmergencyResponse:
    """
    Quick emergency function to send Return to Launch command.
    
    Args:
        drone_id: Target drone identifier
        connection_string: MAVLink connection string
        
    Returns:
        EmergencyResponse with execution result
    """
    conn = await get_emergency_connection(connection_string)
    if conn:
        return await conn.send_emergency_command(EmergencyCommand.RETURN_TO_LAUNCH, drone_id)
    else:
        return EmergencyResponse(
            success=False,
            command=EmergencyCommand.RETURN_TO_LAUNCH.value,
            drone_id=drone_id,
            timestamp=datetime.now(),
            message="Emergency MAVLink connection unavailable"
        )


async def send_emergency_land(drone_id: str, connection_string: str = "udp:127.0.0.1:14550") -> EmergencyResponse:
    """
    Quick emergency function to send Land command.
    
    Args:
        drone_id: Target drone identifier
        connection_string: MAVLink connection string
        
    Returns:
        EmergencyResponse with execution result
    """
    conn = await get_emergency_connection(connection_string)
    if conn:
        return await conn.send_emergency_command(EmergencyCommand.LAND_NOW, drone_id)
    else:
        return EmergencyResponse(
            success=False,
            command=EmergencyCommand.LAND_NOW.value,
            drone_id=drone_id,
            timestamp=datetime.now(),
            message="Emergency MAVLink connection unavailable"
        )

