"""
WebSocket Manager for SAR Drone Swarm
Handles real-time communication between frontend and backend.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Set, Any, Optional, Callable
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from fastapi import WebSocket, WebSocketDisconnect
import aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Real WebSocket connection manager with Redis pub/sub integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_pubsub = None
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_callbacks: List[Callable] = []
        self.disconnection_callbacks: List[Callable] = []
        self.is_running = False
        
    async def start(self) -> bool:
        """Start the WebSocket manager and Redis connection"""
        try:
            # Connect to Redis
            self.redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis")
            
            # Start Redis pub/sub listener
            self.redis_pubsub = self.redis_client.pubsub()
            await self.redis_pubsub.subscribe("drone_telemetry", "mission_updates", "system_alerts")
            
            # Start background task for Redis messages
            asyncio.create_task(self._redis_message_processor())
            
            self.is_running = True
            self.logger.info("WebSocket Manager started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket Manager: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """Stop the WebSocket manager and close all connections"""
        try:
            self.is_running = False
            
            # Close all WebSocket connections
            for connection_id, websocket in self.active_connections.items():
                try:
                    await websocket.close()
                except Exception as e:
                    self.logger.error(f"Error closing connection {connection_id}: {e}")
            
            self.active_connections.clear()
            self.connection_metadata.clear()
            
            # Close Redis connection
            if self.redis_pubsub:
                await self.redis_pubsub.unsubscribe()
                await self.redis_pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("WebSocket Manager stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping WebSocket Manager: {e}", exc_info=True)
            return False
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            
            # Generate unique connection ID
            connection_id = client_id or str(uuid.uuid4())
            
            # Store connection
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                'connected_at': datetime.utcnow(),
                'last_ping': datetime.utcnow(),
                'message_count': 0,
                'client_type': 'unknown',
                'subscriptions': set()
            }
            
            # Notify connection callbacks
            for callback in self.connection_callbacks:
                try:
                    await callback(connection_id, websocket)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
            
            self.logger.info(f"WebSocket connection established: {connection_id}")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Error accepting WebSocket connection: {e}", exc_info=True)
            raise
    
    async def disconnect(self, connection_id: str) -> bool:
        """Disconnect a WebSocket connection"""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.close()
                
                # Remove from tracking
                del self.active_connections[connection_id]
                if connection_id in self.connection_metadata:
                    del self.connection_metadata[connection_id]
                
                # Notify disconnection callbacks
                for callback in self.disconnection_callbacks:
                    try:
                        await callback(connection_id)
                    except Exception as e:
                        self.logger.error(f"Error in disconnection callback: {e}")
                
                self.logger.info(f"WebSocket connection closed: {connection_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error disconnecting WebSocket {connection_id}: {e}", exc_info=True)
            return False
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection"""
        try:
            if connection_id not in self.active_connections:
                self.logger.warning(f"Connection {connection_id} not found")
                return False
            
            websocket = self.active_connections[connection_id]
            
            # Add metadata
            message['timestamp'] = datetime.utcnow().isoformat()
            message['message_id'] = str(uuid.uuid4())
            
            # Send message
            await websocket.send_text(json.dumps(message))
            
            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['message_count'] += 1
                self.connection_metadata[connection_id]['last_ping'] = datetime.utcnow()
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            self.logger.error(f"Error sending message to {connection_id}: {e}")
            return False
    
    async def broadcast_message(self, message: Dict[str, Any], 
                              exclude: Optional[Set[str]] = None) -> int:
        """Broadcast a message to all connected clients"""
        try:
            exclude = exclude or set()
            sent_count = 0
            
            for connection_id in list(self.active_connections.keys()):
                if connection_id not in exclude:
                    if await self.send_message(connection_id, message):
                        sent_count += 1
            
            self.logger.info(f"Broadcasted message to {sent_count} connections")
            return sent_count
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}", exc_info=True)
            return 0
    
    async def send_to_subscribers(self, channel: str, message: Dict[str, Any]) -> int:
        """Send message to clients subscribed to a specific channel"""
        try:
            sent_count = 0
            
            for connection_id, metadata in self.connection_metadata.items():
                if channel in metadata.get('subscriptions', set()):
                    if await self.send_message(connection_id, {
                        'type': 'channel_message',
                        'channel': channel,
                        'data': message
                    }):
                        sent_count += 1
            
            return sent_count
            
        except Exception as e:
            self.logger.error(f"Error sending to subscribers of {channel}: {e}")
            return 0
    
    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe a connection to a channel"""
        try:
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['subscriptions'].add(channel)
                self.logger.info(f"Connection {connection_id} subscribed to {channel}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error subscribing {connection_id} to {channel}: {e}")
            return False
    
    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe a connection from a channel"""
        try:
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['subscriptions'].discard(channel)
                self.logger.info(f"Connection {connection_id} unsubscribed from {channel}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing {connection_id} from {channel}: {e}")
            return False
    
    async def handle_message(self, connection_id: str, message: str) -> bool:
        """Handle incoming message from a client"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            # Update metadata
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['last_ping'] = datetime.utcnow()
            
            # Route to appropriate handler
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(connection_id, data)
                return True
            else:
                # Default message handling
                await self._handle_default_message(connection_id, data)
                return True
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message from {connection_id}: {message}")
            return False
        except Exception as e:
            self.logger.error(f"Error handling message from {connection_id}: {e}", exc_info=True)
            return False
    
    async def _handle_default_message(self, connection_id: str, data: Dict[str, Any]) -> None:
        """Handle default message types"""
        try:
            message_type = data.get('type', 'unknown')
            
            if message_type == 'ping':
                await self.send_message(connection_id, {'type': 'pong', 'timestamp': datetime.utcnow().isoformat()})
            
            elif message_type == 'subscribe':
                channel = data.get('channel')
                if channel:
                    await self.subscribe(connection_id, channel)
                    await self.send_message(connection_id, {
                        'type': 'subscription_confirmed',
                        'channel': channel
                    })
            
            elif message_type == 'unsubscribe':
                channel = data.get('channel')
                if channel:
                    await self.unsubscribe(connection_id, channel)
                    await self.send_message(connection_id, {
                        'type': 'unsubscription_confirmed',
                        'channel': channel
                    })
            
            elif message_type == 'get_status':
                status = await self.get_connection_status(connection_id)
                await self.send_message(connection_id, {
                    'type': 'status_response',
                    'data': status
                })
            
            else:
                self.logger.warning(f"Unknown message type from {connection_id}: {message_type}")
                
        except Exception as e:
            self.logger.error(f"Error in default message handler: {e}", exc_info=True)
    
    async def _redis_message_processor(self) -> None:
        """Background task to process Redis pub/sub messages"""
        try:
            while self.is_running and self.redis_pubsub:
                try:
                    message = await self.redis_pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        await self._process_redis_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing Redis message: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Redis message processor error: {e}", exc_info=True)
    
    async def _process_redis_message(self, message: Dict[str, Any]) -> None:
        """Process a message from Redis pub/sub"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            # Send to subscribers of this channel
            await self.send_to_subscribers(channel, data)
            
        except Exception as e:
            self.logger.error(f"Error processing Redis message: {e}", exc_info=True)
    
    async def publish_telemetry(self, drone_id: str, telemetry_data: Dict[str, Any]) -> bool:
        """Publish drone telemetry data to Redis"""
        try:
            if not self.redis_client:
                return False
            
            message = {
                'drone_id': drone_id,
                'telemetry': telemetry_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish('drone_telemetry', json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing telemetry: {e}")
            return False
    
    async def publish_mission_update(self, mission_id: str, update_data: Dict[str, Any]) -> bool:
        """Publish mission update to Redis"""
        try:
            if not self.redis_client:
                return False
            
            message = {
                'mission_id': mission_id,
                'update': update_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish('mission_updates', json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing mission update: {e}")
            return False
    
    async def publish_system_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Publish system alert to Redis"""
        try:
            if not self.redis_client:
                return False
            
            message = {
                'alert': alert_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish('system_alerts', json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing system alert: {e}")
            return False
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
    
    def register_connection_callback(self, callback: Callable) -> None:
        """Register a callback for new connections"""
        self.connection_callbacks.append(callback)
    
    def register_disconnection_callback(self, callback: Callable) -> None:
        """Register a callback for disconnections"""
        self.disconnection_callbacks.append(callback)
    
    async def get_connection_status(self, connection_id: str) -> Dict[str, Any]:
        """Get status information for a connection"""
        try:
            if connection_id not in self.connection_metadata:
                return {'error': 'Connection not found'}
            
            metadata = self.connection_metadata[connection_id]
            return {
                'connection_id': connection_id,
                'connected_at': metadata['connected_at'].isoformat(),
                'last_ping': metadata['last_ping'].isoformat(),
                'message_count': metadata['message_count'],
                'subscriptions': list(metadata['subscriptions']),
                'is_active': connection_id in self.active_connections
            }
            
        except Exception as e:
            self.logger.error(f"Error getting connection status: {e}")
            return {'error': str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            return {
                'active_connections': len(self.active_connections),
                'total_messages': sum(meta['message_count'] for meta in self.connection_metadata.values()),
                'is_running': self.is_running,
                'redis_connected': self.redis_client is not None,
                'channels': ['drone_telemetry', 'mission_updates', 'system_alerts']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

# Global instance
websocket_manager = WebSocketManager()

# Convenience functions
async def start_websocket_manager() -> bool:
    """Start the global WebSocket manager"""
    return await websocket_manager.start()

async def stop_websocket_manager() -> bool:
    """Stop the global WebSocket manager"""
    return await websocket_manager.stop()

async def connect_websocket(websocket: WebSocket, client_id: Optional[str] = None) -> str:
    """Connect a new WebSocket"""
    return await websocket_manager.connect(websocket, client_id)

async def disconnect_websocket(connection_id: str) -> bool:
    """Disconnect a WebSocket"""
    return await websocket_manager.disconnect(connection_id)

async def send_websocket_message(connection_id: str, message: Dict[str, Any]) -> bool:
    """Send a message to a WebSocket"""
    return await websocket_manager.send_message(connection_id, message)

async def broadcast_websocket_message(message: Dict[str, Any], exclude: Optional[Set[str]] = None) -> int:
    """Broadcast a message to all WebSockets"""
    return await websocket_manager.broadcast_message(message, exclude)