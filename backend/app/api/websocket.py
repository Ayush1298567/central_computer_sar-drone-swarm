"""
WebSocket handlers for real-time communication in the SAR drone system
"""
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.config import settings
from ..models.mission import Mission, MissionStatus
from ..models.drone import Drone, DroneStatus
from ..services.notification_service import NotificationService
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionType:
    CLIENT = "client"
    DRONE = "drone"
    ADMIN = "admin"

class MessageType:
    # Client messages
    SUBSCRIBE_MISSION = "subscribe_mission"
    UNSUBSCRIBE_MISSION = "unsubscribe_mission"
    SUBSCRIBE_DRONE = "subscribe_drone"
    UNSUBSCRIBE_DRONE = "unsubscribe_drone"
    SUBSCRIBE_NOTIFICATIONS = "subscribe_notifications"
    
    # Drone messages
    TELEMETRY_UPDATE = "telemetry_update"
    STATUS_UPDATE = "status_update"
    MISSION_PROGRESS = "mission_progress"
    DISCOVERY_REPORT = "discovery_report"
    
    # System messages
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    NOTIFICATION = "notification"
    
    # Broadcast messages
    MISSION_STARTED = "mission_started"
    MISSION_COMPLETED = "mission_completed"
    MISSION_ABORTED = "mission_aborted"
    DRONE_CONNECTED = "drone_connected"
    DRONE_DISCONNECTED = "drone_disconnected"

class WebSocketConnection:
    """Represents a WebSocket connection"""
    
    def __init__(self, websocket: WebSocket, connection_type: str, identifier: str):
        self.websocket = websocket
        self.connection_type = connection_type
        self.identifier = identifier  # user_id for clients, drone_id for drones
        self.connection_id = f"{connection_type}_{uuid.uuid4().hex[:8]}"
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        
    async def send_message(self, message_type: str, data: Any = None, error: str = None):
        """Send a message to this connection"""
        try:
            if self.websocket.client_state != WebSocketState.CONNECTED:
                return False
                
            message = {
                "type": message_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                "error": error
            }
            
            await self.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message to {self.connection_id}: {str(e)}")
            return False
    
    async def send_heartbeat(self):
        """Send heartbeat to connection"""
        return await self.send_message(MessageType.HEARTBEAT, {"connection_id": self.connection_id})

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.mission_subscribers: Dict[str, Set[str]] = {}  # mission_id -> connection_ids
        self.drone_subscribers: Dict[str, Set[str]] = {}    # drone_id -> connection_ids
        self.notification_subscribers: Set[str] = set()     # connection_ids
        self.heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, connection_type: str, identifier: str) -> WebSocketConnection:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, connection_type, identifier)
        self.connections[connection.connection_id] = connection
        
        # Start heartbeat task if this is the first connection
        if len(self.connections) == 1 and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"WebSocket connected: {connection.connection_id} ({connection_type}:{identifier})")
        
        # Send welcome message
        await connection.send_message("connected", {
            "connection_id": connection.connection_id,
            "connection_type": connection_type,
            "identifier": identifier,
            "server_time": datetime.utcnow().isoformat()
        })
        
        # Broadcast connection event
        if connection_type == ConnectionType.DRONE:
            await self._broadcast_to_clients(MessageType.DRONE_CONNECTED, {
                "drone_id": identifier,
                "connected_at": connection.connected_at.isoformat()
            })
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """Disconnect and clean up a connection"""
        if connection_id not in self.connections:
            return
            
        connection = self.connections[connection_id]
        
        # Clean up subscriptions
        for mission_id, subscribers in self.mission_subscribers.items():
            subscribers.discard(connection_id)
        for drone_id, subscribers in self.drone_subscribers.items():
            subscribers.discard(connection_id)
        self.notification_subscribers.discard(connection_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        # Broadcast disconnection event
        if connection.connection_type == ConnectionType.DRONE:
            await self._broadcast_to_clients(MessageType.DRONE_DISCONNECTED, {
                "drone_id": connection.identifier,
                "disconnected_at": datetime.utcnow().isoformat()
            })
        
        # Stop heartbeat task if no connections remain
        if len(self.connections) == 0 and self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_mission(self, connection_id: str, mission_id: str):
        """Subscribe connection to mission updates"""
        if connection_id not in self.connections:
            return False
            
        if mission_id not in self.mission_subscribers:
            self.mission_subscribers[mission_id] = set()
        
        self.mission_subscribers[mission_id].add(connection_id)
        self.connections[connection_id].subscriptions.add(f"mission:{mission_id}")
        
        logger.debug(f"Connection {connection_id} subscribed to mission {mission_id}")
        return True
    
    async def unsubscribe_from_mission(self, connection_id: str, mission_id: str):
        """Unsubscribe connection from mission updates"""
        if mission_id in self.mission_subscribers:
            self.mission_subscribers[mission_id].discard(connection_id)
        
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.discard(f"mission:{mission_id}")
        
        logger.debug(f"Connection {connection_id} unsubscribed from mission {mission_id}")
    
    async def subscribe_to_drone(self, connection_id: str, drone_id: str):
        """Subscribe connection to drone updates"""
        if connection_id not in self.connections:
            return False
            
        if drone_id not in self.drone_subscribers:
            self.drone_subscribers[drone_id] = set()
        
        self.drone_subscribers[drone_id].add(connection_id)
        self.connections[connection_id].subscriptions.add(f"drone:{drone_id}")
        
        logger.debug(f"Connection {connection_id} subscribed to drone {drone_id}")
        return True
    
    async def subscribe_to_notifications(self, connection_id: str):
        """Subscribe connection to notifications"""
        if connection_id not in self.connections:
            return False
            
        self.notification_subscribers.add(connection_id)
        self.connections[connection_id].subscriptions.add("notifications")
        
        logger.debug(f"Connection {connection_id} subscribed to notifications")
        return True
    
    async def broadcast_to_mission_subscribers(self, mission_id: str, message_type: str, data: Any):
        """Broadcast message to all mission subscribers"""
        if mission_id not in self.mission_subscribers:
            return 0
        
        subscribers = self.mission_subscribers[mission_id].copy()
        successful_sends = 0
        
        for connection_id in subscribers:
            if connection_id in self.connections:
                success = await self.connections[connection_id].send_message(message_type, data)
                if success:
                    successful_sends += 1
                else:
                    # Remove failed connection
                    await self.disconnect(connection_id)
        
        logger.debug(f"Broadcasted {message_type} to {successful_sends} mission subscribers")
        return successful_sends
    
    async def broadcast_to_drone_subscribers(self, drone_id: str, message_type: str, data: Any):
        """Broadcast message to all drone subscribers"""
        if drone_id not in self.drone_subscribers:
            return 0
        
        subscribers = self.drone_subscribers[drone_id].copy()
        successful_sends = 0
        
        for connection_id in subscribers:
            if connection_id in self.connections:
                success = await self.connections[connection_id].send_message(message_type, data)
                if success:
                    successful_sends += 1
                else:
                    # Remove failed connection
                    await self.disconnect(connection_id)
        
        logger.debug(f"Broadcasted {message_type} to {successful_sends} drone subscribers")
        return successful_sends
    
    async def broadcast_notification(self, notification_data: Dict[str, Any]):
        """Broadcast notification to all notification subscribers"""
        subscribers = self.notification_subscribers.copy()
        successful_sends = 0
        
        for connection_id in subscribers:
            if connection_id in self.connections:
                success = await self.connections[connection_id].send_message(
                    MessageType.NOTIFICATION, 
                    notification_data
                )
                if success:
                    successful_sends += 1
                else:
                    # Remove failed connection
                    await self.disconnect(connection_id)
        
        logger.debug(f"Broadcasted notification to {successful_sends} subscribers")
        return successful_sends
    
    async def send_to_drone(self, drone_id: str, message_type: str, data: Any) -> bool:
        """Send message to a specific drone"""
        for connection in self.connections.values():
            if (connection.connection_type == ConnectionType.DRONE and 
                connection.identifier == drone_id):
                return await connection.send_message(message_type, data)
        
        logger.warning(f"Drone {drone_id} not connected via WebSocket")
        return False
    
    async def _broadcast_to_clients(self, message_type: str, data: Any):
        """Broadcast to all client connections"""
        client_connections = [
            conn for conn in self.connections.values() 
            if conn.connection_type == ConnectionType.CLIENT
        ]
        
        for connection in client_connections:
            await connection.send_message(message_type, data)
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat to maintain connections"""
        try:
            while True:
                await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)
                
                # Send heartbeat to all connections
                failed_connections = []
                for connection_id, connection in self.connections.items():
                    success = await connection.send_heartbeat()
                    if not success:
                        failed_connections.append(connection_id)
                
                # Clean up failed connections
                for connection_id in failed_connections:
                    await self.disconnect(connection_id)
                    
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {str(e)}")

# Global connection manager instance
connection_manager = ConnectionManager()

@router.websocket("/ws/client/{user_id}")
async def websocket_client_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for client connections"""
    connection = await connection_manager.connect(websocket, ConnectionType.CLIENT, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await _handle_client_message(connection, message)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection.connection_id)
    except Exception as e:
        logger.error(f"Error in client WebSocket {user_id}: {str(e)}")
        await connection_manager.disconnect(connection.connection_id)

@router.websocket("/ws/drone/{drone_id}")
async def websocket_drone_endpoint(websocket: WebSocket, drone_id: str):
    """WebSocket endpoint for drone connections"""
    connection = await connection_manager.connect(websocket, ConnectionType.DRONE, drone_id)
    
    try:
        while True:
            # Receive message from drone
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await _handle_drone_message(connection, message)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection.connection_id)
    except Exception as e:
        logger.error(f"Error in drone WebSocket {drone_id}: {str(e)}")
        await connection_manager.disconnect(connection.connection_id)

@router.websocket("/ws/admin/{admin_id}")
async def websocket_admin_endpoint(websocket: WebSocket, admin_id: str):
    """WebSocket endpoint for admin connections"""
    connection = await connection_manager.connect(websocket, ConnectionType.ADMIN, admin_id)
    
    try:
        while True:
            # Receive message from admin
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await _handle_admin_message(connection, message)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(connection.connection_id)
    except Exception as e:
        logger.error(f"Error in admin WebSocket {admin_id}: {str(e)}")
        await connection_manager.disconnect(connection.connection_id)

# Message handlers
async def _handle_client_message(connection: WebSocketConnection, message: Dict[str, Any]):
    """Handle messages from client connections"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        if message_type == MessageType.SUBSCRIBE_MISSION:
            mission_id = data.get("mission_id")
            if mission_id:
                success = await connection_manager.subscribe_to_mission(connection.connection_id, mission_id)
                await connection.send_message("subscription_result", {
                    "type": "mission",
                    "target": mission_id,
                    "success": success
                })
        
        elif message_type == MessageType.UNSUBSCRIBE_MISSION:
            mission_id = data.get("mission_id")
            if mission_id:
                await connection_manager.unsubscribe_from_mission(connection.connection_id, mission_id)
                await connection.send_message("unsubscription_result", {
                    "type": "mission",
                    "target": mission_id,
                    "success": True
                })
        
        elif message_type == MessageType.SUBSCRIBE_DRONE:
            drone_id = data.get("drone_id")
            if drone_id:
                success = await connection_manager.subscribe_to_drone(connection.connection_id, drone_id)
                await connection.send_message("subscription_result", {
                    "type": "drone",
                    "target": drone_id,
                    "success": success
                })
        
        elif message_type == MessageType.SUBSCRIBE_NOTIFICATIONS:
            success = await connection_manager.subscribe_to_notifications(connection.connection_id)
            await connection.send_message("subscription_result", {
                "type": "notifications",
                "success": success
            })
        
        elif message_type == MessageType.HEARTBEAT:
            connection.last_heartbeat = datetime.utcnow()
            await connection.send_message(MessageType.HEARTBEAT, {"status": "ok"})
        
        else:
            await connection.send_message(MessageType.ERROR, error=f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling client message: {str(e)}")
        await connection.send_message(MessageType.ERROR, error="Internal server error")

async def _handle_drone_message(connection: WebSocketConnection, message: Dict[str, Any]):
    """Handle messages from drone connections"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        drone_id = connection.identifier
        
        if message_type == MessageType.TELEMETRY_UPDATE:
            # Broadcast telemetry to subscribers
            await connection_manager.broadcast_to_drone_subscribers(
                drone_id, 
                MessageType.TELEMETRY_UPDATE, 
                {
                    "drone_id": drone_id,
                    "telemetry": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        elif message_type == MessageType.STATUS_UPDATE:
            # Broadcast status update to subscribers
            await connection_manager.broadcast_to_drone_subscribers(
                drone_id,
                MessageType.STATUS_UPDATE,
                {
                    "drone_id": drone_id,
                    "status": data.get("status"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        elif message_type == MessageType.MISSION_PROGRESS:
            # Broadcast mission progress to mission subscribers
            mission_id = data.get("mission_id")
            if mission_id:
                await connection_manager.broadcast_to_mission_subscribers(
                    mission_id,
                    MessageType.MISSION_PROGRESS,
                    {
                        "drone_id": drone_id,
                        "mission_id": mission_id,
                        "progress": data.get("progress"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        elif message_type == MessageType.DISCOVERY_REPORT:
            # Broadcast discovery to mission and drone subscribers
            mission_id = data.get("mission_id")
            discovery_data = {
                "drone_id": drone_id,
                "discovery": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to mission subscribers
            if mission_id:
                await connection_manager.broadcast_to_mission_subscribers(
                    mission_id, MessageType.DISCOVERY_REPORT, discovery_data
                )
            
            # Send to drone subscribers
            await connection_manager.broadcast_to_drone_subscribers(
                drone_id, MessageType.DISCOVERY_REPORT, discovery_data
            )
            
            # Send as notification
            await connection_manager.broadcast_notification({
                "type": "discovery",
                "title": "Object Discovered",
                "message": f"Drone {drone_id} discovered an object",
                "data": discovery_data
            })
        
        elif message_type == MessageType.HEARTBEAT:
            connection.last_heartbeat = datetime.utcnow()
            await connection.send_message(MessageType.HEARTBEAT, {"status": "ok"})
        
        else:
            await connection.send_message(MessageType.ERROR, error=f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling drone message: {str(e)}")
        await connection.send_message(MessageType.ERROR, error="Internal server error")

async def _handle_admin_message(connection: WebSocketConnection, message: Dict[str, Any]):
    """Handle messages from admin connections"""
    try:
        message_type = message.get("type")
        data = message.get("data", {})
        
        # Admin can send commands to drones
        if message_type == "drone_command":
            drone_id = data.get("drone_id")
            command = data.get("command")
            
            if drone_id and command:
                success = await connection_manager.send_to_drone(drone_id, "command", command)
                await connection.send_message("command_result", {
                    "drone_id": drone_id,
                    "success": success
                })
        
        # Admin can broadcast messages
        elif message_type == "broadcast":
            broadcast_type = data.get("broadcast_type", "notification")
            broadcast_data = data.get("data", {})
            
            if broadcast_type == "notification":
                await connection_manager.broadcast_notification(broadcast_data)
            
        else:
            # Handle like client message
            await _handle_client_message(connection, message)
            
    except Exception as e:
        logger.error(f"Error handling admin message: {str(e)}")
        await connection.send_message(MessageType.ERROR, error="Internal server error")

# API endpoints for WebSocket management
@router.get("/ws/connections")
async def get_connections():
    """Get current WebSocket connections (admin only)"""
    connections_info = []
    
    for connection_id, connection in connection_manager.connections.items():
        connections_info.append({
            "connection_id": connection_id,
            "type": connection.connection_type,
            "identifier": connection.identifier,
            "connected_at": connection.connected_at.isoformat(),
            "last_heartbeat": connection.last_heartbeat.isoformat(),
            "subscriptions": list(connection.subscriptions)
        })
    
    return {
        "total_connections": len(connection_manager.connections),
        "connections": connections_info,
        "mission_subscribers": {
            mission_id: len(subscribers) 
            for mission_id, subscribers in connection_manager.mission_subscribers.items()
        },
        "drone_subscribers": {
            drone_id: len(subscribers)
            for drone_id, subscribers in connection_manager.drone_subscribers.items()
        },
        "notification_subscribers": len(connection_manager.notification_subscribers)
    }

@router.post("/ws/broadcast")
async def broadcast_message(
    message_type: str,
    data: Dict[str, Any],
    target_type: Optional[str] = None,
    target_id: Optional[str] = None
):
    """Broadcast a message via WebSocket (admin only)"""
    try:
        if target_type == "mission" and target_id:
            count = await connection_manager.broadcast_to_mission_subscribers(target_id, message_type, data)
        elif target_type == "drone" and target_id:
            count = await connection_manager.broadcast_to_drone_subscribers(target_id, message_type, data)
        elif target_type == "notifications":
            count = await connection_manager.broadcast_notification(data)
        else:
            # Broadcast to all clients
            client_connections = [
                conn for conn in connection_manager.connections.values()
                if conn.connection_type == ConnectionType.CLIENT
            ]
            count = 0
            for connection in client_connections:
                if await connection.send_message(message_type, data):
                    count += 1
        
        return {"message": "Broadcast sent", "recipients": count}
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")

# Export connection manager for use in other modules
__all__ = ["connection_manager", "ConnectionManager", "MessageType"]