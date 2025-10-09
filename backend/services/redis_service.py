"""
Redis service for pub/sub communication between AI agents
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for agent communication"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, Callable] = {}
        self._running = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        self._running = False
        logger.info("Disconnected from Redis")
    
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        return self.redis_client is not None
    
    async def publish(self, channel: str, message: Any):
        """Publish message to channel"""
        if not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            message_str = json.dumps(message) if not isinstance(message, str) else message
            await self.redis_client.publish(channel, message_str)
            logger.debug(f"Published to {channel}: {message_str[:100]}...")
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            raise
    
    async def subscribe(self, channel: str, callback: Callable[[str, Any], None]):
        """Subscribe to channel with callback"""
        if not self.pubsub:
            raise RuntimeError("Redis not connected")
        
        self.subscribers[channel] = callback
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        if not self.pubsub:
            return
        
        if channel in self.subscribers:
            del self.subscribers[channel]
        await self.pubsub.unsubscribe(channel)
        logger.info(f"Unsubscribed from channel: {channel}")
    
    async def start_message_loop(self):
        """Start message processing loop"""
        if not self.pubsub:
            raise RuntimeError("Redis not connected")
        
        self._running = True
        logger.info("Started Redis message loop")
        
        try:
            async for message in self.pubsub.listen():
                if not self._running:
                    break
                
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    if channel in self.subscribers:
                        try:
                            # Try to parse as JSON, fallback to string
                            try:
                                parsed_data = json.loads(data)
                            except json.JSONDecodeError:
                                parsed_data = data
                            
                            await self.subscribers[channel](channel, parsed_data)
                        except Exception as e:
                            logger.error(f"Error processing message from {channel}: {e}")
        except Exception as e:
            logger.error(f"Redis message loop error: {e}")
        finally:
            self._running = False
            logger.info("Redis message loop stopped")
    
    async def stop_message_loop(self):
        """Stop message processing loop"""
        self._running = False
        if self.pubsub:
            await self.pubsub.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis_client:
            return None
        
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set value by key"""
        if not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await self.redis_client.set(key, value_str, ex=expire)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            raise
    
    async def delete(self, key: str):
        """Delete key"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
    
    async def lpush(self, key: str, value: Any):
        """Push to list"""
        if not self.redis_client:
            raise RuntimeError("Redis not connected")
        
        try:
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await self.redis_client.lpush(key, value_str)
        except Exception as e:
            logger.error(f"Failed to lpush to {key}: {e}")
            raise
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from list"""
        if not self.redis_client:
            return None
        
        try:
            return await self.redis_client.rpop(key)
        except Exception as e:
            logger.error(f"Failed to rpop from {key}: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        if not self.redis_client:
            return 0
        
        try:
            return await self.redis_client.llen(key)
        except Exception as e:
            logger.error(f"Failed to get length of {key}: {e}")
            return 0

# Global Redis service instance
redis_service = RedisService()