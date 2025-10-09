"""
WebSocket manager for real-time communication with frontend
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

from .redis_service import RedisService

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time communication"""
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        self.active_connections: List[WebSocket] = []
        self._running = False
        self._message_queue: List[Dict[str, Any]] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send any queued messages
        if self._message_queue:
            for message in self._message_queue:
                await self._send_to_websocket(websocket, message)
            self._message_queue.clear()
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            # Queue message if no connections
            self._message_queue.append(message)
            return
        
        # Send to all active connections
        disconnected = []
        for websocket in self.active_connections:
            try:
                await self._send_to_websocket(websocket, message)
            except WebSocketDisconnect:
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def send_telemetry(self, drone_id: str, telemetry_data: Dict[str, Any]):
        """Send drone telemetry data"""
        message = {
            "type": "telemetry",
            "drone_id": drone_id,
            "data": telemetry_data,
            "timestamp": telemetry_data.get("timestamp")
        }
        await self.broadcast(message)
    
    async def send_discovery(self, discovery_data: Dict[str, Any]):
        """Send discovery alert"""
        message = {
            "type": "discovery",
            "data": discovery_data
        }
        await self.broadcast(message)
    
    async def send_mission_progress(self, mission_id: str, progress_data: Dict[str, Any]):
        """Send mission progress update"""
        message = {
            "type": "mission_progress",
            "mission_id": mission_id,
            "data": progress_data
        }
        await self.broadcast(message)
    
    async def send_system_status(self, status_data: Dict[str, Any]):
        """Send system status update"""
        message = {
            "type": "system_status",
            "data": status_data
        }
        await self.broadcast(message)
    
    async def send_ai_response(self, response_data: Dict[str, Any]):
        """Send AI conversation response"""
        message = {
            "type": "ai_response",
            "data": response_data
        }
        await self.broadcast(message)
    
    async def send_command_feedback(self, command_id: str, feedback: Dict[str, Any]):
        """Send command execution feedback"""
        message = {
            "type": "command_feedback",
            "command_id": command_id,
            "data": feedback
        }
        await self.broadcast(message)
    
    async def start_redis_subscriber(self):
        """Start Redis subscriber for real-time updates"""
        self._running = True
        
        # Subscribe to telemetry channel
        await self.redis_service.subscribe("telemetry", self._handle_telemetry_message)
        
        # Subscribe to discovery channel
        await self.redis_service.subscribe("discovery", self._handle_discovery_message)
        
        # Subscribe to mission progress channel
        await self.redis_service.subscribe("mission_progress", self._handle_mission_progress_message)
        
        # Subscribe to AI response channel
        await self.redis_service.subscribe("ai_response", self._handle_ai_response_message)
        
        # Subscribe to command feedback channel
        await self.redis_service.subscribe("command_feedback", self._handle_command_feedback_message)
        
        logger.info("WebSocket Redis subscriber started")
    
    async def _handle_telemetry_message(self, channel: str, message: Any):
        """Handle telemetry message from Redis"""
        try:
            if isinstance(message, dict):
                await self.send_telemetry(
                    message.get("drone_id", "unknown"),
                    message
                )
        except Exception as e:
            logger.error(f"Error handling telemetry message: {e}")
    
    async def _handle_discovery_message(self, channel: str, message: Any):
        """Handle discovery message from Redis"""
        try:
            if isinstance(message, dict):
                await self.send_discovery(message)
        except Exception as e:
            logger.error(f"Error handling discovery message: {e}")
    
    async def _handle_mission_progress_message(self, channel: str, message: Any):
        """Handle mission progress message from Redis"""
        try:
            if isinstance(message, dict):
                await self.send_mission_progress(
                    message.get("mission_id", "unknown"),
                    message
                )
        except Exception as e:
            logger.error(f"Error handling mission progress message: {e}")
    
    async def _handle_ai_response_message(self, channel: str, message: Any):
        """Handle AI response message from Redis"""
        try:
            if isinstance(message, dict):
                await self.send_ai_response(message)
        except Exception as e:
            logger.error(f"Error handling AI response message: {e}")
    
    async def _handle_command_feedback_message(self, channel: str, message: Any):
        """Handle command feedback message from Redis"""
        try:
            if isinstance(message, dict):
                await self.send_command_feedback(
                    message.get("command_id", "unknown"),
                    message
                )
        except Exception as e:
            logger.error(f"Error handling command feedback message: {e}")
    
    async def start(self):
        """Start WebSocket manager"""
        await self.start_redis_subscriber()
        
        # Start Redis message loop in background
        asyncio.create_task(self.redis_service.start_message_loop())
    
    async def stop(self):
        """Stop WebSocket manager"""
        self._running = False
        await self.redis_service.stop_message_loop()
        
        # Close all connections
        for websocket in self.active_connections:
            try:
                await websocket.close()
            except:
                pass
        self.active_connections.clear()
    
    def is_running(self) -> bool:
        """Check if manager is running"""
        return self._running
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)