"""
Area Calculator Service for SAR Drone Operations

This service provides comprehensive area calculation capabilities including:
- Coverage analysis based on drone capabilities
- Environmental impact calculations
- Performance optimization
- Confidence assessment and metrics
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TerrainType(Enum):
    """Terrain types affecting search operations"""
    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"
    FOREST = "forest"
    URBAN = "urban"
    WATER = "water"


class WeatherCondition(Enum):
    """Weather conditions affecting drone performance"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    WINDY = "windy"
    FOG = "fog"


@dataclass
class DroneCapabilities:
    """Drone performance specifications"""
    max_flight_time_minutes: float
    max_speed_kmh: float
    max_range_km: float
    camera_resolution: Tuple[int, int]
    camera_fov_degrees: float
    optimal_altitude_m: float
    max_altitude_m: float
    wind_resistance_kmh: float
    battery_capacity_mah: int
    power_consumption_w: float


@dataclass
class EnvironmentalFactors:
    """Environmental conditions affecting search operations"""
    terrain_type: TerrainType
    weather_condition: WeatherCondition
    wind_speed_kmh: float
    visibility_km: float
    temperature_c: float
    altitude_m: float
    obstacles_density: float  # 0.0 to 1.0


@dataclass
class CoverageAnalysis:
    """Results of coverage capability analysis"""
    total_searchable_area_km2: float
    effective_coverage_area_km2: float
    coverage_confidence: float  # 0.0 to 1.0
    estimated_time_minutes: float
    recommended_drone_count: int
    coverage_overlap_percentage: float
    search_pattern_efficiency: float
    environmental_impact_factor: float
    battery_usage_percentage: float
    risk_assessment: str


@dataclass
class PerformanceMetrics:
    """Drone performance tracking metrics"""
    actual_coverage_km2: float
    planned_coverage_km2: float
    efficiency_ratio: float
    battery_consumption_rate: float
    average_speed_kmh: float
    altitude_variance_m: float
    detection_accuracy: float
    mission_completion_time: timedelta
    weather_impact_factor: float


class AreaCalculator:
    """
    Advanced area calculation service for SAR drone operations.
    
    Provides comprehensive analysis of searchable areas based on:
    - Drone capabilities and performance
    - Environmental conditions
    - Mission requirements
    - Historical performance data
    """

    def __init__(self):
        self.performance_history: List[PerformanceMetrics] = []
        self.terrain_multipliers = {
            TerrainType.FLAT: 1.0,
            TerrainType.HILLY: 0.8,
            TerrainType.MOUNTAINOUS: 0.6,
            TerrainType.FOREST: 0.7,
            TerrainType.URBAN: 0.9,
            TerrainType.WATER: 1.1
        }
        self.weather_multipliers = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.CLOUDY: 0.9,
            WeatherCondition.LIGHT_RAIN: 0.7,
            WeatherCondition.HEAVY_RAIN: 0.3,
            WeatherCondition.WINDY: 0.6,
            WeatherCondition.FOG: 0.4
        }

    async def calculate_searchable_area(
        self,
        drone_count: int,
        drone_capabilities: DroneCapabilities,
        environmental_factors: EnvironmentalFactors,
        battery_levels: List[float],
        travel_distance_km: float,
        mission_time_limit_minutes: Optional[float] = None
    ) -> CoverageAnalysis:
        """
        Calculate total searchable area based on drone fleet capabilities.
        
        Args:
            drone_count: Number of available drones
            drone_capabilities: Specifications of drone fleet
            environmental_factors: Current environmental conditions
            battery_levels: Current battery levels for each drone (0.0 to 1.0)
            travel_distance_km: Distance to search area
            mission_time_limit_minutes: Optional time constraint
            
        Returns:
            CoverageAnalysis with detailed area calculations
        """
        logger.info(f"Calculating searchable area for {drone_count} drones")

        # Calculate environmental impact
        terrain_factor = self.terrain_multipliers[environmental_factors.terrain_type]
        weather_factor = self.weather_multipliers[environmental_factors.weather_condition]
        wind_factor = self._calculate_wind_impact(
            environmental_factors.wind_speed_kmh,
            drone_capabilities.wind_resistance_kmh
        )
        
        environmental_impact = terrain_factor * weather_factor * wind_factor
        
        # Calculate effective flight time per drone
        avg_battery = sum(battery_levels) / len(battery_levels) if battery_levels else 1.0
        travel_time = (travel_distance_km / drone_capabilities.max_speed_kmh) * 60 * 2  # round trip
        
        available_flight_time = (
            drone_capabilities.max_flight_time_minutes * avg_battery - travel_time
        )
        
        if mission_time_limit_minutes:
            available_flight_time = min(available_flight_time, mission_time_limit_minutes)
            
        # Calculate coverage per drone
        coverage_per_drone = self._calculate_single_drone_coverage(
            drone_capabilities,
            environmental_factors,
            available_flight_time,
            environmental_impact
        )
        
        # Calculate total coverage with overlap consideration
        overlap_factor = self._calculate_overlap_factor(drone_count)
        total_coverage = coverage_per_drone * drone_count * overlap_factor
        
        # Calculate confidence based on conditions
        confidence = self._calculate_coverage_confidence(
            environmental_factors,
            drone_capabilities,
            avg_battery
        )
        
        # Optimize drone count recommendation
        recommended_count = self._optimize_drone_count(
            total_coverage,
            drone_capabilities,
            environmental_factors
        )
        
        return CoverageAnalysis(
            total_searchable_area_km2=total_coverage,
            effective_coverage_area_km2=total_coverage * confidence,
            coverage_confidence=confidence,
            estimated_time_minutes=available_flight_time,
            recommended_drone_count=recommended_count,
            coverage_overlap_percentage=(1 - overlap_factor) * 100,
            search_pattern_efficiency=environmental_impact,
            environmental_impact_factor=environmental_impact,
            battery_usage_percentage=(1 - avg_battery) * 100,
            risk_assessment=self._assess_mission_risk(environmental_factors, avg_battery)
        )

    def _calculate_single_drone_coverage(
        self,
        capabilities: DroneCapabilities,
        environment: EnvironmentalFactors,
        flight_time_minutes: float,
        environmental_impact: float
    ) -> float:
        """Calculate coverage area for a single drone"""
        
        # Calculate effective speed considering environmental factors
        effective_speed = capabilities.max_speed_kmh * environmental_impact
        
        # Calculate camera footprint at optimal altitude
        altitude = min(capabilities.optimal_altitude_m, capabilities.max_altitude_m)
        fov_radians = math.radians(capabilities.camera_fov_degrees)
        
        # Camera footprint calculation
        footprint_width = 2 * altitude * math.tan(fov_radians / 2) / 1000  # km
        
        # Distance covered in available time
        distance_km = (effective_speed * flight_time_minutes) / 60
        
        # Coverage area (simplified grid pattern)
        coverage_area = distance_km * footprint_width * 0.8  # 80% efficiency factor
        
        return max(0, coverage_area)

    def _calculate_wind_impact(self, wind_speed: float, wind_resistance: float) -> float:
        """Calculate wind impact factor on drone performance"""
        if wind_speed <= wind_resistance:
            return 1.0 - (wind_speed / wind_resistance) * 0.3
        else:
            # Severe wind conditions
            return max(0.1, 1.0 - (wind_speed / wind_resistance))

    def _calculate_overlap_factor(self, drone_count: int) -> float:
        """Calculate overlap reduction factor for multiple drones"""
        if drone_count <= 1:
            return 1.0
        
        # Diminishing returns with more drones due to coordination overhead
        base_efficiency = 0.85  # 15% overlap for coordination
        efficiency_reduction = (drone_count - 1) * 0.02  # 2% reduction per additional drone
        
        return max(0.5, base_efficiency - efficiency_reduction)

    def _calculate_coverage_confidence(
        self,
        environment: EnvironmentalFactors,
        capabilities: DroneCapabilities,
        battery_level: float
    ) -> float:
        """Calculate confidence level for coverage estimate"""
        
        base_confidence = 0.9
        
        # Environmental factors
        if environment.weather_condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.FOG]:
            base_confidence -= 0.3
        elif environment.weather_condition in [WeatherCondition.LIGHT_RAIN, WeatherCondition.WINDY]:
            base_confidence -= 0.1
            
        if environment.visibility_km < 5.0:
            base_confidence -= 0.2
            
        # Battery factor
        if battery_level < 0.5:
            base_confidence -= 0.1
        elif battery_level < 0.3:
            base_confidence -= 0.2
            
        # Terrain complexity
        if environment.terrain_type in [TerrainType.MOUNTAINOUS, TerrainType.FOREST]:
            base_confidence -= 0.1
            
        return max(0.1, min(1.0, base_confidence))

    def _optimize_drone_count(
        self,
        current_coverage: float,
        capabilities: DroneCapabilities,
        environment: EnvironmentalFactors
    ) -> int:
        """Recommend optimal drone count for mission"""
        
        # Base recommendation on coverage efficiency
        if current_coverage < 1.0:  # Less than 1 km²
            return 1
        elif current_coverage < 5.0:
            return 2
        elif current_coverage < 15.0:
            return 3
        elif current_coverage < 30.0:
            return 4
        else:
            return min(6, int(current_coverage / 8) + 1)

    def _assess_mission_risk(
        self,
        environment: EnvironmentalFactors,
        battery_level: float
    ) -> str:
        """Assess overall mission risk level"""
        
        risk_factors = []
        
        if battery_level < 0.3:
            risk_factors.append("Low battery levels")
            
        if environment.weather_condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.FOG]:
            risk_factors.append("Poor weather conditions")
            
        if environment.wind_speed_kmh > 25:
            risk_factors.append("High wind speeds")
            
        if environment.visibility_km < 2.0:
            risk_factors.append("Limited visibility")
            
        if environment.terrain_type == TerrainType.MOUNTAINOUS:
            risk_factors.append("Challenging terrain")
            
        if not risk_factors:
            return "Low risk - Optimal conditions for search operation"
        elif len(risk_factors) <= 2:
            return f"Moderate risk - {', '.join(risk_factors)}"
        else:
            return f"High risk - Multiple challenges: {', '.join(risk_factors)}"

    async def analyze_drone_performance(
        self,
        drone_id: str,
        actual_coverage: float,
        planned_coverage: float,
        mission_duration: timedelta,
        environmental_conditions: EnvironmentalFactors
    ) -> PerformanceMetrics:
        """
        Analyze individual drone performance against predictions.
        
        Args:
            drone_id: Unique drone identifier
            actual_coverage: Actual area covered (km²)
            planned_coverage: Planned area coverage (km²)
            mission_duration: Actual mission duration
            environmental_conditions: Conditions during mission
            
        Returns:
            PerformanceMetrics with detailed analysis
        """
        logger.info(f"Analyzing performance for drone {drone_id}")
        
        efficiency_ratio = actual_coverage / planned_coverage if planned_coverage > 0 else 0
        
        # Calculate weather impact factor
        weather_impact = self.weather_multipliers[environmental_conditions.weather_condition]
        
        metrics = PerformanceMetrics(
            actual_coverage_km2=actual_coverage,
            planned_coverage_km2=planned_coverage,
            efficiency_ratio=efficiency_ratio,
            battery_consumption_rate=0.0,  # To be calculated from telemetry
            average_speed_kmh=0.0,  # To be calculated from telemetry
            altitude_variance_m=0.0,  # To be calculated from telemetry
            detection_accuracy=0.0,  # To be updated from mission results
            mission_completion_time=mission_duration,
            weather_impact_factor=weather_impact
        )
        
        # Store for learning
        self.performance_history.append(metrics)
        
        return metrics

    async def calculate_environmental_impact(
        self,
        environment: EnvironmentalFactors,
        drone_capabilities: DroneCapabilities
    ) -> Dict[str, float]:
        """
        Calculate detailed environmental impact on drone operations.
        
        Returns:
            Dictionary with impact factors for different aspects
        """
        
        impacts = {
            "terrain_impact": self.terrain_multipliers[environment.terrain_type],
            "weather_impact": self.weather_multipliers[environment.weather_condition],
            "wind_impact": self._calculate_wind_impact(
                environment.wind_speed_kmh,
                drone_capabilities.wind_resistance_kmh
            ),
            "visibility_impact": min(1.0, environment.visibility_km / 10.0),
            "altitude_impact": 1.0 - (environment.altitude_m / 3000.0) * 0.2,
            "obstacle_impact": 1.0 - environment.obstacles_density * 0.3
        }
        
        # Calculate composite impact
        impacts["composite_impact"] = (
            impacts["terrain_impact"] *
            impacts["weather_impact"] *
            impacts["wind_impact"] *
            impacts["visibility_impact"] *
            impacts["altitude_impact"] *
            impacts["obstacle_impact"]
        )
        
        return impacts

    async def optimize_coverage_pattern(
        self,
        search_area_km2: float,
        drone_count: int,
        drone_capabilities: DroneCapabilities,
        priority_zones: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Optimize search coverage pattern for maximum efficiency.
        
        Args:
            search_area_km2: Total area to search
            drone_count: Available drones
            drone_capabilities: Drone specifications
            priority_zones: Optional high-priority search zones
            
        Returns:
            Optimized coverage pattern recommendations
        """
        
        # Calculate optimal grid size based on camera capabilities
        altitude = drone_capabilities.optimal_altitude_m
        fov_radians = math.radians(drone_capabilities.camera_fov_degrees)
        footprint_width_m = 2 * altitude * math.tan(fov_radians / 2)
        
        # Recommended overlap for reliability
        overlap_percentage = 0.2
        effective_width_m = footprint_width_m * (1 - overlap_percentage)
        
        # Calculate grid pattern
        area_per_drone = search_area_km2 / drone_count
        grid_spacing_m = math.sqrt(area_per_drone * 1000000)  # Convert km² to m²
        
        pattern = {
            "pattern_type": "parallel_strips" if drone_count <= 2 else "grid_search",
            "footprint_width_m": footprint_width_m,
            "effective_width_m": effective_width_m,
            "recommended_overlap": overlap_percentage,
            "grid_spacing_m": grid_spacing_m,
            "area_per_drone_km2": area_per_drone,
            "estimated_strips": int(math.sqrt(search_area_km2 * 1000000) / effective_width_m),
            "coordination_buffer_m": 50.0  # Safety buffer between drones
        }
        
        if priority_zones:
            pattern["priority_zones"] = len(priority_zones)
            pattern["priority_coverage_first"] = True
            
        return pattern

    async def update_performance_metrics(
        self,
        mission_id: str,
        performance_data: Dict[str, Any]
    ) -> None:
        """
        Update performance learning system with mission results.
        
        Args:
            mission_id: Unique mission identifier
            performance_data: Mission performance data
        """
        logger.info(f"Updating performance metrics for mission {mission_id}")
        
        # This would integrate with a learning system to improve future predictions
        # For now, we'll log the data for analysis
        
        # Store performance data for machine learning improvements
        # In a full implementation, this would update ML models
        
        logger.info(f"Performance data logged for mission {mission_id}")

    def get_performance_history(self) -> List[PerformanceMetrics]:
        """Get historical performance metrics for analysis"""
        return self.performance_history.copy()

    def calculate_confidence_intervals(
        self,
        coverage_estimate: float,
        environmental_factors: EnvironmentalFactors
    ) -> Tuple[float, float]:
        """
        Calculate confidence intervals for coverage estimates.
        
        Returns:
            Tuple of (lower_bound, upper_bound) in km²
        """
        
        # Base uncertainty of ±15%
        base_uncertainty = 0.15
        
        # Increase uncertainty for challenging conditions
        if environmental_factors.weather_condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.FOG]:
            base_uncertainty += 0.1
            
        if environmental_factors.terrain_type in [TerrainType.MOUNTAINOUS, TerrainType.FOREST]:
            base_uncertainty += 0.05
            
        if environmental_factors.wind_speed_kmh > 20:
            base_uncertainty += 0.05
            
        uncertainty_range = coverage_estimate * base_uncertainty
        
        return (
            max(0, coverage_estimate - uncertainty_range),
            coverage_estimate + uncertainty_range
        )