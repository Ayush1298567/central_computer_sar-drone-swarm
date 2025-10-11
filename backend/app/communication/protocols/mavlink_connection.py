"""
MAVLink Connection for Drone Communication
Implements MAVLink protocol for ArduPilot/PX4 drones
"""
import asyncio
import serial
import socket
import logging
from typing import Dict, Optional, Union
from datetime import datetime
import threading

try:
    from pymavlink import mavutil
    MAVLINK_AVAILABLE = True
except ImportError:
    MAVLINK_AVAILABLE = False
    mavutil = None

from .base_connection import BaseConnection, ConnectionConfig, DroneMessage, ConnectionStatus

logger = logging.getLogger(__name__)

class MAVLinkConnectionConfig(ConnectionConfig):
    """MAVLink-specific connection configuration"""
    connection_type: str = "serial"  # serial, tcp, udp
    baudrate: int = 57600  # For serial connections
    device: str = "/dev/ttyUSB0"  # For serial connections
    mavlink_version: int = 2  # MAVLink version (1 or 2)
    heartbeat_interval: float = 1.0  # MAVLink heartbeat interval
    system_id: int = 255  # Ground control system ID
    component_id: int = 190  # Ground control component ID

class MAVLinkConnection(BaseConnection):
    """MAVLink-based drone connection"""
    
    def __init__(self, connection_id: str, config: MAVLinkConnectionConfig):
        super().__init__(connection_id, config)
        self.config: MAVLinkConnectionConfig = config
        self.mav = None
        self._mavlink_thread = None
        self._message_callbacks = {}
        
        if not MAVLINK_AVAILABLE:
            logger.error("pymavlink not available. Install with: pip install pymavlink")
    
    async def connect(self) -> bool:
        """Establish MAVLink connection to drone"""
        try:
            if not MAVLINK_AVAILABLE:
                logger.error("MAVLink not available")
                self.status = ConnectionStatus.FAILED
                return False
            
            async with self._connection_lock:
                if self.status == ConnectionStatus.CONNECTED:
                    return True
                
                self.status = ConnectionStatus.CONNECTING
                
                # Create MAVLink connection string
                connection_string = self._build_connection_string()
                
                # Create MAVLink connection
                self.mav = mavutil.mavlink_connection(
                    connection_string,
                    source_system=self.config.system_id,
                    source_component=self.config.component_id,
                    dialect='ardupilotmega'  # Use ArduPilot dialect
                )
                
                # Wait for heartbeat
                if await self._wait_for_heartbeat():
                    self.status = ConnectionStatus.CONNECTED
                    self.last_heartbeat = datetime.utcnow()
                    
                    # Start MAVLink message processing
                    self._mavlink_thread = threading.Thread(
                        target=self._process_mavlink_messages,
                        daemon=True
                    )
                    self._mavlink_thread.start()
                    
                    logger.info(f"MAVLink connection established: {connection_string}")
                    return True
                else:
                    logger.error("MAVLink heartbeat timeout")
                    self.status = ConnectionStatus.TIMEOUT
                    return False
                
        except Exception as e:
            logger.error(f"Failed to connect via MAVLink: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    def _build_connection_string(self) -> str:
        """Build MAVLink connection string"""
        if self.config.connection_type == "serial":
            return f"{self.config.device}:{self.config.baudrate}"
        elif self.config.connection_type == "tcp":
            return f"tcp:{self.config.host}:{self.config.port}"
        elif self.config.connection_type == "udp":
            return f"udp:{self.config.host}:{self.config.port}"
        else:
            raise ValueError(f"Unsupported MAVLink connection type: {self.config.connection_type}")
    
    async def _wait_for_heartbeat(self) -> bool:
        """Wait for MAVLink heartbeat from drone"""
        try:
            # Wait for heartbeat message
            heartbeat = self.mav.wait_heartbeat(timeout=self.config.timeout)
            if heartbeat:
                logger.info(f"Heartbeat received from system {heartbeat.get_srcSystem()}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for heartbeat: {e}")
            return False
    
    def _process_mavlink_messages(self):
        """Process incoming MAVLink messages in background thread"""
        while self._running and self.mav:
            try:
                # Get next message
                msg = self.mav.recv_match(blocking=True, timeout=1.0)
                if msg:
                    # Convert to our message format
                    drone_message = self._convert_mavlink_message(msg)
                    if drone_message:
                        # Put message in queue for processing
                        asyncio.run_coroutine_threadsafe(
                            self._handle_message(drone_message),
                            asyncio.get_event_loop()
                        )
                
            except Exception as e:
                logger.error(f"Error processing MAVLink message: {e}")
                if self._running:
                    asyncio.sleep(0.1)
    
    def _convert_mavlink_message(self, msg) -> Optional[DroneMessage]:
        """Convert MAVLink message to our standard format"""
        try:
            message_type = msg.get_type()
            
            if message_type == "HEARTBEAT":
                # Update heartbeat
                self.last_heartbeat = datetime.utcnow()
                return None  # Heartbeat is handled separately
            
            elif message_type == "GLOBAL_POSITION_INT":
                # Telemetry message
                return DroneMessage(
                    message_id=f"mav_{msg.seq}",
                    drone_id=str(msg.get_srcSystem()),
                    message_type="telemetry",
                    payload={
                        "position": {
                            "lat": msg.lat / 1e7,
                            "lon": msg.lon / 1e7,
                            "alt": msg.alt / 1000.0
                        },
                        "heading": msg.hdg / 100.0,
                        "ground_speed": msg.vx / 100.0,
                        "vertical_speed": msg.vz / 100.0
                    },
                    timestamp=datetime.utcnow()
                )
            
            elif message_type == "SYS_STATUS":
                # System status message
                return DroneMessage(
                    message_id=f"mav_{msg.seq}",
                    drone_id=str(msg.get_srcSystem()),
                    message_type="system_status",
                    payload={
                        "battery_voltage": msg.voltage_battery / 1000.0,
                        "battery_current": msg.current_battery / 100.0,
                        "battery_remaining": msg.battery_remaining,
                        "errors": {
                            "sensors": msg.onboard_control_sensors_present,
                            "health": msg.onboard_control_sensors_health,
                            "enabled": msg.onboard_control_sensors_enabled
                        }
                    },
                    timestamp=datetime.utcnow()
                )
            
            elif message_type == "ATTITUDE":
                # Attitude message
                return DroneMessage(
                    message_id=f"mav_{msg.seq}",
                    drone_id=str(msg.get_srcSystem()),
                    message_type="attitude",
                    payload={
                        "roll": msg.roll,
                        "pitch": msg.pitch,
                        "yaw": msg.yaw,
                        "roll_speed": msg.rollspeed,
                        "pitch_speed": msg.pitchspeed,
                        "yaw_speed": msg.yawspeed
                    },
                    timestamp=datetime.utcnow()
                )
            
            else:
                # Generic message
                return DroneMessage(
                    message_id=f"mav_{msg.seq}",
                    drone_id=str(msg.get_srcSystem()),
                    message_type=message_type.lower(),
                    payload=msg.to_dict(),
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error converting MAVLink message: {e}")
            return None
    
    async def disconnect(self) -> bool:
        """Close MAVLink connection"""
        try:
            async with self._connection_lock:
                self.status = ConnectionStatus.DISCONNECTED
                
                # Stop MAVLink processing
                if self._mavlink_thread and self._mavlink_thread.is_alive():
                    # Thread will stop when _running becomes False
                    pass
                
                # Close MAVLink connection
                if self.mav:
                    self.mav.close()
                    self.mav = None
                
                logger.info(f"MAVLink connection closed: {self.connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error closing MAVLink connection: {e}")
            return False
    
    async def send_message(self, message: DroneMessage) -> bool:
        """Send message via MAVLink"""
        try:
            if self.status != ConnectionStatus.CONNECTED or not self.mav:
                logger.warning(f"Cannot send message, MAVLink connection not established: {self.connection_id}")
                return False
            
            # Convert message to MAVLink command
            if message.message_type == "command":
                return await self._send_mavlink_command(message)
            else:
                # Send as generic message
                return await self._send_mavlink_message(message)
                
        except Exception as e:
            logger.error(f"Error sending message via MAVLink: {e}")
            return False
    
    async def _send_mavlink_command(self, message: DroneMessage) -> bool:
        """Send command via MAVLink"""
        try:
            # CommandMessage has direct fields; fall back to payload if needed
            command_type = getattr(message, "command_type", None)
            parameters = getattr(message, "parameters", None)
            if not command_type:
                payload = getattr(message, "payload", {}) or {}
                command_type = payload.get("command_type")
                parameters = payload.get("parameters", {})
            if parameters is None:
                parameters = {}

            # Map command types to MAVLink commands using pymavlink constants
            mav = mavutil.mavlink
            mavlink_commands = {
                "takeoff": getattr(mav, "MAV_CMD_NAV_TAKEOFF", 22),
                "land": getattr(mav, "MAV_CMD_NAV_LAND", 21),
                "return_home": getattr(mav, "MAV_CMD_NAV_RETURN_TO_LAUNCH", 20),
                "set_altitude": getattr(mav, "MAV_CMD_NAV_CONTINUE_AND_CHANGE_ALT", 30),
                "set_heading": getattr(mav, "MAV_CMD_CONDITION_YAW", 115),
                # Immediate flight termination; supported on ArduPilot/PX4 when enabled
                "emergency_stop": getattr(mav, "MAV_CMD_DO_FLIGHTTERMINATION", 185),
            }

            command_id = mavlink_commands.get(command_type)
            if command_id is None:
                logger.warning(f"Unknown command type: {command_type}")
                return False

            # Send command
            self.mav.mav.command_long_send(
                self.mav.target_system,
                self.mav.target_component,
                command_id,
                0,  # confirmation
                *self._prepare_command_params(command_type, parameters)
            )

            logger.info(f"Sent MAVLink command: {command_type}")
            return True

        except Exception as e:
            logger.error(f"Error sending MAVLink command: {e}")
            return False
    
    def _prepare_command_params(self, command_type: str, parameters: Dict) -> list:
        """Prepare command parameters for MAVLink"""
        param_count = 7  # MAVLink commands have 7 parameters
        params = [0.0] * param_count
        
        if command_type == "takeoff":
            params[0] = parameters.get("altitude", 10.0)  # Altitude
            params[1] = 0.0  # Pitch
            params[2] = 0.0  # Empty
            params[3] = 0.0  # Yaw
            params[4] = parameters.get("latitude", 0.0)  # Latitude
            params[5] = parameters.get("longitude", 0.0)  # Longitude
            params[6] = parameters.get("altitude", 10.0)  # Altitude
            
        elif command_type == "land":
            params[0] = 0.0  # Abort altitude
            params[1] = 0.0  # Land mode
            params[2] = 0.0  # Empty
            params[3] = 0.0  # Yaw angle
            params[4] = parameters.get("latitude", 0.0)  # Latitude
            params[5] = parameters.get("longitude", 0.0)  # Longitude
            params[6] = parameters.get("altitude", 0.0)  # Altitude
            
        elif command_type == "set_altitude":
            params[0] = parameters.get("altitude", 0.0)  # Altitude
            
        elif command_type == "set_heading":
            params[0] = parameters.get("heading", 0.0)  # Yaw angle
            params[1] = parameters.get("speed", 0.0)    # Speed
            params[2] = parameters.get("direction", 0)  # Direction
            params[3] = parameters.get("relative", 0)   # Relative angle
        elif command_type == "return_home":
            # No parameters required for RTL
            pass
        elif command_type == "emergency_stop":
            # MAV_CMD_DO_FLIGHTTERMINATION param1=1 to terminate
            params[0] = 1.0
        
        return params
    
    async def _send_mavlink_message(self, message: DroneMessage) -> bool:
        """Send generic message via MAVLink"""
        try:
            # For now, just log the message
            # In a full implementation, you would convert to appropriate MAVLink message
            logger.info(f"Sending generic MAVLink message: {message.message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending generic MAVLink message: {e}")
            return False
    
    async def receive_message(self) -> Optional[DroneMessage]:
        """Receive message via MAVLink"""
        # MAVLink messages are processed in background thread
        # This method is not used in MAVLink implementation
        return None
    
    def get_connection_info(self) -> Dict:
        """Get MAVLink connection information"""
        return {
            **self.get_status(),
            "connection_type": self.config.connection_type,
            "device": self.config.device if self.config.connection_type == "serial" else None,
            "baudrate": self.config.baudrate if self.config.connection_type == "serial" else None,
            "host": self.config.host if self.config.connection_type in ["tcp", "udp"] else None,
            "port": self.config.port if self.config.connection_type in ["tcp", "udp"] else None,
            "mavlink_version": self.config.mavlink_version,
            "system_id": self.config.system_id,
            "component_id": self.config.component_id
        }
