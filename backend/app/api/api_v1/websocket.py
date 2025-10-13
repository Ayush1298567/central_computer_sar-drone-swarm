import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.routing import APIRouter
import asyncio
import json
from datetime import datetime

from app.core.security import get_current_user_ws
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """WebSocket connection manager with authentication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_users: Dict[str, int] = {}  # connection_id -> user_id
        self.subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of topics
    
    async def connect(self, websocket: WebSocket, user: User) -> str:
        """Accept WebSocket connection and authenticate user"""
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = f"conn_{datetime.now().timestamp()}_{user.id}"
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Track user connections
        if user.id not in self.user_connections:
            self.user_connections[user.id] = set()
        self.user_connections[user.id].add(connection_id)
        self.connection_users[connection_id] = user.id
        
        # Initialize subscriptions
        self.subscriptions[connection_id] = set()
        
        logger.info(f"WebSocket connected: {connection_id} for user {user.username} (ID: {user.id})")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to SAR Mission Control",
            "user": {
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin
            },
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            user_id = self.connection_users.get(connection_id)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Clean up
            del self.active_connections[connection_id]
            del self.connection_users[connection_id]
            if connection_id in self.subscriptions:
                del self.subscriptions[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: int):
        """Send message to all connections of a user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_topic(self, message: Dict[str, Any], topic: str):
        """Broadcast message to all connections subscribed to topic"""
        for connection_id, topics in self.subscriptions.items():
            if topic in topics:
                await self.send_personal_message(message, connection_id)
    
    async def subscribe_to_topic(self, connection_id: str, topics: list):
        """Subscribe connection to topics"""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].update(topics)
            logger.info(f"Connection {connection_id} subscribed to: {topics}")
    
    async def unsubscribe_from_topic(self, connection_id: str, topics: list):
        """Unsubscribe connection from topics"""
        if connection_id in self.subscriptions:
            for topic in topics:
                self.subscriptions[connection_id].discard(topic)
            logger.info(f"Connection {connection_id} unsubscribed from: {topics}")

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """WebSocket endpoint; allows guest access if no token provided."""
    connection_id = None
    
    try:
        # Authenticate WebSocket connection if token provided, else create guest
        user = None
        if token:
            user = await get_current_user_ws(token)
        if not user:
            # Create a lightweight guest user object
            from types import SimpleNamespace
            user = SimpleNamespace(id=0, username="guest", is_admin=False)
        
        # Accept connection
        connection_id = await manager.connect(websocket, user)
        logger.info(f"WebSocket authenticated: user {user.username} (ID: {user.id})")
        
        try:
            while True:
                # Receive message with timeout
                try:
                    async with asyncio.timeout(30):
                        data = await websocket.receive_json()
                        await handle_websocket_message(data, connection_id, user)
                except asyncio.TimeoutError:
                    logger.error(f"WebSocket message handling timeout for user {user.username}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Request timeout"
                    }, connection_id)
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user {user.username}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user.username}: {e}", exc_info=True)
        finally:
            if connection_id:
                manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass

async def handle_websocket_message(data: Dict[str, Any], connection_id: str, user: User):
    """Handle incoming WebSocket messages"""
    try:
        message_type = data.get("type")
        payload = data.get("payload", {})
        
        logger.debug(f"WebSocket message from {user.username}: {message_type}")
        
        if message_type == "ping":
            # Respond to ping
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
        
        elif message_type == "subscribe":
            # Subscribe to topics
            topics = payload.get("topics", [])
            await manager.subscribe_to_topic(connection_id, topics)
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "topics": topics,
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
        
        elif message_type == "unsubscribe":
            # Unsubscribe from topics
            topics = payload.get("topics", [])
            await manager.unsubscribe_from_topic(connection_id, topics)
            await manager.send_personal_message({
                "type": "unsubscription_confirmed",
                "topics": topics,
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
        
        elif message_type == "request_telemetry":
            # Request telemetry data
            await handle_telemetry_request(connection_id, user)
        
        elif message_type == "drone_command":
            # Handle drone command
            await handle_drone_command(payload, user, connection_id)
        
        elif message_type == "emergency_stop":
            # Handle emergency stop
            await handle_emergency_stop(payload, user, connection_id)
        
        elif message_type == "mission_planning_request":
            # Handle mission planning request
            await handle_mission_planning_request(payload, user, connection_id)
        
        elif message_type == "detection_report":
            # Handle detection report
            await handle_detection_report(payload, user, connection_id)
        
        else:
            # Unknown message type
            await manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            }, connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket message handling failed: {e}", exc_info=True)
        await manager.send_personal_message({
            "type": "error",
            "message": "Message processing failed",
            "timestamp": datetime.utcnow().isoformat()
        }, connection_id)

async def handle_telemetry_request(connection_id: str, user: User):
    """Handle telemetry data request"""
    try:
        # Get telemetry snapshot lazily
        try:
            from app.communication.telemetry_receiver import get_telemetry_receiver
            from app.communication.drone_registry import get_registry
            recv = get_telemetry_receiver()
            recv.start()
            snap = recv.cache.snapshot()
            reg = get_registry()
            drones_list = []
            for drone_id, telem in snap.items():
                reg_status = reg.get_status(drone_id) if hasattr(reg, 'get_status') else None
                last_seen = reg.get_last_seen(drone_id) if hasattr(reg, 'get_last_seen') else None
                mission_status = reg.get_mission_status(drone_id) if hasattr(reg, 'get_mission_status') else None
                drones_list.append({
                    "id": drone_id,
                    **telem,
                    "status": reg_status,
                    "last_seen": last_seen,
                    "mission_status": mission_status,
                    "last_update": telem.get("last_update") or datetime.utcnow().isoformat(),
                })
        except Exception:
            logger.exception("Telemetry receiver unavailable; sending placeholder")
            drones_list = []

        telemetry_data = {
            "type": "telemetry",
            "payload": {
                "drones": drones_list,
            },
        }
        await manager.send_personal_message(telemetry_data, connection_id)
        
    except Exception as e:
        logger.error(f"Telemetry request failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to retrieve telemetry data"
        }, connection_id)

async def handle_drone_command(payload: Dict[str, Any], user: User, connection_id: str):
    """Handle drone command"""
    try:
        drone_id = payload.get("drone_id")
        command = payload.get("command")
        params = payload.get("params", {})
        
        logger.info(f"Drone command from {user.username}: {command} for {drone_id}")
        
        # TODO: Implement actual drone command execution
        # This would interface with MAVLink or drone control systems
        
        # Send command acknowledgment
        await manager.send_personal_message({
            "type": "command_acknowledged",
            "payload": {
                "drone_id": drone_id,
                "command": command,
                "status": "sent",
                "timestamp": datetime.utcnow().isoformat()
            }
        }, connection_id)
        
        # Broadcast command to other users
        await manager.broadcast_to_topic({
            "type": "drone_command_broadcast",
            "payload": {
                "drone_id": drone_id,
                "command": command,
                "operator": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, "drone_commands")
        
    except Exception as e:
        logger.error(f"Drone command failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Drone command failed: {str(e)}"
        }, connection_id)

async def handle_emergency_stop(payload: Dict[str, Any], user: User, connection_id: str):
    """Handle emergency stop request"""
    try:
        reason = payload.get("reason", "Emergency stop triggered")
        
        logger.critical(f"🚨 EMERGENCY STOP from {user.username}: {reason}")
        
        # TODO: Implement actual emergency stop logic
        # This would immediately halt all drone operations
        
        # Send emergency stop acknowledgment
        await manager.send_personal_message({
            "type": "emergency_stop_acknowledged",
            "payload": {
                "status": "activated",
                "reason": reason,
                "operator": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, connection_id)
        
        # Broadcast emergency stop to all users
        await manager.broadcast_to_topic({
            "type": "emergency_stop_broadcast",
            "payload": {
                "status": "activated",
                "reason": reason,
                "operator": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, "alerts")
        
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Emergency stop failed: {str(e)}"
        }, connection_id)

async def handle_mission_planning_request(payload: Dict[str, Any], user: User, connection_id: str):
    """Handle mission planning request"""
    try:
        user_input = payload.get("user_input")
        context = payload.get("context", {})
        conversation_id = payload.get("conversation_id", "default")
        
        logger.info(f"Mission planning request from {user.username}")
        
        # TODO: Integrate with mission planner service
        from app.services.mission_planner import mission_planner
        
        result = await mission_planner.plan_mission(
            user_input=user_input,
            context=context,
            conversation_id=conversation_id
        )
        
        # Send planning response
        await manager.send_personal_message({
            "type": "mission_planning_response",
            "payload": result
        }, connection_id)
        
    except Exception as e:
        logger.error(f"Mission planning failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Mission planning failed: {str(e)}"
        }, connection_id)

async def handle_detection_report(payload: Dict[str, Any], user: User, connection_id: str):
    """Handle detection report"""
    try:
        logger.info(f"Detection report from {user.username}")
        
        # TODO: Process detection with computer vision service
        # This would analyze the detection and update mission status
        
        # Broadcast detection to subscribed users
        await manager.broadcast_to_topic({
            "type": "detections",
            "payload": {
                **payload,
                "reported_by": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, "detections")
        
    except Exception as e:
        logger.error(f"Detection report failed: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Detection report failed: {str(e)}"
        }, connection_id)

# Utility functions for broadcasting messages
async def broadcast_telemetry(telemetry_data: Dict[str, Any]):
    """Broadcast telemetry data to all subscribed connections"""
    await manager.broadcast_to_topic({
        "type": "telemetry",
        "payload": telemetry_data
    }, "telemetry")


async def broadcast_telemetry_snapshot_once() -> None:
    """Fetch normalized telemetry from cache and broadcast to 'telemetry' topic once."""
    try:
        from app.communication.telemetry_receiver import get_telemetry_receiver
        recv = get_telemetry_receiver()
        recv.start()
        snapshot = await recv.cache.get_all()
        drones = list(snapshot.values())
        await manager.broadcast_to_topic({
            "type": "telemetry",
            "payload": {"drones": drones},
        }, "telemetry")
    except Exception:
        logger.exception("Failed to broadcast telemetry snapshot")


async def telemetry_broadcast_loop(stop_event: asyncio.Event) -> None:
    """Periodic broadcaster that emits telemetry every second."""
    try:
        while not stop_event.is_set():
            await broadcast_telemetry_snapshot_once()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        return

async def broadcast_detection(detection_data: Dict[str, Any]):
    """Broadcast detection data to all subscribed connections"""
    await manager.broadcast_to_topic({
        "type": "detections",
        "payload": detection_data
    }, "detections")

async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast alert to all subscribed connections"""
    await manager.broadcast_to_topic({
        "type": "alerts",
        "payload": alert_data
    }, "alerts")

async def broadcast_mission_update(mission_data: Dict[str, Any]):
    """Broadcast mission update to all subscribed connections"""
    await manager.broadcast_to_topic({
        "type": "mission_updates",
        "payload": mission_data
    }, "mission_updates")