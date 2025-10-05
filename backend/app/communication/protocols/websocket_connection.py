"""
WebSocket Connection for Drone Communication
Implements WebSocket communication for drone connections
"""
import asyncio
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .base_connection import BaseConnection, ConnectionConfig, DroneMessage, ConnectionStatus

logger = logging.getLogger(__name__)

class WebSocketConnectionConfig(ConnectionConfig):
    """WebSocket-specific connection configuration"""
    protocol: str = "ws"  # ws or wss
    path: str = "/ws"     # WebSocket path
    subprotocols: Optional[list] = None
    ping_interval: float = 20.0
    ping_timeout: float = 20.0
    close_timeout: float = 10.0
    max_size: int = 2**20  # 1MB max message size
    compression: Optional[str] = None

class WebSocketDroneConnection(BaseConnection):
    """WebSocket-based drone connection"""
    
    def __init__(self, connection_id: str, config: WebSocketConnectionConfig):
        super().__init__(connection_id, config)
        self.config: WebSocketConnectionConfig = config
        self.websocket = None
        self._message_queue = asyncio.Queue()
        self._receive_task = None
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to drone"""
        try:
            async with self._connection_lock:
                if self.status == ConnectionStatus.CONNECTED:
                    return True
                
                self.status = ConnectionStatus.CONNECTING
                
                # Build WebSocket URL
                protocol = "wss" if self.config.protocol.lower() == "wss" else "ws"
                url = f"{protocol}://{self.config.host}:{self.config.port}{self.config.path}"
                
                # Create WebSocket connection
                self.websocket = await websockets.connect(
                    url,
                    subprotocols=self.config.subprotocols,
                    ping_interval=self.config.ping_interval,
                    ping_timeout=self.config.ping_timeout,
                    close_timeout=self.config.close_timeout,
                    max_size=self.config.max_size,
                    compression=self.config.compression
                )
                
                # Send connection handshake
                handshake = {
                    "type": "handshake",
                    "connection_id": self.connection_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "capabilities": ["telemetry", "commands", "status"]
                }
                
                await self.websocket.send(json.dumps(handshake))
                
                # Wait for handshake response
                response_data = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=self.config.timeout
                )
                
                response = json.loads(response_data)
                if response.get("status") == "accepted":
                    self.status = ConnectionStatus.CONNECTED
                    self.last_heartbeat = datetime.utcnow()
                    
                    # Start receive task
                    self._receive_task = asyncio.create_task(self._receive_loop())
                    
                    logger.info(f"WebSocket connection established: {url}")
                    return True
                else:
                    logger.error(f"WebSocket handshake rejected: {response}")
                    self.status = ConnectionStatus.FAILED
                    return False
                
        except asyncio.TimeoutError:
            logger.error(f"WebSocket connection timeout to {self.config.host}:{self.config.port}")
            self.status = ConnectionStatus.TIMEOUT
            return False
        except WebSocketException as e:
            logger.error(f"WebSocket connection error: {e}")
            self.status = ConnectionStatus.FAILED
            return False
        except Exception as e:
            logger.error(f"Failed to connect via WebSocket: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    async def disconnect(self) -> bool:
        """Close WebSocket connection"""
        try:
            async with self._connection_lock:
                self.status = ConnectionStatus.DISCONNECTED
                
                # Cancel receive task
                if self._receive_task:
                    self._receive_task.cancel()
                    try:
                        await self._receive_task
                    except asyncio.CancelledError:
                        pass
                
                # Close WebSocket connection
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                
                logger.info(f"WebSocket connection closed: {self.connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error closing WebSocket connection: {e}")
            return False
    
    async def send_message(self, message: DroneMessage) -> bool:
        """Send message via WebSocket"""
        try:
            if self.status != ConnectionStatus.CONNECTED or not self.websocket:
                logger.warning(f"Cannot send message, WebSocket connection not established: {self.connection_id}")
                return False
            
            # Serialize message
            message_data = self._serialize_message(message)
            
            # Send via WebSocket
            await self.websocket.send(message_data)
            logger.debug(f"Sent WebSocket message: {message.message_type}")
            return True
            
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self._handle_connection_lost()
            return False
        except WebSocketException as e:
            logger.error(f"WebSocket error sending message: {e}")
            await self._handle_connection_lost()
            return False
        except Exception as e:
            logger.error(f"Error sending message via WebSocket: {e}")
            return False
    
    async def receive_message(self) -> Optional[DroneMessage]:
        """Receive message via WebSocket"""
        try:
            # Check if message is available in queue
            if not self._message_queue.empty():
                return await self._message_queue.get()
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message via WebSocket: {e}")
            return None
    
    async def _receive_loop(self):
        """Background task to receive WebSocket messages"""
        while self._running and self.websocket:
            try:
                # Wait for message
                message_data = await self.websocket.recv()
                
                # Deserialize message
                message = self._deserialize_message(message_data)
                if message:
                    await self._message_queue.put(message)
                
            except ConnectionClosed:
                logger.info("WebSocket connection closed by remote")
                await self._handle_connection_lost()
                break
            except WebSocketException as e:
                logger.error(f"WebSocket error in receive loop: {e}")
                await self._handle_connection_lost()
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket receive loop: {e}")
                await asyncio.sleep(0.1)
    
    def _serialize_message(self, message: DroneMessage) -> str:
        """Serialize message for WebSocket transmission"""
        message_dict = {
            "message_id": message.message_id,
            "drone_id": message.drone_id,
            "message_type": message.message_type,
            "payload": message.payload,
            "timestamp": message.timestamp.isoformat(),
            "priority": message.priority,
            "response_required": message.response_required
        }
        
        # Add command-specific fields
        if hasattr(message, 'command_type'):
            message_dict["command_type"] = message.command_type
        if hasattr(message, 'parameters'):
            message_dict["parameters"] = message.parameters
        if hasattr(message, 'execution_time'):
            message_dict["execution_time"] = message.execution_time.isoformat() if message.execution_time else None
        
        # Add telemetry-specific fields
        if hasattr(message, 'position'):
            message_dict["position"] = message.position
        if hasattr(message, 'battery_level'):
            message_dict["battery_level"] = message.battery_level
        if hasattr(message, 'speed'):
            message_dict["speed"] = message.speed
        if hasattr(message, 'heading'):
            message_dict["heading"] = message.heading
        if hasattr(message, 'signal_strength'):
            message_dict["signal_strength"] = message.signal_strength
        if hasattr(message, 'gps_accuracy'):
            message_dict["gps_accuracy"] = message.gps_accuracy
        if hasattr(message, 'temperature'):
            message_dict["temperature"] = message.temperature
        if hasattr(message, 'humidity'):
            message_dict["humidity"] = message.humidity
        if hasattr(message, 'wind_speed'):
            message_dict["wind_speed"] = message.wind_speed
        
        return json.dumps(message_dict)
    
    def _deserialize_message(self, data: str) -> Optional[DroneMessage]:
        """Deserialize received WebSocket message"""
        try:
            message_dict = json.loads(data)
            
            # Create base message
            message = DroneMessage(
                message_id=message_dict["message_id"],
                drone_id=message_dict["drone_id"],
                message_type=message_dict["message_type"],
                payload=message_dict["payload"],
                timestamp=datetime.fromisoformat(message_dict["timestamp"]),
                priority=message_dict.get("priority", 1),
                response_required=message_dict.get("response_required", False)
            )
            
            # Add command-specific fields
            if "command_type" in message_dict:
                from .base_connection import CommandMessage
                message = CommandMessage(
                    message_id=message.message_id,
                    drone_id=message.drone_id,
                    message_type=message.message_type,
                    payload=message.payload,
                    timestamp=message.timestamp,
                    priority=message.priority,
                    response_required=message.response_required,
                    command_type=message_dict["command_type"],
                    parameters=message_dict.get("parameters", {}),
                    execution_time=datetime.fromisoformat(message_dict["execution_time"]) if message_dict.get("execution_time") else None
                )
            
            # Add telemetry-specific fields
            if "position" in message_dict:
                from .base_connection import TelemetryMessage
                message = TelemetryMessage(
                    message_id=message.message_id,
                    drone_id=message.drone_id,
                    message_type=message.message_type,
                    payload=message.payload,
                    timestamp=message.timestamp,
                    priority=message.priority,
                    response_required=message.response_required,
                    position=message_dict["position"],
                    battery_level=message_dict["battery_level"],
                    speed=message_dict["speed"],
                    heading=message_dict["heading"],
                    signal_strength=message_dict["signal_strength"],
                    gps_accuracy=message_dict["gps_accuracy"],
                    temperature=message_dict.get("temperature"),
                    humidity=message_dict.get("humidity"),
                    wind_speed=message_dict.get("wind_speed")
                )
            
            return message
            
        except Exception as e:
            logger.error(f"Error deserializing WebSocket message: {e}")
            return None
    
    def get_connection_info(self) -> Dict:
        """Get WebSocket connection information"""
        return {
            **self.get_status(),
            "protocol": self.config.protocol,
            "host": self.config.host,
            "port": self.config.port,
            "path": self.config.path,
            "ping_interval": self.config.ping_interval,
            "ping_timeout": self.config.ping_timeout,
            "max_message_size": self.config.max_size,
            "compression": self.config.compression
        }
