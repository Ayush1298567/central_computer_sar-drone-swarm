"""
Mission Planner Service for SAR Drone Operations

This service provides comprehensive mission planning capabilities including:
- Mission plan creation and validation
- Drone mission context generation
- Safety zone calculation
- Mission timeline generation
- Integration with area calculator and geometry services
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import uuid

from .area_calculator import AreaCalculator, DroneCapabilities, EnvironmentalFactors, CoverageAnalysis

logger = logging.getLogger(__name__)


class MissionType(Enum):
    """Types of SAR missions"""
    MISSING_PERSON = "missing_person"
    VEHICLE_SEARCH = "vehicle_search"
    DISASTER_RESPONSE = "disaster_response"
    MEDICAL_EMERGENCY = "medical_emergency"
    RECONNAISSANCE = "reconnaissance"
    TRAINING = "training"


class MissionPriority(Enum):
    """Mission priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class MissionStatus(Enum):
    """Mission execution status"""
    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class Coordinates:
    """Geographic coordinates"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None


@dataclass
class SearchArea:
    """Defined search area for mission"""
    center: Coordinates
    boundaries: List[Coordinates]
    area_km2: float
    terrain_type: str
    elevation_min_m: float
    elevation_max_m: float
    obstacles: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SafetyZone:
    """Safety constraints for mission"""
    no_fly_zones: List[List[Coordinates]] = field(default_factory=list)
    altitude_restrictions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    weather_minimums: Dict[str, float] = field(default_factory=dict)
    emergency_landing_sites: List[Coordinates] = field(default_factory=list)
    communication_dead_zones: List[List[Coordinates]] = field(default_factory=list)


@dataclass
class DroneAssignment:
    """Individual drone mission assignment"""
    drone_id: str
    search_zones: List[List[Coordinates]]
    flight_path: List[Coordinates]
    estimated_flight_time: timedelta
    battery_requirement: float
    altitude_profile: List[float]
    contingency_routes: List[List[Coordinates]] = field(default_factory=list)


@dataclass
class MissionTimeline:
    """Mission execution timeline"""
    preparation_time: timedelta
    deployment_time: timedelta
    search_time: timedelta
    recovery_time: timedelta
    total_duration: timedelta
    checkpoints: List[Tuple[datetime, str]] = field(default_factory=list)
    contingency_time: timedelta = field(default=timedelta(minutes=30))


@dataclass
class MissionPlan:
    """Complete mission plan specification"""
    mission_id: str
    mission_type: MissionType
    priority: MissionPriority
    status: MissionStatus
    created_at: datetime
    
    # Mission parameters
    search_area: SearchArea
    safety_zone: SafetyZone
    drone_assignments: List[DroneAssignment]
    timeline: MissionTimeline
    
    # Analysis results
    coverage_analysis: Optional[CoverageAnalysis] = None
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.0
    
    # Operational details
    command_center: Coordinates = None
    communication_plan: Dict[str, Any] = field(default_factory=dict)
    weather_requirements: Dict[str, Any] = field(default_factory=dict)
    equipment_checklist: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: str = ""
    approved_by: Optional[str] = None
    notes: str = ""


class GeometryCalculator:
    """Helper class for geometric calculations"""
    
    @staticmethod
    def calculate_distance_km(coord1: Coordinates, coord2: Coordinates) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371.0  # Earth's radius in kilometers
        
        lat1_rad = math.radians(coord1.latitude)
        lat2_rad = math.radians(coord2.latitude)
        dlat_rad = math.radians(coord2.latitude - coord1.latitude)
        dlon_rad = math.radians(coord2.longitude - coord1.longitude)
        
        a = (math.sin(dlat_rad / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def calculate_area_km2(boundary_coords: List[Coordinates]) -> float:
        """Calculate area of polygon using shoelace formula"""
        if len(boundary_coords) < 3:
            return 0.0
            
        # Convert to projected coordinates (simplified)
        n = len(boundary_coords)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += boundary_coords[i].latitude * boundary_coords[j].longitude
            area -= boundary_coords[j].latitude * boundary_coords[i].longitude
            
        area = abs(area) / 2.0
        
        # Convert to km² (rough approximation)
        return area * 111.32 * 111.32  # degrees to km conversion
    
    @staticmethod
    def generate_search_grid(
        search_area: SearchArea,
        grid_spacing_m: float,
        drone_count: int
    ) -> List[List[Coordinates]]:
        """Generate search grid patterns for drones"""
        
        # Calculate bounding box
        lats = [coord.latitude for coord in search_area.boundaries]
        lons = [coord.longitude for coord in search_area.boundaries]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Convert grid spacing to degrees (rough approximation)
        lat_step = grid_spacing_m / 111320.0  # meters to degrees latitude
        lon_step = grid_spacing_m / (111320.0 * math.cos(math.radians(search_area.center.latitude)))
        
        # Generate grid points
        grid_zones = []
        zone_id = 0
        
        lat = min_lat
        while lat <= max_lat and zone_id < drone_count:
            lon = min_lon
            zone_points = []
            
            while lon <= max_lon:
                zone_points.append(Coordinates(lat, lon))
                lon += lon_step
                
            if zone_points:
                grid_zones.append(zone_points)
                zone_id += 1
                
            lat += lat_step
            
        return grid_zones


class MissionPlannerService:
    """
    Comprehensive mission planning service for SAR drone operations.
    
    Integrates with AreaCalculator and GeometryCalculator to create
    detailed mission plans with safety validation and timeline generation.
    """
    
    def __init__(self, area_calculator: Optional[AreaCalculator] = None):
        self.area_calculator = area_calculator or AreaCalculator()
        self.geometry_calculator = GeometryCalculator()
        self.active_missions: Dict[str, MissionPlan] = {}
        
        # Default safety parameters
        self.default_safety_minimums = {
            "min_visibility_km": 3.0,
            "max_wind_speed_kmh": 25.0,
            "min_battery_percentage": 30.0,
            "min_communication_range_km": 5.0,
            "max_altitude_m": 120.0,
            "min_temperature_c": -10.0,
            "max_temperature_c": 45.0
        }

    async def create_mission_plan(
        self,
        mission_type: MissionType,
        priority: MissionPriority,
        search_area: SearchArea,
        available_drones: List[Dict[str, Any]],
        environmental_conditions: EnvironmentalFactors,
        mission_requirements: Dict[str, Any],
        created_by: str
    ) -> MissionPlan:
        """
        Create a comprehensive mission plan.
        
        Args:
            mission_type: Type of SAR mission
            priority: Mission priority level
            search_area: Defined search area
            available_drones: List of available drones with capabilities
            environmental_conditions: Current environmental conditions
            mission_requirements: Specific mission requirements
            created_by: Mission creator identifier
            
        Returns:
            Complete MissionPlan with all components
        """
        
        logger.info(f"Creating {mission_type.value} mission plan with {len(available_drones)} drones")
        
        mission_id = str(uuid.uuid4())
        
        # Extract drone capabilities
        drone_capabilities = self._extract_drone_capabilities(available_drones)
        battery_levels = [drone.get("battery_level", 1.0) for drone in available_drones]
        
        # Calculate coverage analysis
        travel_distance = mission_requirements.get("travel_distance_km", 0.0)
        time_limit = mission_requirements.get("time_limit_minutes")
        
        coverage_analysis = await self.area_calculator.calculate_searchable_area(
            drone_count=len(available_drones),
            drone_capabilities=drone_capabilities,
            environmental_factors=environmental_conditions,
            battery_levels=battery_levels,
            travel_distance_km=travel_distance,
            mission_time_limit_minutes=time_limit
        )
        
        # Generate safety zone
        safety_zone = await self._calculate_safety_zone(
            search_area,
            environmental_conditions,
            mission_requirements
        )
        
        # Create drone assignments
        drone_assignments = await self._generate_drone_assignments(
            available_drones,
            search_area,
            drone_capabilities,
            coverage_analysis
        )
        
        # Generate mission timeline
        timeline = await self._generate_mission_timeline(
            mission_type,
            search_area,
            drone_assignments,
            coverage_analysis
        )
        
        # Assess risks
        risk_assessment = await self._assess_mission_risks(
            search_area,
            environmental_conditions,
            drone_assignments,
            coverage_analysis
        )
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            coverage_analysis,
            risk_assessment,
            environmental_conditions
        )
        
        # Create mission plan
        mission_plan = MissionPlan(
            mission_id=mission_id,
            mission_type=mission_type,
            priority=priority,
            status=MissionStatus.PLANNING,
            created_at=datetime.now(),
            search_area=search_area,
            safety_zone=safety_zone,
            drone_assignments=drone_assignments,
            timeline=timeline,
            coverage_analysis=coverage_analysis,
            risk_assessment=risk_assessment,
            success_probability=success_probability,
            command_center=mission_requirements.get("command_center"),
            created_by=created_by
        )
        
        # Add operational details
        await self._add_operational_details(mission_plan, mission_requirements)
        
        # Store mission
        self.active_missions[mission_id] = mission_plan
        
        logger.info(f"Mission plan {mission_id} created successfully")
        return mission_plan

    def _extract_drone_capabilities(self, available_drones: List[Dict[str, Any]]) -> DroneCapabilities:
        """Extract average drone capabilities from available fleet"""
        
        if not available_drones:
            # Default capabilities
            return DroneCapabilities(
                max_flight_time_minutes=30.0,
                max_speed_kmh=50.0,
                max_range_km=10.0,
                camera_resolution=(1920, 1080),
                camera_fov_degrees=90.0,
                optimal_altitude_m=50.0,
                max_altitude_m=120.0,
                wind_resistance_kmh=20.0,
                battery_capacity_mah=5000,
                power_consumption_w=100.0
            )
        
        # Calculate average capabilities
        avg_flight_time = sum(drone.get("max_flight_time", 30) for drone in available_drones) / len(available_drones)
        avg_speed = sum(drone.get("max_speed_kmh", 50) for drone in available_drones) / len(available_drones)
        avg_range = sum(drone.get("max_range_km", 10) for drone in available_drones) / len(available_drones)
        
        return DroneCapabilities(
            max_flight_time_minutes=avg_flight_time,
            max_speed_kmh=avg_speed,
            max_range_km=avg_range,
            camera_resolution=(1920, 1080),  # Standard assumption
            camera_fov_degrees=90.0,
            optimal_altitude_m=50.0,
            max_altitude_m=120.0,
            wind_resistance_kmh=20.0,
            battery_capacity_mah=5000,
            power_consumption_w=100.0
        )

    async def _calculate_safety_zone(
        self,
        search_area: SearchArea,
        environmental_conditions: EnvironmentalFactors,
        mission_requirements: Dict[str, Any]
    ) -> SafetyZone:
        """Calculate safety constraints for the mission"""
        
        safety_zone = SafetyZone()
        
        # Add no-fly zones from requirements
        if "no_fly_zones" in mission_requirements:
            safety_zone.no_fly_zones = mission_requirements["no_fly_zones"]
        
        # Add altitude restrictions based on terrain and regulations
        safety_zone.altitude_restrictions = {
            "minimum_agl": 30.0,  # Above Ground Level
            "maximum_agl": 120.0,  # Regulatory limit
            "terrain_clearance": 15.0  # Minimum terrain clearance
        }
        
        # Weather minimums based on environmental conditions
        safety_zone.weather_minimums = {
            "min_visibility_km": 3.0,
            "max_wind_speed_kmh": 25.0,
            "min_temperature_c": -10.0,
            "max_temperature_c": 45.0
        }
        
        # Generate emergency landing sites
        safety_zone.emergency_landing_sites = self._generate_emergency_landing_sites(search_area)
        
        return safety_zone

    def _generate_emergency_landing_sites(self, search_area: SearchArea) -> List[Coordinates]:
        """Generate emergency landing sites within search area"""
        
        landing_sites = []
        
        # Add center point as primary landing site
        landing_sites.append(search_area.center)
        
        # Add boundary points as backup sites
        for i in range(0, len(search_area.boundaries), max(1, len(search_area.boundaries) // 4)):
            landing_sites.append(search_area.boundaries[i])
        
        return landing_sites

    async def _generate_drone_assignments(
        self,
        available_drones: List[Dict[str, Any]],
        search_area: SearchArea,
        drone_capabilities: DroneCapabilities,
        coverage_analysis: CoverageAnalysis
    ) -> List[DroneAssignment]:
        """Generate individual drone assignments"""
        
        assignments = []
        
        # Generate search grid
        grid_spacing = 500.0  # 500m grid spacing
        search_zones = self.geometry_calculator.generate_search_grid(
            search_area,
            grid_spacing,
            len(available_drones)
        )
        
        for i, drone in enumerate(available_drones):
            drone_id = drone.get("id", f"drone_{i}")
            
            # Assign search zone
            assigned_zones = [search_zones[i % len(search_zones)]] if search_zones else []
            
            # Generate flight path
            flight_path = self._generate_flight_path(assigned_zones, search_area)
            
            # Calculate flight time
            total_distance = self._calculate_path_distance(flight_path)
            estimated_time = timedelta(
                hours=total_distance / drone_capabilities.max_speed_kmh
            )
            
            # Calculate battery requirement
            battery_requirement = min(1.0, (estimated_time.total_seconds() / 3600) / 
                                   (drone_capabilities.max_flight_time_minutes / 60) + 0.2)  # 20% safety margin
            
            # Generate altitude profile
            altitude_profile = [drone_capabilities.optimal_altitude_m] * len(flight_path)
            
            assignment = DroneAssignment(
                drone_id=drone_id,
                search_zones=assigned_zones,
                flight_path=flight_path,
                estimated_flight_time=estimated_time,
                battery_requirement=battery_requirement,
                altitude_profile=altitude_profile
            )
            
            assignments.append(assignment)
        
        return assignments

    def _generate_flight_path(
        self,
        search_zones: List[List[Coordinates]],
        search_area: SearchArea
    ) -> List[Coordinates]:
        """Generate optimized flight path for drone"""
        
        if not search_zones or not search_zones[0]:
            return [search_area.center]
        
        # Simple path generation - start from first zone point
        flight_path = []
        
        for zone in search_zones:
            flight_path.extend(zone)
        
        # Add return to start
        if flight_path:
            flight_path.append(flight_path[0])
        
        return flight_path

    def _calculate_path_distance(self, flight_path: List[Coordinates]) -> float:
        """Calculate total distance of flight path"""
        
        if len(flight_path) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(flight_path) - 1):
            total_distance += self.geometry_calculator.calculate_distance_km(
                flight_path[i], flight_path[i + 1]
            )
        
        return total_distance

    async def _generate_mission_timeline(
        self,
        mission_type: MissionType,
        search_area: SearchArea,
        drone_assignments: List[DroneAssignment],
        coverage_analysis: CoverageAnalysis
    ) -> MissionTimeline:
        """Generate detailed mission timeline"""
        
        # Base preparation time varies by mission type
        prep_times = {
            MissionType.MEDICAL_EMERGENCY: timedelta(minutes=15),
            MissionType.MISSING_PERSON: timedelta(minutes=45),
            MissionType.DISASTER_RESPONSE: timedelta(minutes=60),
            MissionType.RECONNAISSANCE: timedelta(minutes=30),
            MissionType.TRAINING: timedelta(minutes=60),
            MissionType.VEHICLE_SEARCH: timedelta(minutes=45)
        }
        
        preparation_time = prep_times.get(mission_type, timedelta(minutes=45))
        
        # Deployment time based on travel distance and drone count
        deployment_time = timedelta(minutes=15 + len(drone_assignments) * 2)
        
        # Search time from coverage analysis
        search_time = timedelta(minutes=coverage_analysis.estimated_time_minutes)
        
        # Recovery time
        recovery_time = timedelta(minutes=10 + len(drone_assignments) * 2)
        
        total_duration = preparation_time + deployment_time + search_time + recovery_time
        
        # Generate checkpoints
        now = datetime.now()
        checkpoints = [
            (now + preparation_time, "Preparation Complete"),
            (now + preparation_time + deployment_time, "Drones Deployed"),
            (now + preparation_time + deployment_time + search_time * 0.25, "25% Search Complete"),
            (now + preparation_time + deployment_time + search_time * 0.5, "50% Search Complete"),
            (now + preparation_time + deployment_time + search_time * 0.75, "75% Search Complete"),
            (now + preparation_time + deployment_time + search_time, "Search Complete"),
            (now + total_duration, "Mission Complete")
        ]
        
        return MissionTimeline(
            preparation_time=preparation_time,
            deployment_time=deployment_time,
            search_time=search_time,
            recovery_time=recovery_time,
            total_duration=total_duration,
            checkpoints=checkpoints
        )

    async def _assess_mission_risks(
        self,
        search_area: SearchArea,
        environmental_conditions: EnvironmentalFactors,
        drone_assignments: List[DroneAssignment],
        coverage_analysis: CoverageAnalysis
    ) -> Dict[str, Any]:
        """Comprehensive mission risk assessment"""
        
        risks = {
            "overall_risk_level": "low",
            "risk_factors": [],
            "mitigation_strategies": [],
            "abort_conditions": [],
            "contingency_plans": []
        }
        
        # Environmental risks
        if environmental_conditions.wind_speed_kmh > 20:
            risks["risk_factors"].append("High wind conditions")
            risks["mitigation_strategies"].append("Reduce flight altitude and speed")
            
        if environmental_conditions.visibility_km < 5:
            risks["risk_factors"].append("Limited visibility")
            risks["mitigation_strategies"].append("Use GPS navigation with increased separation")
            
        # Coverage risks
        if coverage_analysis.coverage_confidence < 0.7:
            risks["risk_factors"].append("Low coverage confidence")
            risks["mitigation_strategies"].append("Increase overlap percentage")
            
        # Battery risks
        high_battery_risk = any(
            assignment.battery_requirement > 0.8 
            for assignment in drone_assignments
        )
        if high_battery_risk:
            risks["risk_factors"].append("High battery consumption")
            risks["mitigation_strategies"].append("Reduce search time or add charging stops")
            
        # Determine overall risk level
        if len(risks["risk_factors"]) == 0:
            risks["overall_risk_level"] = "low"
        elif len(risks["risk_factors"]) <= 2:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "high"
            
        # Add abort conditions
        risks["abort_conditions"] = [
            "Wind speed exceeds 30 km/h",
            "Visibility drops below 2 km",
            "Drone battery below 20%",
            "Loss of communication for more than 5 minutes"
        ]
        
        return risks

    def _calculate_success_probability(
        self,
        coverage_analysis: CoverageAnalysis,
        risk_assessment: Dict[str, Any],
        environmental_conditions: EnvironmentalFactors
    ) -> float:
        """Calculate mission success probability"""
        
        base_probability = 0.8
        
        # Adjust for coverage confidence
        base_probability *= coverage_analysis.coverage_confidence
        
        # Adjust for risk level
        risk_multipliers = {
            "low": 1.0,
            "medium": 0.9,
            "high": 0.7
        }
        base_probability *= risk_multipliers.get(risk_assessment["overall_risk_level"], 0.8)
        
        # Adjust for environmental conditions
        if environmental_conditions.weather_condition.value in ["heavy_rain", "fog"]:
            base_probability *= 0.8
        elif environmental_conditions.weather_condition.value in ["light_rain", "windy"]:
            base_probability *= 0.9
            
        return min(1.0, max(0.1, base_probability))

    async def _add_operational_details(
        self,
        mission_plan: MissionPlan,
        mission_requirements: Dict[str, Any]
    ) -> None:
        """Add operational details to mission plan"""
        
        # Communication plan
        mission_plan.communication_plan = {
            "primary_frequency": mission_requirements.get("radio_frequency", "462.5625 MHz"),
            "backup_frequency": mission_requirements.get("backup_frequency", "462.5750 MHz"),
            "check_in_interval": mission_requirements.get("check_in_minutes", 10),
            "emergency_contact": mission_requirements.get("emergency_contact", "911")
        }
        
        # Weather requirements
        mission_plan.weather_requirements = {
            "max_wind_speed": 25.0,
            "min_visibility": 3.0,
            "no_precipitation": mission_plan.mission_type in [MissionType.TRAINING]
        }
        
        # Equipment checklist
        mission_plan.equipment_checklist = [
            "Drone batteries (charged)",
            "Spare propellers",
            "First aid kit",
            "Radio communication equipment",
            "GPS devices",
            "Weather monitoring equipment",
            "Emergency landing markers",
            "Mission maps and coordinates"
        ]

    async def update_mission_status(
        self,
        mission_id: str,
        new_status: MissionStatus,
        updated_by: str,
        notes: Optional[str] = None
    ) -> MissionPlan:
        """Update mission status"""
        
        if mission_id not in self.active_missions:
            raise ValueError(f"Mission {mission_id} not found")
            
        mission = self.active_missions[mission_id]
        mission.status = new_status
        
        if notes:
            mission.notes += f"\n[{datetime.now()}] Status updated to {new_status.value} by {updated_by}: {notes}"
            
        logger.info(f"Mission {mission_id} status updated to {new_status.value}")
        return mission

    async def get_mission_plan(self, mission_id: str) -> Optional[MissionPlan]:
        """Retrieve mission plan by ID"""
        return self.active_missions.get(mission_id)

    async def list_active_missions(self) -> List[MissionPlan]:
        """List all active missions"""
        return [
            mission for mission in self.active_missions.values()
            if mission.status in [MissionStatus.PLANNING, MissionStatus.READY, MissionStatus.ACTIVE]
        ]

    async def validate_mission_plan(self, mission_plan: MissionPlan) -> Dict[str, Any]:
        """Validate mission plan for safety and feasibility"""
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check battery requirements
        for assignment in mission_plan.drone_assignments:
            if assignment.battery_requirement > 0.9:
                validation_result["warnings"].append(
                    f"Drone {assignment.drone_id} requires {assignment.battery_requirement*100:.1f}% battery"
                )
                
        # Check weather conditions
        if mission_plan.risk_assessment["overall_risk_level"] == "high":
            validation_result["warnings"].append("High risk conditions detected")
            
        # Check coverage
        if mission_plan.coverage_analysis and mission_plan.coverage_analysis.coverage_confidence < 0.6:
            validation_result["recommendations"].append("Consider adding more drones for better coverage")
            
        return validation_result