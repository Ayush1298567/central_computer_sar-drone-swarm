"""
WiFi Connection for Drone Communication
Implements TCP/UDP communication over WiFi networks
"""
import asyncio
import socket
import json
import struct
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from .base_connection import BaseConnection, ConnectionConfig, DroneMessage, ConnectionStatus

logger = logging.getLogger(__name__)

class WiFiConnectionConfig(ConnectionConfig):
    """WiFi-specific connection configuration"""
    protocol: str = "tcp"  # tcp or udp
    encryption_key: Optional[str] = None
    compression: bool = False
    multicast_group: Optional[str] = None  # For multicast UDP

class WiFiConnection(BaseConnection):
    """WiFi-based drone connection using TCP/UDP"""
    
    def __init__(self, connection_id: str, config: WiFiConnectionConfig):
        super().__init__(connection_id, config)
        self.config: WiFiConnectionConfig = config
        self.socket = None
        self.reader = None
        self.writer = None
        self._message_buffer = b""
        self._message_lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        """Establish WiFi connection to drone"""
        try:
            async with self._connection_lock:
                if self.status == ConnectionStatus.CONNECTED:
                    return True
                
                self.status = ConnectionStatus.CONNECTING
                
                if self.config.protocol.lower() == "tcp":
                    return await self._connect_tcp()
                elif self.config.protocol.lower() == "udp":
                    return await self._connect_udp()
                else:
                    logger.error(f"Unsupported protocol: {self.config.protocol}")
                    self.status = ConnectionStatus.FAILED
                    return False
                
        except Exception as e:
            logger.error(f"Failed to connect via WiFi: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    async def _connect_tcp(self) -> bool:
        """Establish TCP connection"""
        try:
            # Create TCP connection
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.config.host,
                    self.config.port
                ),
                timeout=self.config.timeout
            )
            
            # Send connection handshake
            handshake = {
                "type": "handshake",
                "connection_id": self.connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            
            await self._send_raw_data(json.dumps(handshake).encode())
            
            # Wait for handshake response
            response_data = await self._receive_raw_data()
            if response_data:
                response = json.loads(response_data.decode())
                if response.get("status") == "accepted":
                    self.status = ConnectionStatus.CONNECTED
                    self.last_heartbeat = datetime.utcnow()
                    logger.info(f"TCP connection established to {self.config.host}:{self.config.port}")
                    return True
            
            logger.error("TCP handshake failed")
            self.status = ConnectionStatus.FAILED
            return False
            
        except asyncio.TimeoutError:
            logger.error(f"TCP connection timeout to {self.config.host}:{self.config.port}")
            self.status = ConnectionStatus.TIMEOUT
            return False
        except Exception as e:
            logger.error(f"TCP connection error: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    async def _connect_udp(self) -> bool:
        """Establish UDP connection"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            
            # Bind to local port if specified
            if hasattr(self.config, 'local_port') and self.config.local_port:
                self.socket.bind(('', self.config.local_port))
            
            # Send connection handshake
            handshake = {
                "type": "handshake",
                "connection_id": self.connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            
            await self._send_udp_data(json.dumps(handshake).encode())
            
            # Wait for handshake response
            response_data = await self._receive_udp_data()
            if response_data:
                response = json.loads(response_data.decode())
                if response.get("status") == "accepted":
                    self.status = ConnectionStatus.CONNECTED
                    self.last_heartbeat = datetime.utcnow()
                    logger.info(f"UDP connection established to {self.config.host}:{self.config.port}")
                    return True
            
            logger.error("UDP handshake failed")
            self.status = ConnectionStatus.FAILED
            return False
            
        except Exception as e:
            logger.error(f"UDP connection error: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    async def disconnect(self) -> bool:
        """Close WiFi connection"""
        try:
            async with self._connection_lock:
                self.status = ConnectionStatus.DISCONNECTED
                
                # Close TCP connection
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()
                    self.writer = None
                    self.reader = None
                
                # Close UDP socket
                if self.socket:
                    self.socket.close()
                    self.socket = None
                
                logger.info(f"WiFi connection closed: {self.connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error closing WiFi connection: {e}")
            return False
    
    async def send_message(self, message: DroneMessage) -> bool:
        """Send message via WiFi"""
        try:
            if self.status != ConnectionStatus.CONNECTED:
                logger.warning(f"Cannot send message, connection not established: {self.connection_id}")
                return False
            
            # Serialize message
            message_data = self._serialize_message(message)
            
            if self.config.protocol.lower() == "tcp":
                return await self._send_raw_data(message_data)
            elif self.config.protocol.lower() == "udp":
                return await self._send_udp_data(message_data)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error sending message via WiFi: {e}")
            return False
    
    async def receive_message(self) -> Optional[DroneMessage]:
        """Receive message via WiFi"""
        try:
            if self.status != ConnectionStatus.CONNECTED:
                return None
            
            # Receive raw data
            if self.config.protocol.lower() == "tcp":
                raw_data = await self._receive_raw_data()
            elif self.config.protocol.lower() == "udp":
                raw_data = await self._receive_udp_data()
            else:
                return None
            
            if raw_data:
                return self._deserialize_message(raw_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message via WiFi: {e}")
            return None
    
    async def _send_raw_data(self, data: bytes) -> bool:
        """Send raw data via TCP"""
        try:
            if not self.writer:
                return False
            
            # Add message length header
            length_header = struct.pack('!I', len(data))
            self.writer.write(length_header + data)
            await self.writer.drain()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending raw data: {e}")
            return False
    
    async def _receive_raw_data(self) -> Optional[bytes]:
        """Receive raw data via TCP"""
        try:
            if not self.reader:
                return None
            
            # Read message length header
            length_header = await self.reader.read(4)
            if len(length_header) != 4:
                return None
            
            message_length = struct.unpack('!I', length_header)[0]
            
            # Read message data
            message_data = await self.reader.read(message_length)
            if len(message_data) != message_length:
                return None
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error receiving raw data: {e}")
            return None
    
    async def _send_udp_data(self, data: bytes) -> bool:
        """Send data via UDP"""
        try:
            if not self.socket:
                return False
            
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.socket, data, (self.config.host, self.config.port))
            return True
            
        except Exception as e:
            logger.error(f"Error sending UDP data: {e}")
            return False
    
    async def _receive_udp_data(self) -> Optional[bytes]:
        """Receive data via UDP"""
        try:
            if not self.socket:
                return None
            
            loop = asyncio.get_event_loop()
            data, addr = await loop.sock_recvfrom(self.socket, self.config.buffer_size)
            return data
            
        except Exception as e:
            logger.error(f"Error receiving UDP data: {e}")
            return None
    
    def _serialize_message(self, message: DroneMessage) -> bytes:
        """Serialize message for transmission"""
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
        
        return json.dumps(message_dict).encode()
    
    def _deserialize_message(self, data: bytes) -> Optional[DroneMessage]:
        """Deserialize received message"""
        try:
            message_dict = json.loads(data.decode())
            
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
            logger.error(f"Error deserializing message: {e}")
            return None
    
    def get_connection_info(self) -> Dict:
        """Get WiFi connection information"""
        return {
            **self.get_status(),
            "protocol": self.config.protocol,
            "host": self.config.host,
            "port": self.config.port,
            "encryption_enabled": bool(self.config.encryption_key),
            "compression_enabled": self.config.compression
        }
