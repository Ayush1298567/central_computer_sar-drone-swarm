"""
Base Connection Class for Drone Communication Protocols
Provides common interface for all drone communication methods
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class ConnectionConfig:
    """Base connection configuration"""
    host: str
    port: int
    timeout: float = 10.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    heartbeat_interval: float = 5.0
    buffer_size: int = 4096

@dataclass
class DroneMessage:
    """Standardized drone message format"""
    message_id: str
    drone_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=normal, 2=high, 3=emergency
    response_required: bool = False

@dataclass
class TelemetryMessage:
    """Telemetry data message"""
    message_id: str
    drone_id: str
    message_type: str = "telemetry"
    payload: Dict[str, Any] = None
    timestamp: datetime = None
    priority: int = 1
    response_required: bool = False
    position: Dict[str, float] = None  # lat, lon, alt
    battery_level: float = 0.0
    speed: float = 0.0
    heading: float = 0.0
    signal_strength: float = 0.0
    gps_accuracy: float = 0.0
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None

@dataclass
class CommandMessage:
    """Command message to drone"""
    message_id: str
    drone_id: str
    message_type: str = "command"
    payload: Dict[str, Any] = None
    timestamp: datetime = None
    priority: int = 1
    response_required: bool = False
    command_type: str = ""
    parameters: Dict[str, Any] = None
    execution_time: Optional[datetime] = None

class BaseConnection(ABC):
    """Abstract base class for drone communication connections"""
    
    def __init__(self, connection_id: str, config: ConnectionConfig):
        self.connection_id = connection_id
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.last_heartbeat = None
        self.message_handlers: Dict[str, Callable] = {}
        self.telemetry_callbacks: List[Callable] = []
        self.connection_callbacks: List[Callable] = []
        self._running = False
        self._heartbeat_task = None
        self._message_queue = asyncio.Queue()
        self._connection_lock = asyncio.Lock()
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to drone"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to drone"""
        pass
    
    @abstractmethod
    async def send_message(self, message: DroneMessage) -> bool:
        """Send message to drone"""
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[DroneMessage]:
        """Receive message from drone"""
        pass
    
    async def start(self) -> bool:
        """Start the connection service"""
        try:
            self._running = True
            
            # Start heartbeat monitoring
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            # Start message processing
            asyncio.create_task(self._process_messages())
            
            logger.info(f"Connection {self.connection_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start connection {self.connection_id}: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the connection service"""
        try:
            self._running = False
            
            # Cancel heartbeat task
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect if connected
            if self.status == ConnectionStatus.CONNECTED:
                await self.disconnect()
            
            logger.info(f"Connection {self.connection_id} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop connection {self.connection_id}: {e}")
            return False
    
    async def send_telemetry_request(self, drone_id: str) -> bool:
        """Request telemetry data from drone"""
        message = DroneMessage(
            message_id=f"tel_req_{datetime.utcnow().timestamp()}",
            drone_id=drone_id,
            message_type="telemetry_request",
            payload={},
            timestamp=datetime.utcnow()
        )
        return await self.send_message(message)
    
    async def send_command(self, drone_id: str, command_type: str, 
                          parameters: Dict[str, Any], priority: int = 1) -> bool:
        """Send command to drone"""
        message = CommandMessage(
            message_id=f"cmd_{datetime.utcnow().timestamp()}",
            drone_id=drone_id,
            message_type="command",
            command_type=command_type,
            parameters=parameters,
            timestamp=datetime.utcnow(),
            priority=priority
        )
        return await self.send_message(message)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type] = handler
    
    def register_telemetry_callback(self, callback: Callable):
        """Register callback for telemetry data"""
        self.telemetry_callbacks.append(callback)
    
    def register_connection_callback(self, callback: Callable):
        """Register callback for connection status changes"""
        self.connection_callbacks.append(callback)
    
    async def _heartbeat_monitor(self):
        """Monitor connection heartbeat"""
        while self._running:
            try:
                if self.status == ConnectionStatus.CONNECTED:
                    # Check if heartbeat is recent
                    if (self.last_heartbeat and 
                        datetime.utcnow() - self.last_heartbeat > timedelta(seconds=self.config.heartbeat_interval * 3)):
                        logger.warning(f"Heartbeat timeout for connection {self.connection_id}")
                        await self._handle_connection_lost()
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error for {self.connection_id}: {e}")
                await asyncio.sleep(1)
    
    async def _process_messages(self):
        """Process incoming messages"""
        while self._running:
            try:
                message = await self.receive_message()
                if message:
                    await self._handle_message(message)
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error for {self.connection_id}: {e}")
                await asyncio.sleep(0.1)
    
    async def _handle_message(self, message: DroneMessage):
        """Handle incoming message"""
        try:
            # Update heartbeat
            self.last_heartbeat = datetime.utcnow()
            
            # Call specific message handler
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message)
            
            # Handle telemetry messages
            if message.message_type == "telemetry":
                for callback in self.telemetry_callbacks:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Telemetry callback error: {e}")
            
            logger.debug(f"Processed message {message.message_type} from {message.drone_id}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_connection_lost(self):
        """Handle connection lost event"""
        self.status = ConnectionStatus.DISCONNECTED
        
        for callback in self.connection_callbacks:
            try:
                await callback(self.connection_id, ConnectionStatus.DISCONNECTED)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")
        
        # Attempt reconnection
        if self._running:
            await self._attempt_reconnection()
    
    async def _attempt_reconnection(self):
        """Attempt to reconnect to drone"""
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(f"Reconnection attempt {attempt + 1}/{self.config.retry_attempts} for {self.connection_id}")
                
                self.status = ConnectionStatus.RECONNECTING
                
                if await self.connect():
                    logger.info(f"Successfully reconnected {self.connection_id}")
                    return True
                
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        logger.error(f"Failed to reconnect {self.connection_id} after {self.config.retry_attempts} attempts")
        self.status = ConnectionStatus.FAILED
        
        for callback in self.connection_callbacks:
            try:
                await callback(self.connection_id, ConnectionStatus.FAILED)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "connection_id": self.connection_id,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "running": self._running,
            "config": asdict(self.config)
        }
