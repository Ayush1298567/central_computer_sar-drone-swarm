"""
Base agent class for all AI agents
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from ..services.redis_service import RedisService
from ..services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_id: str, redis_service: RedisService, 
                 websocket_manager: WebSocketManager):
        self.agent_id = agent_id
        self.redis_service = redis_service
        self.websocket_manager = websocket_manager
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._subscribed_channels: list[str] = []
    
    @abstractmethod
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming message from Redis channel"""
        pass
    
    @abstractmethod
    async def start_agent(self) -> None:
        """Start the agent"""
        pass
    
    @abstractmethod
    async def stop_agent(self) -> None:
        """Stop the agent"""
        pass
    
    async def subscribe_to_channel(self, channel: str) -> None:
        """Subscribe to Redis channel"""
        await self.redis_service.subscribe(channel, self.process_message)
        self._subscribed_channels.append(channel)
        logger.info(f"Agent {self.agent_id} subscribed to {channel}")
    
    async def publish_message(self, channel: str, message: Any) -> None:
        """Publish message to Redis channel"""
        await self.redis_service.publish(channel, message)
        logger.debug(f"Agent {self.agent_id} published to {channel}")
    
    async def send_websocket_message(self, message_type: str, data: Any) -> None:
        """Send message via WebSocket"""
        message = {
            "type": message_type,
            "agent_id": self.agent_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.websocket_manager.broadcast(message)
    
    async def start(self) -> None:
        """Start the agent task"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_agent())
        logger.info(f"Agent {self.agent_id} started")
    
    async def stop(self) -> None:
        """Stop the agent task"""
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Unsubscribe from all channels
        for channel in self._subscribed_channels:
            await self.redis_service.unsubscribe(channel)
        
        await self.stop_agent()
        logger.info(f"Agent {self.agent_id} stopped")
    
    async def _run_agent(self) -> None:
        """Main agent run loop"""
        try:
            await self.start_agent()
            while self._running:
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
        finally:
            await self.stop_agent()
    
    def is_running(self) -> bool:
        """Check if agent is running"""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "subscribed_channels": self._subscribed_channels,
            "task_running": self._task is not None and not self._task.done()
        }