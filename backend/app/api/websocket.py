"""
WebSocket endpoints for SAR Mission Commander
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import json
import asyncio
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()

        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "user_agent": websocket.headers.get("user-agent", "Unknown")
        }

        print(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]

        print(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except:
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
            except:
                disconnected_clients.append(client_id)

        # Clean up broken connections
        for client_id in disconnected_clients:
            self.disconnect(client_id)

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

@router.websocket("/client/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections"""
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

                elif message.get("type") == "chat_message":
                    # Handle chat messages
                    await handle_chat_message(client_id, message)

            except json.JSONDecodeError:
                # Invalid JSON, ignore
                pass

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)

async def handle_subscription(client_id: str, message: dict):
    """Handle subscription requests"""
    subscriptions = message.get("subscriptions", [])

    # Send confirmation
    await connection_manager.send_personal_message({
        "type": "subscription_confirmed",
        "subscriptions": subscriptions,
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