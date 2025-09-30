from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from typing import Dict, List

router = APIRouter()
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str, websocket: WebSocket):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"WebSocket client {client_id} disconnected")

    async def send_to_client(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            message_text = json.dumps(message)
            disconnected_clients = []
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message_text)
                except:
                    disconnected_clients.append(connection)

            # Clean up disconnected clients
            for connection in disconnected_clients:
                self.disconnect(client_id, connection)

manager = ConnectionManager()

@router.websocket("/mission/{mission_id}")
async def websocket_endpoint(websocket: WebSocket, mission_id: str):
    """WebSocket endpoint for real-time mission updates."""
    client_id = f"mission_{mission_id}"
    await manager.connect(client_id, websocket)

    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                # Process client message here
                logger.info(f"Received WebSocket message for mission {mission_id}: {message}")

                # Send acknowledgment
                await manager.send_to_client(client_id, {
                    "type": "acknowledgment",
                    "status": "received",
                    "mission_id": mission_id
                })

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {client_id}")

    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id, websocket)