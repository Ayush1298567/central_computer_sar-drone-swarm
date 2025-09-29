import asyncio
import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CoordinationPriority(Enum):
    """Priority levels for coordination decisions."""
    CRITICAL = 4  # Emergency situations, immediate threats
    HIGH = 3      # Mission-critical adjustments needed
    MEDIUM = 2    # Operational optimizations
    LOW = 1       # Minor adjustments

class DroneStatus(Enum):
    """Current status of a drone."""
    OFFLINE = "offline"
    ONLINE = "online"
    FLYING = "flying"
    RETURNING = "returning"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"

@dataclass
class DroneState:
    """Current state of a drone."""
    drone_id: str
    status: DroneStatus
    position: Tuple[float, float, float]  # lat, lng, alt
    battery_level: float
    heading: float
    speed: float
    mission_id: Optional[str] = None
    assigned_area: Optional[Dict] = None
    current_waypoint: Optional[int] = None
    last_update: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MissionState:
    """Current state of a mission."""
    mission_id: str
    status: str
    drones: List[DroneState] = field(default_factory=list)
    search_areas: List[Dict] = field(default_factory=list)
    discoveries: List[Dict] = field(default_factory=list)
    weather_conditions: Optional[Dict] = None
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

@dataclass
class CoordinationCommand:
    """Command to be sent to a drone."""
    drone_id: str
    command_type: str
    parameters: Dict[str, Any]
    priority: CoordinationPriority
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

class CoordinationEngine:
    """
    Multi-drone coordination engine for SAR operations.

    Handles conflict resolution, real-time adjustments, and optimal
    resource allocation across multiple drones.
    """

    def __init__(self):
        self.active_missions: Dict[str, MissionState] = {}
        self.drone_states: Dict[str, DroneState] = {}
        self.command_queue: List[CoordinationCommand] = []
        self.conflict_resolution_active = False

        # Coordination parameters
        self.min_drone_separation = 50  # meters
        self.max_mission_duration = 120  # minutes
        self.battery_reserve_threshold = 25  # percentage
        self.coverage_overlap_tolerance = 0.1  # 10% overlap allowed

        # Performance tracking
        self.coordination_history: List[Dict] = []
        self.performance_metrics: Dict[str, Any] = {}

    def register_drone(self, drone_state: DroneState) -> None:
        """Register a drone with the coordination engine."""
        self.drone_states[drone_state.drone_id] = drone_state
        logger.info(f"Drone {drone_state.drone_id} registered with coordination engine")

    def unregister_drone(self, drone_id: str) -> None:
        """Unregister a drone from the coordination engine."""
        if drone_id in self.drone_states:
            del self.drone_states[drone_id]
            logger.info(f"Drone {drone_id} unregistered from coordination engine")

    def start_mission(self, mission_state: MissionState) -> List[CoordinationCommand]:
        """Initialize coordination for a new mission."""
        self.active_missions[mission_state.mission_id] = mission_state

        commands = []

        # Assign initial search areas to drones
        for i, drone in enumerate(mission_state.drones):
            if i < len(mission_state.search_areas):
                area = mission_state.search_areas[i]

                # Generate waypoints for the assigned area
                waypoints = self._generate_search_waypoints(area)

                command = CoordinationCommand(
                    drone_id=drone.drone_id,
                    command_type="navigate_to_area",
                    parameters={
                        "waypoints": waypoints,
                        "search_area": area,
                        "search_pattern": "lawnmower",
                        "altitude": area.get("altitude", 20)
                    },
                    priority=CoordinationPriority.HIGH,
                    reason="Initial area assignment"
                )
                commands.append(command)

        logger.info(f"Mission {mission_state.mission_id} coordination initialized with {len(commands)} commands")
        return commands

    def update_drone_state(self, drone_id: str, updates: Dict) -> List[CoordinationCommand]:
        """Update drone state and trigger coordination adjustments."""
        if drone_id not in self.drone_states:
            logger.warning(f"Update received for unregistered drone {drone_id}")
            return []

        # Update drone state
        drone = self.drone_states[drone_id]
        for key, value in updates.items():
            if hasattr(drone, key):
                setattr(drone, key, value)
        drone.last_update = datetime.utcnow()

        commands = []

        # Check for coordination needs
        commands.extend(self._check_battery_levels())
        commands.extend(self._check_mission_progress())
        commands.extend(self._check_drone_separation())
        commands.extend(self._check_weather_impact())
        commands.extend(self._check_discovery_priorities())

        # Filter and prioritize commands
        commands = self._prioritize_commands(commands)

        # Log coordination event
        self._log_coordination_event("drone_update", {
            "drone_id": drone_id,
            "updates": updates,
            "commands_generated": len(commands)
        })

        return commands

    def _check_battery_levels(self) -> List[CoordinationCommand]:
        """Check battery levels and initiate return-to-home if needed."""
        commands = []

        for drone_id, drone in self.drone_states.items():
            if drone.battery_level <= self.battery_reserve_threshold:
                # Find mission for this drone
                mission_id = drone.mission_id
                if mission_id and mission_id in self.active_missions:
                    mission = self.active_missions[mission_id]

                    # Find replacement drone or adjust mission
                    available_drones = [d for d in mission.drones if d.drone_id != drone_id and d.battery_level > 50]

                    if available_drones:
                        # Reassign area to another drone
                        replacement_drone = available_drones[0]

                        command = CoordinationCommand(
                            drone_id=drone_id,
                            command_type="return_to_home",
                            parameters={"reason": "low_battery"},
                            priority=CoordinationPriority.CRITICAL,
                            reason="Battery level critically low"
                        )
                        commands.append(command)

                        # Assign area to replacement drone
                        if drone.assigned_area:
                            command = CoordinationCommand(
                                drone_id=replacement_drone.drone_id,
                                command_type="take_over_area",
                                parameters={"area": drone.assigned_area},
                                priority=CoordinationPriority.HIGH,
                                reason="Taking over area from low-battery drone"
                            )
                            commands.append(command)

                    else:
                        # No replacement available, return drone home
                        command = CoordinationCommand(
                            drone_id=drone_id,
                            command_type="return_to_home",
                            parameters={"reason": "low_battery_no_replacement"},
                            priority=CoordinationPriority.CRITICAL,
                            reason="Battery level critically low, no replacement available"
                        )
                        commands.append(command)

        return commands

    def _check_mission_progress(self) -> List[CoordinationCommand]:
        """Check mission progress and optimize resource allocation."""
        commands = []

        for mission_id, mission in self.active_missions.items():
            if mission.status != "active":
                continue

            # Calculate overall mission progress
            total_progress = sum(drone.current_waypoint or 0 for drone in mission.drones if drone.current_waypoint)
            max_waypoints = sum(len(drone.assigned_area.get("waypoints", [])) for drone in mission.drones if drone.assigned_area)

            if max_waypoints > 0:
                mission_progress = total_progress / max_waypoints
            else:
                mission_progress = 0

            # If mission is progressing slowly, optimize
            if mission_progress < 0.3 and (datetime.utcnow() - mission.start_time).total_seconds() > 1800:  # 30 minutes
                commands.extend(self._optimize_slow_mission(mission))

        return commands

    def _optimize_slow_mission(self, mission: MissionState) -> List[CoordinationCommand]:
        """Optimize resource allocation for slow-progressing missions."""
        commands = []

        # Identify underperforming drones
        underperforming_drones = []
        for drone in mission.drones:
            if drone.current_waypoint and drone.current_waypoint < 5:  # Less than 5 waypoints completed
                underperforming_drones.append(drone)

        if len(underperforming_drones) > 0:
            # Reallocate areas from slow drones to faster ones
            fast_drones = [d for d in mission.drones if d not in underperforming_drones and d.battery_level > 40]

            for slow_drone in underperforming_drones[:len(fast_drones)]:
                if fast_drones:
                    target_drone = fast_drones.pop(0)

                    if slow_drone.assigned_area:
                        # Split area between drones
                        split_areas = self._split_search_area(slow_drone.assigned_area, 2)

                        command1 = CoordinationCommand(
                            drone_id=slow_drone.drone_id,
                            command_type="update_search_area",
                            parameters={"area": split_areas[0]},
                            priority=CoordinationPriority.MEDIUM,
                            reason="Area optimization for slow mission progress"
                        )
                        commands.append(command1)

                        command2 = CoordinationCommand(
                            drone_id=target_drone.drone_id,
                            command_type="add_search_area",
                            parameters={"area": split_areas[1]},
                            priority=CoordinationPriority.MEDIUM,
                            reason="Taking additional area from slow drone"
                        )
                        commands.append(command2)

        return commands

    def _check_drone_separation(self) -> List[CoordinationCommand]:
        """Ensure drones maintain safe separation distances."""
        commands = []

        active_drones = [drone for drone in self.drone_states.values() if drone.status == DroneStatus.FLYING]

        for i, drone1 in enumerate(active_drones):
            for drone2 in active_drones[i+1:]:
                distance = self._calculate_distance(drone1.position, drone2.position)

                if distance < self.min_drone_separation:
                    # Calculate avoidance maneuver
                    avoidance_command = self._calculate_avoidance_maneuver(drone1, drone2, distance)
                    if avoidance_command:
                        commands.append(avoidance_command)

        return commands

    def _check_weather_impact(self) -> List[CoordinationCommand]:
        """Adjust mission parameters based on weather conditions."""
        commands = []

        for mission_id, mission in self.active_missions.items():
            if not mission.weather_conditions:
                continue

            wind_speed = mission.weather_conditions.get("wind_speed", 0)
            visibility = mission.weather_conditions.get("visibility", 10000)

            # High wind adjustments
            if wind_speed > 10:
                for drone in mission.drones:
                    if drone.status == DroneStatus.FLYING:
                        command = CoordinationCommand(
                            drone_id=drone.drone_id,
                            command_type="adjust_altitude",
                            parameters={
                                "altitude": max(10, drone.position[2] - 5),  # Reduce altitude
                                "reason": "high_wind"
                            },
                            priority=CoordinationPriority.HIGH,
                            reason="Reducing altitude due to high winds"
                        )
                        commands.append(command)

            # Low visibility adjustments
            if visibility < 2000:
                for drone in mission.drones:
                    if drone.status == DroneStatus.FLYING:
                        command = CoordinationCommand(
                            drone_id=drone.drone_id,
                            command_type="enable_obstacle_avoidance",
                            parameters={"sensitivity": "high"},
                            priority=CoordinationPriority.HIGH,
                            reason="Enabling obstacle avoidance due to low visibility"
                        )
                        commands.append(command)

        return commands

    def _check_discovery_priorities(self) -> List[CoordinationCommand]:
        """Adjust drone priorities based on discoveries."""
        commands = []

        for mission_id, mission in self.active_missions.items():
            high_priority_discoveries = [
                d for d in mission.discoveries
                if d.get("priority_level", 1) >= 3
            ]

            if high_priority_discoveries:
                # Find nearest available drone to investigate
                available_drones = [
                    drone for drone in mission.drones
                    if drone.status == DroneStatus.FLYING and drone.battery_level > 30
                ]

                for discovery in high_priority_discoveries[:len(available_drones)]:
                    nearest_drone = min(
                        available_drones,
                        key=lambda d: self._calculate_distance(d.position, (discovery["lat"], discovery["lng"], 0))
                    )

                    command = CoordinationCommand(
                        drone_id=nearest_drone.drone_id,
                        command_type="investigate_discovery",
                        parameters={
                            "location": {"lat": discovery["lat"], "lng": discovery["lng"]},
                            "discovery_id": discovery["id"],
                            "investigation_radius": 100  # meters
                        },
                        priority=CoordinationPriority.HIGH,
                        reason="Investigating high-priority discovery"
                    )
                    commands.append(command)

                    # Remove from available drones
                    available_drones.remove(nearest_drone)

        return commands

    def _generate_search_waypoints(self, search_area: Dict) -> List[Tuple[float, float, float]]:
        """Generate waypoints for systematic area coverage."""
        waypoints = []

        # Extract area boundaries
        coordinates = search_area.get("coordinates", [])
        if not coordinates or len(coordinates[0]) < 3:
            return waypoints

        # Simple lawnmower pattern
        min_lat, max_lat = min(c[0] for c in coordinates[0]), max(c[0] for c in coordinates[0])
        min_lng, max_lng = min(c[1] for c in coordinates[0]), max(c[1] for c in coordinates[0])

        altitude = search_area.get("altitude", 20)
        spacing = 20  # meters between passes

        # Generate parallel search lines
        current_lat = min_lat
        direction = 1

        while current_lat <= max_lat:
            if direction == 1:
                line_waypoints = [(current_lat, lng, altitude) for lng in range(int(min_lng*1000), int(max_lng*1000), int(spacing*1000/111000))]
            else:
                line_waypoints = [(current_lat, lng, altitude) for lng in range(int(max_lng*1000), int(min_lng*1000), -int(spacing*1000/111000))]

            waypoints.extend(line_waypoints)
            current_lat += spacing / 111000  # Convert meters to degrees
            direction *= -1

        return waypoints

    def _split_search_area(self, area: Dict, parts: int) -> List[Dict]:
        """Split a search area into multiple parts."""
        if parts <= 1:
            return [area]

        coordinates = area.get("coordinates", [])
        if not coordinates or len(coordinates[0]) < 3:
            return [area]

        # Simple split along the longer dimension
        min_lat, max_lat = min(c[0] for c in coordinates[0]), max(c[0] for c in coordinates[0])
        min_lng, max_lng = min(c[1] for c in coordinates[0]), max(c[1] for c in coordinates[0])

        lat_range = max_lat - min_lat
        lng_range = max_lng - min_lng

        split_areas = []

        if lat_range > lng_range:
            # Split along latitude
            split_point = min_lat + lat_range / parts
            for i in range(parts):
                part_min_lat = min_lat + i * lat_range / parts
                part_max_lat = min_lat + (i + 1) * lat_range / parts

                part_coords = [
                    [(lat, lng) for lat, lng in coordinates[0]
                     if part_min_lat <= lat <= part_max_lat]
                ]

                if part_coords[0]:
                    split_areas.append({
                        **area,
                        "coordinates": part_coords,
                        "id": f"{area.get('id', 'area')}_part_{i+1}"
                    })
        else:
            # Split along longitude
            split_point = min_lng + lng_range / parts
            for i in range(parts):
                part_min_lng = min_lng + i * lng_range / parts
                part_max_lng = min_lng + (i + 1) * lng_range / parts

                part_coords = [
                    [(lat, lng) for lat, lng in coordinates[0]
                     if part_min_lng <= lng <= part_max_lng]
                ]

                if part_coords[0]:
                    split_areas.append({
                        **area,
                        "coordinates": part_coords,
                        "id": f"{area.get('id', 'area')}_part_{i+1}"
                    })

        return split_areas

    def _calculate_distance(self, pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]) -> float:
        """Calculate 3D distance between two positions."""
        lat1, lng1, alt1 = pos1
        lat2, lng2, alt2 = pos2

        # Haversine formula for horizontal distance
        R = 6371000  # Earth radius in meters
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2) * math.sin(dlng/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        horizontal_distance = R * c

        # Add vertical distance
        vertical_distance = abs(alt2 - alt1)

        return math.sqrt(horizontal_distance**2 + vertical_distance**2)

    def _calculate_avoidance_maneuver(self, drone1: DroneState, drone2: DroneState, distance: float) -> Optional[CoordinationCommand]:
        """Calculate avoidance maneuver for two drones that are too close."""
        if distance >= self.min_drone_separation:
            return None

        # Calculate direction to move
        lat1, lng1, alt1 = drone1.position
        lat2, lng2, alt2 = drone2.position

        # Move apart along the line connecting them
        bearing = math.atan2(lng2 - lng1, lat2 - lat1)
        move_distance = (self.min_drone_separation - distance) / 2

        # Determine which drone to move (the one with more battery or lower priority)
        if drone1.battery_level > drone2.battery_level:
            move_drone = drone1
        else:
            move_drone = drone2

        # Calculate new position
        move_lat = move_drone.position[0] + math.sin(bearing) * move_distance / 111000
        move_lng = move_drone.position[1] + math.cos(bearing) * move_distance / 111000

        return CoordinationCommand(
            drone_id=move_drone.drone_id,
            command_type="adjust_position",
            parameters={
                "latitude": move_lat,
                "longitude": move_lng,
                "altitude": move_drone.position[2] + 5  # Gain altitude
            },
            priority=CoordinationPriority.HIGH,
            reason="Maintaining safe separation from other drone"
        )

    def _prioritize_commands(self, commands: List[CoordinationCommand]) -> List[CoordinationCommand]:
        """Prioritize and filter coordination commands."""
        # Sort by priority (highest first)
        prioritized = sorted(commands, key=lambda c: c.priority.value, reverse=True)

        # Remove duplicate commands for same drone
        filtered = []
        seen_drones = set()

        for command in prioritized:
            if command.drone_id not in seen_drones:
                filtered.append(command)
                seen_drones.add(command.drone_id)
            else:
                # Merge parameters if multiple commands for same drone
                existing = next(c for c in filtered if c.drone_id == command.drone_id)
                existing.parameters.update(command.parameters)

        return filtered

    def _log_coordination_event(self, event_type: str, data: Dict) -> None:
        """Log coordination events for analysis."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }

        self.coordination_history.append(event)

        # Keep only last 1000 events
        if len(self.coordination_history) > 1000:
            self.coordination_history = self.coordination_history[-1000:]

    def get_coordination_status(self, mission_id: Optional[str] = None) -> Dict:
        """Get current coordination status."""
        status = {
            "total_drones": len(self.drone_states),
            "active_missions": len(self.active_missions),
            "pending_commands": len(self.command_queue),
            "recent_events": len([e for e in self.coordination_history if (datetime.utcnow() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 300])
        }

        if mission_id and mission_id in self.active_missions:
            mission = self.active_missions[mission_id]
            status["mission"] = {
                "id": mission_id,
                "status": mission.status,
                "drone_count": len(mission.drones),
                "progress": self._calculate_mission_progress(mission)
            }

        return status

    def _calculate_mission_progress(self, mission: MissionState) -> float:
        """Calculate overall mission progress percentage."""
        if not mission.drones:
            return 0.0

        total_progress = 0
        for drone in mission.drones:
            if drone.assigned_area and drone.current_waypoint:
                max_waypoints = len(drone.assigned_area.get("waypoints", []))
                if max_waypoints > 0:
                    total_progress += drone.current_waypoint / max_waypoints

        return min(1.0, total_progress / len(mission.drones))

    async def process_emergency(self, emergency_type: str, drone_id: str, details: Dict) -> List[CoordinationCommand]:
        """Process emergency situations requiring immediate coordination response."""
        commands = []

        if emergency_type == "communication_loss":
            # Handle lost drone
            if drone_id in self.drone_states:
                drone = self.drone_states[drone_id]

                # Find nearby drones to search for lost drone
                nearby_drones = [
                    d for d in self.drone_states.values()
                    if d.drone_id != drone_id and d.status == DroneStatus.FLYING
                    and self._calculate_distance(d.position, drone.position) < 1000
                ]

                for nearby_drone in nearby_drones[:2]:  # Max 2 drones for search
                    command = CoordinationCommand(
                        drone_id=nearby_drone.drone_id,
                        command_type="search_for_lost_drone",
                        parameters={
                            "last_known_position": drone.position,
                            "search_radius": 500,
                            "search_pattern": "expanding_spiral"
                        },
                        priority=CoordinationPriority.CRITICAL,
                        reason="Searching for drone with lost communication"
                    )
                    commands.append(command)

        elif emergency_type == "critical_battery":
            # Immediate return to home
            command = CoordinationCommand(
                drone_id=drone_id,
                command_type="emergency_return",
                parameters={"immediate": True},
                priority=CoordinationPriority.CRITICAL,
                reason="Critical battery level - emergency return"
            )
            commands.append(command)

        elif emergency_type == "weather_emergency":
            # All drones return to base
            for mission_id, mission in self.active_missions.items():
                for drone in mission.drones:
                    command = CoordinationCommand(
                        drone_id=drone.drone_id,
                        command_type="emergency_return",
                        parameters={"reason": "severe_weather"},
                        priority=CoordinationPriority.CRITICAL,
                        reason="Severe weather - all drones returning to base"
                    )
                    commands.append(command)

        return commands

# Global coordination engine instance
coordination_engine = CoordinationEngine()