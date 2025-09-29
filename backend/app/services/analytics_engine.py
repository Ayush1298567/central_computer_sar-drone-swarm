"""
Analytics engine for mission performance analysis and insights.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.database import SessionLocal
from app.models import Mission, Drone, Discovery, DroneTelemetry

logger = logging.getLogger(__name__)


@dataclass
class MissionMetrics:
    """Mission performance metrics."""
    mission_id: str
    total_duration: float  # hours
    area_covered: float  # square meters
    discoveries_found: int
    average_discovery_confidence: float
    drone_utilization_rate: float
    mission_efficiency_score: float
    weather_impact_score: float
    recommendations: List[str]


@dataclass
class DronePerformanceMetrics:
    """Individual drone performance metrics."""
    drone_id: str
    flight_time: float  # hours
    distance_traveled: float  # meters
    battery_efficiency: float  # percentage
    discoveries_found: int
    mission_participation_rate: float
    maintenance_needed: bool
    performance_score: float


class AnalyticsEngine:
    """
    Analytics engine for processing mission data and generating insights.
    """

    def __init__(self):
        self.analysis_cache: Dict[str, Any] = {}
        self.cache_duration = timedelta(hours=1)

    async def initialize(self):
        """Initialize the analytics engine."""
        logger.info("Analytics engine initialized")

    def get_mission_analytics(self, mission_id: str) -> Optional[MissionMetrics]:
        """
        Get comprehensive analytics for a specific mission.

        Args:
            mission_id: ID of the mission to analyze

        Returns:
            MissionMetrics object or None if mission not found
        """
        try:
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if not mission:
                    return None

                # Calculate metrics
                total_duration = self._calculate_mission_duration(mission)
                area_covered = mission.area_covered
                discoveries_count = mission.discoveries_count

                # Get discovery confidence average
                discoveries = db.query(Discovery).filter(Discovery.mission_id == mission.id).all()
                avg_confidence = np.mean([d.confidence for d in discoveries]) if discoveries else 0.0

                # Get drone utilization
                mission_drones = len(mission.drones) if mission.drones else 1
                drone_utilization = min(1.0, discoveries_count / (mission_drones * 10))  # Normalize

                # Calculate efficiency score
                efficiency_score = self._calculate_efficiency_score(
                    total_duration, area_covered, discoveries_count, mission_drones
                )

                # Get weather impact
                weather_score = self._calculate_weather_impact(mission)

                # Generate recommendations
                recommendations = self._generate_mission_recommendations(
                    mission, discoveries, total_duration, efficiency_score
                )

                return MissionMetrics(
                    mission_id=mission_id,
                    total_duration=total_duration,
                    area_covered=area_covered,
                    discoveries_found=discoveries_count,
                    average_discovery_confidence=avg_confidence,
                    drone_utilization_rate=drone_utilization,
                    mission_efficiency_score=efficiency_score,
                    weather_impact_score=weather_score,
                    recommendations=recommendations
                )

        except Exception as e:
            logger.error(f"Error calculating mission analytics: {e}")
            return None

    def get_drone_performance_analytics(self, drone_id: str, days: int = 30) -> Optional[DronePerformanceMetrics]:
        """
        Get performance analytics for a specific drone.

        Args:
            drone_id: ID of the drone to analyze
            days: Number of days to analyze (default 30)

        Returns:
            DronePerformanceMetrics object or None if drone not found
        """
        try:
            with SessionLocal() as db:
                drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
                if not drone:
                    return None

                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Get telemetry data
                telemetry = db.query(DroneTelemetry).filter(
                    and_(
                        DroneTelemetry.drone_id == drone.id,
                        DroneTelemetry.timestamp >= cutoff_date
                    )
                ).all()

                if not telemetry:
                    return DronePerformanceMetrics(
                        drone_id=drone_id,
                        flight_time=0.0,
                        distance_traveled=0.0,
                        battery_efficiency=100.0,
                        discoveries_found=0,
                        mission_participation_rate=0.0,
                        maintenance_needed=False,
                        performance_score=50.0
                    )

                # Calculate flight time
                flight_time = len(telemetry) * 5 / 3600  # Assuming 5-second intervals

                # Calculate distance traveled
                positions = [(t.position_lat, t.position_lng) for t in telemetry if t.position_lat and t.position_lng]
                distance = self._calculate_total_distance(positions) if len(positions) > 1 else 0.0

                # Calculate battery efficiency
                battery_levels = [t.battery_level for t in telemetry]
                battery_efficiency = np.mean(battery_levels) if battery_levels else 100.0

                # Get discoveries found by this drone
                discoveries = db.query(Discovery).filter(
                    and_(
                        Discovery.detected_by_drone == drone_id,
                        Discovery.detected_at >= cutoff_date
                    )
                ).count()

                # Calculate mission participation rate
                total_missions = db.query(MissionDrone).filter(
                    and_(
                        MissionDrone.drone_id == drone.id,
                        MissionDrone.assigned_at >= cutoff_date
                    )
                ).count()

                participation_rate = min(1.0, total_missions / max(1, days))

                # Determine maintenance needed
                maintenance_needed = battery_efficiency < 70 or flight_time > 50  # 50 hours

                # Calculate performance score
                performance_score = self._calculate_drone_performance_score(
                    flight_time, distance, battery_efficiency, discoveries, participation_rate
                )

                return DronePerformanceMetrics(
                    drone_id=drone_id,
                    flight_time=flight_time,
                    distance_traveled=distance,
                    battery_efficiency=battery_efficiency,
                    discoveries_found=discoveries,
                    mission_participation_rate=participation_rate,
                    maintenance_needed=maintenance_needed,
                    performance_score=performance_score
                )

        except Exception as e:
            logger.error(f"Error calculating drone analytics: {e}")
            return None

    def get_system_overview_analytics(self) -> Dict[str, Any]:
        """
        Get system-wide analytics overview.

        Returns:
            Dictionary containing system analytics
        """
        try:
            with SessionLocal() as db:
                # Get basic counts
                total_missions = db.query(Mission).count()
                total_drones = db.query(Drone).count()
                total_discoveries = db.query(Discovery).count()

                # Get active missions
                active_missions = db.query(Mission).filter(
                    Mission.status.in_(["active", "ready"])
                ).count()

                # Get recent mission success rate
                recent_missions = db.query(Mission).filter(
                    Mission.created_at >= datetime.utcnow() - timedelta(days=7)
                ).all()

                completed_missions = [m for m in recent_missions if m.status == "completed"]
                success_rate = len(completed_missions) / max(1, len(recent_missions))

                # Get drone status distribution
                drone_statuses = db.query(Drone.status, func.count(Drone.id)).group_by(Drone.status).all()
                status_distribution = {status: count for status, count in drone_statuses}

                # Get discovery types distribution
                discovery_types = db.query(Discovery.discovery_type, func.count(Discovery.id)).group_by(Discovery.discovery_type).all()
                type_distribution = {dtype: count for dtype, count in discovery_types}

                # Get average mission duration
                completed_missions_with_duration = [
                    m for m in recent_missions
                    if m.actual_end_time and m.actual_start_time
                ]
                avg_duration = np.mean([
                    (m.actual_end_time - m.actual_start_time).total_seconds() / 3600
                    for m in completed_missions_with_duration
                ]) if completed_missions_with_duration else 0.0

                return {
                    "total_missions": total_missions,
                    "total_drones": total_drones,
                    "total_discoveries": total_discoveries,
                    "active_missions": active_missions,
                    "success_rate": success_rate,
                    "average_mission_duration": avg_duration,
                    "drone_status_distribution": status_distribution,
                    "discovery_type_distribution": type_distribution,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error calculating system overview: {e}")
            return {}

    def _calculate_mission_duration(self, mission: Mission) -> float:
        """Calculate total mission duration in hours."""
        if mission.actual_end_time and mission.actual_start_time:
            duration = mission.actual_end_time - mission.actual_start_time
            return duration.total_seconds() / 3600
        elif mission.estimated_duration:
            return mission.estimated_duration / 60  # Convert minutes to hours
        return 0.0

    def _calculate_efficiency_score(self, duration: float, area: float, discoveries: int, drones: int) -> float:
        """Calculate mission efficiency score (0-100)."""
        # Base score from discoveries per hour per drone
        discoveries_per_hour_per_drone = (discoveries / max(1, duration)) / max(1, drones)

        # Area coverage efficiency
        area_per_hour_per_drone = (area / max(1, duration)) / max(1, drones)

        # Normalize and combine scores
        discovery_score = min(100, discoveries_per_hour_per_drone * 20)
        area_score = min(100, (area_per_hour_per_drone / 10000) * 100)  # Normalize for 10k sqm/hour target

        return (discovery_score + area_score) / 2

    def _calculate_weather_impact(self, mission: Mission) -> float:
        """Calculate weather impact score (0-100, higher is better)."""
        if not mission.weather_conditions:
            return 75.0  # Neutral score if no weather data

        weather = mission.weather_conditions

        # Penalize high wind and poor visibility
        wind_penalty = max(0, (weather.get("wind_speed", 0) - 10) * 5)
        visibility_penalty = max(0, (10000 - weather.get("visibility", 10000)) / 100)

        return max(0, 100 - wind_penalty - visibility_penalty)

    def _generate_mission_recommendations(self, mission: Mission, discoveries: List[Discovery],
                                        duration: float, efficiency: float) -> List[str]:
        """Generate recommendations based on mission analysis."""
        recommendations = []

        if efficiency < 50:
            recommendations.append("Consider optimizing search patterns for better area coverage")

        if duration > 4:  # More than 4 hours
            recommendations.append("Long missions detected - consider breaking into multiple shorter missions")

        if len(discoveries) == 0:
            recommendations.append("No discoveries found - consider adjusting detection sensitivity or search areas")

        # Check discovery confidence
        low_confidence = [d for d in discoveries if d.confidence < 0.7]
        if len(low_confidence) > len(discoveries) * 0.3:
            recommendations.append("High number of low-confidence detections - consider improving detection algorithms")

        return recommendations

    def _calculate_total_distance(self, positions: List[tuple]) -> float:
        """Calculate total distance traveled from position list."""
        if len(positions) < 2:
            return 0.0

        distance = 0.0
        for i in range(1, len(positions)):
            # Simple Euclidean distance (for approximate calculation)
            lat1, lng1 = positions[i-1]
            lat2, lng2 = positions[i]

            # Haversine formula approximation for small distances
            dlat = abs(lat2 - lat1)
            dlng = abs(lng2 - lng1)
            distance += np.sqrt(dlat**2 + dlng**2) * 111000  # Convert degrees to meters

        return distance

    def _calculate_drone_performance_score(self, flight_time: float, distance: float,
                                         battery_efficiency: float, discoveries: int,
                                         participation_rate: float) -> float:
        """Calculate overall drone performance score (0-100)."""
        # Flight time score (0-30 points)
        flight_score = min(30, flight_time * 3)  # 10 hours = 30 points

        # Distance score (0-25 points)
        distance_score = min(25, (distance / 10000) * 25)  # 10km = 25 points

        # Battery efficiency score (0-20 points)
        battery_score = battery_efficiency * 0.2

        # Discoveries score (0-15 points)
        discovery_score = min(15, discoveries * 3)  # 5 discoveries = 15 points

        # Participation score (0-10 points)
        participation_score = participation_rate * 10

        return flight_score + distance_score + battery_score + discovery_score + participation_score


# Global analytics engine instance
analytics_engine = AnalyticsEngine()