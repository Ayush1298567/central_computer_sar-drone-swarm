"""
WebSocket endpoints for SAR Mission Commander
Real-time data streaming for telemetry, missions, detections, and alerts.
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import json
import asyncio
import logging
import uuid
from typing import Dict, List, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    """Manages WebSocket connections and real-time data broadcasting"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of topics
        self._broadcaster_tasks: List[asyncio.Task] = []
        self._running = False

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()

        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "user_agent": websocket.headers.get("user-agent", "Unknown")
        }
        self.subscriptions[client_id] = set()

        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                # Connection might be broken, remove it
                self.disconnect(client_id)

    async def broadcast_notification(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up broken connections
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_to_subscribers(self, topic: str, message: dict):
        """Broadcast message only to clients subscribed to a specific topic"""
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            # Only send if client is subscribed to this topic
            if topic in self.subscriptions.get(client_id, set()):
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Failed to send {topic} to {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up broken connections
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def subscribe_client(self, client_id: str, topics: List[str]):
        """Subscribe client to specific topics"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].update(topics)
            logger.info(f"Client {client_id} subscribed to: {topics}")
    
    def unsubscribe_client(self, client_id: str, topics: List[str]):
        """Unsubscribe client from specific topics"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].difference_update(topics)
            logger.info(f"Client {client_id} unsubscribed from: {topics}")

    async def send_to_user(self, message: dict, user_id: str):
        """Send message to specific user (if multiple connections per user)"""
        # For now, send to all connections
        await self.broadcast_notification(message)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> Dict[str, any]:
        """Get connection information"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "client_id": client_id,
                    "metadata": metadata
                }
                for client_id, metadata in self.connection_metadata.items()
            ]
        }

# Global connection manager instance
connection_manager = ConnectionManager()

@router.websocket("")
async def websocket_endpoint_auto(websocket: WebSocket):
    """WebSocket endpoint - auto-generates client ID (frontend compatible)"""
    client_id = str(uuid.uuid4())
    await connection_manager.connect(websocket, client_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    # Respond to ping
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)

                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    await handle_subscription(client_id, message)
                
                elif message.get("type") == "unsubscribe":
                    # Handle unsubscribe requests
                    await handle_unsubscribe(client_id, message)

                elif message.get("type") == "chat_message":
                    # Handle chat messages
                    await handle_chat_message(client_id, message)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_id}")
                pass

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)

@router.websocket("/client/{client_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, client_id: str):
    """WebSocket endpoint with explicit client ID (backward compatible)"""
    await connection_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "ping":
                    await connection_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)

                elif message.get("type") == "subscribe":
                    await handle_subscription(client_id, message)
                
                elif message.get("type") == "unsubscribe":
                    await handle_unsubscribe(client_id, message)

                elif message.get("type") == "chat_message":
                    await handle_chat_message(client_id, message)

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)

async def handle_subscription(client_id: str, message: dict):
    """Handle subscription requests"""
    topics = message.get("payload", {}).get("topics", message.get("subscriptions", []))
    
    connection_manager.subscribe_client(client_id, topics)

    # Send confirmation
    await connection_manager.send_personal_message({
        "type": "subscription_confirmed",
        "payload": {"topics": topics},
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)

async def handle_unsubscribe(client_id: str, message: dict):
    """Handle unsubscribe requests"""
    topics = message.get("payload", {}).get("topics", [])
    
    connection_manager.unsubscribe_client(client_id, topics)

    # Send confirmation
    await connection_manager.send_personal_message({
        "type": "unsubscribe_confirmed",
        "payload": {"topics": topics},
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)

async def handle_chat_message(client_id: str, message: dict):
    """Handle incoming chat messages"""
    # This could trigger notifications to other users
    # For now, just echo back
    await connection_manager.send_personal_message({
        "type": "chat_message_echo",
        "original_message": message,
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)

# Additional utility functions for the notification service
async def broadcast_system_message(message_type: str, data: dict):
    """Broadcast system message to all clients"""
    await connection_manager.broadcast_notification({
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })

async def send_user_message(user_id: str, message_type: str, data: dict):
    """Send message to specific user"""
    await connection_manager.send_to_user({
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }, user_id)


# ==================== BACKGROUND BROADCASTERS ====================

async def telemetry_broadcaster():
    """
    Background task: Stream telemetry data to subscribed clients every 1 second.
    Reads from TelemetryReceiver and broadcasts to 'telemetry' topic subscribers.
    """
    logger.info("🚁 Telemetry broadcaster started")
    
    while connection_manager._running:
        try:
            # Import here to avoid circular dependencies
            from app.communication.telemetry_receiver import get_telemetry_receiver
            
            receiver = get_telemetry_receiver()
            snapshot = receiver.cache.snapshot()
            
            if snapshot:
                # Format telemetry data
                drones = []
                for drone_id, telemetry in snapshot.items():
                    drones.append({
                        "id": drone_id,
                        **telemetry
                    })
                
                # Broadcast to telemetry subscribers
                await connection_manager.broadcast_to_subscribers("telemetry", {
                    "type": "telemetry",
                    "payload": {"drones": drones},
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            await asyncio.sleep(1.0)  # 1 second interval
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Telemetry broadcaster error: {e}")
            await asyncio.sleep(1.0)
    
    logger.info("🚁 Telemetry broadcaster stopped")


async def mission_updates_broadcaster():
    """
    Background task: Stream mission status updates to subscribed clients every 1 second.
    Reads from RealMissionExecutionEngine and broadcasts to 'mission_updates' subscribers.
    """
    logger.info("📋 Mission updates broadcaster started")
    
    while connection_manager._running:
        try:
            from app.services.real_mission_execution import real_mission_execution_engine
            
            if hasattr(real_mission_execution_engine, '_running_missions'):
                missions = []
                for mission_id, mission_data in real_mission_execution_engine._running_missions.items():
                    missions.append({
                        "mission_id": mission_id,
                        "status": mission_data.get("status", "UNKNOWN"),
                        "drones": mission_data.get("drones", []),
                        "payload": mission_data.get("payload", {}),
                        "updated_at": datetime.utcnow().isoformat()
                    })
                
                if missions:
                    await connection_manager.broadcast_to_subscribers("mission_updates", {
                        "type": "mission_updates",
                        "payload": {"missions": missions},
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            await asyncio.sleep(1.0)  # 1 second interval
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Mission updates broadcaster error: {e}")
            await asyncio.sleep(1.0)
    
    logger.info("📋 Mission updates broadcaster stopped")


async def detections_broadcaster():
    """
    Background task: Stream detection events to subscribed clients every 2 seconds.
    Reads from computer vision system and broadcasts to 'detections' subscribers.
    """
    logger.info("🔍 Detections broadcaster started")
    
    while connection_manager._running:
        try:
            # Placeholder for computer vision integration
            # In production, this would read from real_computer_vision module
            # For now, we'll just maintain the broadcaster infrastructure
            
            # Example structure (uncomment when CV system is ready):
            # from app.ai.real_computer_vision import get_recent_detections
            # detections = get_recent_detections(limit=10)
            # if detections:
            #     await connection_manager.broadcast_to_subscribers("detections", {
            #         "type": "detections",
            #         "payload": {"detections": detections},
            #         "timestamp": datetime.utcnow().isoformat()
            #     })
            
            await asyncio.sleep(2.0)  # 2 second interval
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Detections broadcaster error: {e}")
            await asyncio.sleep(2.0)
    
    logger.info("🔍 Detections broadcaster stopped")


async def alerts_broadcaster():
    """
    Background task: Stream alert events to subscribed clients (event-driven).
    Monitors alerting system and broadcasts to 'alerts' subscribers.
    """
    logger.info("⚠️  Alerts broadcaster started")
    
    while connection_manager._running:
        try:
            # Placeholder for monitoring/alerting integration
            # In production, this would read from monitoring.alerting module
            # For now, we maintain the broadcaster infrastructure
            
            # Example structure (uncomment when alerting system is ready):
            # from app.monitoring.alerting import get_active_alerts
            # alerts = get_active_alerts()
            # if alerts:
            #     await connection_manager.broadcast_to_subscribers("alerts", {
            #         "type": "alerts",
            #         "payload": {"alerts": alerts},
            #         "timestamp": datetime.utcnow().isoformat()
            #     })
            
            await asyncio.sleep(1.0)  # Check every second
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Alerts broadcaster error: {e}")
            await asyncio.sleep(1.0)
    
    logger.info("⚠️  Alerts broadcaster stopped")


async def start_broadcasters():
    """Start all background broadcasters"""
    if connection_manager._running:
        logger.warning("Broadcasters already running")
        return
    
    connection_manager._running = True
    
    # Create broadcaster tasks
    connection_manager._broadcaster_tasks = [
        asyncio.create_task(telemetry_broadcaster()),
        asyncio.create_task(mission_updates_broadcaster()),
        asyncio.create_task(detections_broadcaster()),
        asyncio.create_task(alerts_broadcaster())
    ]
    
    logger.info("✅ All WebSocket broadcasters started")


async def stop_broadcasters():
    """Stop all background broadcasters gracefully"""
    connection_manager._running = False
    
    # Cancel all broadcaster tasks
    for task in connection_manager._broadcaster_tasks:
        task.cancel()
    
    # Wait for tasks to complete
    if connection_manager._broadcaster_tasks:
        await asyncio.gather(*connection_manager._broadcaster_tasks, return_exceptions=True)
    
    connection_manager._broadcaster_tasks.clear()
    logger.info("✅ All WebSocket broadcasters stopped")