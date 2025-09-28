"""
Mission Analytics Engine for SAR Operations.

Comprehensive mission data collection and analysis system that provides insights
for manual improvement and future AI training. Collects everything, provides
tools for analysis and improvement.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of mission events for logging and analysis."""
    MISSION_START = "mission_start"
    MISSION_END = "mission_end"
    DRONE_ASSIGNMENT = "drone_assignment"
    DRONE_TAKEOFF = "drone_takeoff"
    DRONE_LANDING = "drone_landing"
    DISCOVERY = "discovery"
    INVESTIGATION_START = "investigation_start"
    INVESTIGATION_END = "investigation_end"
    WEATHER_CHANGE = "weather_change"
    EMERGENCY = "emergency"
    COMMAND_ISSUED = "command_issued"
    COMMAND_EXECUTED = "command_executed"
    BATTERY_WARNING = "battery_warning"
    SIGNAL_LOSS = "signal_loss"
    COORDINATION_DECISION = "coordination_decision"

class MissionOutcome(Enum):
    """Possible outcomes for mission analysis."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ABORTED = "aborted"
    ONGOING = "ongoing"

@dataclass
class MissionEvent:
    """Represents a single mission event for analytics."""
    event_type: EventType
    timestamp: datetime
    mission_id: str
    drone_id: Optional[str] = None
    event_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "mission_id": self.mission_id,
            "drone_id": self.drone_id,
            "event_data": self.event_data,
            "metadata": self.metadata
        }

@dataclass
class MissionAnalysis:
    """Results of mission performance analysis."""
    mission_id: str
    duration_analysis: Dict[str, Any]
    coverage_efficiency: Dict[str, Any]
    discovery_effectiveness: Dict[str, Any]
    resource_utilization: Dict[str, Any]
    decision_quality: Dict[str, Any]
    overall_score: float
    recommendations: List[str]
    lessons_learned: List[str]

class MissionDatabase:
    """Simple in-memory mission database for analytics."""

    def __init__(self):
        self.events: List[MissionEvent] = []
        self.missions: Dict[str, Dict[str, Any]] = {}

    def store_event(self, event: MissionEvent):
        """Store a mission event."""
        self.events.append(event)

        # Keep only last 10,000 events to prevent memory issues
        if len(self.events) > 10000:
            self.events = self.events[-10000:]

    def get_mission_events(self, mission_id: str) -> List[MissionEvent]:
        """Get all events for a specific mission."""
        return [event for event in self.events if event.mission_id == mission_id]

    def get_events_by_type(self, event_type: EventType, mission_id: Optional[str] = None) -> List[MissionEvent]:
        """Get events by type, optionally filtered by mission."""
        events = [event for event in self.events if event.event_type == event_type]
        if mission_id:
            events = [event for event in events if event.mission_id == mission_id]
        return events

    def store_mission_summary(self, mission_id: str, summary: Dict[str, Any]):
        """Store mission summary data."""
        self.missions[mission_id] = summary

    def get_mission_summary(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get mission summary data."""
        return self.missions.get(mission_id)

class MissionAnalyticsEngine:
    """
    Comprehensive mission analytics engine for SAR operations.

    Collects detailed mission data and provides analysis for performance
    improvement and operator training.
    """

    def __init__(self):
        self.database = MissionDatabase()
        self.analysis_cache: Dict[str, MissionAnalysis] = {}

    def log_mission_event(
        self,
        event_type: EventType,
        mission_id: str,
        drone_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a mission event for later analysis.

        Args:
            event_type: Type of event
            mission_id: Mission identifier
            drone_id: Optional drone identifier
            event_data: Event-specific data
            metadata: Additional metadata
        """
        event = MissionEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            mission_id=mission_id,
            drone_id=drone_id,
            event_data=event_data or {},
            metadata=metadata or {}
        )

        self.database.store_event(event)
        logger.debug(f"Logged mission event: {event_type.value} for mission {mission_id}")

    def analyze_mission_performance(self, mission_id: str) -> MissionAnalysis:
        """
        Comprehensive mission performance analysis.

        Args:
            mission_id: Mission to analyze

        Returns:
            Detailed performance analysis
        """
        # Check cache first
        if mission_id in self.analysis_cache:
            cache_age = datetime.utcnow() - self.analysis_cache[mission_id].duration_analysis.get("analyzed_at", datetime.min)
            if cache_age.total_seconds() < 3600:  # Cache for 1 hour
                return self.analysis_cache[mission_id]

        # Get mission events
        events = self.database.get_mission_events(mission_id)

        if not events:
            raise ValueError(f"No events found for mission {mission_id}")

        # Perform comprehensive analysis
        analysis = MissionAnalysis(
            mission_id=mission_id,
            duration_analysis=self.analyze_mission_duration(events),
            coverage_efficiency=self.analyze_coverage_efficiency(events),
            discovery_effectiveness=self.analyze_discovery_rate(events),
            resource_utilization=self.analyze_resource_usage(events),
            decision_quality=self.analyze_decision_outcomes(events),
            overall_score=self.calculate_overall_score(events),
            recommendations=self.generate_improvement_recommendations(events),
            lessons_learned=self.extract_lessons(events)
        )

        # Cache the analysis
        self.analysis_cache[mission_id] = analysis
        return analysis

    def analyze_mission_duration(self, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze mission timing and duration efficiency."""
        if not events:
            return {"error": "No events to analyze"}

        # Find mission start and end
        start_events = [e for e in events if e.event_type == EventType.MISSION_START]
        end_events = [e for e in events if e.event_type == EventType.MISSION_END]

        if not start_events:
            return {"error": "No mission start event found"}

        start_time = start_events[0].timestamp
        end_time = end_events[0].timestamp if end_events else datetime.utcnow()

        actual_duration = (end_time - start_time).total_seconds()

        # Calculate planned vs actual duration
        mission_summary = self.database.get_mission_summary(events[0].mission_id)
        planned_duration = mission_summary.get("estimated_duration", 0) if mission_summary else 0

        duration_efficiency = (planned_duration / actual_duration * 100) if planned_duration > 0 else 0

        # Analyze phase durations
        phases = self._analyze_mission_phases(events, start_time)

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "actual_duration_minutes": actual_duration / 60,
            "planned_duration_minutes": planned_duration,
            "duration_efficiency": duration_efficiency,
            "phase_analysis": phases,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_coverage_efficiency(self, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze search area coverage efficiency."""
        mission_summary = self.database.get_mission_summary(events[0].mission_id)
        if not mission_summary:
            return {"error": "No mission summary available"}

        search_area = mission_summary.get("search_area", {})
        total_area = self._calculate_polygon_area(search_area.get("coordinates", []))

        # Calculate actual coverage based on drone paths
        drone_assignments = [e for e in events if e.event_type == EventType.DRONE_ASSIGNMENT]
        coverage_data = []

        for assignment in drone_assignments:
            drone_id = assignment.drone_id
            if drone_id:
                drone_events = [e for e in events if e.drone_id == drone_id]
                coverage = self._calculate_drone_coverage(drone_events)
                coverage_data.append({
                    "drone_id": drone_id,
                    "coverage_area": coverage
                })

        total_coverage = sum(drone["coverage_area"] for drone in coverage_data)
        coverage_percentage = (total_coverage / total_area * 100) if total_area > 0 else 0

        # Analyze coverage patterns
        coverage_patterns = self._analyze_coverage_patterns(coverage_data)

        return {
            "total_search_area_km2": total_area,
            "total_coverage_km2": total_coverage,
            "coverage_percentage": coverage_percentage,
            "drone_coverage": coverage_data,
            "coverage_patterns": coverage_patterns,
            "coverage_efficiency": coverage_percentage,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_discovery_rate(self, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze discovery effectiveness and patterns."""
        discoveries = [e for e in events if e.event_type == EventType.DISCOVERY]

        if not discoveries:
            return {
                "total_discoveries": 0,
                "discovery_rate": 0,
                "false_positive_rate": 0,
                "investigation_success_rate": 0,
                "discovery_patterns": [],
                "analyzed_at": datetime.utcnow().isoformat()
            }

        # Analyze discovery timing
        discovery_times = [d.timestamp for d in discoveries]
        discovery_intervals = []

        for i in range(1, len(discovery_times)):
            interval = (discovery_times[i] - discovery_times[i-1]).total_seconds()
            discovery_intervals.append(interval)

        avg_discovery_interval = statistics.mean(discovery_intervals) if discovery_intervals else 0

        # Analyze discovery quality
        investigation_events = [e for e in events if e.event_type == EventType.INVESTIGATION_START]
        successful_investigations = 0

        for investigation in investigation_events:
            # Check if this led to a successful outcome
            investigation_id = investigation.event_data.get("investigation_id")
            if investigation_id:
                # Look for investigation end events
                end_events = [e for e in events
                            if e.event_type == EventType.INVESTIGATION_END
                            and e.event_data.get("investigation_id") == investigation_id
                            and e.event_data.get("outcome") == "successful"]
                if end_events:
                    successful_investigations += 1

        investigation_success_rate = (successful_investigations / len(investigation_events) * 100) if investigation_events else 0

        # Analyze discovery patterns
        discovery_patterns = self._analyze_discovery_patterns(discoveries)

        return {
            "total_discoveries": len(discoveries),
            "discovery_rate_per_hour": len(discoveries) / (len(events) / 3600) if events else 0,
            "average_discovery_interval_minutes": avg_discovery_interval / 60,
            "investigation_success_rate": investigation_success_rate,
            "discovery_patterns": discovery_patterns,
            "discovery_effectiveness": investigation_success_rate,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_resource_usage(self, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze resource utilization and efficiency."""
        drone_events = defaultdict(list)

        # Group events by drone
        for event in events:
            if event.drone_id:
                drone_events[event.drone_id].append(event)

        resource_analysis = []

        for drone_id, drone_event_list in drone_events.items():
            analysis = self._analyze_drone_resource_usage(drone_id, drone_event_list)
            resource_analysis.append(analysis)

        # Overall resource metrics
        total_flight_time = sum(drone["total_flight_time_minutes"] for drone in resource_analysis)
        avg_battery_consumption = statistics.mean([drone["avg_battery_consumption"] for drone in resource_analysis]) if resource_analysis else 0
        resource_efficiency = self._calculate_resource_efficiency(resource_analysis)

        return {
            "total_flight_time_minutes": total_flight_time,
            "average_battery_consumption": avg_battery_consumption,
            "resource_efficiency": resource_efficiency,
            "drone_analysis": resource_analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_decision_outcomes(self, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze the quality and outcomes of coordination decisions."""
        coordination_events = [e for e in events if e.event_type == EventType.COORDINATION_DECISION]
        command_events = [e for e in events if e.event_type == EventType.COMMAND_ISSUED]

        if not coordination_events:
            return {
                "total_decisions": 0,
                "decision_success_rate": 0,
                "average_response_time": 0,
                "decision_patterns": [],
                "analyzed_at": datetime.utcnow().isoformat()
            }

        # Analyze decision success rates
        successful_decisions = 0
        response_times = []

        for coord_event in coordination_events:
            decision_id = coord_event.event_data.get("decision_id")
            decision_time = coord_event.timestamp

            # Look for corresponding command execution
            command_event = next(
                (e for e in command_events
                 if e.event_data.get("decision_id") == decision_id),
                None
            )

            if command_event:
                response_time = (command_event.timestamp - decision_time).total_seconds()
                response_times.append(response_time)

                # Check if command was executed successfully
                execution_events = [e for e in events
                                  if e.event_type == EventType.COMMAND_EXECUTED
                                  and e.event_data.get("decision_id") == decision_id]

                if execution_events:
                    successful_decisions += 1

        success_rate = (successful_decisions / len(coordination_events) * 100) if coordination_events else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0

        # Analyze decision patterns
        decision_patterns = self._analyze_decision_patterns(coordination_events)

        return {
            "total_decisions": len(coordination_events),
            "decision_success_rate": success_rate,
            "average_response_time_seconds": avg_response_time,
            "decision_patterns": decision_patterns,
            "decision_quality": success_rate,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def calculate_overall_score(self, events: List[MissionEvent]) -> float:
        """Calculate overall mission performance score."""
        try:
            duration_analysis = self.analyze_mission_duration(events)
            coverage_analysis = self.analyze_coverage_efficiency(events)
            discovery_analysis = self.analyze_discovery_rate(events)
            resource_analysis = self.analyze_resource_usage(events)
            decision_analysis = self.analyze_decision_outcomes(events)

            # Weighted scoring
            duration_score = min(duration_analysis.get("duration_efficiency", 0) / 100, 1.0) if duration_analysis.get("duration_efficiency", 0) > 0 else 0.5
            coverage_score = min(coverage_analysis.get("coverage_percentage", 0) / 100, 1.0)
            discovery_score = discovery_analysis.get("investigation_success_rate", 0) / 100
            resource_score = resource_analysis.get("resource_efficiency", 0.5)
            decision_score = decision_analysis.get("decision_success_rate", 0) / 100

            # Weighted average
            overall_score = (
                duration_score * 0.2 +
                coverage_score * 0.3 +
                discovery_score * 0.3 +
                resource_score * 0.1 +
                decision_score * 0.1
            )

            return min(overall_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.5  # Default neutral score

    def generate_improvement_recommendations(self, events: List[MissionEvent]) -> List[str]:
        """Generate specific recommendations for improvement."""
        recommendations = []

        try:
            analysis = self.analyze_mission_performance(events[0].mission_id) if events else None

            if not analysis:
                return ["Insufficient data for recommendations"]

            # Duration-based recommendations
            duration_eff = analysis.duration_analysis.get("duration_efficiency", 100)
            if duration_eff < 80:
                recommendations.append(
                    f"Mission duration was {100-duration_eff:.1f}% longer than planned - consider optimizing flight paths and reducing unnecessary maneuvers"
                )

            # Coverage-based recommendations
            coverage_pct = analysis.coverage_efficiency.get("coverage_percentage", 100)
            if coverage_pct < 85:
                recommendations.append(
                    f"Search area coverage was only {coverage_pct:.1f}% - consider adjusting search patterns or increasing drone density"
                )

            # Discovery-based recommendations
            discovery_success = analysis.discovery_effectiveness.get("investigation_success_rate", 100)
            if discovery_success < 70:
                recommendations.append(
                    f"Investigation success rate was {discovery_success:.1f}% - improve discovery validation before deploying ground teams"
                )

            # Resource-based recommendations
            resource_eff = analysis.resource_utilization.get("resource_efficiency", 0.5)
            if resource_eff < 0.7:
                recommendations.append(
                    "Resource utilization could be improved - consider better coordination between drones and optimized flight planning"
                )

            # Decision-based recommendations
            decision_success = analysis.decision_quality.get("decision_success_rate", 100)
            if decision_success < 85:
                recommendations.append(
                    f"Decision success rate was {decision_success:.1f}% - review coordination logic and consider additional training scenarios"
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations due to analysis error")

        return recommendations[:5]  # Limit to top 5 recommendations

    def extract_lessons(self, events: List[MissionEvent]) -> List[str]:
        """Extract lessons learned from mission events."""
        lessons = []

        try:
            # Look for patterns in successful vs unsuccessful events
            successful_events = []
            unsuccessful_events = []

            for event in events:
                if event.event_type == EventType.DISCOVERY:
                    outcome = event.event_data.get("outcome", "unknown")
                    if outcome == "successful":
                        successful_events.append(event)
                    elif outcome == "false_positive":
                        unsuccessful_events.append(event)

            # Extract timing patterns
            if successful_events:
                avg_time_to_discovery = self._calculate_avg_time_between_events(
                    [e.timestamp for e in events if e.event_type == EventType.MISSION_START],
                    [e.timestamp for e in successful_events]
                )

                if avg_time_to_discovery:
                    lessons.append(
                        f"Successful discoveries typically occurred after {avg_time_to_discovery:.1f} minutes of search time"
                    )

            # Extract environmental patterns
            weather_events = [e for e in events if e.event_type == EventType.WEATHER_CHANGE]
            if weather_events:
                weather_patterns = self._analyze_weather_impact(weather_events, successful_events)
                lessons.extend(weather_patterns)

            # Extract decision patterns
            coordination_events = [e for e in events if e.event_type == EventType.COORDINATION_DECISION]
            if coordination_events:
                decision_patterns = self._analyze_coordination_patterns(coordination_events)
                lessons.extend(decision_patterns)

        except Exception as e:
            logger.error(f"Error extracting lessons: {e}")

        return lessons[:5]  # Limit to top 5 lessons

    def create_mission_replay(self, mission_id: str) -> Dict[str, Any]:
        """Create detailed mission replay for training and analysis."""
        events = self.database.get_mission_events(mission_id)

        if not events:
            return {"error": "No events available for replay"}

        # Create timeline
        timeline = self._create_timeline(events)

        # Identify decision points
        decision_points = self._identify_decision_points(events)

        # Suggest alternative strategies
        alternative_strategies = self._suggest_alternatives(events)

        # Extract lessons learned
        lessons_learned = self.extract_lessons(events)

        return {
            "mission_id": mission_id,
            "mission_timeline": timeline,
            "decision_points": decision_points,
            "alternative_strategies": alternative_strategies,
            "lessons_learned": lessons_learned,
            "created_at": datetime.utcnow().isoformat()
        }

    def _analyze_mission_phases(self, events: List[MissionEvent], start_time: datetime) -> Dict[str, Any]:
        """Analyze different phases of the mission."""
        phases = {}

        # Define phase transitions
        takeoff_events = [e for e in events if e.event_type == EventType.DRONE_TAKEOFF]
        discovery_events = [e for e in events if e.event_type == EventType.DISCOVERY]
        end_events = [e for e in events if e.event_type == EventType.MISSION_END]

        if takeoff_events:
            first_takeoff = min(e.timestamp for e in takeoff_events)
            phases["planning_to_execution"] = (first_takeoff - start_time).total_seconds() / 60

        if discovery_events:
            first_discovery = min(e.timestamp for e in discovery_events)
            if takeoff_events:
                first_takeoff = min(e.timestamp for e in takeoff_events)
                phases["execution_to_discovery"] = (first_discovery - first_takeoff).total_seconds() / 60

        if end_events:
            end_time = end_events[0].timestamp
            if discovery_events:
                last_discovery = max(e.timestamp for e in discovery_events)
                phases["last_discovery_to_end"] = (end_time - last_discovery).total_seconds() / 60
            else:
                phases["execution_to_end"] = (end_time - start_time).total_seconds() / 60

        return phases

    def _calculate_polygon_area(self, coordinates: List[List[float]]) -> float:
        """Calculate area of a polygon in square kilometers."""
        if len(coordinates) < 3:
            return 0.0

        # Simple polygon area calculation using shoelace formula
        # In production, use proper geographic libraries
        area = 0.0
        j = len(coordinates) - 1

        for i in range(len(coordinates)):
            coord1 = coordinates[i]
            coord2 = coordinates[j]
            area += coord1[0] * coord2[1]
            area -= coord2[0] * coord1[1]
            j = i

        area = abs(area) / 2.0

        # Rough conversion to km² (this is approximate)
        # In production, use proper geodesic calculations
        return area * 111 * 111  # Rough conversion factor

    def _calculate_drone_coverage(self, drone_events: List[MissionEvent]) -> float:
        """Calculate area covered by a single drone."""
        # Simplified coverage calculation
        # In production, this would use actual flight path data

        takeoff_events = [e for e in drone_events if e.event_type == EventType.DRONE_TAKEOFF]
        landing_events = [e for e in drone_events if e.event_type == EventType.DRONE_LANDING]

        if not takeoff_events or not landing_events:
            return 0.0

        flight_time = (landing_events[0].timestamp - takeoff_events[0].timestamp).total_seconds()

        # Assume average coverage rate of 0.1 km² per minute
        # In production, this would be calculated from actual flight paths
        coverage_rate = 0.1  # km² per minute
        return flight_time / 60 * coverage_rate

    def _analyze_coverage_patterns(self, coverage_data: List[Dict]) -> List[str]:
        """Analyze patterns in area coverage."""
        patterns = []

        if not coverage_data:
            return patterns

        coverage_values = [drone["coverage_area"] for drone in coverage_data]
        avg_coverage = statistics.mean(coverage_values)
        std_coverage = statistics.stdev(coverage_values) if len(coverage_values) > 1 else 0

        if std_coverage / avg_coverage > 0.3:  # High variance
            patterns.append("High variance in drone coverage - consider more balanced area assignments")
        elif avg_coverage < 0.5:
            patterns.append("Low overall coverage - consider optimizing search patterns")

        return patterns

    def _analyze_discovery_patterns(self, discoveries: List[MissionEvent]) -> List[str]:
        """Analyze patterns in discoveries."""
        patterns = []

        if len(discoveries) < 2:
            return patterns

        # Analyze discovery clustering
        discovery_times = sorted([d.timestamp for d in discoveries])
        intervals = [(discovery_times[i+1] - discovery_times[i]).total_seconds() / 60
                    for i in range(len(discovery_times)-1)]

        avg_interval = statistics.mean(intervals)

        if avg_interval < 10:  # Discoveries very close together
            patterns.append("Discoveries clustered closely - may indicate high-probability area")
        elif avg_interval > 60:  # Discoveries far apart
            patterns.append("Discoveries spread out - may need to adjust search intensity")

        return patterns

    def _analyze_drone_resource_usage(self, drone_id: str, events: List[MissionEvent]) -> Dict[str, Any]:
        """Analyze resource usage for a single drone."""
        battery_events = [e for e in events if e.event_type == EventType.BATTERY_WARNING]
        flight_events = [e for e in events if e.event_type in [EventType.DRONE_TAKEOFF, EventType.DRONE_LANDING]]

        total_flight_time = 0
        battery_warnings = len(battery_events)

        if len(flight_events) >= 2:
            for i in range(0, len(flight_events), 2):
                if i + 1 < len(flight_events):
                    flight_time = (flight_events[i+1].timestamp - flight_events[i].timestamp).total_seconds()
                    total_flight_time += flight_time

        avg_battery_consumption = 100 / (total_flight_time / 3600) if total_flight_time > 0 else 0

        return {
            "drone_id": drone_id,
            "total_flight_time_minutes": total_flight_time / 60,
            "battery_warnings": battery_warnings,
            "avg_battery_consumption": avg_battery_consumption
        }

    def _calculate_resource_efficiency(self, drone_analysis: List[Dict]) -> float:
        """Calculate overall resource efficiency."""
        if not drone_analysis:
            return 0.0

        # Simple efficiency metric based on flight time vs warnings
        total_flight_time = sum(drone["total_flight_time_minutes"] for drone in drone_analysis)
        total_warnings = sum(drone["battery_warnings"] for drone in drone_analysis)

        if total_flight_time == 0:
            return 0.0

        # Efficiency decreases with more warnings
        efficiency = total_flight_time / (total_flight_time + total_warnings * 10)
        return min(efficiency, 1.0)

    def _analyze_decision_patterns(self, coordination_events: List[MissionEvent]) -> List[str]:
        """Analyze patterns in coordination decisions."""
        patterns = []

        if len(coordination_events) < 3:
            return patterns

        # Analyze decision frequency
        decision_times = sorted([e.timestamp for e in coordination_events])
        intervals = [(decision_times[i+1] - decision_times[i]).total_seconds() / 60
                    for i in range(len(decision_times)-1)]

        avg_interval = statistics.mean(intervals)

        if avg_interval < 5:  # Very frequent decisions
            patterns.append("High frequency of coordination decisions - may indicate reactive rather than proactive coordination")
        elif avg_interval > 30:  # Infrequent decisions
            patterns.append("Low frequency of coordination decisions - may be missing optimization opportunities")

        return patterns

    def _create_timeline(self, events: List[MissionEvent]) -> List[Dict[str, Any]]:
        """Create a timeline of mission events."""
        timeline = []

        for event in sorted(events, key=lambda e: e.timestamp):
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "drone_id": event.drone_id,
                "description": self._get_event_description(event),
                "data": event.event_data
            })

        return timeline

    def _identify_decision_points(self, events: List[MissionEvent]) -> List[Dict[str, Any]]:
        """Identify key decision points in the mission."""
        decision_points = []

        # Key decision events
        key_events = [
            EventType.DISCOVERY,
            EventType.EMERGENCY,
            EventType.WEATHER_CHANGE,
            EventType.BATTERY_WARNING,
            EventType.SIGNAL_LOSS
        ]

        for event in events:
            if event.event_type in key_events:
                decision_points.append({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "description": self._get_event_description(event),
                    "required_action": self._get_required_action(event),
                    "context": event.event_data
                })

        return decision_points

    def _suggest_alternatives(self, events: List[MissionEvent]) -> List[Dict[str, Any]]:
        """Suggest alternative strategies based on mission events."""
        alternatives = []

        # Analyze if different search patterns might have been better
        discoveries = [e for e in events if e.event_type == EventType.DISCOVERY]

        if len(discoveries) < 2:
            alternatives.append({
                "type": "search_pattern",
                "description": "Consider different search patterns for better coverage",
                "rationale": "Limited discoveries may indicate suboptimal search strategy"
            })

        # Analyze if different resource allocation might have helped
        coordination_events = [e for e in events if e.event_type == EventType.COORDINATION_DECISION]

        if len(coordination_events) > 10:  # Many coordination events
            alternatives.append({
                "type": "resource_allocation",
                "description": "Consider more proactive resource allocation",
                "rationale": "High number of coordination events suggests reactive management"
            })

        return alternatives

    def _get_event_description(self, event: MissionEvent) -> str:
        """Get human-readable description of an event."""
        descriptions = {
            EventType.MISSION_START: "Mission started",
            EventType.MISSION_END: "Mission completed",
            EventType.DRONE_ASSIGNMENT: f"Drone {event.drone_id} assigned to area",
            EventType.DRONE_TAKEOFF: f"Drone {event.drone_id} took off",
            EventType.DRONE_LANDING: f"Drone {event.drone_id} landed",
            EventType.DISCOVERY: f"Discovery made: {event.event_data.get('object_type', 'unknown')}",
            EventType.INVESTIGATION_START: "Investigation initiated",
            EventType.INVESTIGATION_END: "Investigation completed",
            EventType.WEATHER_CHANGE: f"Weather changed: {event.event_data.get('condition', 'unknown')}",
            EventType.EMERGENCY: f"Emergency: {event.event_data.get('type', 'unknown')}",
            EventType.COMMAND_ISSUED: f"Command issued to drone {event.drone_id}",
            EventType.COMMAND_EXECUTED: f"Command executed by drone {event.drone_id}",
            EventType.BATTERY_WARNING: f"Low battery warning for drone {event.drone_id}",
            EventType.SIGNAL_LOSS: f"Signal loss with drone {event.drone_id}",
            EventType.COORDINATION_DECISION: "Coordination decision made"
        }

        return descriptions.get(event.event_type, f"Event: {event.event_type.value}")

    def _get_required_action(self, event: MissionEvent) -> str:
        """Get required action for a decision point."""
        actions = {
            EventType.DISCOVERY: "Investigate discovery",
            EventType.EMERGENCY: "Implement emergency protocols",
            EventType.WEATHER_CHANGE: "Adjust for new weather conditions",
            EventType.BATTERY_WARNING: "Consider drone return or battery management",
            EventType.SIGNAL_LOSS: "Reestablish communication or initiate recovery"
        }

        return actions.get(event.event_type, "Assess situation and determine appropriate response")

    def _calculate_avg_time_between_events(self, start_events: List[datetime], end_events: List[datetime]) -> Optional[float]:
        """Calculate average time between start and end events."""
        if not start_events or not end_events or len(start_events) != len(end_events):
            return None

        start_time = min(start_events)
        intervals = [(end_time - start_time).total_seconds() / 60 for end_time in end_events]

        return statistics.mean(intervals)

    def _analyze_weather_impact(self, weather_events: List[MissionEvent], successful_events: List[MissionEvent]) -> List[str]:
        """Analyze impact of weather on mission success."""
        lessons = []

        if not weather_events or not successful_events:
            return lessons

        # Simple analysis - could be much more sophisticated
        weather_changes = len(weather_events)
        successful_discoveries = len(successful_events)

        if weather_changes > 0 and successful_discoveries == 0:
            lessons.append("Weather changes may have impacted discovery success - monitor weather more closely")

        return lessons

    def _analyze_coordination_patterns(self, coordination_events: List[MissionEvent]) -> List[str]:
        """Analyze patterns in coordination decisions."""
        lessons = []

        if len(coordination_events) < 2:
            return lessons

        # Analyze response patterns
        decision_types = [e.event_data.get("decision_type", "unknown") for e in coordination_events]

        if decision_types.count("emergency") > len(decision_types) * 0.3:
            lessons.append("High proportion of emergency decisions - improve proactive situation awareness")

        return lessons

    def get_system_status(self) -> Dict[str, Any]:
        """Get current analytics engine status."""
        return {
            "total_events_stored": len(self.database.events),
            "total_missions_tracked": len(self.database.missions),
            "analysis_cache_size": len(self.analysis_cache),
            "last_event_timestamp": self.database.events[-1].timestamp.isoformat() if self.database.events else None
        }