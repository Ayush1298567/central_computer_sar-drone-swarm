"""
Raspberry Pi Communication Module for SAR Drone Swarm System

This module handles communication between the central computer and Raspberry Pi
units running on each drone. It uses Redis pub/sub for real-time telemetry
and WebSocket for bidirectional command/status communication.

Author: SAR Drone Swarm System
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict, field
import uuid

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        aioredis = None

logger = logging.getLogger(__name__)


class PiCommandType(Enum):
    """Commands that can be sent to Raspberry Pi"""
    START_MISSION = "start_mission"
    PAUSE_MISSION = "pause_mission"
    RESUME_MISSION = "resume_mission"
    ABORT_MISSION = "abort_mission"
    UPDATE_WAYPOINT = "update_waypoint"
    REQUEST_STATUS = "request_status"
    REQUEST_TELEMETRY = "request_telemetry"
    UPDATE_DETECTION_MODEL = "update_detection_model"
    EMERGENCY_RTL = "emergency_rtl"
    EMERGENCY_LAND = "emergency_land"


@dataclass
class PiTelemetry:
    """Telemetry data from Raspberry Pi"""
    drone_id: str
    timestamp: datetime
    position: Dict[str, float]  # lat, lon, alt
    battery: float
    signal_strength: float
    mission_status: str
    current_waypoint: Optional[int] = None
    detections: List[Dict] = field(default_factory=list)
    system_health: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with JSON-serializable types"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PiTelemetry':
        """Create from dictionary"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class PiCommand:
    """Command to send to Raspberry Pi"""
    command_id: str
    drone_id: str
    command_type: PiCommandType
    parameters: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=normal, 2=high, 3=emergency
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with JSON-serializable types"""
        return {
            'command_id': self.command_id,
            'drone_id': self.drone_id,
            'command_type': self.command_type.value,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PiCommand':
        """Create from dictionary"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data['command_type'], str):
            data['command_type'] = PiCommandType(data['command_type'])
        return cls(**data)


class PiCommunicationHub:
    """
    Communication hub for Raspberry Pi units.
    
    Architecture:
        - Redis Pub/Sub: Used for real-time telemetry from Pi to Central
        - Redis Streams: Used for command delivery from Central to Pi
        - Redis Hash: Used for status caching
    
    Channels:
        - telemetry:{drone_id} - Pi publishes telemetry
        - commands:{drone_id} - Central publishes commands
        - status:{drone_id} - Shared status information
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Pi communication hub.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[Any] = None
        self.pubsub: Optional[Any] = None
        self._running = False
        self._telemetry_callbacks: List[Callable] = []
        self._status_callbacks: List[Callable] = []
        self._command_ack_callbacks: Dict[str, Callable] = {}
        self._subscriber_task: Optional[asyncio.Task] = None
        self._connected_drones: Dict[str, datetime] = {}
        self._telemetry_cache: Dict[str, PiTelemetry] = {}
        
    async def connect(self) -> bool:
        """
        Establish connection to Redis.
        
        Returns:
            True if connected, False otherwise
        """
        if not REDIS_AVAILABLE:
            logger.error("Redis client not available. Install with: pip install redis aioredis")
            return False
        
        try:
            # Create Redis connection
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
            
            # Create pub/sub
            self.pubsub = self.redis_client.pubsub()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            try:
                await self.pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")
        
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        
        logger.info("Disconnected from Redis")
    
    async def start(self) -> bool:
        """
        Start the communication hub.
        
        Returns:
            True if started successfully
        """
        if not self.redis_client:
            if not await self.connect():
                return False
        
        self._running = True
        
        # Start subscriber task
        self._subscriber_task = asyncio.create_task(self._subscriber_loop())
        
        logger.info("Pi Communication Hub started")
        return True
    
    async def stop(self) -> None:
        """Stop the communication hub."""
        await self.disconnect()
        logger.info("Pi Communication Hub stopped")
    
    async def subscribe_telemetry(self, drone_id: str) -> bool:
        """
        Subscribe to telemetry from specific drone.
        
        Args:
            drone_id: Drone identifier
            
        Returns:
            True if subscribed successfully
        """
        try:
            channel = f"telemetry:{drone_id}"
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to telemetry channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to telemetry for {drone_id}: {e}")
            return False
    
    async def subscribe_all_telemetry(self) -> bool:
        """
        Subscribe to telemetry from all drones using pattern.
        
        Returns:
            True if subscribed successfully
        """
        try:
            pattern = "telemetry:*"
            await self.pubsub.psubscribe(pattern)
            logger.info(f"Subscribed to telemetry pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to telemetry pattern: {e}")
            return False
    
    async def send_command(
        self,
        drone_id: str,
        command_type: PiCommandType,
        parameters: Dict[str, Any],
        priority: int = 1
    ) -> str:
        """
        Send command to Raspberry Pi.
        
        Args:
            drone_id: Target drone identifier
            command_type: Type of command to send
            parameters: Command parameters
            priority: Command priority (1=normal, 2=high, 3=emergency)
            
        Returns:
            Command ID for tracking
        """
        try:
            command = PiCommand(
                command_id=str(uuid.uuid4()),
                drone_id=drone_id,
                command_type=command_type,
                parameters=parameters,
                timestamp=datetime.now(),
                priority=priority
            )
            
            # Publish command to drone's command channel
            channel = f"commands:{drone_id}"
            message = json.dumps(command.to_dict())
            
            await self.redis_client.publish(channel, message)
            
            logger.info(f"Sent command {command_type.value} to {drone_id}: {command.command_id}")
            
            return command.command_id
            
        except Exception as e:
            logger.error(f"Failed to send command to {drone_id}: {e}", exc_info=True)
            raise
    
    async def send_mission_start(
        self,
        drone_id: str,
        mission_data: Dict[str, Any]
    ) -> str:
        """
        Send mission start command with full mission context.
        
        Args:
            drone_id: Target drone identifier
            mission_data: Complete mission data including waypoints, search area, etc.
            
        Returns:
            Command ID
        """
        return await self.send_command(
            drone_id=drone_id,
            command_type=PiCommandType.START_MISSION,
            parameters={"mission": mission_data},
            priority=2
        )
    
    async def send_emergency_rtl(self, drone_id: str) -> str:
        """
        Send emergency Return to Launch command.
        
        Args:
            drone_id: Target drone identifier
            
        Returns:
            Command ID
        """
        return await self.send_command(
            drone_id=drone_id,
            command_type=PiCommandType.EMERGENCY_RTL,
            parameters={},
            priority=3
        )
    
    async def send_emergency_land(self, drone_id: str) -> str:
        """
        Send emergency land command.
        
        Args:
            drone_id: Target drone identifier
            
        Returns:
            Command ID
        """
        return await self.send_command(
            drone_id=drone_id,
            command_type=PiCommandType.EMERGENCY_LAND,
            parameters={},
            priority=3
        )
    
    def register_telemetry_callback(self, callback: Callable) -> None:
        """
        Register callback for telemetry data.
        
        Args:
            callback: Async function(telemetry: PiTelemetry) -> None
        """
        self._telemetry_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable) -> None:
        """
        Register callback for status updates.
        
        Args:
            callback: Async function(drone_id: str, status: Dict) -> None
        """
        self._status_callbacks.append(callback)
    
    async def _subscriber_loop(self) -> None:
        """Main subscriber loop for processing messages."""
        logger.info("Starting subscriber loop")
        
        try:
            while self._running:
                try:
                    # Get messages from pubsub
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    
                    if message and message['type'] in ['message', 'pmessage']:
                        await self._handle_message(message)
                    
                    await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in subscriber loop: {e}", exc_info=True)
                    await asyncio.sleep(1.0)
        finally:
            logger.info("Subscriber loop stopped")
    
    async def _handle_message(self, message: Dict) -> None:
        """Handle incoming Redis pub/sub message."""
        try:
            channel = message.get('channel') or message.get('pattern', '')
            data = message.get('data')
            
            if not data:
                return
            
            # Parse message
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse message from {channel}: {data}")
                return
            
            # Route based on channel
            if channel.startswith('telemetry:') or 'telemetry' in channel:
                await self._handle_telemetry(payload)
            elif channel.startswith('status:'):
                await self._handle_status(payload)
            elif channel.startswith('command_ack:'):
                await self._handle_command_ack(payload)
            else:
                logger.warning(f"Unknown channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    async def _handle_telemetry(self, payload: Dict) -> None:
        """Handle telemetry message."""
        try:
            telemetry = PiTelemetry.from_dict(payload)
            
            # Update cache
            self._telemetry_cache[telemetry.drone_id] = telemetry
            self._connected_drones[telemetry.drone_id] = datetime.now()
            
            # Notify callbacks
            for callback in self._telemetry_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(telemetry)
                    else:
                        callback(telemetry)
                except Exception as e:
                    logger.error(f"Error in telemetry callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}", exc_info=True)
    
    async def _handle_status(self, payload: Dict) -> None:
        """Handle status message."""
        try:
            drone_id = payload.get('drone_id')
            if not drone_id:
                logger.error("Status message missing drone_id")
                return
            
            # Notify callbacks
            for callback in self._status_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(drone_id, payload)
                    else:
                        callback(drone_id, payload)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing status: {e}", exc_info=True)
    
    async def _handle_command_ack(self, payload: Dict) -> None:
        """Handle command acknowledgment."""
        try:
            command_id = payload.get('command_id')
            if command_id and command_id in self._command_ack_callbacks:
                callback = self._command_ack_callbacks.pop(command_id)
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
        except Exception as e:
            logger.error(f"Error processing command ack: {e}", exc_info=True)
    
    def get_telemetry(self, drone_id: str) -> Optional[PiTelemetry]:
        """Get cached telemetry for specific drone."""
        return self._telemetry_cache.get(drone_id)
    
    def get_connected_drones(self, timeout_seconds: int = 30) -> List[str]:
        """
        Get list of drones that have sent telemetry recently.
        
        Args:
            timeout_seconds: Time since last telemetry to consider disconnected
            
        Returns:
            List of drone IDs
        """
        now = datetime.now()
        threshold = now - timedelta(seconds=timeout_seconds)
        
        return [
            drone_id for drone_id, last_seen in self._connected_drones.items()
            if last_seen > threshold
        ]
    
    async def publish_telemetry(self, telemetry: PiTelemetry) -> bool:
        """
        Publish telemetry (used for testing/simulation).
        
        Args:
            telemetry: Telemetry data to publish
            
        Returns:
            True if published successfully
        """
        try:
            channel = f"telemetry:{telemetry.drone_id}"
            message = json.dumps(telemetry.to_dict())
            await self.redis_client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish telemetry: {e}")
            return False


# Global instance
_pi_communication_hub: Optional[PiCommunicationHub] = None


async def get_pi_communication_hub(redis_url: str = "redis://localhost:6379") -> PiCommunicationHub:
    """
    Get or create global Pi communication hub.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        PiCommunicationHub instance
    """
    global _pi_communication_hub
    
    if _pi_communication_hub is None:
        _pi_communication_hub = PiCommunicationHub(redis_url)
        if not await _pi_communication_hub.start():
            raise RuntimeError("Failed to start Pi communication hub")
    
    return _pi_communication_hub

