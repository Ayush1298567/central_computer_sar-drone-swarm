"""
WebSocket API Router

Handles WebSocket connections for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import Dict, List
import asyncio

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

manager = ConnectionManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    client_id = f"client_{len(manager.active_connections)}"
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "unknown")

                # Echo back the message for now
                response = {
                    "type": f"response_{message_type}",
                    "data": message_data.get("data", {}),
                    "timestamp": "2024-01-01T00:00:00Z",
                    "id": message_data.get("id")
                }

                await manager.send_personal_message(response, client_id)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                    "timestamp": "2024-01-01T00:00:00Z"
                }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)