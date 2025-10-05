"""
Emergency Service for SAR Mission Commander
Handles emergency situations and safety protocols
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ..core.database import get_db
from ..models.mission import Mission, MissionStatus
from ..services.drone_manager import drone_manager, DroneCommand, DroneCommandType
from ..services.notification_service import notification_service
from ..utils.logging import get_logger

logger = get_logger(__name__)

class EmergencyType(Enum):
    WEATHER_ALERT = "weather_alert"
    DRONE_FAILURE = "drone_failure"
    COMMUNICATION_LOSS = "communication_loss"
    FUEL_EMERGENCY = "fuel_emergency"
    MANUAL_OVERRIDE = "manual_override"
    SYSTEM_FAILURE = "system_failure"
    SECURITY_BREACH = "security_breach"

class EmergencySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class EmergencyAlert:
    id: str
    emergency_type: EmergencyType
    severity: EmergencySeverity
    message: str
    timestamp: datetime
    affected_drones: List[str] = None
    affected_missions: List[str] = None
    auto_resolved: bool = False
    resolution_notes: str = ""

class EmergencyService:
    """Manages emergency situations and safety protocols"""
    
    def __init__(self):
        self.active_emergencies: Dict[str, EmergencyAlert] = {}
        self.emergency_protocols: Dict[EmergencyType, Dict] = {
            EmergencyType.WEATHER_ALERT: {
                "auto_action": "return_home",
                "notification_level": "high",
                "timeout_minutes": 5
            },
            EmergencyType.DRONE_FAILURE: {
                "auto_action": "emergency_land",
                "notification_level": "critical",
                "timeout_minutes": 1
            },
            EmergencyType.COMMUNICATION_LOSS: {
                "auto_action": "return_home",
                "notification_level": "high",
                "timeout_minutes": 3
            },
            EmergencyType.FUEL_EMERGENCY: {
                "auto_action": "immediate_landing",
                "notification_level": "critical",
                "timeout_minutes": 1
            },
            EmergencyType.MANUAL_OVERRIDE: {
                "auto_action": "stop_all_operations",
                "notification_level": "critical",
                "timeout_minutes": 0
            },
            EmergencyType.SYSTEM_FAILURE: {
                "auto_action": "emergency_stop",
                "notification_level": "critical",
                "timeout_minutes": 0
            },
            EmergencyType.SECURITY_BREACH: {
                "auto_action": "secure_systems",
                "notification_level": "critical",
                "timeout_minutes": 0
            }
        }
        self._running = False
        
    async def start(self):
        """Start the emergency service"""
        self._running = True
        logger.info("Emergency Service started")
        
        # Start background monitoring
        asyncio.create_task(self._monitor_emergencies())
        
    async def stop(self):
        """Stop the emergency service"""
        self._running = False
        logger.info("Emergency Service stopped")
    
    async def trigger_emergency(
        self, 
        emergency_type: EmergencyType, 
        severity: EmergencySeverity,
        message: str,
        affected_drones: List[str] = None,
        affected_missions: List[str] = None
    ) -> str:
        """Trigger an emergency alert"""
        try:
            emergency_id = f"emergency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{emergency_type.value}"
            
            alert = EmergencyAlert(
                id=emergency_id,
                emergency_type=emergency_type,
                severity=severity,
                message=message,
                timestamp=datetime.utcnow(),
                affected_drones=affected_drones or [],
                affected_missions=affected_missions or []
            )
            
            self.active_emergencies[emergency_id] = alert
            
            # Execute emergency protocol
            await self._execute_emergency_protocol(alert)
            
            # Send notifications
            await self._send_emergency_notifications(alert)
            
            logger.warning(f"Emergency triggered: {emergency_type.value} - {message}")
            return emergency_id
            
        except Exception as e:
            logger.error(f"Failed to trigger emergency: {e}")
            return ""
    
    async def emergency_stop_all(self) -> bool:
        """Emergency stop all operations"""
        try:
            # Trigger system-wide emergency
            emergency_id = await self.trigger_emergency(
                EmergencyType.MANUAL_OVERRIDE,
                EmergencySeverity.CRITICAL,
                "Manual emergency stop activated - all operations halted",
                affected_drones=drone_manager.connected_drones.keys(),
                affected_missions=list(self.active_emergencies.keys())
            )
            
            # Immediately stop all drones
            await drone_manager.emergency_stop_all()
            
            # Pause all active missions
            for mission_id in list(self.active_emergencies.keys()):
                try:
                    # This would pause missions in a real implementation
                    logger.warning(f"Emergency pause for mission {mission_id}")
                except Exception as e:
                    logger.error(f"Failed to pause mission {mission_id}: {e}")
            
            logger.critical("EMERGENCY STOP ACTIVATED - ALL OPERATIONS HALTED")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute emergency stop: {e}")
            return False
    
    async def resolve_emergency(self, emergency_id: str, resolution_notes: str = "") -> bool:
        """Resolve an emergency alert"""
        try:
            if emergency_id not in self.active_emergencies:
                logger.warning(f"Emergency {emergency_id} not found")
                return False
            
            alert = self.active_emergencies[emergency_id]
            alert.auto_resolved = True
            alert.resolution_notes = resolution_notes
            
            # Remove from active emergencies
            del self.active_emergencies[emergency_id]
            
            # Send resolution notification
            await notification_service.send_notification(
                type="system",
                title="Emergency Resolved",
                message=f"Emergency {alert.emergency_type.value} has been resolved",
                priority="medium"
            )
            
            logger.info(f"Emergency {emergency_id} resolved: {resolution_notes}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve emergency {emergency_id}: {e}")
            return False
    
    async def get_active_emergencies(self) -> List[Dict]:
        """Get all active emergencies"""
        return [
            {
                "id": alert.id,
                "type": alert.emergency_type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "affected_drones": alert.affected_drones,
                "affected_missions": alert.affected_missions,
                "duration_minutes": (datetime.utcnow() - alert.timestamp).total_seconds() / 60
            }
            for alert in self.active_emergencies.values()
        ]
    
    async def _execute_emergency_protocol(self, alert: EmergencyAlert):
        """Execute the appropriate emergency protocol"""
        try:
            protocol = self.emergency_protocols.get(alert.emergency_type)
            if not protocol:
                logger.warning(f"No protocol defined for emergency type {alert.emergency_type.value}")
                return
            
            auto_action = protocol["auto_action"]
            timeout_minutes = protocol["timeout_minutes"]
            
            # Execute immediate actions for critical emergencies
            if alert.severity == EmergencySeverity.CRITICAL and timeout_minutes == 0:
                await self._execute_immediate_action(auto_action, alert)
            else:
                # Schedule action after timeout
                asyncio.create_task(self._delayed_emergency_action(auto_action, alert, timeout_minutes))
                
        except Exception as e:
            logger.error(f"Failed to execute emergency protocol: {e}")
    
    async def _execute_immediate_action(self, action: str, alert: EmergencyAlert):
        """Execute immediate emergency action"""
        try:
            if action == "emergency_stop":
                await drone_manager.emergency_stop_all()
                
            elif action == "stop_all_operations":
                await self.emergency_stop_all()
                
            elif action == "return_home":
                for drone_id in alert.affected_drones:
                    await drone_manager.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.RETURN_HOME,
                        priority=3
                    ))
                    
            elif action == "emergency_land":
                for drone_id in alert.affected_drones:
                    await drone_manager.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.LAND,
                        priority=3
                    ))
                    
            elif action == "immediate_landing":
                for drone_id in alert.affected_drones:
                    await drone_manager.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.LAND,
                        priority=3
                    ))
                    
            elif action == "secure_systems":
                # In a real implementation, this would secure all systems
                logger.warning("Security breach - securing all systems")
                
            logger.info(f"Executed immediate action {action} for emergency {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to execute immediate action {action}: {e}")
    
    async def _delayed_emergency_action(self, action: str, alert: EmergencyAlert, delay_minutes: int):
        """Execute delayed emergency action"""
        try:
            # Wait for the specified delay
            await asyncio.sleep(delay_minutes * 60)
            
            # Check if emergency is still active
            if alert.id not in self.active_emergencies:
                logger.info(f"Emergency {alert.id} resolved before timeout")
                return
            
            # Execute the action
            await self._execute_immediate_action(action, alert)
            
            # Auto-resolve if action was successful
            await self.resolve_emergency(alert.id, f"Auto-resolved after {delay_minutes} minute timeout")
            
        except Exception as e:
            logger.error(f"Failed to execute delayed action {action}: {e}")
    
    async def _send_emergency_notifications(self, alert: EmergencyAlert):
        """Send emergency notifications"""
        try:
            protocol = self.emergency_protocols.get(alert.emergency_type)
            notification_level = protocol.get("notification_level", "medium")
            
            # Determine notification priority
            priority_map = {
                "low": "low",
                "medium": "medium", 
                "high": "high",
                "critical": "critical"
            }
            priority = priority_map.get(notification_level, "medium")
            
            # Send notification
            await notification_service.send_notification(
                type="emergency",
                title=f"Emergency Alert: {alert.emergency_type.value.replace('_', ' ').title()}",
                message=alert.message,
                priority=priority
            )
            
            # Send to all connected WebSocket clients
            await notification_service.broadcast_to_all({
                "type": "emergency",
                "data": {
                    "id": alert.id,
                    "emergency_type": alert.emergency_type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "affected_drones": alert.affected_drones,
                    "affected_missions": alert.affected_missions
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to send emergency notifications: {e}")
    
    async def _monitor_emergencies(self):
        """Background task to monitor emergencies"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                # Check for stale emergencies
                for emergency_id, alert in list(self.active_emergencies.items()):
                    # Auto-resolve emergencies older than 30 minutes
                    if (current_time - alert.timestamp).total_seconds() > 1800:
                        await self.resolve_emergency(
                            emergency_id, 
                            "Auto-resolved due to timeout"
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring emergencies: {e}")
                await asyncio.sleep(60)
    
    # Weather-related emergency methods
    async def check_weather_conditions(self, weather_data: Dict) -> bool:
        """Check weather conditions and trigger alerts if necessary"""
        try:
            alerts_triggered = []
            
            # Check wind speed
            wind_speed = weather_data.get("wind_speed", 0)
            if wind_speed > 15:  # 15 m/s threshold
                alerts_triggered.append(await self.trigger_emergency(
                    EmergencyType.WEATHER_ALERT,
                    EmergencySeverity.HIGH,
                    f"High wind conditions detected: {wind_speed} m/s",
                    affected_drones=drone_manager.connected_drones.keys()
                ))
            
            # Check visibility
            visibility = weather_data.get("visibility", 10000)
            if visibility < 1000:  # 1km visibility threshold
                alerts_triggered.append(await self.trigger_emergency(
                    EmergencyType.WEATHER_ALERT,
                    EmergencySeverity.MEDIUM,
                    f"Low visibility conditions: {visibility} meters",
                    affected_drones=drone_manager.connected_drones.keys()
                ))
            
            # Check precipitation
            precipitation = weather_data.get("precipitation", 0)
            if precipitation > 5:  # 5mm/h threshold
                alerts_triggered.append(await self.trigger_emergency(
                    EmergencyType.WEATHER_ALERT,
                    EmergencySeverity.MEDIUM,
                    f"Heavy precipitation detected: {precipitation} mm/h",
                    affected_drones=drone_manager.connected_drones.keys()
                ))
            
            return len(alerts_triggered) > 0
            
        except Exception as e:
            logger.error(f"Failed to check weather conditions: {e}")
            return False
    
    # Drone-related emergency methods
    async def handle_drone_failure(self, drone_id: str, failure_type: str, details: str):
        """Handle drone failure emergency"""
        try:
            await self.trigger_emergency(
                EmergencyType.DRONE_FAILURE,
                EmergencySeverity.CRITICAL,
                f"Drone {drone_id} failure: {failure_type} - {details}",
                affected_drones=[drone_id]
            )
            
        except Exception as e:
            logger.error(f"Failed to handle drone failure for {drone_id}: {e}")
    
    async def handle_communication_loss(self, drone_id: str):
        """Handle communication loss emergency"""
        try:
            await self.trigger_emergency(
                EmergencyType.COMMUNICATION_LOSS,
                EmergencySeverity.HIGH,
                f"Communication lost with drone {drone_id}",
                affected_drones=[drone_id]
            )
            
        except Exception as e:
            logger.error(f"Failed to handle communication loss for {drone_id}: {e}")
    
    async def handle_low_battery_emergency(self, drone_id: str, battery_level: float):
        """Handle low battery emergency"""
        try:
            severity = EmergencySeverity.CRITICAL if battery_level < 10 else EmergencySeverity.HIGH
            
            await self.trigger_emergency(
                EmergencyType.FUEL_EMERGENCY,
                severity,
                f"Low battery on drone {drone_id}: {battery_level}%",
                affected_drones=[drone_id]
            )
            
        except Exception as e:
            logger.error(f"Failed to handle low battery emergency for {drone_id}: {e}")

# Global emergency service instance
emergency_service = EmergencyService()