"""
Advanced Alerting System for SAR Drone Operations
Real-time alerting with escalation and notification management
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
from twilio.rest import Client

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable[[Dict[str, Any]], bool]
    cooldown_minutes: int = 5
    escalation_minutes: int = 15
    notification_channels: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    name: str
    type: str  # email, sms, slack, webhook
    config: Dict[str, Any]
    enabled: bool = True

class AlertManager:
    """Comprehensive alerting system"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.alert_history: List[Alert] = []
        self.metrics_cache: Dict[str, Any] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.escalation_timers: Dict[str, asyncio.Task] = {}
        self.running = False
        
        # Initialize default alert rules
        self._setup_default_rules()
        
        # Initialize notification channels
        self._setup_default_channels()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        
        # System resource alerts
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            description="High CPU usage detected",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: metrics.get('system', {}).get('cpu_percent', 0) > 80,
            cooldown_minutes=5,
            escalation_minutes=15,
            notification_channels=["email", "slack"],
            tags={"component": "system", "resource": "cpu"}
        ))
        
        self.add_rule(AlertRule(
            name="critical_cpu_usage",
            description="Critical CPU usage detected",
            severity=AlertSeverity.CRITICAL,
            condition=lambda metrics: metrics.get('system', {}).get('cpu_percent', 0) > 95,
            cooldown_minutes=2,
            escalation_minutes=5,
            notification_channels=["email", "sms", "slack"],
            tags={"component": "system", "resource": "cpu"}
        ))
        
        self.add_rule(AlertRule(
            name="high_memory_usage",
            description="High memory usage detected",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: metrics.get('system', {}).get('memory_percent', 0) > 85,
            cooldown_minutes=5,
            escalation_minutes=15,
            notification_channels=["email", "slack"],
            tags={"component": "system", "resource": "memory"}
        ))
        
        # Drone-specific alerts
        self.add_rule(AlertRule(
            name="drone_battery_low",
            description="Drone battery level is low",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: self._check_drone_battery(metrics, threshold=20),
            cooldown_minutes=10,
            escalation_minutes=30,
            notification_channels=["email", "slack"],
            tags={"component": "drone", "resource": "battery"}
        ))
        
        self.add_rule(AlertRule(
            name="drone_battery_critical",
            description="Drone battery level is critical",
            severity=AlertSeverity.CRITICAL,
            condition=lambda metrics: self._check_drone_battery(metrics, threshold=10),
            cooldown_minutes=2,
            escalation_minutes=5,
            notification_channels=["email", "sms", "slack"],
            tags={"component": "drone", "resource": "battery"}
        ))
        
        self.add_rule(AlertRule(
            name="drone_connection_lost",
            description="Drone connection lost",
            severity=AlertSeverity.CRITICAL,
            condition=lambda metrics: self._check_drone_connections(metrics),
            cooldown_minutes=1,
            escalation_minutes=3,
            notification_channels=["email", "sms", "slack"],
            tags={"component": "drone", "resource": "connection"}
        ))
        
        self.add_rule(AlertRule(
            name="drone_signal_weak",
            description="Drone signal strength is weak",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: self._check_drone_signal(metrics, threshold=30),
            cooldown_minutes=5,
            escalation_minutes=15,
            notification_channels=["email", "slack"],
            tags={"component": "drone", "resource": "signal"}
        ))
        
        # Mission-specific alerts
        self.add_rule(AlertRule(
            name="mission_coverage_low",
            description="Mission coverage is below threshold",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: self._check_mission_coverage(metrics, threshold=70),
            cooldown_minutes=15,
            escalation_minutes=30,
            notification_channels=["email", "slack"],
            tags={"component": "mission", "resource": "coverage"}
        ))
        
        # Emergency alerts
        self.add_rule(AlertRule(
            name="emergency_detected",
            description="Emergency situation detected",
            severity=AlertSeverity.EMERGENCY,
            condition=lambda metrics: metrics.get('emergency_events', 0) > 0,
            cooldown_minutes=0,
            escalation_minutes=1,
            notification_channels=["email", "sms", "slack", "webhook"],
            tags={"component": "emergency", "resource": "safety"}
        ))
        
        # API performance alerts
        self.add_rule(AlertRule(
            name="high_error_rate",
            description="High API error rate detected",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: self._check_error_rate(metrics, threshold=0.05),
            cooldown_minutes=5,
            escalation_minutes=15,
            notification_channels=["email", "slack"],
            tags={"component": "api", "resource": "performance"}
        ))
        
        self.add_rule(AlertRule(
            name="slow_response_time",
            description="API response time is slow",
            severity=AlertSeverity.WARNING,
            condition=lambda metrics: self._check_response_time(metrics, threshold=5.0),
            cooldown_minutes=5,
            escalation_minutes=15,
            notification_channels=["email", "slack"],
            tags={"component": "api", "resource": "performance"}
        ))
    
    def _setup_default_channels(self):
        """Setup default notification channels"""
        
        # Email channel
        self.add_channel(NotificationChannel(
            name="email",
            type="email",
            config={
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "alerts@sardrone.com",
                "password": "your_app_password",
                "to_addresses": ["ops@sardrone.com", "admin@sardrone.com"]
            }
        ))
        
        # Slack channel
        self.add_channel(NotificationChannel(
            name="slack",
            type="slack",
            config={
                "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                "channel": "#sar-alerts",
                "username": "SAR Alert Bot"
            }
        ))
        
        # SMS channel (Twilio)
        self.add_channel(NotificationChannel(
            name="sms",
            type="sms",
            config={
                "account_sid": "your_twilio_account_sid",
                "auth_token": "your_twilio_auth_token",
                "from_number": "+1234567890",
                "to_numbers": ["+1234567890", "+0987654321"]
            }
        ))
        
        # Webhook channel
        self.add_channel(NotificationChannel(
            name="webhook",
            type="webhook",
            config={
                "url": "https://your-webhook-endpoint.com/alerts",
                "headers": {"Authorization": "Bearer your_token"},
                "timeout": 30
            }
        ))
    
    def _check_drone_battery(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if any drone has battery below threshold"""
        drones = metrics.get('drones', {})
        for drone_id, drone_metrics in drones.items():
            if drone_metrics.get('battery_level', 100) < threshold:
                return True
        return False
    
    def _check_drone_connections(self, metrics: Dict[str, Any]) -> bool:
        """Check if any drone has lost connection"""
        drones = metrics.get('drones', {})
        for drone_id, drone_metrics in drones.items():
            last_heartbeat = drone_metrics.get('last_heartbeat')
            if last_heartbeat:
                try:
                    heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                    if datetime.utcnow() - heartbeat_time > timedelta(minutes=2):
                        return True
                except:
                    pass
        return False
    
    def _check_drone_signal(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if any drone has weak signal"""
        drones = metrics.get('drones', {})
        for drone_id, drone_metrics in drones.items():
            if drone_metrics.get('signal_strength', 100) < threshold:
                return True
        return False
    
    def _check_mission_coverage(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if mission coverage is below threshold"""
        # This would check actual mission coverage metrics
        return False  # Placeholder
    
    def _check_error_rate(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if API error rate is above threshold"""
        # This would check actual API error rates
        return False  # Placeholder
    
    def _check_response_time(self, metrics: Dict[str, Any], threshold: float) -> bool:
        """Check if API response time is above threshold"""
        # This would check actual response times
        return False  # Placeholder
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def add_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.notification_channels[channel.name] = channel
        logger.info(f"Added notification channel: {channel.name}")
    
    async def start_monitoring(self):
        """Start the alerting system"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting alert monitoring system")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Start escalation monitoring
        asyncio.create_task(self._escalation_monitor())
    
    async def stop_monitoring(self):
        """Stop the alerting system"""
        self.running = False
        
        # Cancel escalation timers
        for timer in self.escalation_timers.values():
            if not timer.done():
                timer.cancel()
        
        logger.info("Alert monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check all alert rules
                for rule_name, rule in self.rules.items():
                    if self._should_check_rule(rule_name):
                        if rule.condition(self.metrics_cache):
                            await self._trigger_alert(rule)
                        else:
                            await self._resolve_alert(rule_name)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    def _should_check_rule(self, rule_name: str) -> bool:
        """Check if rule should be evaluated (respecting cooldown)"""
        rule = self.rules[rule_name]
        last_alert = self.last_alert_times.get(rule_name)
        
        if last_alert is None:
            return True
        
        cooldown = timedelta(minutes=rule.cooldown_minutes)
        return datetime.utcnow() - last_alert > cooldown
    
    async def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert"""
        alert_id = f"{rule.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create alert
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            title=rule.description,
            description=f"Alert triggered: {rule.description}",
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow(),
            metadata={
                "rule_tags": rule.tags,
                "metrics_snapshot": self.metrics_cache
            }
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[rule.name] = datetime.utcnow()
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
        
        # Send notifications
        await self._send_notifications(alert, rule)
        
        # Setup escalation timer
        if rule.escalation_minutes > 0:
            self.escalation_timers[alert_id] = asyncio.create_task(
                self._schedule_escalation(alert, rule)
            )
    
    async def _resolve_alert(self, rule_name: str):
        """Resolve an alert if conditions are no longer met"""
        # Find active alerts for this rule
        active_alerts = [alert for alert in self.active_alerts.values() 
                        if alert.rule_name == rule_name and alert.status == AlertStatus.ACTIVE]
        
        for alert in active_alerts:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            logger.info(f"Alert resolved: {alert.rule_name}")
            
            # Cancel escalation timer
            if alert.id in self.escalation_timers:
                self.escalation_timers[alert.id].cancel()
                del self.escalation_timers[alert.id]
    
    async def _schedule_escalation(self, alert: Alert, rule: AlertRule):
        """Schedule alert escalation"""
        await asyncio.sleep(rule.escalation_minutes * 60)
        
        if alert.status == AlertStatus.ACTIVE:
            await self._escalate_alert(alert, rule)
    
    async def _escalate_alert(self, alert: Alert, rule: AlertRule):
        """Escalate an alert"""
        alert.metadata['escalated'] = True
        alert.metadata['escalated_at'] = datetime.utcnow().isoformat()
        
        logger.critical(f"Alert escalated: {alert.rule_name}")
        
        # Send escalation notifications
        escalation_channels = rule.notification_channels.copy()
        if 'sms' not in escalation_channels:
            escalation_channels.append('sms')
        
        await self._send_notifications(alert, rule, escalation_channels)
    
    async def _send_notifications(self, alert: Alert, rule: AlertRule, 
                                channels: Optional[List[str]] = None):
        """Send notifications through configured channels"""
        if channels is None:
            channels = rule.notification_channels
        
        for channel_name in channels:
            channel = self.notification_channels.get(channel_name)
            if not channel or not channel.enabled:
                continue
            
            try:
                await self._send_notification(alert, channel)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel_name}: {e}")
    
    async def _send_notification(self, alert: Alert, channel: NotificationChannel):
        """Send notification via specific channel"""
        if channel.type == "email":
            await self._send_email(alert, channel)
        elif channel.type == "slack":
            await self._send_slack(alert, channel)
        elif channel.type == "sms":
            await self._send_sms(alert, channel)
        elif channel.type == "webhook":
            await self._send_webhook(alert, channel)
    
    async def _send_email(self, alert: Alert, channel: NotificationChannel):
        """Send email notification"""
        config = channel.config
        
        msg = MimeMultipart()
        msg['From'] = config['username']
        msg['To'] = ', '.join(config['to_addresses'])
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
Alert Details:
- Title: {alert.title}
- Description: {alert.description}
- Severity: {alert.severity.value.upper()}
- Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Rule: {alert.rule_name}

Metadata:
{json.dumps(alert.metadata, indent=2)}

This is an automated alert from the SAR Drone System.
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
    
    async def _send_slack(self, alert: Alert, channel: NotificationChannel):
        """Send Slack notification"""
        config = channel.config
        
        # Determine color based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffaa00",
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.EMERGENCY: "#8B0000"
        }
        
        payload = {
            "channel": config['channel'],
            "username": config['username'],
            "attachments": [{
                "color": color_map[alert.severity],
                "title": alert.title,
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Time", "value": alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": True},
                    {"title": "Rule", "value": alert.rule_name, "short": True}
                ],
                "footer": "SAR Drone System",
                "ts": int(alert.created_at.timestamp())
            }]
        }
        
        response = requests.post(config['webhook_url'], json=payload, timeout=30)
        response.raise_for_status()
    
    async def _send_sms(self, alert: Alert, channel: NotificationChannel):
        """Send SMS notification"""
        config = channel.config
        
        client = Client(config['account_sid'], config['auth_token'])
        
        message = f"[{alert.severity.value.upper()}] {alert.title}\n{alert.description}\nTime: {alert.created_at.strftime('%H:%M:%S UTC')}"
        
        for to_number in config['to_numbers']:
            client.messages.create(
                body=message,
                from_=config['from_number'],
                to=to_number
            )
    
    async def _send_webhook(self, alert: Alert, channel: NotificationChannel):
        """Send webhook notification"""
        config = channel.config
        
        payload = {
            "alert": {
                "id": alert.id,
                "rule_name": alert.rule_name,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
        }
        
        headers = config.get('headers', {})
        response = requests.post(config['url'], json=payload, headers=headers, 
                               timeout=config.get('timeout', 30))
        response.raise_for_status()
    
    async def _escalation_monitor(self):
        """Monitor for escalation events"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check for alerts that need escalation
                for alert in self.active_alerts.values():
                    if alert.status == AlertStatus.ACTIVE:
                        rule = self.rules[alert.rule_name]
                        escalation_time = alert.created_at + timedelta(minutes=rule.escalation_minutes)
                        
                        if current_time >= escalation_time and not alert.metadata.get('escalated'):
                            await self._escalate_alert(alert, rule)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in escalation monitor: {e}")
                await asyncio.sleep(300)
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            # Cancel escalation timer
            if alert_id in self.escalation_timers:
                self.escalation_timers[alert_id].cancel()
                del self.escalation_timers[alert_id]
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update metrics cache for alert evaluation"""
        self.metrics_cache = metrics
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [alert for alert in self.active_alerts.values() 
                if alert.status == AlertStatus.ACTIVE]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get alerting system metrics"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = {}
        for alert in active_alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "active_alerts": len(active_alerts),
            "severity_breakdown": severity_counts,
            "total_rules": len(self.rules),
            "enabled_channels": len([c for c in self.notification_channels.values() if c.enabled]),
            "last_update": datetime.utcnow().isoformat()
        }

# Global alert manager instance
alert_manager = AlertManager()
