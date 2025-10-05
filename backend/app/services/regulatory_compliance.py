"""
Regulatory Compliance Service for SAR Mission Commander
Comprehensive compliance checking for drone operations across different jurisdictions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import math

from ..utils.logging import get_logger

logger = get_logger(__name__)

class Jurisdiction(Enum):
    USA_FAA = "usa_faa"
    EU_EASA = "eu_easa"
    CANADA_TC = "canada_tc"
    UK_CAA = "uk_caa"
    AUSTRALIA_CASA = "australia_casa"
    JAPAN_MLIT = "japan_mlit"
    UNKNOWN = "unknown"

class ComplianceRuleType(Enum):
    ALTITUDE_LIMIT = "altitude_limit"
    SPEED_LIMIT = "speed_limit"
    FLIGHT_TIME_LIMIT = "flight_time_limit"
    DISTANCE_FROM_PEOPLE = "distance_from_people"
    DISTANCE_FROM_BUILDINGS = "distance_from_buildings"
    NO_FLY_ZONE = "no_fly_zone"
    WEATHER_RESTRICTIONS = "weather_restrictions"
    PILOT_CERTIFICATION = "pilot_certification"
    AIRCRAFT_REGISTRATION = "aircraft_registration"
    INSURANCE_REQUIREMENT = "insurance_requirement"
    EMERGENCY_PROCEDURES = "emergency_procedures"
    DATA_PRIVACY = "data_privacy"

class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_APPROVAL = "requires_approval"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"

class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceRule:
    """Regulatory compliance rule"""
    rule_id: str
    rule_type: ComplianceRuleType
    jurisdiction: Jurisdiction
    description: str
    parameters: Dict[str, Any]
    severity: ViolationSeverity
    auto_enforcement: bool
    effective_date: datetime
    expiration_date: Optional[datetime] = None

@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_id: str
    rule: ComplianceRule
    mission_id: str
    drone_id: str
    timestamp: datetime
    location: Tuple[float, float, float]  # lat, lng, alt
    parameters: Dict[str, Any]
    result: ComplianceLevel
    violation_details: Optional[str] = None
    recommended_action: Optional[str] = None

@dataclass
class ComplianceViolation:
    """Compliance violation"""
    violation_id: str
    check_id: str
    rule: ComplianceRule
    severity: ViolationSeverity
    description: str
    timestamp: datetime
    location: Tuple[float, float, float]
    mission_id: str
    drone_id: str
    auto_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class RegulatoryComplianceService:
    """Regulatory compliance service for SAR operations"""
    
    def __init__(self):
        self.compliance_rules = {}
        self.compliance_history = []
        self.active_violations = {}
        self.jurisdiction_detector = JurisdictionDetector()
        
        # Initialize compliance rules for different jurisdictions
        self._initialize_compliance_rules()
        
    def _initialize_compliance_rules(self):
        """Initialize compliance rules for different jurisdictions"""
        
        # USA FAA Rules (Part 107)
        self._add_faa_rules()
        
        # EU EASA Rules
        self._add_easa_rules()
        
        # Canada TC Rules
        self._add_canada_rules()
        
        # UK CAA Rules
        self._add_uk_rules()
        
        # Australia CASA Rules
        self._add_australia_rules()
        
        logger.info(f"Initialized {len(self.compliance_rules)} compliance rules")
    
    def _add_faa_rules(self):
        """Add FAA Part 107 compliance rules"""
        
        # Altitude limit
        self._add_rule(
            rule_id="faa_altitude_400ft",
            rule_type=ComplianceRuleType.ALTITUDE_LIMIT,
            jurisdiction=Jurisdiction.USA_FAA,
            description="Maximum altitude 400 feet AGL",
            parameters={"max_altitude_ft": 400, "agl_only": True},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
        
        # Speed limit
        self._add_rule(
            rule_id="faa_speed_100mph",
            rule_type=ComplianceRuleType.SPEED_LIMIT,
            jurisdiction=Jurisdiction.USA_FAA,
            description="Maximum speed 100 mph",
            parameters={"max_speed_mph": 100},
            severity=ViolationSeverity.MEDIUM,
            auto_enforcement=True
        )
        
        # Distance from people
        self._add_rule(
            rule_id="faa_distance_people",
            rule_type=ComplianceRuleType.DISTANCE_FROM_PEOPLE,
            jurisdiction=Jurisdiction.USA_FAA,
            description="Maintain distance from people not involved in operation",
            parameters={"min_distance_ft": 25},
            severity=ViolationSeverity.CRITICAL,
            auto_enforcement=True
        )
        
        # Flight time limit
        self._add_rule(
            rule_id="faa_flight_time",
            rule_type=ComplianceRuleType.FLIGHT_TIME_LIMIT,
            jurisdiction=Jurisdiction.USA_FAA,
            description="Maximum flight time per battery",
            parameters={"max_flight_time_minutes": 30},
            severity=ViolationSeverity.MEDIUM,
            auto_enforcement=True
        )
        
        # Weather restrictions
        self._add_rule(
            rule_id="faa_weather",
            rule_type=ComplianceRuleType.WEATHER_RESTRICTIONS,
            jurisdiction=Jurisdiction.USA_FAA,
            description="No flight in adverse weather",
            parameters={"max_wind_speed_mph": 25, "min_visibility_miles": 3},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
    
    def _add_easa_rules(self):
        """Add EU EASA compliance rules"""
        
        # Altitude limit (Open Category A1/A3)
        self._add_rule(
            rule_id="easa_altitude_400ft",
            rule_type=ComplianceRuleType.ALTITUDE_LIMIT,
            jurisdiction=Jurisdiction.EU_EASA,
            description="Maximum altitude 400 feet AGL",
            parameters={"max_altitude_ft": 400, "agl_only": True},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
        
        # Speed limit
        self._add_rule(
            rule_id="easa_speed_60mph",
            rule_type=ComplianceRuleType.SPEED_LIMIT,
            jurisdiction=Jurisdiction.EU_EASA,
            description="Maximum speed 60 mph",
            parameters={"max_speed_mph": 60},
            severity=ViolationSeverity.MEDIUM,
            auto_enforcement=True
        )
        
        # Distance from people (A3 category)
        self._add_rule(
            rule_id="easa_distance_people",
            rule_type=ComplianceRuleType.DISTANCE_FROM_PEOPLE,
            jurisdiction=Jurisdiction.EU_EASA,
            description="Maintain distance from people",
            parameters={"min_distance_ft": 50},
            severity=ViolationSeverity.CRITICAL,
            auto_enforcement=True
        )
    
    def _add_canada_rules(self):
        """Add Canada TC compliance rules"""
        
        # Altitude limit
        self._add_rule(
            rule_id="canada_altitude_400ft",
            rule_type=ComplianceRuleType.ALTITUDE_LIMIT,
            jurisdiction=Jurisdiction.CANADA_TC,
            description="Maximum altitude 400 feet AGL",
            parameters={"max_altitude_ft": 400, "agl_only": True},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
        
        # Distance from people
        self._add_rule(
            rule_id="canada_distance_people",
            rule_type=ComplianceRuleType.DISTANCE_FROM_PEOPLE,
            jurisdiction=Jurisdiction.CANADA_TC,
            description="Maintain distance from people",
            parameters={"min_distance_ft": 30},
            severity=ViolationSeverity.CRITICAL,
            auto_enforcement=True
        )
    
    def _add_uk_rules(self):
        """Add UK CAA compliance rules"""
        
        # Altitude limit
        self._add_rule(
            rule_id="uk_altitude_400ft",
            rule_type=ComplianceRuleType.ALTITUDE_LIMIT,
            jurisdiction=Jurisdiction.UK_CAA,
            description="Maximum altitude 400 feet AGL",
            parameters={"max_altitude_ft": 400, "agl_only": True},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
        
        # Distance from people
        self._add_rule(
            rule_id="uk_distance_people",
            rule_type=ComplianceRuleType.DISTANCE_FROM_PEOPLE,
            jurisdiction=Jurisdiction.UK_CAA,
            description="Maintain distance from people",
            parameters={"min_distance_ft": 50},
            severity=ViolationSeverity.CRITICAL,
            auto_enforcement=True
        )
    
    def _add_australia_rules(self):
        """Add Australia CASA compliance rules"""
        
        # Altitude limit
        self._add_rule(
            rule_id="australia_altitude_400ft",
            rule_type=ComplianceRuleType.ALTITUDE_LIMIT,
            jurisdiction=Jurisdiction.AUSTRALIA_CASA,
            description="Maximum altitude 400 feet AGL",
            parameters={"max_altitude_ft": 400, "agl_only": True},
            severity=ViolationSeverity.HIGH,
            auto_enforcement=True
        )
        
        # Distance from people
        self._add_rule(
            rule_id="australia_distance_people",
            rule_type=ComplianceRuleType.DISTANCE_FROM_PEOPLE,
            jurisdiction=Jurisdiction.AUSTRALIA_CASA,
            description="Maintain distance from people",
            parameters={"min_distance_ft": 30},
            severity=ViolationSeverity.CRITICAL,
            auto_enforcement=True
        )
    
    def _add_rule(self, rule_id: str, rule_type: ComplianceRule, jurisdiction: Jurisdiction,
                  description: str, parameters: Dict[str, Any], severity: ViolationSeverity,
                  auto_enforcement: bool):
        """Add a compliance rule"""
        rule = ComplianceRule(
            rule_id=rule_id,
            rule_type=rule_type,
            jurisdiction=jurisdiction,
            description=description,
            parameters=parameters,
            severity=severity,
            auto_enforcement=auto_enforcement,
            effective_date=datetime.now()
        )
        
        self.compliance_rules[rule_id] = rule
    
    async def check_compliance(self, mission_id: str, drone_id: str, 
                             location: Tuple[float, float, float],
                             mission_parameters: Dict[str, Any]) -> List[ComplianceCheck]:
        """Check compliance for a mission at a specific location"""
        try:
            # Detect jurisdiction
            jurisdiction = await self.jurisdiction_detector.detect_jurisdiction(location)
            
            # Get applicable rules for jurisdiction
            applicable_rules = self._get_applicable_rules(jurisdiction)
            
            compliance_checks = []
            
            # Perform compliance checks
            for rule in applicable_rules:
                check = await self._perform_compliance_check(
                    rule, mission_id, drone_id, location, mission_parameters
                )
                compliance_checks.append(check)
                
                # Record compliance history
                self.compliance_history.append(check)
                
                # Handle violations
                if check.result == ComplianceLevel.NON_COMPLIANT:
                    await self._handle_compliance_violation(check)
            
            logger.info(f"Completed {len(compliance_checks)} compliance checks for mission {mission_id}")
            return compliance_checks
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return []
    
    async def _perform_compliance_check(self, rule: ComplianceRule, mission_id: str,
                                      drone_id: str, location: Tuple[float, float, float],
                                      mission_parameters: Dict[str, Any]) -> ComplianceCheck:
        """Perform a specific compliance check"""
        try:
            check_id = f"check_{rule.rule_id}_{int(datetime.now().timestamp())}"
            
            # Perform rule-specific check
            if rule.rule_type == ComplianceRuleType.ALTITUDE_LIMIT:
                result, violation_details, recommended_action = await self._check_altitude_compliance(
                    rule, location, mission_parameters
                )
            elif rule.rule_type == ComplianceRuleType.SPEED_LIMIT:
                result, violation_details, recommended_action = await self._check_speed_compliance(
                    rule, mission_parameters
                )
            elif rule.rule_type == ComplianceRuleType.DISTANCE_FROM_PEOPLE:
                result, violation_details, recommended_action = await self._check_distance_compliance(
                    rule, location, mission_parameters
                )
            elif rule.rule_type == ComplianceRuleType.WEATHER_RESTRICTIONS:
                result, violation_details, recommended_action = await self._check_weather_compliance(
                    rule, location, mission_parameters
                )
            elif rule.rule_type == ComplianceRuleType.FLIGHT_TIME_LIMIT:
                result, violation_details, recommended_action = await self._check_flight_time_compliance(
                    rule, mission_parameters
                )
            else:
                result = ComplianceLevel.UNKNOWN
                violation_details = "Rule type not implemented"
                recommended_action = "Manual review required"
            
            return ComplianceCheck(
                check_id=check_id,
                rule=rule,
                mission_id=mission_id,
                drone_id=drone_id,
                timestamp=datetime.now(),
                location=location,
                parameters=mission_parameters,
                result=result,
                violation_details=violation_details,
                recommended_action=recommended_action
            )
            
        except Exception as e:
            logger.error(f"Error performing compliance check for rule {rule.rule_id}: {e}")
            return ComplianceCheck(
                check_id=f"check_{rule.rule_id}_error_{int(datetime.now().timestamp())}",
                rule=rule,
                mission_id=mission_id,
                drone_id=drone_id,
                timestamp=datetime.now(),
                location=location,
                parameters=mission_parameters,
                result=ComplianceLevel.UNKNOWN,
                violation_details=f"Error during check: {e}",
                recommended_action="Manual review required"
            )
    
    async def _check_altitude_compliance(self, rule: ComplianceRule, 
                                       location: Tuple[float, float, float],
                                       mission_parameters: Dict[str, Any]) -> Tuple[ComplianceLevel, str, str]:
        """Check altitude compliance"""
        try:
            altitude_ft = location[2] * 3.28084  # Convert meters to feet
            max_altitude = rule.parameters.get('max_altitude_ft', 400)
            
            if altitude_ft > max_altitude:
                violation_details = f"Altitude {altitude_ft:.1f} ft exceeds limit of {max_altitude} ft"
                recommended_action = f"Reduce altitude to maximum {max_altitude} ft"
                return ComplianceLevel.NON_COMPLIANT, violation_details, recommended_action
            else:
                return ComplianceLevel.COMPLIANT, None, None
                
        except Exception as e:
            logger.error(f"Error checking altitude compliance: {e}")
            return ComplianceLevel.UNKNOWN, f"Error checking altitude: {e}", "Manual review required"
    
    async def _check_speed_compliance(self, rule: ComplianceRule,
                                    mission_parameters: Dict[str, Any]) -> Tuple[ComplianceLevel, str, str]:
        """Check speed compliance"""
        try:
            speed_mph = mission_parameters.get('speed_mph', 0)
            max_speed = rule.parameters.get('max_speed_mph', 100)
            
            if speed_mph > max_speed:
                violation_details = f"Speed {speed_mph:.1f} mph exceeds limit of {max_speed} mph"
                recommended_action = f"Reduce speed to maximum {max_speed} mph"
                return ComplianceLevel.NON_COMPLIANT, violation_details, recommended_action
            else:
                return ComplianceLevel.COMPLIANT, None, None
                
        except Exception as e:
            logger.error(f"Error checking speed compliance: {e}")
            return ComplianceLevel.UNKNOWN, f"Error checking speed: {e}", "Manual review required"
    
    async def _check_distance_compliance(self, rule: ComplianceRule,
                                       location: Tuple[float, float, float],
                                       mission_parameters: Dict[str, Any]) -> Tuple[ComplianceLevel, str, str]:
        """Check distance from people compliance"""
        try:
            min_distance_ft = rule.parameters.get('min_distance_ft', 25)
            
            # In real implementation, this would check actual distance to people
            # For now, assume compliance if no people detected nearby
            nearest_person_distance = mission_parameters.get('nearest_person_distance_ft', 100)
            
            if nearest_person_distance < min_distance_ft:
                violation_details = f"Distance to nearest person {nearest_person_distance:.1f} ft is less than required {min_distance_ft} ft"
                recommended_action = f"Maintain minimum distance of {min_distance_ft} ft from people"
                return ComplianceLevel.NON_COMPLIANT, violation_details, recommended_action
            else:
                return ComplianceLevel.COMPLIANT, None, None
                
        except Exception as e:
            logger.error(f"Error checking distance compliance: {e}")
            return ComplianceLevel.UNKNOWN, f"Error checking distance: {e}", "Manual review required"
    
    async def _check_weather_compliance(self, rule: ComplianceRule,
                                      location: Tuple[float, float, float],
                                      mission_parameters: Dict[str, Any]) -> Tuple[ComplianceLevel, str, str]:
        """Check weather compliance"""
        try:
            max_wind_speed = rule.parameters.get('max_wind_speed_mph', 25)
            min_visibility = rule.parameters.get('min_visibility_miles', 3)
            
            current_wind_speed = mission_parameters.get('wind_speed_mph', 0)
            current_visibility = mission_parameters.get('visibility_miles', 10)
            
            violations = []
            
            if current_wind_speed > max_wind_speed:
                violations.append(f"Wind speed {current_wind_speed:.1f} mph exceeds limit of {max_wind_speed} mph")
            
            if current_visibility < min_visibility:
                violations.append(f"Visibility {current_visibility:.1f} miles is below minimum of {min_visibility} miles")
            
            if violations:
                violation_details = "; ".join(violations)
                recommended_action = "Postpone flight until weather conditions improve"
                return ComplianceLevel.NON_COMPLIANT, violation_details, recommended_action
            else:
                return ComplianceLevel.COMPLIANT, None, None
                
        except Exception as e:
            logger.error(f"Error checking weather compliance: {e}")
            return ComplianceLevel.UNKNOWN, f"Error checking weather: {e}", "Manual review required"
    
    async def _check_flight_time_compliance(self, rule: ComplianceRule,
                                          mission_parameters: Dict[str, Any]) -> Tuple[ComplianceLevel, str, str]:
        """Check flight time compliance"""
        try:
            max_flight_time = rule.parameters.get('max_flight_time_minutes', 30)
            current_flight_time = mission_parameters.get('flight_time_minutes', 0)
            
            if current_flight_time > max_flight_time:
                violation_details = f"Flight time {current_flight_time:.1f} minutes exceeds limit of {max_flight_time} minutes"
                recommended_action = f"Land immediately or return to base"
                return ComplianceLevel.NON_COMPLIANT, violation_details, recommended_action
            else:
                return ComplianceLevel.COMPLIANT, None, None
                
        except Exception as e:
            logger.error(f"Error checking flight time compliance: {e}")
            return ComplianceLevel.UNKNOWN, f"Error checking flight time: {e}", "Manual review required"
    
    def _get_applicable_rules(self, jurisdiction: Jurisdiction) -> List[ComplianceRule]:
        """Get compliance rules applicable to a jurisdiction"""
        applicable_rules = []
        
        for rule in self.compliance_rules.values():
            if rule.jurisdiction == jurisdiction:
                applicable_rules.append(rule)
        
        return applicable_rules
    
    async def _handle_compliance_violation(self, check: ComplianceCheck):
        """Handle a compliance violation"""
        try:
            violation_id = f"violation_{check.check_id}_{int(datetime.now().timestamp())}"
            
            violation = ComplianceViolation(
                violation_id=violation_id,
                check_id=check.check_id,
                rule=check.rule,
                severity=check.rule.severity,
                description=check.violation_details or f"Violation of {check.rule.description}",
                timestamp=datetime.now(),
                location=check.location,
                mission_id=check.mission_id,
                drone_id=check.drone_id
            )
            
            self.active_violations[violation_id] = violation
            
            # Log violation
            logger.warning(f"Compliance violation: {violation.description}")
            
            # Auto-enforce if rule requires it
            if check.rule.auto_enforcement:
                await self._auto_enforce_violation(violation)
            
        except Exception as e:
            logger.error(f"Error handling compliance violation: {e}")
    
    async def _auto_enforce_violation(self, violation: ComplianceViolation):
        """Auto-enforce a compliance violation"""
        try:
            # In real implementation, this would trigger automatic responses
            # such as forcing drone to land, returning to base, etc.
            
            if violation.severity == ViolationSeverity.CRITICAL:
                logger.critical(f"Critical compliance violation - immediate action required: {violation.description}")
                # Force immediate landing
                await self._force_emergency_landing(violation.drone_id)
                
            elif violation.severity == ViolationSeverity.HIGH:
                logger.error(f"High severity violation - corrective action required: {violation.description}")
                # Force return to base
                await self._force_return_to_base(violation.drone_id)
                
            elif violation.severity == ViolationSeverity.MEDIUM:
                logger.warning(f"Medium severity violation - monitoring required: {violation.description}")
                # Issue warning and monitor
                await self._issue_compliance_warning(violation)
                
        except Exception as e:
            logger.error(f"Error auto-enforcing violation: {e}")
    
    async def _force_emergency_landing(self, drone_id: str):
        """Force emergency landing for compliance violation"""
        try:
            logger.critical(f"Forcing emergency landing for drone {drone_id} due to compliance violation")
            # In real implementation, this would send emergency landing command
            await asyncio.sleep(0.1)  # Simulate command execution
            
        except Exception as e:
            logger.error(f"Error forcing emergency landing: {e}")
    
    async def _force_return_to_base(self, drone_id: str):
        """Force return to base for compliance violation"""
        try:
            logger.error(f"Forcing return to base for drone {drone_id} due to compliance violation")
            # In real implementation, this would send return to base command
            await asyncio.sleep(0.1)  # Simulate command execution
            
        except Exception as e:
            logger.error(f"Error forcing return to base: {e}")
    
    async def _issue_compliance_warning(self, violation: ComplianceViolation):
        """Issue compliance warning"""
        try:
            logger.warning(f"Issuing compliance warning: {violation.description}")
            # In real implementation, this would send warning to operator
            await asyncio.sleep(0.1)  # Simulate warning issuance
            
        except Exception as e:
            logger.error(f"Error issuing compliance warning: {e}")
    
    async def resolve_violation(self, violation_id: str, resolution_notes: str = "") -> bool:
        """Resolve a compliance violation"""
        try:
            if violation_id in self.active_violations:
                violation = self.active_violations[violation_id]
                violation.auto_resolved = True
                violation.resolved_at = datetime.now()
                violation.resolution_notes = resolution_notes
                
                del self.active_violations[violation_id]
                
                logger.info(f"Compliance violation {violation_id} resolved: {resolution_notes}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving violation: {e}")
            return False
    
    def get_compliance_summary(self, mission_id: str) -> Dict[str, Any]:
        """Get compliance summary for a mission"""
        try:
            mission_checks = [check for check in self.compliance_history if check.mission_id == mission_id]
            
            if not mission_checks:
                return {
                    'mission_id': mission_id,
                    'total_checks': 0,
                    'compliant_checks': 0,
                    'non_compliant_checks': 0,
                    'compliance_rate': 0.0,
                    'active_violations': 0,
                    'jurisdictions': []
                }
            
            compliant_checks = len([check for check in mission_checks if check.result == ComplianceLevel.COMPLIANT])
            non_compliant_checks = len([check for check in mission_checks if check.result == ComplianceLevel.NON_COMPLIANT])
            compliance_rate = (compliant_checks / len(mission_checks)) * 100
            
            jurisdictions = list(set([check.rule.jurisdiction.value for check in mission_checks]))
            active_violations = len([v for v in self.active_violations.values() if v.mission_id == mission_id])
            
            return {
                'mission_id': mission_id,
                'total_checks': len(mission_checks),
                'compliant_checks': compliant_checks,
                'non_compliant_checks': non_compliant_checks,
                'compliance_rate': compliance_rate,
                'active_violations': active_violations,
                'jurisdictions': jurisdictions
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance summary: {e}")
            return {}

class JurisdictionDetector:
    """Detect regulatory jurisdiction based on location"""
    
    def __init__(self):
        # Simplified jurisdiction boundaries (in real implementation, use proper GIS data)
        self.jurisdiction_boundaries = {
            Jurisdiction.USA_FAA: {
                'name': 'United States',
                'bounds': {
                    'north': 71.0, 'south': 18.0,
                    'east': -66.0, 'west': -180.0
                }
            },
            Jurisdiction.EU_EASA: {
                'name': 'European Union',
                'bounds': {
                    'north': 72.0, 'south': 35.0,
                    'east': 45.0, 'west': -25.0
                }
            },
            Jurisdiction.CANADA_TC: {
                'name': 'Canada',
                'bounds': {
                    'north': 84.0, 'south': 41.0,
                    'east': -52.0, 'west': -141.0
                }
            },
            Jurisdiction.UK_CAA: {
                'name': 'United Kingdom',
                'bounds': {
                    'north': 61.0, 'south': 49.0,
                    'east': 2.0, 'west': -8.0
                }
            },
            Jurisdiction.AUSTRALIA_CASA: {
                'name': 'Australia',
                'bounds': {
                    'north': -10.0, 'south': -44.0,
                    'east': 154.0, 'west': 113.0
                }
            },
            Jurisdiction.JAPAN_MLIT: {
                'name': 'Japan',
                'bounds': {
                    'north': 46.0, 'south': 24.0,
                    'east': 146.0, 'west': 129.0
                }
            }
        }
    
    async def detect_jurisdiction(self, location: Tuple[float, float, float]) -> Jurisdiction:
        """Detect jurisdiction based on location coordinates"""
        try:
            lat, lng, alt = location
            
            for jurisdiction, bounds in self.jurisdiction_boundaries.items():
                bounds_data = bounds['bounds']
                
                if (bounds_data['south'] <= lat <= bounds_data['north'] and
                    bounds_data['west'] <= lng <= bounds_data['east']):
                    return jurisdiction
            
            # Default to unknown if no jurisdiction matches
            return Jurisdiction.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error detecting jurisdiction: {e}")
            return Jurisdiction.UNKNOWN

# Global instance
regulatory_compliance_service = RegulatoryComplianceService()
