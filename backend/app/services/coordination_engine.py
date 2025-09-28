"""
Hybrid Coordination Engine for SAR Drone Operations.

Combines simple rule-based coordination with LLM intelligence for complex decisions.
This provides reliable basic coordination with intelligent decision-making for complex situations.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

from ..ai.llm_intelligence import LLMIntelligenceEngine

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Priority levels for coordination decisions."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class CommandType(Enum):
    """Types of coordination commands."""
    NAVIGATION = "navigation"
    SEARCH = "search"
    INVESTIGATION = "investigation"
    RETURN = "return"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"

@dataclass
class CoordinationCommand:
    """Represents a coordination command for a drone."""
    drone_id: str
    command_type: CommandType
    priority: Priority
    parameters: Dict[str, Any]
    reason: str
    timestamp: datetime = None
    expires_at: Optional[datetime] = None
    executed: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

        # Commands expire after 5 minutes by default
        if self.expires_at is None:
            self.expires_at = self.timestamp + timedelta(minutes=5)

    def is_expired(self) -> bool:
        """Check if command has expired."""
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for serialization."""
        return {
            "drone_id": self.drone_id,
            "command_type": self.command_type.value,
            "priority": self.priority.value,
            "parameters": self.parameters,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "executed": self.executed
        }

class CoordinationRules:
    """
    Simple, reliable rules for routine drone coordination operations.

    These rules handle common scenarios and ensure safe, predictable behavior.
    """

    def __init__(self):
        self.rule_violations = []

    def apply_rules(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """
        Apply coordination rules to generate commands.

        Args:
            mission_state: Current state of the mission including drones, discoveries, etc.

        Returns:
            List of coordination commands to execute
        """
        commands = []
        drones = mission_state.get("drones", [])

        for drone in drones:
            drone_commands = self._apply_drone_rules(drone, mission_state)
            commands.extend(drone_commands)

        # Apply system-level rules
        system_commands = self._apply_system_rules(mission_state)
        commands.extend(system_commands)

        return commands

    def _apply_drone_rules(self, drone: Dict[str, Any], mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Apply rules specific to individual drones."""
        commands = []
        drone_id = drone.get("id")

        # Battery management rule
        battery_level = drone.get("battery_level", 100)
        if battery_level < 20:
            commands.append(CoordinationCommand(
                drone_id=drone_id,
                command_type=CommandType.RETURN,
                priority=Priority.HIGH,
                parameters={"return_reason": "low_battery"},
                reason=f"Low battery ({battery_level}%) - return to base"
            ))

        # Signal strength rule
        signal_strength = drone.get("signal_strength", 100)
        if signal_strength < 30:
            commands.append(CoordinationCommand(
                drone_id=drone_id,
                command_type=CommandType.NAVIGATION,
                priority=Priority.MEDIUM,
                parameters={
                    "action": "reduce_range",
                    "max_distance": 500  # Reduce operational range
                },
                reason=f"Weak signal ({signal_strength}%) - reduce operational range"
            ))

        # Area completion rule
        area_progress = drone.get("area_progress", 0)
        if area_progress > 95:
            commands.append(CoordinationCommand(
                drone_id=drone_id,
                command_type=CommandType.SEARCH,
                priority=Priority.LOW,
                parameters={"action": "await_new_assignment"},
                reason="Search area completed - awaiting new assignment"
            ))

        # Emergency situation rule
        if mission_state.get("emergency_situation"):
            emergency_type = mission_state.get("emergency_type", "unknown")
            commands.append(CoordinationCommand(
                drone_id=drone_id,
                command_type=CommandType.EMERGENCY,
                priority=Priority.EMERGENCY,
                parameters={
                    "emergency_type": emergency_type,
                    "action": "hover_safely"
                },
                reason=f"Emergency situation: {emergency_type}"
            ))

        return commands

    def _apply_system_rules(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Apply rules that affect the entire system."""
        commands = []

        # Weather-based rules
        weather = mission_state.get("weather", {})
        wind_speed = weather.get("wind_speed", 0)

        if wind_speed > 15:  # m/s
            commands.append(CoordinationCommand(
                drone_id="all_drones",
                command_type=CommandType.NAVIGATION,
                priority=Priority.HIGH,
                parameters={
                    "action": "reduce_speed",
                    "max_speed": 8,  # Reduce max speed in high winds
                    "altitude_adjustment": "increase"
                },
                reason=f"High wind speed ({wind_speed} m/s) - reduce speed and increase altitude"
            ))

        # Resource conflict resolution
        if self._detect_resource_conflicts(mission_state):
            conflict_commands = self._resolve_resource_conflicts(mission_state)
            commands.extend(conflict_commands)

        return commands

    def _detect_resource_conflicts(self, mission_state: Dict[str, Any]) -> bool:
        """Detect conflicts between drone operations."""
        drones = mission_state.get("drones", [])

        # Check for drones operating too close to each other
        for i, drone1 in enumerate(drones):
            for drone2 in drones[i+1:]:
                pos1 = drone1.get("current_position", {})
                pos2 = drone2.get("current_position", {})

                if pos1 and pos2:
                    distance = self._calculate_distance(
                        (pos1.get("lat", 0), pos1.get("lng", 0)),
                        (pos2.get("lat", 0), pos2.get("lng", 0))
                    )

                    if distance < 50:  # Less than 50 meters apart
                        return True

        return False

    def _resolve_resource_conflicts(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Resolve conflicts between drone operations."""
        commands = []
        drones = mission_state.get("drones", [])

        # Simple conflict resolution: assign altitude separation
        for i, drone in enumerate(drones):
            commands.append(CoordinationCommand(
                drone_id=drone.get("id"),
                command_type=CommandType.NAVIGATION,
                priority=Priority.MEDIUM,
                parameters={
                    "target_altitude": 20 + (i * 5),  # Stagger altitudes
                    "separation_reason": "conflict_resolution"
                },
                reason="Conflict resolution - adjusting altitude for separation"
            ))

        return commands

    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in meters."""
        # Simple Euclidean distance for conflict detection
        # In production, use proper geodesic calculation
        lat_diff = coord2[0] - coord1[0]
        lng_diff = coord2[1] - coord1[1]

        # Rough conversion: 1 degree ≈ 111km
        return ((lat_diff * 111000) ** 2 + (lng_diff * 111000) ** 2) ** 0.5

class HybridCoordinationEngine:
    """
    Hybrid coordination engine combining rule-based and LLM intelligence.

    Rules handle routine operations, LLM handles complex decisions.
    This provides reliability with intelligent decision-making capabilities.
    """

    def __init__(self):
        self.coordination_rules = CoordinationRules()
        self.llm_engine = LLMIntelligenceEngine()
        self.active_commands: Dict[str, List[CoordinationCommand]] = {}
        self.command_history: List[CoordinationCommand] = []

        # Initialize LLM engine
        self.llm_initialized = False

    async def initialize(self):
        """Initialize the coordination engine."""
        try:
            await self.llm_engine.initialize()
            self.llm_initialized = True
            logger.info("Hybrid coordination engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM engine: {e}")
            logger.warning("Operating in rule-based only mode")

    async def coordinate_drones(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """
        Coordinate multiple drones using hybrid approach.

        Args:
            mission_state: Current mission state including drones, discoveries, weather, etc.

        Returns:
            List of coordination commands for drones
        """
        commands = []

        try:
            # Apply simple rules first (always reliable)
            rule_based_commands = self.coordination_rules.apply_rules(mission_state)
            commands.extend(rule_based_commands)

            # Use LLM for complex decisions if available
            if self.llm_initialized and self._requires_intelligent_decision(mission_state):
                try:
                    llm_commands = await self._generate_llm_commands(mission_state)
                    commands.extend(llm_commands)
                except Exception as e:
                    logger.error(f"LLM command generation failed: {e}")
                    # Continue with rule-based commands only

            # Filter and prioritize commands
            commands = self._prioritize_and_filter_commands(commands)

            # Store commands for tracking
            self._store_commands(commands)

            logger.info(f"Generated {len(commands)} coordination commands")
            return commands

        except Exception as e:
            logger.error(f"Coordination failed: {e}")
            # Return emergency commands as fallback
            return self._generate_emergency_commands(mission_state)

    def _requires_intelligent_decision(self, mission_state: Dict[str, Any]) -> bool:
        """Determine if situation requires LLM intelligence."""
        return (
            len(mission_state.get("discoveries", [])) > 0 or
            mission_state.get("emergency_situation") or
            mission_state.get("resource_conflicts") or
            mission_state.get("weather_changes") or
            mission_state.get("complex_terrain") or
            len(mission_state.get("drones", [])) > 5  # Complex multi-drone scenarios
        )

    async def _generate_llm_commands(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Generate intelligent commands using LLM."""
        commands = []

        try:
            # Prepare context for LLM
            context = self._prepare_llm_context(mission_state)

            # Get tactical decisions from LLM
            tactical_response = await self.llm_engine.make_tactical_decision(context)

            # Parse LLM response into commands
            commands = self._parse_tactical_commands(tactical_response, mission_state)

        except Exception as e:
            logger.error(f"Failed to generate LLM commands: {e}")

        return commands

    def _prepare_llm_context(self, mission_state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context information for LLM decision-making."""
        return {
            "mission_id": mission_state.get("mission_id"),
            "mission_status": mission_state.get("status"),
            "active_drones": len(mission_state.get("drones", [])),
            "discoveries": mission_state.get("discoveries", []),
            "weather_conditions": mission_state.get("weather", {}),
            "emergency_situations": mission_state.get("emergency_situation"),
            "terrain_complexity": mission_state.get("terrain_complexity", "normal"),
            "time_remaining": mission_state.get("time_remaining"),
            "priority_objectives": mission_state.get("priority_objectives", [])
        }

    def _parse_tactical_commands(self, llm_response: Dict[str, Any], mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Parse LLM tactical decisions into coordination commands."""
        commands = []

        # Parse resource reallocation decisions
        if "resource_reallocation" in llm_response:
            for reallocation in llm_response["resource_reallocation"]:
                command = CoordinationCommand(
                    drone_id=reallocation.get("drone_id", "all_drones"),
                    command_type=CommandType.NAVIGATION,
                    priority=Priority.HIGH,
                    parameters=reallocation.get("parameters", {}),
                    reason=f"LLM tactical decision: {reallocation.get('reason', 'Resource reallocation')}"
                )
                commands.append(command)

        # Parse priority adjustments
        if "priority_adjustments" in llm_response:
            for adjustment in llm_response["priority_adjustments"]:
                command = CoordinationCommand(
                    drone_id=adjustment.get("drone_id", "all_drones"),
                    command_type=CommandType.SEARCH,
                    priority=Priority.HIGH,
                    parameters=adjustment.get("parameters", {}),
                    reason=f"LLM tactical decision: {adjustment.get('reason', 'Priority adjustment')}"
                )
                commands.append(command)

        # Parse investigation strategies
        if "investigation_strategies" in llm_response:
            for investigation in llm_response["investigation_strategies"]:
                command = CoordinationCommand(
                    drone_id=investigation.get("drone_id"),
                    command_type=CommandType.INVESTIGATION,
                    priority=Priority.HIGH,
                    parameters=investigation.get("parameters", {}),
                    reason=f"LLM tactical decision: {investigation.get('reason', 'Investigation strategy')}"
                )
                commands.append(command)

        return commands

    def _prioritize_and_filter_commands(self, commands: List[CoordinationCommand]) -> List[CoordinationCommand]:
        """Prioritize and filter coordination commands."""
        if not commands:
            return []

        # Sort by priority (highest first)
        commands.sort(key=lambda c: c.priority.value, reverse=True)

        # Remove expired commands
        commands = [cmd for cmd in commands if not cmd.is_expired()]

        # Remove duplicate commands for same drone
        seen_drones = set()
        filtered_commands = []

        for command in commands:
            drone_key = f"{command.drone_id}:{command.command_type.value}"
            if drone_key not in seen_drones:
                seen_drones.add(drone_key)
                filtered_commands.append(command)
            else:
                logger.debug(f"Filtered duplicate command: {drone_key}")

        return filtered_commands

    def _generate_emergency_commands(self, mission_state: Dict[str, Any]) -> List[CoordinationCommand]:
        """Generate emergency commands as fallback."""
        commands = []

        drones = mission_state.get("drones", [])
        for drone in drones:
            commands.append(CoordinationCommand(
                drone_id=drone.get("id"),
                command_type=CommandType.EMERGENCY,
                priority=Priority.EMERGENCY,
                parameters={"action": "return_to_home"},
                reason="Emergency fallback - return to home"
            ))

        return commands

    def _store_commands(self, commands: List[CoordinationCommand]):
        """Store commands for tracking and history."""
        for command in commands:
            self.command_history.append(command)

            # Keep only last 1000 commands
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]

            # Track active commands per drone
            drone_id = command.drone_id
            if drone_id not in self.active_commands:
                self.active_commands[drone_id] = []

            self.active_commands[drone_id].append(command)

    def get_active_commands(self, drone_id: Optional[str] = None) -> List[CoordinationCommand]:
        """Get active commands for a drone or all drones."""
        if drone_id:
            return self.active_commands.get(drone_id, [])

        # Return all active commands
        all_commands = []
        for commands in self.active_commands.values():
            all_commands.extend(commands)
        return all_commands

    def mark_command_executed(self, drone_id: str, command_type: CommandType):
        """Mark a command as executed."""
        if drone_id in self.active_commands:
            for command in self.active_commands[drone_id]:
                if command.command_type == command_type and not command.executed:
                    command.executed = True
                    break

    def get_command_history(self, drone_id: Optional[str] = None, limit: int = 100) -> List[CoordinationCommand]:
        """Get command history for a drone or all drones."""
        if drone_id:
            return [cmd for cmd in self.command_history if cmd.drone_id == drone_id][-limit:]

        return self.command_history[-limit:]

    def get_system_status(self) -> Dict[str, Any]:
        """Get current coordination engine status."""
        return {
            "llm_initialized": self.llm_initialized,
            "active_commands": len(self.get_active_commands()),
            "total_drones_tracked": len(self.active_commands),
            "commands_last_hour": len([cmd for cmd in self.command_history
                                     if cmd.timestamp > datetime.utcnow() - timedelta(hours=1)]),
            "rule_violations": len(self.coordination_rules.rule_violations)
        }