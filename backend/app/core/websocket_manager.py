"""
WebSocket connection manager for real-time communication.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Active connections: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata: client_id -> metadata
        self.connection_metadata: Dict[str, dict] = {}
        
        # Room subscriptions: room_name -> set of client_ids
        self.rooms: Dict[str, set] = {}
        
        # Message history for reconnection
        self.message_history: Dict[str, List[dict]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Store connection
        self.active_connections[client_id] = websocket
        
        # Initialize metadata
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat(),
            "subscribed_rooms": set(),
            "user_type": "operator"  # Default, can be updated
        }
        
        # Initialize message history
        if client_id not in self.message_history:
            self.message_history[client_id] = []
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            }),
            client_id
        )
        
    def disconnect(self, client_id: str):
        """Disconnect a client."""
        if client_id in self.active_connections:
            # Remove from all rooms
            for room_name, members in self.rooms.items():
                members.discard(client_id)
            
            # Clean up empty rooms
            self.rooms = {k: v for k, v in self.rooms.items() if v}
            
            # Remove connection
            del self.active_connections[client_id]
            
            # Keep metadata for potential reconnection
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["disconnected_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(message)
                
                # Store in message history
                self.message_history[client_id].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "outbound",
                    "message": message
                })
                
                # Limit message history size
                if len(self.message_history[client_id]) > 100:
                    self.message_history[client_id] = self.message_history[client_id][-100:]
                    
            except WebSocketDisconnect:
                logger.warning(f"Client {client_id} disconnected during message send")
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str, exclude: Optional[List[str]] = None):
        """Broadcast a message to all connected clients."""
        exclude = exclude or []
        
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await websocket.send_text(message)
                except WebSocketDisconnect:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_to_room(self, room: str, message: str, exclude: Optional[List[str]] = None):
        """Broadcast a message to all clients in a specific room."""
        exclude = exclude or []
        
        if room not in self.rooms:
            logger.warning(f"Attempted to broadcast to non-existent room: {room}")
            return
        
        room_members = list(self.rooms[room])
        disconnected_clients = []
        
        for client_id in room_members:
            if client_id not in exclude and client_id in self.active_connections:
                try:
                    websocket = self.active_connections[client_id]
                    await websocket.send_text(message)
                except WebSocketDisconnect:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id} in room {room}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def join_room(self, client_id: str, room: str):
        """Add a client to a room."""
        if client_id not in self.active_connections:
            logger.warning(f"Cannot join room {room}: client {client_id} not connected")
            return
        
        if room not in self.rooms:
            self.rooms[room] = set()
        
        self.rooms[room].add(client_id)
        self.connection_metadata[client_id]["subscribed_rooms"].add(room)
        
        logger.info(f"Client {client_id} joined room {room}")
    
    def leave_room(self, client_id: str, room: str):
        """Remove a client from a room."""
        if room in self.rooms:
            self.rooms[room].discard(client_id)
            
            # Clean up empty room
            if not self.rooms[room]:
                del self.rooms[room]
        
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["subscribed_rooms"].discard(room)
        
        logger.info(f"Client {client_id} left room {room}")
    
    def get_room_members(self, room: str) -> List[str]:
        """Get list of clients in a room."""
        return list(self.rooms.get(room, set()))
    
    def get_client_rooms(self, client_id: str) -> List[str]:
        """Get list of rooms a client is subscribed to."""
        if client_id in self.connection_metadata:
            return list(self.connection_metadata[client_id]["subscribed_rooms"])
        return []
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self, client_id: str) -> Optional[dict]:
        """Get connection information for a client."""
        return self.connection_metadata.get(client_id)
    
    def update_client_metadata(self, client_id: str, metadata: dict):
        """Update metadata for a client."""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id].update(metadata)
    
    async def ping_all_connections(self):
        """Send ping to all connections to check health."""
        disconnected_clients = []
        ping_message = json.dumps({
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(ping_message)
                self.connection_metadata[client_id]["last_ping"] = datetime.utcnow().isoformat()
            except (WebSocketDisconnect, Exception) as e:
                logger.warning(f"Ping failed for client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def disconnect_all(self):
        """Disconnect all clients."""
        disconnect_message = json.dumps({
            "type": "server_shutdown",
            "message": "Server is shutting down"
        })
        
        # Send shutdown notice
        for client_id in list(self.active_connections.keys()):
            try:
                await self.send_personal_message(disconnect_message, client_id)
            except:
                pass  # Ignore errors during shutdown
        
        # Clear all connections
        self.active_connections.clear()
        self.connection_metadata.clear()
        self.rooms.clear()
        
        logger.info("All WebSocket connections closed")
    
    def get_system_stats(self) -> dict:
        """Get system statistics for monitoring."""
        return {
            "total_connections": len(self.active_connections),
            "total_rooms": len(self.rooms),
            "room_distribution": {room: len(members) for room, members in self.rooms.items()},
            "connection_types": {}  # Could categorize by user type
        }