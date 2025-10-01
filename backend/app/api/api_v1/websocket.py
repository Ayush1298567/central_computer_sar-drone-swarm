from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.mission_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, mission_id: int = None):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if mission_id:
            if mission_id not in self.mission_connections:
                self.mission_connections[mission_id] = []
            self.mission_connections[mission_id].append(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, mission_id: int = None):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if mission_id and mission_id in self.mission_connections:
            if websocket in self.mission_connections[mission_id]:
                self.mission_connections[mission_id].remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_mission(self, mission_id: int, message: dict):
        """Broadcast a message to all clients watching a specific mission."""
        if mission_id not in self.mission_connections:
            return
        
        disconnected = []
        for connection in self.mission_connections[mission_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to mission connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, mission_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            
            elif message.get("type") == "subscribe_mission":
                mission_id = message.get("mission_id")
                if mission_id:
                    if mission_id not in manager.mission_connections:
                        manager.mission_connections[mission_id] = []
                    if websocket not in manager.mission_connections[mission_id]:
                        manager.mission_connections[mission_id].append(websocket)
                    
                    await manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "mission_id": mission_id
                    }, websocket)
            
            elif message.get("type") == "unsubscribe_mission":
                mission_id = message.get("mission_id")
                if mission_id and mission_id in manager.mission_connections:
                    if websocket in manager.mission_connections[mission_id]:
                        manager.mission_connections[mission_id].remove(websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/mission/{mission_id}")
async def mission_websocket(websocket: WebSocket, mission_id: int):
    """WebSocket endpoint for specific mission updates."""
    await manager.connect(websocket, mission_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "mission_id": mission_id,
            "message": "Connected to mission updates"
        }, websocket)
        
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, mission_id)
    except Exception as e:
        logger.error(f"Mission WebSocket error: {e}")
        manager.disconnect(websocket, mission_id)


# Helper function to broadcast updates from other parts of the application
async def broadcast_update(event_type: str, data: dict, mission_id: int = None):
    """Helper function to broadcast updates from anywhere in the application."""
    message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if mission_id:
        await manager.broadcast_to_mission(mission_id, message)
    else:
        await manager.broadcast(message)


# Import datetime for timestamp
from datetime import datetime
