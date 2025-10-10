"""
Real-Time Bridge for SAR Drone Swarm
Bridges Redis pub/sub messages to WebSocket clients for real-time updates.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import aioredis
from app.core.config import settings
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class RealTimeBridge:
    """Real-time bridge between Redis and WebSocket clients"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_pubsub = None
        self.is_running = False
        self.subscribed_channels = set()
        self.message_handlers: Dict[str, callable] = {}
        self.bridge_stats = {
            'messages_processed': 0,
            'messages_sent': 0,
            'errors': 0,
            'started_at': None,
            'last_message_time': None
        }
        
    async def start(self) -> bool:
        """Start the real-time bridge"""
        try:
            self.logger.info("Starting Real-Time Bridge...")
            
            # Connect to Redis
            self.redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis")
            
            # Create pub/sub client
            self.redis_pubsub = self.redis_client.pubsub()
            
            # Subscribe to default channels
            default_channels = [
                'drone_telemetry',
                'mission_updates', 
                'system_alerts',
                'video_analysis',
                'discovery_events',
                'emergency_alerts'
            ]
            
            for channel in default_channels:
                await self.subscribe_channel(channel)
            
            # Start message processing task
            self.is_running = True
            asyncio.create_task(self._message_processor())
            
            # Register default message handlers
            self._register_default_handlers()
            
            self.bridge_stats['started_at'] = datetime.utcnow()
            self.logger.info("Real-Time Bridge started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Real-Time Bridge: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """Stop the real-time bridge"""
        try:
            self.logger.info("Stopping Real-Time Bridge...")
            
            self.is_running = False
            
            # Close Redis pub/sub
            if self.redis_pubsub:
                await self.redis_pubsub.unsubscribe()
                await self.redis_pubsub.close()
            
            # Close Redis client
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("Real-Time Bridge stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Real-Time Bridge: {e}", exc_info=True)
            return False
    
    async def subscribe_channel(self, channel: str) -> bool:
        """Subscribe to a Redis channel"""
        try:
            if not self.redis_pubsub:
                self.logger.error("Redis pub/sub not initialized")
                return False
            
            await self.redis_pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
            self.logger.info(f"Subscribed to channel: {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to channel {channel}: {e}")
            return False
    
    async def unsubscribe_channel(self, channel: str) -> bool:
        """Unsubscribe from a Redis channel"""
        try:
            if not self.redis_pubsub:
                return False
            
            await self.redis_pubsub.unsubscribe(channel)
            self.subscribed_channels.discard(channel)
            self.logger.info(f"Unsubscribed from channel: {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from channel {channel}: {e}")
            return False
    
    async def _message_processor(self) -> None:
        """Process messages from Redis and forward to WebSocket clients"""
        try:
            while self.is_running and self.redis_pubsub:
                try:
                    # Get message with timeout
                    message = await asyncio.wait_for(
                        self.redis_pubsub.get_message(timeout=1.0),
                        timeout=1.0
                    )
                    
                    if message and message['type'] == 'message':
                        await self._process_redis_message(message)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing Redis message: {e}")
                    self.bridge_stats['errors'] += 1
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Message processor error: {e}", exc_info=True)
    
    async def _process_redis_message(self, message: Dict[str, Any]) -> None:
        """Process a message from Redis"""
        try:
            channel = message['channel']
            data = message['data']
            
            # Update stats
            self.bridge_stats['messages_processed'] += 1
            self.bridge_stats['last_message_time'] = datetime.utcnow()
            
            # Parse message data
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid JSON in channel {channel}: {data}")
                return
            
            # Process message based on channel
            if channel in self.message_handlers:
                handler = self.message_handlers[channel]
                await handler(channel, message_data)
            else:
                # Default processing
                await self._default_message_handler(channel, message_data)
            
        except Exception as e:
            self.logger.error(f"Error processing Redis message: {e}", exc_info=True)
            self.bridge_stats['errors'] += 1
    
    async def _default_message_handler(self, channel: str, data: Dict[str, Any]) -> None:
        """Default message handler for all channels"""
        try:
            # Create WebSocket message
            websocket_message = {
                'type': 'real_time_update',
                'channel': channel,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to all WebSocket clients subscribed to this channel
            sent_count = await websocket_manager.send_to_subscribers(channel, data)
            
            if sent_count > 0:
                self.bridge_stats['messages_sent'] += sent_count
                self.logger.debug(f"Sent {channel} message to {sent_count} clients")
            
        except Exception as e:
            self.logger.error(f"Error in default message handler: {e}")
            self.bridge_stats['errors'] += 1
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers for different channels"""
        
        # Drone telemetry handler
        async def handle_drone_telemetry(channel: str, data: Dict[str, Any]) -> None:
            try:
                # Process telemetry data
                processed_data = {
                    'type': 'drone_telemetry',
                    'drone_id': data.get('drone_id'),
                    'telemetry': data.get('telemetry', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel
                }
                
                # Send to WebSocket clients
                sent_count = await websocket_manager.send_to_subscribers(channel, processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling drone telemetry: {e}")
        
        # Mission updates handler
        async def handle_mission_updates(channel: str, data: Dict[str, Any]) -> None:
            try:
                processed_data = {
                    'type': 'mission_update',
                    'mission_id': data.get('mission_id'),
                    'update': data.get('update', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel
                }
                
                sent_count = await websocket_manager.send_to_subscribers(channel, processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling mission updates: {e}")
        
        # System alerts handler
        async def handle_system_alerts(channel: str, data: Dict[str, Any]) -> None:
            try:
                processed_data = {
                    'type': 'system_alert',
                    'alert': data.get('alert', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel,
                    'priority': data.get('alert', {}).get('priority', 'medium')
                }
                
                # Send to all clients for alerts (not just subscribers)
                sent_count = await websocket_manager.broadcast_message(processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling system alerts: {e}")
        
        # Video analysis handler
        async def handle_video_analysis(channel: str, data: Dict[str, Any]) -> None:
            try:
                processed_data = {
                    'type': 'video_analysis',
                    'stream_id': data.get('stream_id'),
                    'drone_id': data.get('drone_id'),
                    'analysis': data.get('analysis', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel
                }
                
                sent_count = await websocket_manager.send_to_subscribers(channel, processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling video analysis: {e}")
        
        # Discovery events handler
        async def handle_discovery_events(channel: str, data: Dict[str, Any]) -> None:
            try:
                processed_data = {
                    'type': 'discovery_event',
                    'discovery_id': data.get('discovery_id'),
                    'event': data.get('event', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel
                }
                
                sent_count = await websocket_manager.send_to_subscribers(channel, processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling discovery events: {e}")
        
        # Emergency alerts handler
        async def handle_emergency_alerts(channel: str, data: Dict[str, Any]) -> None:
            try:
                processed_data = {
                    'type': 'emergency_alert',
                    'alert_id': data.get('alert_id'),
                    'emergency': data.get('emergency', {}),
                    'timestamp': data.get('timestamp'),
                    'channel': channel,
                    'priority': 'critical'
                }
                
                # Emergency alerts go to all clients
                sent_count = await websocket_manager.broadcast_message(processed_data)
                self.bridge_stats['messages_sent'] += sent_count
                
            except Exception as e:
                self.logger.error(f"Error handling emergency alerts: {e}")
        
        # Register handlers
        self.message_handlers['drone_telemetry'] = handle_drone_telemetry
        self.message_handlers['mission_updates'] = handle_mission_updates
        self.message_handlers['system_alerts'] = handle_system_alerts
        self.message_handlers['video_analysis'] = handle_video_analysis
        self.message_handlers['discovery_events'] = handle_discovery_events
        self.message_handlers['emergency_alerts'] = handle_emergency_alerts
    
    def register_message_handler(self, channel: str, handler: callable) -> None:
        """Register a custom message handler for a channel"""
        self.message_handlers[channel] = handler
        self.logger.info(f"Registered custom handler for channel: {channel}")
    
    async def publish_message(self, channel: str, data: Dict[str, Any]) -> bool:
        """Publish a message to a Redis channel"""
        try:
            if not self.redis_client:
                self.logger.error("Redis client not connected")
                return False
            
            # Add timestamp
            data['timestamp'] = datetime.utcnow().isoformat()
            
            # Publish to Redis
            await self.redis_client.publish(channel, json.dumps(data))
            
            self.logger.debug(f"Published message to channel {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing message to {channel}: {e}")
            return False
    
    async def get_bridge_status(self) -> Dict[str, Any]:
        """Get bridge status and statistics"""
        try:
            uptime = None
            if self.bridge_stats['started_at']:
                uptime = (datetime.utcnow() - self.bridge_stats['started_at']).total_seconds()
            
            return {
                'is_running': self.is_running,
                'redis_connected': self.redis_client is not None,
                'subscribed_channels': list(self.subscribed_channels),
                'message_handlers': list(self.message_handlers.keys()),
                'stats': {
                    **self.bridge_stats,
                    'uptime_seconds': uptime,
                    'messages_per_second': self._calculate_messages_per_second()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting bridge status: {e}")
            return {'error': str(e)}
    
    def _calculate_messages_per_second(self) -> float:
        """Calculate messages processed per second"""
        try:
            if not self.bridge_stats['started_at']:
                return 0.0
            
            uptime = (datetime.utcnow() - self.bridge_stats['started_at']).total_seconds()
            if uptime <= 0:
                return 0.0
            
            return self.bridge_stats['messages_processed'] / uptime
            
        except Exception as e:
            self.logger.error(f"Error calculating messages per second: {e}")
            return 0.0
    
    async def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """Get information about a specific channel"""
        try:
            if not self.redis_client:
                return {'error': 'Redis not connected'}
            
            # Get channel info from Redis
            info = await self.redis_client.execute_command('PUBSUB', 'NUMSUB', channel)
            
            return {
                'channel': channel,
                'subscribers': info[1] if len(info) > 1 else 0,
                'is_subscribed': channel in self.subscribed_channels,
                'has_handler': channel in self.message_handlers
            }
            
        except Exception as e:
            self.logger.error(f"Error getting channel info for {channel}: {e}")
            return {'error': str(e)}

# Global instance
real_time_bridge = RealTimeBridge()

# Convenience functions
async def start_real_time_bridge() -> bool:
    """Start the global real-time bridge"""
    return await real_time_bridge.start()

async def stop_real_time_bridge() -> bool:
    """Stop the global real-time bridge"""
    return await real_time_bridge.stop()

async def publish_realtime_message(channel: str, data: Dict[str, Any]) -> bool:
    """Publish a message to the real-time bridge"""
    return await real_time_bridge.publish_message(channel, data)

def register_realtime_handler(channel: str, handler: callable) -> None:
    """Register a handler for real-time messages"""
    real_time_bridge.register_message_handler(channel, handler)