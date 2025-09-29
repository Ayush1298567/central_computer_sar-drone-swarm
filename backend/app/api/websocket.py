"""
WebSocket API endpoints for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[int, List[WebSocket]] = {}


async def connect(websocket: WebSocket, client_type: str, client_id: int):
    """Connect a WebSocket client."""
    await websocket.accept()

    if client_id not in active_connections:
        active_connections[client_id] = []

    active_connections[client_id].append(websocket)

    logger.info(f"{client_type.title()} WebSocket connected: {client_id}")

    try:
        # Send welcome message
        welcome_msg = {
            "type": "connection_established",
            "client_type": client_type,
            "client_id": client_id,
            "message": f"{client_type.title()} connected successfully"
        }
        await websocket.send_text(json.dumps(welcome_msg))

    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")


async def disconnect(websocket: WebSocket, client_type: str, client_id: int):
    """Disconnect a WebSocket client."""
    if client_id in active_connections:
        if websocket in active_connections[client_id]:
            active_connections[client_id].remove(websocket)

        if not active_connections[client_id]:
            del active_connections[client_id]

    logger.info(f"{client_type.title()} WebSocket disconnected: {client_id}")


async def broadcast_to_mission(mission_id: int, message: dict):
    """Broadcast a message to all clients connected to a specific mission."""
    if mission_id in active_connections:
        disconnected_clients = []

        message_json = json.dumps(message)

        for connection in active_connections[mission_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.append(connection)

        # Remove disconnected clients
        for client in disconnected_clients:
            if client in active_connections[mission_id]:
                active_connections[mission_id].remove(client)


@router.websocket("/mission/{mission_id}")
async def mission_websocket(websocket: WebSocket, mission_id: int):
    """WebSocket endpoint for mission-specific real-time updates."""
    await connect(websocket, "mission", mission_id)

    try:
        while True:
            # Receive messages from clients
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "chat_message":
                    # Broadcast chat message to all mission clients
                    broadcast_msg = {
                        "type": "chat_message",
                        "mission_id": mission_id,
                        "sender": message.get("sender", "unknown"),
                        "message": message.get("message", ""),
                        "timestamp": message.get("timestamp", "2024-01-01T00:00:00Z")
                    }
                    await broadcast_to_mission(mission_id, broadcast_msg)

                elif message.get("type") == "drone_update":
                    # Broadcast drone position/status updates
                    broadcast_msg = {
                        "type": "drone_update",
                        "mission_id": mission_id,
                        "drone_id": message.get("drone_id"),
                        "position": message.get("position", {}),
                        "status": message.get("status", "unknown"),
                        "timestamp": message.get("timestamp", "2024-01-01T00:00:00Z")
                    }
                    await broadcast_to_mission(mission_id, broadcast_msg)

                elif message.get("type") == "discovery_alert":
                    # Broadcast new discovery alerts
                    broadcast_msg = {
                        "type": "discovery_alert",
                        "mission_id": mission_id,
                        "discovery": message.get("discovery", {}),
                        "alert_level": message.get("alert_level", "normal"),
                        "timestamp": message.get("timestamp", "2024-01-01T00:00:00Z")
                    }
                    await broadcast_to_mission(mission_id, broadcast_msg)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                error_msg = {
                    "type": "error",
                    "message": "Invalid JSON format"
                }
                await websocket.send_text(json.dumps(error_msg))

    except WebSocketDisconnect:
        await disconnect(websocket, "mission", mission_id)
    except Exception as e:
        logger.error(f"Mission WebSocket error: {e}")
        await disconnect(websocket, "mission", mission_id)


@router.websocket("/drone/{drone_id}")
async def drone_websocket(websocket: WebSocket, drone_id: int):
    """WebSocket endpoint for drone-specific real-time updates."""
    await connect(websocket, "drone", drone_id)

    try:
        while True:
            # Receive control commands from clients
            data = await websocket.receive_text()
            try:
                command = json.loads(data)

                # Handle drone control commands
                if command.get("type") == "control_command":
                    # Process drone control command
                    control_msg = {
                        "type": "control_command",
                        "drone_id": drone_id,
                        "command": command.get("command", {}),
                        "timestamp": command.get("timestamp", "2024-01-01T00:00:00Z")
                    }

                    # Here you would send the command to the actual drone
                    # For now, just echo back confirmation
                    confirmation_msg = {
                        "type": "command_confirmation",
                        "drone_id": drone_id,
                        "command_id": command.get("command_id"),
                        "status": "sent",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_text(json.dumps(confirmation_msg))

                elif command.get("type") == "telemetry_request":
                    # Send current drone telemetry
                    telemetry_msg = {
                        "type": "telemetry_update",
                        "drone_id": drone_id,
                        "position": {"lat": 37.7749, "lng": -122.4194, "altitude": 50.0},  # Mock data
                        "attitude": {"heading": 0.0, "speed": 15.0},
                        "battery": {"level": 85.0},
                        "status": "flying",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_text(json.dumps(telemetry_msg))

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                error_msg = {
                    "type": "error",
                    "message": "Invalid JSON format"
                }
                await websocket.send_text(json.dumps(error_msg))

    except WebSocketDisconnect:
        await disconnect(websocket, "drone", drone_id)
    except Exception as e:
        logger.error(f"Drone WebSocket error: {e}")
        await disconnect(websocket, "drone", drone_id)


@router.websocket("/system")
async def system_websocket(websocket: WebSocket):
    """WebSocket endpoint for system-wide notifications and alerts."""
    client_id = "system"  # Use a fixed ID for system broadcasts
    await connect(websocket, "system", client_id)

    try:
        while True:
            # Keep connection alive and listen for system status requests
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                if message.get("type") == "status_request":
                    # Send current system status
                    status_msg = {
                        "type": "system_status",
                        "status": "operational",
                        "active_missions": 2,  # Mock data
                        "connected_drones": 5,
                        "total_discoveries": 12,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_text(json.dumps(status_msg))

                elif message.get("type") == "alert_subscribe":
                    # Subscribe to system alerts
                    alert_types = message.get("alert_types", ["mission", "drone", "discovery"])
                    # Here you would register the client for specific alert types
                    # For now, just send confirmation
                    subscribe_msg = {
                        "type": "subscription_confirmed",
                        "alert_types": alert_types,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    await websocket.send_text(json.dumps(subscribe_msg))

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                error_msg = {
                    "type": "error",
                    "message": "Invalid JSON format"
                }
                await websocket.send_text(json.dumps(error_msg))

    except WebSocketDisconnect:
        await disconnect(websocket, "system", client_id)
    except Exception as e:
        logger.error(f"System WebSocket error: {e}")
        await disconnect(websocket, "system", client_id)


# Utility functions for sending real-time updates from other parts of the system
async def send_mission_update(mission_id: int, update_type: str, data: dict):
    """Send a mission update to all connected clients."""
    message = {
        "type": update_type,
        "mission_id": mission_id,
        "data": data,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    await broadcast_to_mission(mission_id, message)


async def send_drone_alert(drone_id: int, alert_type: str, message: str):
    """Send a drone alert to connected clients."""
    alert_msg = {
        "type": "drone_alert",
        "drone_id": drone_id,
        "alert_type": alert_type,
        "message": message,
        "timestamp": "2024-01-01T00:00:00Z"
    }

    # Broadcast to all missions that might be using this drone
    # For now, broadcast to all active connections
    for client_id, connections in active_connections.items():
        for connection in connections:
            try:
                await connection.send_text(json.dumps(alert_msg))
            except Exception as e:
                logger.error(f"Error sending drone alert: {e}")


async def send_discovery_alert(mission_id: int, discovery_data: dict):
    """Send a discovery alert to connected clients."""
    alert_msg = {
        "type": "discovery_alert",
        "mission_id": mission_id,
        "discovery": discovery_data,
        "alert_level": discovery_data.get("priority", "normal"),
        "timestamp": "2024-01-01T00:00:00Z"
    }
    await broadcast_to_mission(mission_id, alert_msg)