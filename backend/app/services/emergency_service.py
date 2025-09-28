"""
Emergency Response and Safety System for SAR Operations.

Manages emergency protocols, safety validation, geofencing, and crisis communication.
Provides immediate response capabilities and comprehensive safety validation.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)

class EmergencyType(Enum):
    """Types of emergencies that can occur."""
    COMMUNICATION_LOSS = "communication_loss"
    BATTERY_CRITICAL = "battery_critical"
    SIGNAL_LOST = "signal_lost"
    WEATHER_HAZARD = "weather_hazard"
    EQUIPMENT_FAILURE = "equipment_failure"
    DRONE_CRASH = "drone_crash"
    GEOFENCE_BREACH = "geofence_breach"
    EMERGENCY_LANDING = "emergency_landing"
    PERSON_DETECTED = "person_detected"
    STRUCTURAL_HAZARD = "structural_hazard"
    MEDICAL_EMERGENCY = "medical_emergency"
    SECURITY_BREACH = "security_breach"

class EmergencySeverity(Enum):
    """Severity levels for emergencies."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    CATASTROPHIC = 5

class SafetyStatus(Enum):
    """Safety validation status."""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"

@dataclass
class EmergencyProtocol:
    """Defines an emergency response protocol."""
    protocol_id: str
    name: str
    emergency_type: EmergencyType
    severity: EmergencySeverity
    description: str
    immediate_actions: List[str]
    notification_targets: List[str]
    escalation_procedures: List[str]
    recovery_steps: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert protocol to dictionary."""
        return {
            "protocol_id": self.protocol_id,
            "name": self.name,
            "emergency_type": self.emergency_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "immediate_actions": self.immediate_actions,
            "notification_targets": self.notification_targets,
            "escalation_procedures": self.escalation_procedures,
            "recovery_steps": self.recovery_steps,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }

@dataclass
class GeofenceZone:
    """Defines a geofence zone for safety."""
    zone_id: str
    name: str
    zone_type: str  # "no_fly", "restricted", "warning"
    coordinates: List[Tuple[float, float]]  # Polygon coordinates
    altitude_min: Optional[float] = None
    altitude_max: Optional[float] = None
    restrictions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def contains_point(self, lat: float, lng: float, alt: Optional[float] = None) -> bool:
        """Check if a point is within the geofence zone."""
        # Simple bounding box check for now
        # In production, use proper polygon containment
        if not self.coordinates:
            return False

        min_lat = min(coord[0] for coord in self.coordinates)
        max_lat = max(coord[0] for coord in self.coordinates)
        min_lng = min(coord[1] for coord in self.coordinates)
        max_lng = max(coord[1] for coord in self.coordinates)

        if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
            return False

        # Altitude check
        if alt is not None:
            if self.altitude_min is not None and alt < self.altitude_min:
                return False
            if self.altitude_max is not None and alt > self.altitude_max:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert zone to dictionary."""
        return {
            "zone_id": self.zone_id,
            "name": self.name,
            "zone_type": self.zone_type,
            "coordinates": self.coordinates,
            "altitude_min": self.altitude_min,
            "altitude_max": self.altitude_max,
            "restrictions": self.restrictions,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class EmergencyEvent:
    """Represents an emergency event."""
    event_id: str
    emergency_type: EmergencyType
    severity: EmergencySeverity
    description: str
    affected_drones: List[str]
    location: Optional[Dict[str, float]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # active, resolved, escalated
    protocols_applied: List[str] = field(default_factory=list)
    notifications_sent: List[str] = field(default_factory=list)
    resolution_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "emergency_type": self.emergency_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "affected_drones": self.affected_drones,
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "protocols_applied": self.protocols_applied,
            "notifications_sent": self.notifications_sent,
            "resolution_notes": self.resolution_notes
        }

class SafetyValidator:
    """Validates safety of drone operations and mission plans."""

    def __init__(self):
        self.validation_rules = []

    def validate_mission_safety(self, mission_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of a mission plan.

        Args:
            mission_plan: Mission plan to validate

        Returns:
            Safety validation results
        """
        issues = []
        warnings = []

        # Check weather conditions
        weather = mission_plan.get("weather_conditions", {})
        wind_speed = weather.get("wind_speed", 0)
        visibility = weather.get("visibility", 10)

        if wind_speed > 15:  # m/s
            issues.append(f"High wind speed ({wind_speed} m/s) exceeds safe operating limits")
        elif wind_speed > 10:
            warnings.append(f"Moderate wind speed ({wind_speed} m/s) - monitor conditions")

        if visibility < 1:  # km
            issues.append(f"Low visibility ({visibility} km) - unsafe for drone operations")

        # Check search area safety
        search_area = mission_plan.get("search_area", {})
        if self._is_area_too_large(search_area):
            warnings.append("Large search area may exceed drone capabilities")

        if self._has_hazardous_terrain(search_area):
            warnings.append("Search area contains potentially hazardous terrain")

        # Check drone assignments
        drone_assignments = mission_plan.get("drone_assignments", [])
        for assignment in drone_assignments:
            drone_safety = self._validate_drone_assignment(assignment)
            issues.extend(drone_safety.get("issues", []))
            warnings.extend(drone_safety.get("warnings", []))

        # Determine overall safety status
        if issues:
            overall_status = SafetyStatus.DANGEROUS if len(issues) > 2 else SafetyStatus.WARNING
        elif warnings:
            overall_status = SafetyStatus.WARNING
        else:
            overall_status = SafetyStatus.SAFE

        return {
            "overall_status": overall_status.value,
            "issues": issues,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    def validate_drone_operation(self, drone_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of individual drone operation.

        Args:
            drone_state: Current drone state

        Returns:
            Safety validation results
        """
        issues = []
        warnings = []

        # Check battery level
        battery_level = drone_state.get("battery_level", 100)
        if battery_level < 15:
            issues.append(f"Critical battery level ({battery_level}%) - immediate return required")
        elif battery_level < 25:
            warnings.append(f"Low battery level ({battery_level}%) - consider return to base")

        # Check signal strength
        signal_strength = drone_state.get("signal_strength", 100)
        if signal_strength < 20:
            issues.append(f"Critical signal loss ({signal_strength}%) - emergency protocols required")
        elif signal_strength < 40:
            warnings.append(f"Weak signal ({signal_strength}%) - monitor connection")

        # Check altitude safety
        altitude = drone_state.get("altitude", 0)
        if altitude > 120:  # meters
            warnings.append(f"High altitude ({altitude}m) - monitor for safety")
        elif altitude < 5 and drone_state.get("status") == "flying":
            warnings.append("Very low altitude - potential ground hazard")

        # Check speed safety
        ground_speed = drone_state.get("ground_speed", 0)
        if ground_speed > 20:  # m/s
            warnings.append(f"High speed ({ground_speed} m/s) - ensure safe operation")

        # Determine safety status
        if issues:
            overall_status = SafetyStatus.DANGEROUS if len(issues) > 1 else SafetyStatus.WARNING
        elif warnings:
            overall_status = SafetyStatus.WARNING
        else:
            overall_status = SafetyStatus.SAFE

        return {
            "overall_status": overall_status.value,
            "issues": issues,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    def _is_area_too_large(self, search_area: Dict[str, Any]) -> bool:
        """Check if search area is too large for safe operation."""
        coordinates = search_area.get("coordinates", [])
        if len(coordinates) < 3:
            return False

        # Simple area calculation (rough estimate)
        area = 0
        for i in range(len(coordinates)):
            j = (i + 1) % len(coordinates)
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]

        area = abs(area) / 2

        # Rough conversion to km²
        area_km2 = area * 111 * 111 / 1000000  # Very rough estimate

        return area_km2 > 50  # More than 50 km²

    def _has_hazardous_terrain(self, search_area: Dict[str, Any]) -> bool:
        """Check if search area contains hazardous terrain."""
        # This would use terrain data in production
        # For now, simple heuristic based on area characteristics
        return False  # Placeholder

    def _validate_drone_assignment(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Validate safety of drone assignment."""
        issues = []
        warnings = []

        drone_id = assignment.get("drone_id")
        assigned_area = assignment.get("assigned_area", {})

        if not drone_id:
            issues.append("No drone assigned to area")

        if not assigned_area:
            issues.append("No search area assigned")

        # Check area size vs drone capability
        area_size = self._calculate_area_size(assigned_area.get("coordinates", []))
        if area_size > 5:  # km²
            warnings.append(f"Large area ({area_size:.1f} km²) assigned to single drone")

        return {"issues": issues, "warnings": warnings}

    def _calculate_area_size(self, coordinates: List[List[float]]) -> float:
        """Calculate approximate area size in km²."""
        if len(coordinates) < 3:
            return 0.0

        area = 0.0
        j = len(coordinates) - 1

        for i in range(len(coordinates)):
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
            j = i

        area = abs(area) / 2.0
        return area * 111 * 111 / 1000000  # Rough km² conversion

class CrisisCommunicationManager:
    """Manages crisis communication protocols and notifications."""

    def __init__(self):
        self.notification_handlers: Dict[str, Callable] = {}
        self.communication_log: List[Dict[str, Any]] = []

    def register_notification_handler(self, handler_name: str, handler: Callable):
        """Register a notification handler."""
        self.notification_handlers[handler_name] = handler

    async def send_emergency_notification(
        self,
        emergency_type: EmergencyType,
        message: str,
        recipients: List[str],
        priority: str = "high",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Send emergency notification to specified recipients."""
        notification = {
            "timestamp": datetime.utcnow().isoformat(),
            "emergency_type": emergency_type.value,
            "message": message,
            "recipients": recipients,
            "priority": priority,
            "metadata": metadata or {},
            "notification_id": f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }

        # Log the notification
        self.communication_log.append(notification)

        # Send to all registered handlers
        for handler_name, handler in self.notification_handlers.items():
            try:
                await handler(notification)
                logger.info(f"Emergency notification sent via {handler_name}")
            except Exception as e:
                logger.error(f"Failed to send notification via {handler_name}: {e}")

    async def broadcast_emergency_alert(
        self,
        emergency_event: EmergencyEvent,
        message: str
    ):
        """Broadcast emergency alert to all relevant parties."""
        # Determine recipients based on emergency type and severity
        recipients = self._determine_recipients(emergency_event)

        await self.send_emergency_notification(
            emergency_type=emergency_event.emergency_type,
            message=message,
            recipients=recipients,
            priority="critical",
            metadata={
                "emergency_event_id": emergency_event.event_id,
                "severity": emergency_event.severity.value,
                "affected_drones": emergency_event.affected_drones,
                "location": emergency_event.location
            }
        )

    def _determine_recipients(self, emergency_event: EmergencyEvent) -> List[str]:
        """Determine notification recipients based on emergency."""
        recipients = ["mission_control", "safety_officer"]

        if emergency_event.severity in [EmergencySeverity.HIGH, EmergencySeverity.CRITICAL]:
            recipients.extend(["emergency_services", "command_center"])

        if emergency_event.emergency_type == EmergencyType.MEDICAL_EMERGENCY:
            recipients.append("medical_team")

        if emergency_event.emergency_type == EmergencyType.SECURITY_BREACH:
            recipients.append("security_team")

        return recipients

class EmergencyResponseManager:
    """
    Manages emergency response protocols and safety systems.

    Provides immediate response capabilities, safety validation,
    geofencing, and crisis communication protocols.
    """

    def __init__(self):
        self.emergency_protocols: Dict[str, EmergencyProtocol] = {}
        self.geofence_zones: Dict[str, GeofenceZone] = {}
        self.active_emergencies: Dict[str, EmergencyEvent] = {}
        self.safety_validator = SafetyValidator()
        self.communication_manager = CrisisCommunicationManager()
        self.emergency_history: List[EmergencyEvent] = []

        # Initialize default protocols
        self._initialize_default_protocols()

        # Register communication handlers
        self._register_communication_handlers()

    def _initialize_default_protocols(self):
        """Initialize default emergency response protocols."""
        protocols = [
            EmergencyProtocol(
                protocol_id="battery_critical",
                name="Critical Battery Protocol",
                emergency_type=EmergencyType.BATTERY_CRITICAL,
                severity=EmergencySeverity.HIGH,
                description="Drone battery level critically low",
                immediate_actions=[
                    "Command immediate return to base",
                    "Notify ground crew for battery replacement",
                    "Monitor drone during return flight"
                ],
                notification_targets=["mission_control", "maintenance_team"],
                escalation_procedures=[
                    "If drone becomes unresponsive, initiate search and recovery",
                    "Prepare replacement drone if needed"
                ],
                recovery_steps=[
                    "Replace or recharge battery",
                    "Perform post-incident inspection",
                    "Update flight planning parameters"
                ]
            ),
            EmergencyProtocol(
                protocol_id="communication_loss",
                name="Communication Loss Protocol",
                emergency_type=EmergencyType.COMMUNICATION_LOSS,
                severity=EmergencySeverity.CRITICAL,
                description="Complete loss of communication with drone",
                immediate_actions=[
                    "Attempt to reestablish communication",
                    "Monitor last known position",
                    "Prepare emergency recovery team"
                ],
                notification_targets=["mission_control", "emergency_services"],
                escalation_procedures=[
                    "If communication not restored within 5 minutes, dispatch recovery team",
                    "Alert aviation authorities if in controlled airspace"
                ],
                recovery_steps=[
                    "Investigate cause of communication failure",
                    "Repair or replace communication equipment",
                    "Update communication protocols"
                ]
            ),
            EmergencyProtocol(
                protocol_id="weather_hazard",
                name="Weather Hazard Protocol",
                emergency_type=EmergencyType.WEATHER_HAZARD,
                severity=EmergencySeverity.HIGH,
                description="Dangerous weather conditions detected",
                immediate_actions=[
                    "Command all drones to safe altitude",
                    "Reduce speed and increase separation",
                    "Monitor weather radar and forecasts"
                ],
                notification_targets=["mission_control", "weather_team"],
                escalation_procedures=[
                    "If conditions worsen, initiate emergency return",
                    "Prepare indoor operations if available"
                ],
                recovery_steps=[
                    "Wait for weather conditions to improve",
                    "Inspect drones for weather damage",
                    "Update weather monitoring protocols"
                ]
            )
        ]

        for protocol in protocols:
            self.emergency_protocols[protocol.protocol_id] = protocol

    def _register_communication_handlers(self):
        """Register communication handlers for different notification types."""
        # Email handler
        async def email_handler(notification):
            logger.info(f"EMAIL: Emergency notification: {notification['message']}")

        # SMS handler
        async def sms_handler(notification):
            logger.info(f"SMS: Emergency notification: {notification['message']}")

        # WebSocket handler
        async def websocket_handler(notification):
            logger.info(f"WEBSOCKET: Broadcasting emergency: {notification['message']}")

        # Push notification handler
        async def push_handler(notification):
            logger.info(f"PUSH: Emergency alert: {notification['message']}")

        self.communication_manager.register_notification_handler("email", email_handler)
        self.communication_manager.register_notification_handler("sms", sms_handler)
        self.communication_manager.register_notification_handler("websocket", websocket_handler)
        self.communication_manager.register_notification_handler("push", push_handler)

    def add_geofence_zone(self, zone: GeofenceZone):
        """Add a geofence zone."""
        self.geofence_zones[zone.zone_id] = zone
        logger.info(f"Added geofence zone: {zone.name}")

    def remove_geofence_zone(self, zone_id: str):
        """Remove a geofence zone."""
        if zone_id in self.geofence_zones:
            del self.geofence_zones[zone_id]
            logger.info(f"Removed geofence zone: {zone_id}")

    async def declare_emergency(
        self,
        emergency_type: EmergencyType,
        description: str,
        affected_drones: List[str],
        location: Optional[Dict[str, float]] = None,
        severity: Optional[EmergencySeverity] = None
    ) -> EmergencyEvent:
        """
        Declare a new emergency situation.

        Args:
            emergency_type: Type of emergency
            description: Description of the emergency
            affected_drones: List of affected drone IDs
            location: Location data if available
            severity: Emergency severity (auto-detected if not provided)

        Returns:
            Created emergency event
        """
        # Auto-detect severity if not provided
        if severity is None:
            severity = self._detect_emergency_severity(emergency_type, description)

        # Create emergency event
        event_id = f"emergency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        emergency_event = EmergencyEvent(
            event_id=event_id,
            emergency_type=emergency_type,
            severity=severity,
            description=description,
            affected_drones=affected_drones,
            location=location
        )

        # Store emergency
        self.active_emergencies[event_id] = emergency_event

        # Apply emergency protocols
        await self._apply_emergency_protocols(emergency_event)

        # Send notifications
        await self.communication_manager.broadcast_emergency_alert(
            emergency_event,
            f"EMERGENCY DECLARED: {emergency_type.value.upper()} - {description}"
        )

        logger.warning(f"Emergency declared: {emergency_type.value} affecting drones: {affected_drones}")
        return emergency_event

    def _detect_emergency_severity(self, emergency_type: EmergencyType, description: str) -> EmergencySeverity:
        """Auto-detect emergency severity based on type and description."""
        severity_keywords = {
            EmergencySeverity.CRITICAL: ["crash", "lost", "unresponsive", "fire", "critical"],
            EmergencySeverity.HIGH: ["battery", "signal", "weather", "failure", "breach"],
            EmergencySeverity.MEDIUM: ["warning", "hazard", "structural", "medical"],
            EmergencySeverity.LOW: ["detected", "person", "security"]
        }

        description_lower = description.lower()

        for severity, keywords in severity_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return severity

        # Default based on emergency type
        severity_defaults = {
            EmergencyType.DRONE_CRASH: EmergencySeverity.CRITICAL,
            EmergencyType.COMMUNICATION_LOSS: EmergencySeverity.CRITICAL,
            EmergencyType.BATTERY_CRITICAL: EmergencySeverity.HIGH,
            EmergencyType.WEATHER_HAZARD: EmergencySeverity.HIGH,
            EmergencyType.EMERGENCY_LANDING: EmergencySeverity.HIGH,
            EmergencyType.PERSON_DETECTED: EmergencySeverity.MEDIUM,
            EmergencyType.GEOFENCE_BREACH: EmergencySeverity.MEDIUM
        }

        return severity_defaults.get(emergency_type, EmergencySeverity.MEDIUM)

    async def _apply_emergency_protocols(self, emergency_event: EmergencyEvent):
        """Apply appropriate emergency protocols."""
        # Find applicable protocols
        applicable_protocols = [
            protocol for protocol in self.emergency_protocols.values()
            if protocol.emergency_type == emergency_event.emergency_type
        ]

        for protocol in applicable_protocols:
            # Execute immediate actions
            for action in protocol.immediate_actions:
                await self._execute_emergency_action(action, emergency_event)

            # Record protocol application
            emergency_event.protocols_applied.append(protocol.protocol_id)

            logger.info(f"Applied emergency protocol: {protocol.name}")

    async def _execute_emergency_action(self, action: str, emergency_event: EmergencyEvent):
        """Execute a specific emergency action."""
        # This would integrate with the coordination engine to send commands
        logger.info(f"Executing emergency action: {action} for event {emergency_event.event_id}")

        # Example actions (would be implemented based on coordination engine)
        if "return to base" in action.lower():
            # Send return to base command to affected drones
            pass
        elif "notify" in action.lower():
            # Send notification to specified teams
            pass
        elif "monitor" in action.lower():
            # Increase monitoring frequency
            pass

    def resolve_emergency(self, event_id: str, resolution_notes: str):
        """Resolve an emergency situation."""
        if event_id in self.active_emergencies:
            emergency = self.active_emergencies[event_id]
            emergency.status = "resolved"
            emergency.resolution_notes = resolution_notes

            # Move to history
            self.emergency_history.append(emergency)
            del self.active_emergencies[event_id]

            logger.info(f"Emergency resolved: {event_id}")
        else:
            logger.warning(f"Attempted to resolve non-existent emergency: {event_id}")

    def check_geofence_violations(self, drone_positions: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Check for geofence violations.

        Args:
            drone_positions: Current drone positions {drone_id: {lat, lng, alt}}

        Returns:
            List of geofence violations
        """
        violations = []

        for drone_id, position in drone_positions.items():
            lat = position.get("lat")
            lng = position.get("lng")
            alt = position.get("alt")

            if lat is None or lng is None:
                continue

            # Check all geofence zones
            for zone in self.geofence_zones.values():
                if zone.contains_point(lat, lng, alt):
                    violations.append({
                        "drone_id": drone_id,
                        "zone_id": zone.zone_id,
                        "zone_name": zone.name,
                        "zone_type": zone.zone_type,
                        "violation_type": "entry" if zone.zone_type == "no_fly" else "warning",
                        "position": position,
                        "timestamp": datetime.utcnow().isoformat()
                    })

        return violations

    def validate_mission_safety(self, mission_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate safety of a mission plan."""
        return self.safety_validator.validate_mission_safety(mission_plan)

    def validate_drone_operation(self, drone_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate safety of drone operation."""
        return self.safety_validator.validate_drone_operation(drone_state)

    def get_emergency_status(self) -> Dict[str, Any]:
        """Get current emergency status."""
        return {
            "active_emergencies": len(self.active_emergencies),
            "emergency_types": [e.emergency_type.value for e in self.active_emergencies.values()],
            "severity_breakdown": {
                "critical": len([e for e in self.active_emergencies.values() if e.severity == EmergencySeverity.CRITICAL]),
                "high": len([e for e in self.active_emergencies.values() if e.severity == EmergencySeverity.HIGH]),
                "medium": len([e for e in self.active_emergencies.values() if e.severity == EmergencySeverity.MEDIUM]),
                "low": len([e for e in self.active_emergencies.values() if e.severity == EmergencySeverity.LOW])
            },
            "geofence_zones": len(self.geofence_zones),
            "protocols_available": len(self.emergency_protocols)
        }

    def get_emergency_history(self, limit: int = 50) -> List[EmergencyEvent]:
        """Get emergency history."""
        return self.emergency_history[-limit:]