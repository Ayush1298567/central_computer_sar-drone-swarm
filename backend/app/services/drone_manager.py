import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

class DroneManager:
    """Drone connection and management service."""

    def __init__(self):
        self.connected_drones = {}
        self.drone_status = {}

    async def connect_drone(self, drone_id: str) -> dict:
        """Connect to a drone."""
        return {
            "drone_id": drone_id,
            "status": "connected",
            "connection_type": "websocket"
        }

drone_manager = DroneManager()