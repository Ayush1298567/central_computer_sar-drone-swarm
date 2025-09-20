"""
Notification Service for SAR Drone Operations

This service provides comprehensive notification capabilities including:
- Priority-based notification routing
- Discovery alerts and mission updates
- Emergency notifications and system alerts
- WebSocket notification delivery
- Notification history and management
- Multi-channel delivery (WebSocket, Email, SMS, etc.)
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Union, Tuple
from enum import Enum
import uuid
import weakref

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


class NotificationType(Enum):
    """Types of notifications"""
    DISCOVERY = "discovery"
    MISSION_UPDATE = "mission_update"
    DRONE_STATUS = "drone_status"
    SYSTEM_ALERT = "system_alert"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"
    USER_ACTION = "user_action"
    WEATHER = "weather"
    COMMUNICATION = "communication"


class NotificationChannel(Enum):
    """Delivery channels for notifications"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    DESKTOP = "desktop"
    AUDIO = "audio"
    DISPLAY = "display"


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    user_id: str
    name: str
    channels: List[NotificationChannel]
    preferences: Dict[str, Any] = field(default_factory=dict)
    contact_info: Dict[str, str] = field(default_factory=dict)  # email, phone, etc.
    active_sessions: Set[str] = field(default_factory=set)  # WebSocket session IDs


@dataclass
class NotificationRule:
    """Notification routing rule"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]  # Conditions for rule activation
    recipients: List[str]  # User IDs
    channels: List[NotificationChannel]
    priority_override: Optional[NotificationPriority] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Notification:
    """Individual notification"""
    notification_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    
    # Delivery information
    recipients: List[str]  # User IDs
    channels: List[NotificationChannel]
    delivery_status: Dict[str, NotificationStatus] = field(default_factory=dict)
    
    # Content and metadata
    data: Dict[str, Any] = field(default_factory=dict)  # Additional data
    actions: List[Dict[str, Any]] = field(default_factory=list)  # Available actions
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Source information
    source_service: str = ""
    source_id: str = ""
    
    # Delivery tracking
    delivery_attempts: int = 0
    max_attempts: int = 3
    retry_after: Optional[datetime] = None


@dataclass
class NotificationTemplate:
    """Notification template for consistent messaging"""
    template_id: str
    name: str
    notification_type: NotificationType
    title_template: str
    message_template: str
    default_priority: NotificationPriority
    default_channels: List[NotificationChannel]
    required_data: List[str] = field(default_factory=list)
    optional_data: List[str] = field(default_factory=list)


class WebSocketManager:
    """WebSocket connection management for real-time notifications"""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}  # session_id -> websocket
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        
    async def add_connection(self, session_id: str, user_id: str, websocket: Any) -> None:
        """Add WebSocket connection"""
        self.connections[session_id] = websocket
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        logger.info(f"WebSocket connection added for user {user_id}, session {session_id}")
        
    async def remove_connection(self, session_id: str, user_id: str) -> None:
        """Remove WebSocket connection"""
        if session_id in self.connections:
            del self.connections[session_id]
            
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
                
        logger.info(f"WebSocket connection removed for user {user_id}, session {session_id}")
        
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to all user sessions"""
        if user_id not in self.user_sessions:
            return False
            
        success = False
        sessions_to_remove = []
        
        for session_id in self.user_sessions[user_id].copy():
            if session_id in self.connections:
                try:
                    websocket = self.connections[session_id]
                    await websocket.send(json.dumps(message))
                    success = True
                except Exception as e:
                    logger.warning(f"Failed to send to session {session_id}: {e}")
                    sessions_to_remove.append(session_id)
                    
        # Clean up failed connections
        for session_id in sessions_to_remove:
            await self.remove_connection(session_id, user_id)
            
        return success
        
    def get_user_sessions(self, user_id: str) -> Set[str]:
        """Get active sessions for user"""
        return self.user_sessions.get(user_id, set()).copy()


class NotificationService:
    """
    Comprehensive notification service for SAR drone operations.
    
    Provides priority-based routing, multi-channel delivery, and
    comprehensive notification management with WebSocket support.
    """
    
    def __init__(self):
        self.recipients: Dict[str, NotificationRecipient] = {}
        self.rules: Dict[str, NotificationRule] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        self.notifications: Dict[str, Notification] = {}
        self.notification_history: List[Notification] = []
        
        # WebSocket management
        self.websocket_manager = WebSocketManager()
        
        # Delivery tracking
        self.pending_notifications: List[str] = []
        self.failed_notifications: List[str] = []
        
        # Background tasks
        self._delivery_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Configuration
        self.max_history_size = 10000
        self.cleanup_interval_hours = 24
        self.retry_interval_minutes = 5
        
        # Initialize default templates
        self._initialize_default_templates()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())

    def _initialize_default_templates(self) -> None:
        """Initialize default notification templates"""
        
        templates = [
            NotificationTemplate(
                template_id="discovery_new_drone",
                name="New Drone Discovered",
                notification_type=NotificationType.DISCOVERY,
                title_template="New Drone Discovered: {drone_name}",
                message_template="Drone {drone_name} ({drone_id}) has been discovered and is available for missions.",
                default_priority=NotificationPriority.NORMAL,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.DESKTOP],
                required_data=["drone_id", "drone_name"]
            ),
            NotificationTemplate(
                template_id="mission_started",
                name="Mission Started",
                notification_type=NotificationType.MISSION_UPDATE,
                title_template="Mission Started: {mission_name}",
                message_template="Mission {mission_name} ({mission_id}) has started with {drone_count} drones.",
                default_priority=NotificationPriority.HIGH,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
                required_data=["mission_id", "mission_name", "drone_count"]
            ),
            NotificationTemplate(
                template_id="discovery_found",
                name="Object Discovered",
                notification_type=NotificationType.DISCOVERY,
                title_template="Object Discovered in Search Area",
                message_template="Potential object of interest discovered at coordinates {latitude}, {longitude} by drone {drone_id}.",
                default_priority=NotificationPriority.URGENT,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH, NotificationChannel.AUDIO],
                required_data=["latitude", "longitude", "drone_id"]
            ),
            NotificationTemplate(
                template_id="emergency_alert",
                name="Emergency Alert",
                notification_type=NotificationType.EMERGENCY,
                title_template="EMERGENCY: {alert_type}",
                message_template="Emergency condition detected: {description}. Immediate action required.",
                default_priority=NotificationPriority.EMERGENCY,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH, NotificationChannel.SMS, NotificationChannel.AUDIO],
                required_data=["alert_type", "description"]
            ),
            NotificationTemplate(
                template_id="drone_battery_low",
                name="Low Battery Alert",
                notification_type=NotificationType.DRONE_STATUS,
                title_template="Low Battery: {drone_name}",
                message_template="Drone {drone_name} battery level is {battery_level}%. Return to base recommended.",
                default_priority=NotificationPriority.HIGH,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
                required_data=["drone_id", "drone_name", "battery_level"]
            ),
            NotificationTemplate(
                template_id="mission_completed",
                name="Mission Completed",
                notification_type=NotificationType.MISSION_UPDATE,
                title_template="Mission Completed: {mission_name}",
                message_template="Mission {mission_name} completed successfully. Coverage: {coverage_percentage}%",
                default_priority=NotificationPriority.HIGH,
                default_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH],
                required_data=["mission_id", "mission_name", "coverage_percentage"]
            )
        ]
        
        for template in templates:
            self.templates[template.template_id] = template

    async def _start_background_tasks(self) -> None:
        """Start background processing tasks"""
        self._delivery_task = asyncio.create_task(self._delivery_worker())
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())

    async def register_recipient(self, recipient: NotificationRecipient) -> bool:
        """
        Register a notification recipient.
        
        Args:
            recipient: Recipient information
            
        Returns:
            True if registration successful
        """
        logger.info(f"Registering notification recipient: {recipient.user_id}")
        
        self.recipients[recipient.user_id] = recipient
        
        # Initialize default notification rules for the recipient
        await self._create_default_rules_for_recipient(recipient.user_id)
        
        return True

    async def _create_default_rules_for_recipient(self, user_id: str) -> None:
        """Create default notification rules for a new recipient"""
        
        default_rules = [
            NotificationRule(
                rule_id=f"emergency_all_{user_id}",
                name=f"Emergency Notifications - {user_id}",
                conditions={"priority": NotificationPriority.EMERGENCY.value},
                recipients=[user_id],
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH, NotificationChannel.SMS]
            ),
            NotificationRule(
                rule_id=f"discoveries_{user_id}",
                name=f"Discovery Notifications - {user_id}",
                conditions={"type": NotificationType.DISCOVERY.value},
                recipients=[user_id],
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.PUSH]
            ),
            NotificationRule(
                rule_id=f"mission_updates_{user_id}",
                name=f"Mission Updates - {user_id}",
                conditions={"type": NotificationType.MISSION_UPDATE.value},
                recipients=[user_id],
                channels=[NotificationChannel.WEBSOCKET]
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    async def create_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        recipients: Optional[List[str]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        expires_in_minutes: Optional[int] = None,
        source_service: str = "",
        source_id: str = ""
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            recipients: Specific recipients (if None, uses routing rules)
            channels: Delivery channels (if None, uses routing rules)
            data: Additional data
            actions: Available actions
            expires_in_minutes: Expiration time
            source_service: Source service name
            source_id: Source identifier
            
        Returns:
            Created notification
        """
        
        notification_id = str(uuid.uuid4())
        
        # Determine recipients and channels from rules if not specified
        if recipients is None or channels is None:
            rule_recipients, rule_channels = await self._apply_routing_rules(
                notification_type, priority, data or {}
            )
            recipients = recipients or rule_recipients
            channels = channels or rule_channels
            
        # Set expiration
        expires_at = None
        if expires_in_minutes:
            expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
        notification = Notification(
            notification_id=notification_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            recipients=recipients or [],
            channels=channels or [NotificationChannel.WEBSOCKET],
            data=data or {},
            actions=actions or [],
            expires_at=expires_at,
            source_service=source_service,
            source_id=source_id
        )
        
        # Store notification
        self.notifications[notification_id] = notification
        self.pending_notifications.append(notification_id)
        
        logger.info(f"Created notification {notification_id}: {title}")
        
        # Trigger immediate delivery for high priority notifications
        if priority.value >= NotificationPriority.URGENT.value:
            await self._deliver_notification(notification_id)
            
        return notification

    async def create_from_template(
        self,
        template_id: str,
        data: Dict[str, Any],
        recipients: Optional[List[str]] = None,
        priority_override: Optional[NotificationPriority] = None,
        channels_override: Optional[List[NotificationChannel]] = None
    ) -> Notification:
        """
        Create notification from template.
        
        Args:
            template_id: Template identifier
            data: Template data
            recipients: Override recipients
            priority_override: Override priority
            channels_override: Override channels
            
        Returns:
            Created notification
        """
        
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
            
        template = self.templates[template_id]
        
        # Validate required data
        missing_data = [field for field in template.required_data if field not in data]
        if missing_data:
            raise ValueError(f"Missing required data fields: {missing_data}")
            
        # Format title and message
        try:
            title = template.title_template.format(**data)
            message = template.message_template.format(**data)
        except KeyError as e:
            raise ValueError(f"Template formatting error: {e}")
            
        return await self.create_notification(
            title=title,
            message=message,
            notification_type=template.notification_type,
            priority=priority_override or template.default_priority,
            recipients=recipients,
            channels=channels_override or template.default_channels,
            data=data,
            source_service="template_service",
            source_id=template_id
        )

    async def _apply_routing_rules(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        data: Dict[str, Any]
    ) -> Tuple[List[str], List[NotificationChannel]]:
        """Apply routing rules to determine recipients and channels"""
        
        recipients = set()
        channels = set()
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            # Check if rule conditions match
            if await self._rule_matches(rule, notification_type, priority, data):
                recipients.update(rule.recipients)
                channels.update(rule.channels)
                
        return list(recipients), list(channels)

    async def _rule_matches(
        self,
        rule: NotificationRule,
        notification_type: NotificationType,
        priority: NotificationPriority,
        data: Dict[str, Any]
    ) -> bool:
        """Check if a rule matches the notification criteria"""
        
        conditions = rule.conditions
        
        # Check type condition
        if "type" in conditions:
            if conditions["type"] != notification_type.value:
                return False
                
        # Check priority condition
        if "priority" in conditions:
            if conditions["priority"] != priority.value:
                return False
                
        # Check minimum priority
        if "min_priority" in conditions:
            if priority.value < conditions["min_priority"]:
                return False
                
        # Check data conditions
        if "data_conditions" in conditions:
            for key, expected_value in conditions["data_conditions"].items():
                if key not in data or data[key] != expected_value:
                    return False
                    
        return True

    async def _delivery_worker(self) -> None:
        """Background worker for notification delivery"""
        
        while not self._shutdown_event.is_set():
            try:
                # Process pending notifications
                pending_copy = self.pending_notifications.copy()
                self.pending_notifications.clear()
                
                for notification_id in pending_copy:
                    if notification_id in self.notifications:
                        await self._deliver_notification(notification_id)
                        
                # Retry failed notifications
                await self._retry_failed_notifications()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in delivery worker: {e}")
                await asyncio.sleep(10)

    async def _deliver_notification(self, notification_id: str) -> None:
        """Deliver a single notification"""
        
        if notification_id not in self.notifications:
            return
            
        notification = self.notifications[notification_id]
        
        # Check if expired
        if notification.expires_at and datetime.now() > notification.expires_at:
            notification.delivery_status["expired"] = NotificationStatus.EXPIRED
            self._move_to_history(notification_id)
            return
            
        logger.info(f"Delivering notification {notification_id} to {len(notification.recipients)} recipients")
        
        # Deliver to each recipient through each channel
        for recipient_id in notification.recipients:
            if recipient_id not in self.recipients:
                continue
                
            recipient = self.recipients[recipient_id]
            
            for channel in notification.channels:
                # Check if recipient supports this channel
                if channel not in recipient.channels:
                    continue
                    
                delivery_key = f"{recipient_id}_{channel.value}"
                
                try:
                    success = await self._deliver_to_channel(
                        notification, recipient, channel
                    )
                    
                    if success:
                        notification.delivery_status[delivery_key] = NotificationStatus.DELIVERED
                        if not notification.delivered_at:
                            notification.delivered_at = datetime.now()
                    else:
                        notification.delivery_status[delivery_key] = NotificationStatus.FAILED
                        
                except Exception as e:
                    logger.error(f"Delivery error for {delivery_key}: {e}")
                    notification.delivery_status[delivery_key] = NotificationStatus.FAILED
                    
        # Update delivery attempts
        notification.delivery_attempts += 1
        
        # Check if all deliveries completed
        if self._all_deliveries_completed(notification):
            self._move_to_history(notification_id)
        elif notification.delivery_attempts >= notification.max_attempts:
            self.failed_notifications.append(notification_id)
            self._move_to_history(notification_id)
        else:
            # Schedule retry
            notification.retry_after = datetime.now() + timedelta(minutes=self.retry_interval_minutes)

    async def _deliver_to_channel(
        self,
        notification: Notification,
        recipient: NotificationRecipient,
        channel: NotificationChannel
    ) -> bool:
        """Deliver notification through specific channel"""
        
        if channel == NotificationChannel.WEBSOCKET:
            return await self._deliver_websocket(notification, recipient)
        elif channel == NotificationChannel.EMAIL:
            return await self._deliver_email(notification, recipient)
        elif channel == NotificationChannel.SMS:
            return await self._deliver_sms(notification, recipient)
        elif channel == NotificationChannel.PUSH:
            return await self._deliver_push(notification, recipient)
        elif channel == NotificationChannel.DESKTOP:
            return await self._deliver_desktop(notification, recipient)
        elif channel == NotificationChannel.AUDIO:
            return await self._deliver_audio(notification, recipient)
        else:
            logger.warning(f"Unsupported delivery channel: {channel}")
            return False

    async def _deliver_websocket(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver notification via WebSocket"""
        
        message = {
            "type": "notification",
            "notification": {
                "id": notification.notification_id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.notification_type.value,
                "priority": notification.priority.value,
                "data": notification.data,
                "actions": notification.actions,
                "created_at": notification.created_at.isoformat(),
                "expires_at": notification.expires_at.isoformat() if notification.expires_at else None
            }
        }
        
        return await self.websocket_manager.send_to_user(recipient.user_id, message)

    async def _deliver_email(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver notification via email"""
        
        # Email delivery would integrate with email service
        # For now, just log the delivery
        email = recipient.contact_info.get("email")
        if not email:
            return False
            
        logger.info(f"Email notification sent to {email}: {notification.title}")
        return True

    async def _deliver_sms(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver notification via SMS"""
        
        # SMS delivery would integrate with SMS service
        phone = recipient.contact_info.get("phone")
        if not phone:
            return False
            
        logger.info(f"SMS notification sent to {phone}: {notification.title}")
        return True

    async def _deliver_push(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver push notification"""
        
        # Push notification delivery would integrate with push service
        logger.info(f"Push notification sent to {recipient.user_id}: {notification.title}")
        return True

    async def _deliver_desktop(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver desktop notification"""
        
        # Desktop notification delivery
        logger.info(f"Desktop notification sent to {recipient.user_id}: {notification.title}")
        return True

    async def _deliver_audio(
        self,
        notification: Notification,
        recipient: NotificationRecipient
    ) -> bool:
        """Deliver audio notification"""
        
        # Audio notification delivery
        logger.info(f"Audio notification sent to {recipient.user_id}: {notification.title}")
        return True

    def _all_deliveries_completed(self, notification: Notification) -> bool:
        """Check if all deliveries for notification are completed"""
        
        expected_deliveries = len(notification.recipients) * len(notification.channels)
        completed_deliveries = len([
            status for status in notification.delivery_status.values()
            if status in [NotificationStatus.DELIVERED, NotificationStatus.FAILED]
        ])
        
        return completed_deliveries >= expected_deliveries

    async def _retry_failed_notifications(self) -> None:
        """Retry failed notifications"""
        
        now = datetime.now()
        retry_notifications = []
        
        for notification_id in list(self.notifications.keys()):
            notification = self.notifications[notification_id]
            
            if (notification.retry_after and 
                now >= notification.retry_after and
                notification.delivery_attempts < notification.max_attempts):
                retry_notifications.append(notification_id)
                
        for notification_id in retry_notifications:
            await self._deliver_notification(notification_id)

    def _move_to_history(self, notification_id: str) -> None:
        """Move notification to history"""
        
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            self.notification_history.append(notification)
            del self.notifications[notification_id]
            
            # Remove from failed list if present
            if notification_id in self.failed_notifications:
                self.failed_notifications.remove(notification_id)
                
            # Maintain history size
            if len(self.notification_history) > self.max_history_size:
                self.notification_history = self.notification_history[-self.max_history_size:]

    async def _cleanup_worker(self) -> None:
        """Background worker for cleanup tasks"""
        
        while not self._shutdown_event.is_set():
            try:
                await self._cleanup_expired_notifications()
                await asyncio.sleep(3600)  # Run every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_expired_notifications(self) -> None:
        """Clean up expired notifications"""
        
        now = datetime.now()
        expired_notifications = []
        
        for notification_id, notification in self.notifications.items():
            if notification.expires_at and now > notification.expires_at:
                expired_notifications.append(notification_id)
                
        for notification_id in expired_notifications:
            self._move_to_history(notification_id)
            
        if expired_notifications:
            logger.info(f"Cleaned up {len(expired_notifications)} expired notifications")

    async def acknowledge_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        Acknowledge a notification.
        
        Args:
            notification_id: Notification identifier
            user_id: User acknowledging the notification
            
        Returns:
            True if acknowledgment successful
        """
        
        # Check active notifications first
        notification = self.notifications.get(notification_id)
        
        # Check history if not in active
        if not notification:
            notification = next(
                (n for n in self.notification_history if n.notification_id == notification_id),
                None
            )
            
        if not notification:
            return False
            
        if user_id not in notification.recipients:
            return False
            
        notification.acknowledged_at = datetime.now()
        
        # Update delivery status
        for channel in notification.channels:
            delivery_key = f"{user_id}_{channel.value}"
            if delivery_key in notification.delivery_status:
                notification.delivery_status[delivery_key] = NotificationStatus.ACKNOWLEDGED
                
        logger.info(f"Notification {notification_id} acknowledged by user {user_id}")
        return True

    async def get_notifications_for_user(
        self,
        user_id: str,
        include_history: bool = False,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: User identifier
            include_history: Include historical notifications
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        
        notifications = []
        
        # Get active notifications
        for notification in self.notifications.values():
            if user_id in notification.recipients:
                notifications.append(notification)
                
        # Get historical notifications if requested
        if include_history:
            for notification in self.notification_history:
                if user_id in notification.recipients:
                    notifications.append(notification)
                    
        # Sort by creation time (newest first)
        notifications.sort(key=lambda n: n.created_at, reverse=True)
        
        # Apply limit
        if limit:
            notifications = notifications[:limit]
            
        return notifications

    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        
        total_notifications = len(self.notifications) + len(self.notification_history)
        pending_count = len(self.pending_notifications)
        failed_count = len(self.failed_notifications)
        
        # Priority distribution
        priority_counts = {}
        for notification in list(self.notifications.values()) + self.notification_history:
            priority = notification.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
        # Type distribution
        type_counts = {}
        for notification in list(self.notifications.values()) + self.notification_history:
            ntype = notification.notification_type.value
            type_counts[ntype] = type_counts.get(ntype, 0) + 1
            
        return {
            "total_notifications": total_notifications,
            "active_notifications": len(self.notifications),
            "pending_delivery": pending_count,
            "failed_delivery": failed_count,
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "registered_recipients": len(self.recipients),
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "websocket_connections": len(self.websocket_manager.connections),
            "last_updated": datetime.now().isoformat()
        }

    async def add_websocket_connection(
        self,
        session_id: str,
        user_id: str,
        websocket: Any
    ) -> None:
        """Add WebSocket connection for real-time notifications"""
        await self.websocket_manager.add_connection(session_id, user_id, websocket)

    async def remove_websocket_connection(
        self,
        session_id: str,
        user_id: str
    ) -> None:
        """Remove WebSocket connection"""
        await self.websocket_manager.remove_connection(session_id, user_id)

    async def shutdown(self) -> None:
        """Shutdown notification service"""
        
        logger.info("Shutting down notification service")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._delivery_task:
            self._delivery_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
        # Wait for tasks to complete
        tasks = [t for t in [self._delivery_task, self._cleanup_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        logger.info("Notification service shutdown complete")