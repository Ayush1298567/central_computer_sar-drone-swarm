"""
LoRa Connection for Drone Communication
Implements LoRa radio communication for long-range drone connections
"""
import asyncio
import struct
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import time

try:
    import RPi.GPIO as GPIO
    import spidev
    import serial
    LORA_AVAILABLE = True
except ImportError:
    LORA_AVAILABLE = False
    GPIO = None
    spidev = None
    serial = None

from .base_connection import BaseConnection, ConnectionConfig, DroneMessage, ConnectionStatus

logger = logging.getLogger(__name__)

class LoRaConnectionConfig(ConnectionConfig):
    """LoRa-specific connection configuration"""
    frequency: float = 868.1  # MHz
    spreading_factor: int = 7  # 6-12
    bandwidth: int = 125000   # Hz
    coding_rate: int = 5      # 5-8
    tx_power: int = 14        # dBm
    preamble_length: int = 8
    crc: bool = True
    sync_word: int = 0x34
    device_path: str = "/dev/ttyUSB0"  # Serial device for LoRa module
    baudrate: int = 9600

class LoRaConnection(BaseConnection):
    """LoRa-based drone connection for long-range communication"""
    
    def __init__(self, connection_id: str, config: LoRaConnectionConfig):
        super().__init__(connection_id, config)
        self.config: LoRaConnectionConfig = config
        self.serial_connection = None
        self._receive_buffer = b""
        self._message_queue = asyncio.Queue()
        self._receive_task = None
        
        if not LORA_AVAILABLE:
            logger.warning("LoRa libraries not available. Install RPi.GPIO, spidev, and pyserial")
    
    async def connect(self) -> bool:
        """Establish LoRa connection to drone"""
        try:
            if not LORA_AVAILABLE:
                logger.error("LoRa libraries not available")
                self.status = ConnectionStatus.FAILED
                return False
            
            async with self._connection_lock:
                if self.status == ConnectionStatus.CONNECTED:
                    return True
                
                self.status = ConnectionStatus.CONNECTING
                
                # Initialize LoRa module
                if await self._initialize_lora_module():
                    self.status = ConnectionStatus.CONNECTED
                    self.last_heartbeat = datetime.utcnow()
                    
                    # Start receive task
                    self._receive_task = asyncio.create_task(self._receive_loop())
                    
                    logger.info(f"LoRa connection established on {self.config.frequency}MHz")
                    return True
                else:
                    logger.error("Failed to initialize LoRa module")
                    self.status = ConnectionStatus.FAILED
                    return False
                
        except Exception as e:
            logger.error(f"Failed to connect via LoRa: {e}")
            self.status = ConnectionStatus.FAILED
            return False
    
    async def _initialize_lora_module(self) -> bool:
        """Initialize LoRa module with configuration"""
        try:
            # Open serial connection to LoRa module
            self.serial_connection = serial.Serial(
                self.config.device_path,
                self.config.baudrate,
                timeout=1
            )
            
            # Send configuration commands to LoRa module
            config_commands = [
                f"AT+FREQ={self.config.frequency:.3f}",
                f"AT+SF={self.config.spreading_factor}",
                f"AT+BW={self.config.bandwidth}",
                f"AT+CR={self.config.coding_rate}",
                f"AT+POWER={self.config.tx_power}",
                f"AT+PREAMBLE={self.config.preamble_length}",
                f"AT+CRC={'ON' if self.config.crc else 'OFF'}",
                f"AT+SYNC={self.config.sync_word:02X}",
                "AT+SAVE",
                "AT+RESET"
            ]
            
            for command in config_commands:
                await self._send_at_command(command)
                await asyncio.sleep(0.1)
            
            # Wait for module to reset
            await asyncio.sleep(2)
            
            # Test communication
            response = await self._send_at_command("AT+VER")
            if response and "OK" in response:
                logger.info("LoRa module initialized successfully")
                return True
            else:
                logger.error("LoRa module initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing LoRa module: {e}")
            return False
    
    async def _send_at_command(self, command: str) -> Optional[str]:
        """Send AT command to LoRa module"""
        try:
            if not self.serial_connection:
                return None
            
            # Send command
            self.serial_connection.write(f"{command}\r\n".encode())
            
            # Read response
            response = self.serial_connection.readline().decode().strip()
            
            logger.debug(f"LoRa AT command: {command} -> {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error sending AT command: {e}")
            return None
    
    async def disconnect(self) -> bool:
        """Close LoRa connection"""
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
                
                # Close serial connection
                if self.serial_connection:
                    self.serial_connection.close()
                    self.serial_connection = None
                
                logger.info(f"LoRa connection closed: {self.connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error closing LoRa connection: {e}")
            return False
    
    async def send_message(self, message: DroneMessage) -> bool:
        """Send message via LoRa"""
        try:
            if self.status != ConnectionStatus.CONNECTED:
                logger.warning(f"Cannot send message, LoRa connection not established: {self.connection_id}")
                return False
            
            # Serialize and encode message
            message_data = self._serialize_message(message)
            
            # Send via LoRa
            if await self._send_lora_data(message_data):
                logger.debug(f"Sent LoRa message: {message.message_type}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error sending message via LoRa: {e}")
            return False
    
    async def receive_message(self) -> Optional[DroneMessage]:
        """Receive message via LoRa"""
        try:
            # Check if message is available in queue
            if not self._message_queue.empty():
                return await self._message_queue.get()
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message via LoRa: {e}")
            return None
    
    async def _send_lora_data(self, data: bytes) -> bool:
        """Send data via LoRa"""
        try:
            if not self.serial_connection:
                return False
            
            # Convert to hex string for transmission
            hex_data = data.hex()
            
            # Send data command
            command = f"AT+SEND={hex_data}"
            response = await self._send_at_command(command)
            
            return response and "OK" in response
            
        except Exception as e:
            logger.error(f"Error sending LoRa data: {e}")
            return False
    
    async def _receive_loop(self):
        """Background task to receive LoRa messages"""
        while self._running and self.serial_connection:
            try:
                # Check for incoming data
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.readline().decode().strip()
                    
                    # Process received data
                    if data.startswith("+RCV="):
                        # Parse received message
                        hex_data = data.split("=", 1)[1]
                        message_data = bytes.fromhex(hex_data)
                        
                        # Deserialize message
                        message = self._deserialize_message(message_data)
                        if message:
                            await self._message_queue.put(message)
                
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in LoRa receive loop: {e}")
                await asyncio.sleep(0.1)
    
    def _serialize_message(self, message: DroneMessage) -> bytes:
        """Serialize message for LoRa transmission"""
        try:
            # Create compact message format for LoRa
            message_dict = {
                "id": message.message_id,
                "drone": message.drone_id,
                "type": message.message_type,
                "data": message.payload,
                "time": int(message.timestamp.timestamp()),
                "pri": message.priority
            }
            
            # Add command-specific fields
            if hasattr(message, 'command_type'):
                message_dict["cmd"] = message.command_type
            if hasattr(message, 'parameters'):
                message_dict["params"] = message.parameters
            
            # Add telemetry-specific fields
            if hasattr(message, 'position'):
                message_dict["pos"] = message.position
            if hasattr(message, 'battery_level'):
                message_dict["bat"] = message.battery_level
            if hasattr(message, 'speed'):
                message_dict["spd"] = message.speed
            if hasattr(message, 'heading'):
                message_dict["hdg"] = message.heading
            
            # Convert to JSON and compress
            json_data = json.dumps(message_dict, separators=(',', ':'))
            return json_data.encode()
            
        except Exception as e:
            logger.error(f"Error serializing LoRa message: {e}")
            return b""
    
    def _deserialize_message(self, data: bytes) -> Optional[DroneMessage]:
        """Deserialize received LoRa message"""
        try:
            # Parse JSON data
            message_dict = json.loads(data.decode())
            
            # Create base message
            message = DroneMessage(
                message_id=message_dict["id"],
                drone_id=message_dict["drone"],
                message_type=message_dict["type"],
                payload=message_dict["data"],
                timestamp=datetime.fromtimestamp(message_dict["time"]),
                priority=message_dict.get("pri", 1)
            )
            
            # Add command-specific fields
            if "cmd" in message_dict:
                from .base_connection import CommandMessage
                message = CommandMessage(
                    message_id=message.message_id,
                    drone_id=message.drone_id,
                    message_type=message.message_type,
                    payload=message.payload,
                    timestamp=message.timestamp,
                    priority=message.priority,
                    response_required=False,
                    command_type=message_dict["cmd"],
                    parameters=message_dict.get("params", {})
                )
            
            # Add telemetry-specific fields
            if "pos" in message_dict:
                from .base_connection import TelemetryMessage
                message = TelemetryMessage(
                    message_id=message.message_id,
                    drone_id=message.drone_id,
                    message_type=message.message_type,
                    payload=message.payload,
                    timestamp=message.timestamp,
                    priority=message.priority,
                    response_required=False,
                    position=message_dict["pos"],
                    battery_level=message_dict.get("bat", 0.0),
                    speed=message_dict.get("spd", 0.0),
                    heading=message_dict.get("hdg", 0.0),
                    signal_strength=0.0,  # LoRa doesn't provide signal strength
                    gps_accuracy=0.0
                )
            
            return message
            
        except Exception as e:
            logger.error(f"Error deserializing LoRa message: {e}")
            return None
    
    def get_connection_info(self) -> Dict:
        """Get LoRa connection information"""
        return {
            **self.get_status(),
            "frequency": self.config.frequency,
            "spreading_factor": self.config.spreading_factor,
            "bandwidth": self.config.bandwidth,
            "coding_rate": self.config.coding_rate,
            "tx_power": self.config.tx_power,
            "device_path": self.config.device_path,
            "baudrate": self.config.baudrate
        }
