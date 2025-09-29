"""
Notification service for system alerts and user notifications.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationType(Enum):
    """Types of notifications."""
    MISSION_UPDATE = "mission_update"
    DRONE_ALERT = "drone_alert"
    DISCOVERY_ALERT = "discovery_alert"
    SYSTEM_ALERT = "system_alert"
    EMERGENCY = "emergency"


class Notification:
    """Represents a system notification."""

    def __init__(
        self,
        notification_type: NotificationType,
        level: NotificationLevel,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ):
        self.id = f"notif_{datetime.now().timestamp()}"
        self.type = notification_type
        self.level = level
        self.title = title
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        self.read = False

    def to_dict(self) -> Dict:
        """Convert notification to dictionary for API responses."""
        return {
            "id": self.id,
            "type": self.type.value,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read
        }


class NotificationService:
    """Manages system notifications and alerts."""

    def __init__(self):
        self.notifications: List[Notification] = []
        self.subscribers: Dict[str, List[callable]] = {}
        self.max_notifications = 1000  # Keep only the latest 1000 notifications

    def subscribe(self, notification_type: str, callback: callable):
        """Subscribe to a specific type of notification."""
        if notification_type not in self.subscribers:
            self.subscribers[notification_type] = []

        self.subscribers[notification_type].append(callback)
        logger.debug(f"Subscribed to notifications: {notification_type}")

    def unsubscribe(self, notification_type: str, callback: callable):
        """Unsubscribe from a specific type of notification."""
        if notification_type in self.subscribers:
            if callback in self.subscribers[notification_type]:
                self.subscribers[notification_type].remove(callback)
                logger.debug(f"Unsubscribed from notifications: {notification_type}")

    def create_notification(
        self,
        notification_type: NotificationType,
        level: NotificationLevel,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ) -> Notification:
        """Create and broadcast a new notification."""
        notification = Notification(notification_type, level, title, message, data)

        # Add to notifications list
        self.notifications.append(notification)

        # Trim old notifications if needed
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]

        # Broadcast to subscribers
        self._broadcast_notification(notification)

        logger.info(f"Created notification: {title} ({notification_type.value})")
        return notification

    def _broadcast_notification(self, notification: Notification):
        """Broadcast notification to all subscribers."""
        notification_type = notification.type.value

        if notification_type in self.subscribers:
            for callback in self.subscribers[notification_type]:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error(f"Error broadcasting notification to callback: {e}")

    def get_notifications(
        self,
        limit: int = 50,
        unread_only: bool = False,
        notification_type: Optional[str] = None
    ) -> List[Notification]:
        """Get recent notifications with optional filtering."""
        notifications = self.notifications

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        if notification_type:
            notifications = [n for n in notifications if n.type.value == notification_type]

        # Return most recent first
        notifications.sort(key=lambda x: x.timestamp, reverse=True)
        return notifications[:limit]

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                logger.debug(f"Marked notification as read: {notification_id}")
                return True
        return False

    def mark_all_as_read(self, notification_type: Optional[str] = None) -> int:
        """Mark all notifications as read, optionally filtered by type."""
        count = 0
        for notification in self.notifications:
            if notification_type is None or notification.type.value == notification_type:
                if not notification.read:
                    notification.read = True
                    count += 1

        if count > 0:
            logger.debug(f"Marked {count} notifications as read")
        return count

    def get_unread_count(self, notification_type: Optional[str] = None) -> int:
        """Get count of unread notifications."""
        unread = [n for n in self.notifications if not n.read]

        if notification_type:
            unread = [n for n in unread if n.type.value == notification_type]

        return len(unread)

    # Convenience methods for common notification types
    def mission_update(self, mission_name: str, update_message: str, mission_id: int):
        """Create a mission update notification."""
        return self.create_notification(
            NotificationType.MISSION_UPDATE,
            NotificationLevel.INFO,
            f"Mission Update: {mission_name}",
            update_message,
            {"mission_id": mission_id}
        )

    def drone_alert(self, drone_name: str, alert_message: str, drone_id: int, level: NotificationLevel = NotificationLevel.WARNING):
        """Create a drone alert notification."""
        return self.create_notification(
            NotificationType.DRONE_ALERT,
            level,
            f"Drone Alert: {drone_name}",
            alert_message,
            {"drone_id": drone_id}
        )

    def discovery_alert(self, discovery_type: str, location: str, priority: str, mission_id: int):
        """Create a discovery alert notification."""
        level = NotificationLevel.CRITICAL if priority == "critical" else NotificationLevel.WARNING
        return self.create_notification(
            NotificationType.DISCOVERY_ALERT,
            level,
            f"Discovery Alert: {discovery_type.title()}",
            f"Potential {discovery_type} discovered at {location}",
            {"mission_id": mission_id, "priority": priority}
        )

    def emergency_alert(self, title: str, message: str, data: Optional[Dict] = None):
        """Create an emergency alert notification."""
        return self.create_notification(
            NotificationType.EMERGENCY,
            NotificationLevel.CRITICAL,
            f"🚨 EMERGENCY: {title}",
            message,
            data
        )

    def system_alert(self, component: str, status: str, message: str):
        """Create a system status notification."""
        level = NotificationLevel.ERROR if "error" in status.lower() or "failed" in status.lower() else NotificationLevel.INFO
        return self.create_notification(
            NotificationType.SYSTEM_ALERT,
            level,
            f"System Alert: {component}",
            f"{component} status: {status} - {message}",
            {"component": component, "status": status}
        )


# Global instance
notification_service = NotificationService()