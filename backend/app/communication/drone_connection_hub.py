"""
Drone Connection Hub for SAR Mission Commander
Central hub for managing all drone connections and communication protocols
"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import uuid

from .drone_registry import (
    DroneRegistry, DroneInfo, DroneStatus, DroneConnectionType,
    DroneCapabilities, drone_registry, get_registry
)
from .protocols.base_connection import BaseConnection, ConnectionStatus, DroneMessage, TelemetryMessage, CommandMessage

# Lazy/optional protocol imports to avoid heavy deps at import time
try:  # WiFi
    from .protocols.wifi_connection import WiFiConnection, WiFiConnectionConfig
except Exception:  # pragma: no cover - not needed for lightweight tests
    WiFiConnection = None
    WiFiConnectionConfig = None

try:  # LoRa
    from .protocols.lora_connection import LoRaConnection, LoRaConnectionConfig
except Exception:  # pragma: no cover
    LoRaConnection = None
    LoRaConnectionConfig = None

try:  # MAVLink (may require pyserial/pymavlink)
    from .protocols.mavlink_connection import MAVLinkConnection, MAVLinkConnectionConfig
except Exception:  # pragma: no cover
    MAVLinkConnection = None
    MAVLinkConnectionConfig = None

try:  # WebSocket
    from .protocols.websocket_connection import WebSocketDroneConnection, WebSocketConnectionConfig
except Exception:  # pragma: no cover
    WebSocketDroneConnection = None
    WebSocketConnectionConfig = None

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    connection_id: str
    drone_id: str
    connection_type: DroneConnectionType
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    connection_uptime: float = 0.0
    last_message_time: Optional[datetime] = None
    average_latency: float = 0.0
    connection_stability: float = 1.0  # 0-1 scale

class DroneConnectionHub:
    """Central hub for managing drone connections"""
    
    def __init__(self, redis_channel: str = "missions"):
        # Use dynamic registry getter so tests creating new instances are seen
        self.registry = get_registry()
        self.connections: Dict[str, BaseConnection] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.telemetry_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        self.command_callbacks: List[Callable] = []
        self._running = False
        self._monitor_task = None
        self._metrics_task = None
        self.redis_channel = redis_channel
        
    async def start(self) -> bool:
        """Start the drone connection hub"""
        try:
            self._running = True
            
            # Start drone discovery
            await self.registry.start_discovery()
            
            # Start monitoring tasks
            self._monitor_task = asyncio.create_task(self._monitor_connections())
            self._metrics_task = asyncio.create_task(self._update_metrics())
            
            logger.info("Drone Connection Hub started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Drone Connection Hub: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the drone connection hub"""
        try:
            self._running = False
            
            # Stop monitoring tasks
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass
            
            # Stop drone discovery
            await self.registry.stop_discovery()
            
            # Disconnect all connections
            for connection_id in list(self.connections.keys()):
                await self.disconnect_drone(connection_id)
            
            logger.info("Drone Connection Hub stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Drone Connection Hub: {e}")
            return False
    
    async def connect_drone(self, drone_info: DroneInfo) -> bool:
        """Connect to a drone using specified protocol"""
        try:
            connection_id = f"{drone_info.drone_id}_{drone_info.connection_type.value}"
            
            if connection_id in self.connections:
                logger.warning(f"Connection already exists for drone {drone_info.drone_id}")
                return True
            
            # Create connection based on type
            connection = await self._create_connection(drone_info)
            if not connection:
                logger.error(f"Failed to create connection for drone {drone_info.drone_id}")
                return False
            
            # Register connection callbacks
            connection.register_telemetry_callback(self._handle_telemetry)
            connection.register_connection_callback(self._handle_connection_status_change)
            
            # Start connection
            if await connection.start():
                if await connection.connect():
                    # Store connection
                    self.connections[connection_id] = connection
                    
                    # Initialize metrics
                    self.connection_metrics[connection_id] = ConnectionMetrics(
                        connection_id=connection_id,
                        drone_id=drone_info.drone_id,
                        connection_type=drone_info.connection_type,
                        last_message_time=datetime.utcnow()
                    )
                    
                    # Update drone status
                    self.registry.update_drone_status(
                        drone_info.drone_id, 
                        DroneStatus.CONNECTED
                    )
                    
                    logger.info(f"Connected to drone {drone_info.drone_id} via {drone_info.connection_type.value}")
                    return True
                else:
                    logger.error(f"Failed to establish connection to drone {drone_info.drone_id}")
                    return False
            else:
                logger.error(f"Failed to start connection for drone {drone_info.drone_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to drone {drone_info.drone_id}: {e}")
            return False
    
    async def disconnect_drone(self, connection_id: str) -> bool:
        """Disconnect from a drone"""
        try:
            if connection_id not in self.connections:
                logger.warning(f"No connection found for {connection_id}")
                return False
            
            connection = self.connections[connection_id]
            
            # Stop and disconnect
            await connection.stop()
            
            # Update drone status
            metrics = self.connection_metrics.get(connection_id)
            if metrics:
                self.registry.update_drone_status(
                    metrics.drone_id, 
                    DroneStatus.DISCONNECTED
                )
            
            # Remove connection and metrics
            del self.connections[connection_id]
            if connection_id in self.connection_metrics:
                del self.connection_metrics[connection_id]
            
            logger.info(f"Disconnected from drone: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting drone {connection_id}: {e}")
            return False
    
    async def send_command(self, drone_id: str, command_type: str, 
                          parameters: Dict[str, Any], priority: int = 1) -> bool:
        """Send command to a drone"""
        try:
            connection = self._get_connection_by_drone_id(drone_id)
            if not connection:
                logger.warning(f"No connection found for drone {drone_id}")
                return False
            
            # Send command
            success = await connection.send_command(
                drone_id, command_type, parameters, priority
            )
            
            if success:
                # Update metrics
                connection_id = self._get_connection_id_by_drone_id(drone_id)
                if connection_id and connection_id in self.connection_metrics:
                    self.connection_metrics[connection_id].messages_sent += 1
                    self.connection_metrics[connection_id].last_message_time = datetime.utcnow()
                
                # Notify callbacks
                for callback in self.command_callbacks:
                    try:
                        await callback(drone_id, command_type, parameters)
                    except Exception as e:
                        logger.error(f"Command callback error: {e}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending command to drone {drone_id}: {e}")
            return False
    
    async def request_telemetry(self, drone_id: str) -> bool:
        """Request telemetry from a drone"""
        try:
            connection = self._get_connection_by_drone_id(drone_id)
            if not connection:
                logger.warning(f"No connection found for drone {drone_id}")
                return False
            
            return await connection.send_telemetry_request(drone_id)
            
        except Exception as e:
            logger.error(f"Error requesting telemetry from drone {drone_id}: {e}")
            return False
    
    def get_connected_drones(self) -> List[DroneInfo]:
        """Get list of connected drones"""
        connected_drones = []
        for connection_id, metrics in self.connection_metrics.items():
            drone_info = self.registry.get_drone(metrics.drone_id)
            if drone_info and drone_info.status == DroneStatus.CONNECTED:
                connected_drones.append(drone_info)
        
        return connected_drones
    
    def get_connection_status(self, drone_id: str) -> Optional[Dict]:
        """Get connection status for a drone"""
        connection = self._get_connection_by_drone_id(drone_id)
        if connection:
            connection_id = self._get_connection_id_by_drone_id(drone_id)
            metrics = self.connection_metrics.get(connection_id)
            
            status_info = connection.get_status()
            if metrics:
                status_info["metrics"] = asdict(metrics)
            
            return status_info
        
        return None
    
    def get_all_connection_status(self) -> Dict[str, Dict]:
        """Get connection status for all drones"""
        status_info = {}
        for connection_id, connection in self.connections.items():
            metrics = self.connection_metrics.get(connection_id)
            status_info[connection_id] = connection.get_status()
            if metrics:
                status_info[connection_id]["metrics"] = asdict(metrics)
        
        return status_info

    # -------------------- Lightweight mission routing API --------------------
    async def send_mission_to_drone(
        self,
        drone_id: str,
        mission_payload: Dict[str, Any],
        use_http: bool = True,
        use_redis: bool = True,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Try HTTP (if registry has a pi_host) and/or Redis publish.
        Looks up optional callables send_mission_http / publish_mission_redis lazily.
        """
        results: Dict[str, Any] = {"http": None, "redis": None}
        pi_host = self.registry.get_pi_host(drone_id) if hasattr(self.registry, "get_pi_host") else None

        if use_http and pi_host:
            try:
                func = globals().get("send_mission_http")
                if not callable(func):
                    from app.communication.pi_communication import send_mission_http as func  # type: ignore
                res = await func(pi_host, mission_payload, timeout=timeout)
                results["http"] = res
            except Exception as e:
                logger.exception("HTTP send failed: %s", e)
                results["http"] = {"error": str(e)}

        if use_redis:
            try:
                pub = globals().get("publish_mission_redis")
                if not callable(pub):
                    from app.communication.pi_communication import publish_mission_redis as pub  # type: ignore
                await pub(drone_id, mission_payload, channel=self.redis_channel)
                results["redis"] = {"published": True}
            except Exception as e:
                logger.exception("Redis publish failed: %s", e)
                results["redis"] = {"error": str(e)}

        return results

    def send_emergency_command(self, drone_id: Optional[str], command: str) -> bool:
        """
        Synchronous emergency command using lazy MAVLink fallback.
        command in {"arm","disarm","rtl","land"}
        """
        try:
            from app.hardware import emergency_mavlink  # lazy import
        except Exception:
            logger.exception("emergency_mavlink not available")
            return False

        cfg = None
        try:
            if hasattr(self.registry, "_store"):
                cfg = self.registry._store.get(drone_id or "", {}).get("meta", {}).get("mav_config")
        except Exception:
            cfg = None

        try:
            if command == "disarm":
                emergency_mavlink.disarm(cfg)
            elif command == "arm":
                emergency_mavlink.arm(cfg)
            elif command == "rtl":
                emergency_mavlink.return_to_launch(cfg)
            elif command == "land":
                emergency_mavlink.land(cfg)
            else:
                raise ValueError("unknown emergency command")
            return True
        except Exception:
            logger.exception("Failed to send emergency command")
            return False
    
    def register_telemetry_callback(self, callback: Callable):
        """Register callback for telemetry data"""
        self.telemetry_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status changes"""
        self.status_callbacks.append(callback)
    
    def register_command_callback(self, callback: Callable):
        """Register callback for commands"""
        self.command_callbacks.append(callback)
    
    async def _create_connection(self, drone_info: DroneInfo) -> Optional[BaseConnection]:
        """Create connection based on drone connection type"""
        try:
            if drone_info.connection_type == DroneConnectionType.WIFI:
                config = WiFiConnectionConfig(
                    host=drone_info.connection_params.get("host", "192.168.1.100"),
                    port=drone_info.connection_params.get("port", 8080),
                    protocol=drone_info.connection_params.get("protocol", "tcp"),
                    timeout=drone_info.connection_params.get("timeout", 10.0)
                )
                return WiFiConnection(drone_info.drone_id, config)
            
            elif drone_info.connection_type == DroneConnectionType.LORA:
                config = LoRaConnectionConfig(
                    frequency=drone_info.connection_params.get("frequency", 868.1),
                    spreading_factor=drone_info.connection_params.get("spreading_factor", 7),
                    bandwidth=drone_info.connection_params.get("bandwidth", 125000),
                    device_path=drone_info.connection_params.get("device_path", "/dev/ttyUSB0")
                )
                return LoRaConnection(drone_info.drone_id, config)
            
            elif drone_info.connection_type == DroneConnectionType.MAVLINK:
                config = MAVLinkConnectionConfig(
                    connection_type=drone_info.connection_params.get("connection_type", "serial"),
                    device=drone_info.connection_params.get("device", "/dev/ttyUSB0"),
                    host=drone_info.connection_params.get("host", "localhost"),
                    port=drone_info.connection_params.get("port", 14550),
                    baudrate=drone_info.connection_params.get("baudrate", 57600)
                )
                return MAVLinkConnection(drone_info.drone_id, config)
            
            elif drone_info.connection_type == DroneConnectionType.WEBSOCKET:
                config = WebSocketConnectionConfig(
                    host=drone_info.connection_params.get("host", "localhost"),
                    port=drone_info.connection_params.get("port", 8080),
                    protocol=drone_info.connection_params.get("protocol", "ws"),
                    path=drone_info.connection_params.get("path", "/ws")
                )
                return WebSocketDroneConnection(drone_info.drone_id, config)
            
            else:
                logger.error(f"Unsupported connection type: {drone_info.connection_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            return None
    
    def _get_connection_by_drone_id(self, drone_id: str) -> Optional[BaseConnection]:
        """Get connection by drone ID"""
        for connection_id, connection in self.connections.items():
            if connection_id.startswith(drone_id):
                return connection
        return None
    
    def _get_connection_id_by_drone_id(self, drone_id: str) -> Optional[str]:
        """Get connection ID by drone ID"""
        for connection_id in self.connections.keys():
            if connection_id.startswith(drone_id):
                return connection_id
        return None
    
    async def _handle_telemetry(self, message: DroneMessage):
        """Handle incoming telemetry data"""
        try:
            # Update metrics
            connection_id = self._get_connection_id_by_drone_id(message.drone_id)
            if connection_id and connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]
                metrics.messages_received += 1
                metrics.last_message_time = datetime.utcnow()
                
                # Estimate message size (rough approximation)
                message_size = len(str(message.payload))
                metrics.bytes_received += message_size
            
            # Update drone registry
            if message.message_type == "telemetry":
                position = message.payload.get("position", {})
                battery_level = message.payload.get("battery_level", 0.0)
                signal_strength = message.payload.get("signal_strength", 0.0)
                
                self.registry.update_drone_status(
                    message.drone_id,
                    DroneStatus.FLYING,  # Assume flying if sending telemetry
                    position=position,
                    battery_level=battery_level,
                    signal_strength=signal_strength
                )
            
            # Notify callbacks
            for callback in self.telemetry_callbacks:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Telemetry callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
    
    async def _handle_connection_status_change(self, drone_id: str, status: ConnectionStatus):
        """Handle connection status changes"""
        try:
            # Update drone registry
            if status == ConnectionStatus.CONNECTED:
                self.registry.update_drone_status(drone_id, DroneStatus.CONNECTED)
            elif status == ConnectionStatus.DISCONNECTED:
                self.registry.update_drone_status(drone_id, DroneStatus.DISCONNECTED)
            elif status == ConnectionStatus.FAILED:
                self.registry.update_drone_status(drone_id, DroneStatus.OFFLINE)
            
            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    await callback(drone_id, status)
                except Exception as e:
                    logger.error(f"Status callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling connection status change: {e}")
    
    async def _monitor_connections(self):
        """Monitor all connections for health"""
        while self._running:
            try:
                for connection_id, connection in list(self.connections.items()):
                    if connection.status != ConnectionStatus.CONNECTED:
                        # Connection lost, attempt reconnection
                        metrics = self.connection_metrics.get(connection_id)
                        if metrics:
                            logger.warning(f"Connection lost for drone {metrics.drone_id}, attempting reconnection")
                            
                            # Get drone info for reconnection
                            drone_info = self.registry.get_drone(metrics.drone_id)
                            if drone_info:
                                await self.disconnect_drone(connection_id)
                                await asyncio.sleep(5)  # Wait before reconnecting
                                await self.connect_drone(drone_info)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(5)
    
    async def _update_metrics(self):
        """Update connection metrics"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                for connection_id, metrics in self.connection_metrics.items():
                    # Update uptime
                    if metrics.last_message_time:
                        uptime = (current_time - metrics.last_message_time).total_seconds()
                        metrics.connection_uptime = max(0, uptime)
                    
                    # Update connection stability (simple metric)
                    if metrics.messages_received > 0:
                        metrics.connection_stability = min(1.0, 
                            metrics.messages_received / (metrics.messages_sent + 1))
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(10)
    
    def get_hub_statistics(self) -> Dict:
        """Get hub statistics"""
        return {
            "total_connections": len(self.connections),
            "active_connections": len([c for c in self.connections.values() 
                                     if c.status == ConnectionStatus.CONNECTED]),
            "discovery_active": self.registry.discovery_active,
            "total_drones": len(self.registry.drones),
            "connected_drones": len(self.get_connected_drones()),
            "connection_types": {
                connection_type.value: len([c for c in self.connections.values() 
                                          if c.connection_id.endswith(connection_type.value)])
                for connection_type in DroneConnectionType
            }
        }

# Global connection hub instance
drone_connection_hub = DroneConnectionHub()

# Provide a getter consistent with lightweight services/tests
_hub_singleton: Optional[DroneConnectionHub] = drone_connection_hub

def get_hub(singleton: bool = True) -> DroneConnectionHub:
    global _hub_singleton
    if singleton:
        if _hub_singleton is None:
            _hub_singleton = DroneConnectionHub()
        return _hub_singleton
    return DroneConnectionHub()
