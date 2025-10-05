"""
Notification service for SAR Mission Commander
"""
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from ..api.websocket import connection_manager

class NotificationService:
    """Service for managing real-time notifications"""

    def __init__(self):
        self.notification_history = []

    async def send_notification(self, notification_type: str, title: str, message: str, priority: str = "medium", user_id: str = "all"):
        """Send notification via WebSocket"""
        notification_data = {
            "id": f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "type": notification_type,
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "read": False
        }
        
        notification = {
            "type": "notification",
            "user_id": user_id,
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store in history (keep last 100)
        self.notification_history.append(notification)
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]

        # Broadcast to user
        await connection_manager.broadcast_notification(notification)

    async def send_mission_update(self, mission_id: str, update_data: Dict[str, Any]):
        """Send mission update notification"""
        notification_data = {
            "type": "mission_update",
            "mission_id": mission_id,
            "update": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_notification("all", notification_data)

    async def send_discovery_notification(self, discovery_data: Dict[str, Any]):
        """Send discovery notification"""
        notification_data = {
            "type": "discovery",
            "discovery": discovery_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_notification("all", notification_data)

    async def send_drone_status_update(self, drone_id: str, status_data: Dict[str, Any]):
        """Send drone status update notification"""
        notification_data = {
            "type": "drone_status",
            "drone_id": drone_id,
            "status": status_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_notification("all", notification_data)

    async def send_chat_message_notification(self, mission_id: str, message_data: Dict[str, Any]):
        """Send chat message notification"""
        notification_data = {
            "type": "chat_message",
            "mission_id": mission_id,
            "message": message_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_notification("all", notification_data)

    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Send system alert notification"""
        notification_data = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_notification("system_alert", "System Alert", message, severity)

    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notification history"""
        return self.notification_history[-limit:]

    async def broadcast_user_count(self):
        """Broadcast current user count"""
        active_connections = connection_manager.get_connection_count()

        notification_data = {
            "type": "user_count",
            "count": active_connections,
            "timestamp": datetime.utcnow().isoformat()
        }

        await connection_manager.broadcast_notification({
            "type": "user_count",
            "data": notification_data
        })

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        await connection_manager.broadcast_notification(message)

# Global notification service instance
notification_service = NotificationService()