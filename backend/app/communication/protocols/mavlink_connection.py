"""
MAVLink Connection for SAR Drone Swarm
Handles real MAVLink protocol communication with drones.
"""

import asyncio
import logging
import serial
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import struct
import threading
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
from app.core.config import settings

logger = logging.getLogger(__name__)

class MAVLinkConnection:
    """Real MAVLink protocol implementation for drone communication"""
    
    def __init__(self, connection_id: str, connection_string: str):
        self.logger = logging.getLogger(__name__)
        self.connection_id = connection_id
        self.connection_string = connection_string
        self.master = None
        self.is_connected = False
        self.is_running = False
        self.heartbeat_interval = 1.0  # seconds
        self.last_heartbeat = None
        self.telemetry_data = {}
        self.command_callbacks: List[Callable] = []
        self.telemetry_callbacks: List[Callable] = []
        self.connection_callbacks: List[Callable] = []
        self.disconnection_callbacks: List[Callable] = []
        self.message_handlers: Dict[int, Callable] = {}
        self.armed = False
        self.mode = "UNKNOWN"
        self.battery_voltage = 0.0
        self.battery_remaining = 0.0
        self.gps_fix = 0
        self.altitude = 0.0
        self.latitude = 0.0
        self.longitude = 0.0
        self.heading = 0.0
        self.ground_speed = 0.0
        self.vertical_speed = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        
    async def connect(self) -> bool:
        """Connect to the drone via MAVLink"""
        try:
            self.logger.info(f"Connecting to drone via MAVLink: {self.connection_string}")
            
            # Create MAVLink connection
            self.master = mavutil.mavlink_connection(self.connection_string)
            
            if not self.master:
                self.logger.error(f"Failed to create MAVLink connection: {self.connection_string}")
                return False
            
            # Wait for heartbeat
            self.logger.info("Waiting for heartbeat...")
            heartbeat_received = False
            timeout = 30  # 30 seconds timeout
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
                if msg:
                    self.logger.info(f"Heartbeat received from system {msg.get_srcSystem()}")
                    heartbeat_received = True
                    break
            
            if not heartbeat_received:
                self.logger.error("Heartbeat timeout - drone not responding")
                return False
            
            # Request data streams
            await self._request_data_streams()
            
            # Start background tasks
            self.is_running = True
            asyncio.create_task(self._heartbeat_monitor())
            asyncio.create_task(self._message_processor())
            asyncio.create_task(self._telemetry_updater())
            
            self.is_connected = True
            self.last_heartbeat = datetime.utcnow()
            
            # Notify connection callbacks
            for callback in self.connection_callbacks:
                try:
                    await callback(self.connection_id, self.master)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
            
            self.logger.info(f"Successfully connected to drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to drone: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the drone"""
        try:
            self.is_running = False
            self.is_connected = False
            
            if self.master:
                self.master.close()
                self.master = None
            
            # Notify disconnection callbacks
            for callback in self.disconnection_callbacks:
                try:
                    await callback(self.connection_id)
                except Exception as e:
                    self.logger.error(f"Error in disconnection callback: {e}")
            
            self.logger.info(f"Disconnected from drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from drone: {e}", exc_info=True)
            return False
    
    async def _request_data_streams(self) -> None:
        """Request data streams from the drone"""
        try:
            # Request basic telemetry at 10Hz
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_DATA_STREAM_ALL,
                10,  # 10Hz
                1    # Enable
            )
            
            # Request GPS data at 5Hz
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_DATA_STREAM_POSITION,
                5,   # 5Hz
                1    # Enable
            )
            
            self.logger.info("Requested data streams from drone")
            
        except Exception as e:
            self.logger.error(f"Error requesting data streams: {e}")
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor heartbeat from the drone"""
        try:
            while self.is_running and self.is_connected:
                current_time = datetime.utcnow()
                
                # Check if heartbeat is too old
                if self.last_heartbeat:
                    time_since_heartbeat = (current_time - self.last_heartbeat).total_seconds()
                    if time_since_heartbeat > 10:  # 10 seconds timeout
                        self.logger.warning(f"Heartbeat timeout for drone {self.connection_id}")
                        await self.disconnect()
                        break
                
                await asyncio.sleep(self.heartbeat_interval)
                
        except Exception as e:
            self.logger.error(f"Error in heartbeat monitor: {e}", exc_info=True)
    
    async def _message_processor(self) -> None:
        """Process incoming MAVLink messages"""
        try:
            while self.is_running and self.is_connected and self.master:
                try:
                    # Receive message with timeout
                    msg = self.master.recv_match(blocking=False, timeout=0.1)
                    
                    if msg:
                        await self._handle_message(msg)
                    
                    await asyncio.sleep(0.01)  # Small delay to prevent CPU overload
                    
                except Exception as e:
                    self.logger.error(f"Error processing MAVLink message: {e}")
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Error in message processor: {e}", exc_info=True)
    
    async def _handle_message(self, msg) -> None:
        """Handle a specific MAVLink message"""
        try:
            msg_type = msg.get_type()
            
            # Update last heartbeat
            if msg_type == 'HEARTBEAT':
                self.last_heartbeat = datetime.utcnow()
                self.armed = bool(msg.base_mode & mavlink2.MAV_MODE_FLAG_SAFETY_ARMED)
                self.mode = mavlink2.mode_mapping_acronym.get(msg.custom_mode, "UNKNOWN")
            
            # Handle specific message types
            elif msg_type == 'SYS_STATUS':
                self.battery_voltage = msg.voltage_battery / 1000.0  # Convert to volts
                self.battery_remaining = msg.battery_remaining
            
            elif msg_type == 'GPS_RAW_INT':
                self.gps_fix = msg.fix_type
                self.latitude = msg.lat / 1e7  # Convert to degrees
                self.longitude = msg.lon / 1e7
                self.altitude = msg.alt / 1000.0  # Convert to meters
            
            elif msg_type == 'VFR_HUD':
                self.altitude = msg.alt
                self.ground_speed = msg.groundspeed
                self.heading = msg.heading
                self.throttle = msg.throttle
            
            elif msg_type == 'ATTITUDE':
                self.roll = msg.roll
                self.pitch = msg.pitch
                self.yaw = msg.yaw
            
            elif msg_type == 'GLOBAL_POSITION_INT':
                self.latitude = msg.lat / 1e7
                self.longitude = msg.lon / 1e7
                self.altitude = msg.alt / 1000.0
                self.relative_altitude = msg.relative_alt / 1000.0
                self.heading = msg.hdg / 100.0
                self.ground_speed = msg.vx / 100.0
                self.vertical_speed = msg.vz / 100.0
            
            # Call custom message handlers
            if msg_type in self.message_handlers:
                handler = self.message_handlers[msg_type]
                try:
                    await handler(msg)
                except Exception as e:
                    self.logger.error(f"Error in message handler for {msg_type}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling message {msg.get_type()}: {e}")
    
    async def _telemetry_updater(self) -> None:
        """Update telemetry data and notify callbacks"""
        try:
            while self.is_running and self.is_connected:
                # Update telemetry data
                self.telemetry_data = {
                    'connection_id': self.connection_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'armed': self.armed,
                    'mode': self.mode,
                    'battery_voltage': self.battery_voltage,
                    'battery_remaining': self.battery_remaining,
                    'gps_fix': self.gps_fix,
                    'latitude': self.latitude,
                    'longitude': self.longitude,
                    'altitude': self.altitude,
                    'heading': self.heading,
                    'ground_speed': self.ground_speed,
                    'vertical_speed': self.vertical_speed,
                    'roll': self.roll,
                    'pitch': self.pitch,
                    'yaw': self.yaw,
                    'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
                }
                
                # Notify telemetry callbacks
                for callback in self.telemetry_callbacks:
                    try:
                        await callback(self.connection_id, self.telemetry_data)
                    except Exception as e:
                        self.logger.error(f"Error in telemetry callback: {e}")
                
                await asyncio.sleep(0.1)  # Update at 10Hz
                
        except Exception as e:
            self.logger.error(f"Error in telemetry updater: {e}", exc_info=True)
    
    async def arm_drone(self) -> bool:
        """Arm the drone"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send arm command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # Confirmation
                1,  # Arm (1 = arm, 0 = disarm)
                0, 0, 0, 0, 0, 0  # Parameters
            )
            
            self.logger.info(f"Arm command sent to drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error arming drone: {e}")
            return False
    
    async def disarm_drone(self) -> bool:
        """Disarm the drone"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send disarm command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_COMPONENT_ARM_DISARM,
                0,  # Confirmation
                0,  # Disarm (1 = arm, 0 = disarm)
                0, 0, 0, 0, 0, 0  # Parameters
            )
            
            self.logger.info(f"Disarm command sent to drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disarming drone: {e}")
            return False
    
    async def set_mode(self, mode: str) -> bool:
        """Set flight mode"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Map mode string to MAVLink mode
            mode_mapping = {
                'STABILIZE': mavlink2.MAV_MODE_STABILIZE_DISARMED,
                'ACRO': mavlink2.MAV_MODE_ACRO_DISARMED,
                'ALT_HOLD': mavlink2.MAV_MODE_ALT_HOLD_DISARMED,
                'AUTO': mavlink2.MAV_MODE_AUTO_DISARMED,
                'GUIDED': mavlink2.MAV_MODE_GUIDED_DISARMED,
                'LOITER': mavlink2.MAV_MODE_LOITER_DISARMED,
                'RTL': mavlink2.MAV_MODE_RTL_DISARMED,
                'LAND': mavlink2.MAV_MODE_LAND_DISARMED
            }
            
            if mode not in mode_mapping:
                self.logger.error(f"Unknown mode: {mode}")
                return False
            
            # Send mode change command
            self.master.mav.set_mode_send(
                self.master.target_system,
                mavlink2.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_mapping[mode]
            )
            
            self.logger.info(f"Mode change command sent to drone {self.connection_id}: {mode}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting mode: {e}")
            return False
    
    async def takeoff(self, altitude: float) -> bool:
        """Command drone to takeoff"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send takeoff command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_NAV_TAKEOFF,
                0,  # Confirmation
                0,  # Minimum pitch
                0, 0, 0, 0, 0,  # Parameters
                altitude  # Takeoff altitude
            )
            
            self.logger.info(f"Takeoff command sent to drone {self.connection_id} to {altitude}m")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending takeoff command: {e}")
            return False
    
    async def goto_position(self, latitude: float, longitude: float, 
                          altitude: float) -> bool:
        """Command drone to go to a specific position"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send position command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_NAV_WAYPOINT,
                0,  # Confirmation
                0,  # Hold time
                0, 0, 0, 0,  # Parameters
                latitude,   # Latitude
                longitude,  # Longitude
                altitude    # Altitude
            )
            
            self.logger.info(f"Goto position command sent to drone {self.connection_id}: {latitude}, {longitude}, {altitude}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending goto position command: {e}")
            return False
    
    async def land(self) -> bool:
        """Command drone to land"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send land command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_NAV_LAND,
                0,  # Confirmation
                0, 0, 0, 0, 0, 0, 0  # Parameters
            )
            
            self.logger.info(f"Land command sent to drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending land command: {e}")
            return False
    
    async def return_to_launch(self) -> bool:
        """Command drone to return to launch"""
        try:
            if not self.is_connected or not self.master:
                self.logger.error("Drone not connected")
                return False
            
            # Send RTL command
            self.master.mav.command_long_send(
                self.master.target_system,
                self.master.target_component,
                mavlink2.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                0,  # Confirmation
                0, 0, 0, 0, 0, 0, 0  # Parameters
            )
            
            self.logger.info(f"RTL command sent to drone {self.connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending RTL command: {e}")
            return False
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
    
    def register_telemetry_callback(self, callback: Callable) -> None:
        """Register a callback for telemetry updates"""
        self.telemetry_callbacks.append(callback)
    
    def register_connection_callback(self, callback: Callable) -> None:
        """Register a callback for connection events"""
        self.connection_callbacks.append(callback)
    
    def register_disconnection_callback(self, callback: Callable) -> None:
        """Register a callback for disconnection events"""
        self.disconnection_callbacks.append(callback)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current drone status"""
        try:
            return {
                'connection_id': self.connection_id,
                'is_connected': self.is_connected,
                'is_running': self.is_running,
                'armed': self.armed,
                'mode': self.mode,
                'battery_voltage': self.battery_voltage,
                'battery_remaining': self.battery_remaining,
                'gps_fix': self.gps_fix,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'altitude': self.altitude,
                'heading': self.heading,
                'ground_speed': self.ground_speed,
                'vertical_speed': self.vertical_speed,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'telemetry_data': self.telemetry_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

# Global connection manager
class MAVLinkConnectionManager:
    """Manages multiple MAVLink connections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, MAVLinkConnection] = {}
    
    async def create_connection(self, connection_id: str, 
                              connection_string: str) -> MAVLinkConnection:
        """Create a new MAVLink connection"""
        try:
            connection = MAVLinkConnection(connection_id, connection_string)
            self.connections[connection_id] = connection
            return connection
            
        except Exception as e:
            self.logger.error(f"Error creating MAVLink connection: {e}")
            raise
    
    async def connect_drone(self, connection_id: str, 
                          connection_string: str) -> bool:
        """Connect to a drone"""
        try:
            connection = await self.create_connection(connection_id, connection_string)
            return await connection.connect()
            
        except Exception as e:
            self.logger.error(f"Error connecting to drone: {e}")
            return False
    
    async def disconnect_drone(self, connection_id: str) -> bool:
        """Disconnect from a drone"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                success = await connection.disconnect()
                del self.connections[connection_id]
                return success
            return False
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from drone: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[MAVLinkConnection]:
        """Get a connection by ID"""
        return self.connections.get(connection_id)
    
    def get_all_connections(self) -> Dict[str, MAVLinkConnection]:
        """Get all connections"""
        return self.connections.copy()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all connections"""
        try:
            status = {
                'total_connections': len(self.connections),
                'active_connections': 0,
                'connections': {}
            }
            
            for conn_id, connection in self.connections.items():
                conn_status = await connection.get_status()
                status['connections'][conn_id] = conn_status
                
                if conn_status.get('is_connected', False):
                    status['active_connections'] += 1
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

# Global instance
mavlink_manager = MAVLinkConnectionManager()

# Convenience functions
async def connect_drone(connection_id: str, connection_string: str) -> bool:
    """Connect to a drone via MAVLink"""
    return await mavlink_manager.connect_drone(connection_id, connection_string)

async def disconnect_drone(connection_id: str) -> bool:
    """Disconnect from a drone"""
    return await mavlink_manager.disconnect_drone(connection_id)

def get_connection(connection_id: str) -> Optional[MAVLinkConnection]:
    """Get a MAVLink connection"""
    return mavlink_manager.get_connection(connection_id)