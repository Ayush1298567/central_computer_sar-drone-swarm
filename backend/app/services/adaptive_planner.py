"""
Adaptive Planning System for Dynamic Mission Optimization.

This module provides intelligent mission planning capabilities that adapt
to real-time conditions, drone performance, and mission outcomes.
"""

import asyncio
import logging
import math
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models import Mission, Drone, Discovery, MissionDrone
from .weather_service import weather_service
from .coordination_engine import CoordinationEngine, DroneState, MissionState
from ..core.config import settings

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Optimization strategies for mission planning."""
    TIME_EFFICIENT = "time_efficient"  # Minimize mission duration
    COVERAGE_OPTIMAL = "coverage_optimal"  # Maximize area coverage
    BATTERY_CONSERVATIVE = "battery_conservative"  # Minimize battery usage
    ADAPTIVE = "adaptive"  # Dynamic optimization based on conditions


class SearchPattern(Enum):
    """Search pattern types for different scenarios."""
    GRID = "grid"  # Systematic grid search
    SPIRAL = "spiral"  # Spiral from center outward
    CONCENTRIC = "concentric"  # Concentric circles
    LAWNMOWER = "lawnmower"  # Back-and-forth pattern
    ADAPTIVE = "adaptive"  # Dynamic pattern based on conditions


@dataclass
class OptimizationConstraints:
    """Constraints for mission optimization."""
    max_duration_minutes: int = 120
    min_battery_reserve: float = 20.0
    max_altitude: float = 150.0
    min_altitude: float = 30.0
    weather_tolerance: str = "moderate"  # light, moderate, severe
    priority_areas: List[Dict] = field(default_factory=list)
    no_fly_zones: List[Dict] = field(default_factory=list)


@dataclass
class DroneCapabilities:
    """Drone capabilities and performance metrics."""
    drone_id: str
    max_flight_time: int  # minutes
    max_altitude: float  # meters
    max_speed: float  # m/s
    cruise_speed: float  # m/s
    battery_capacity: float  # percentage
    camera_resolution: Tuple[int, int]
    gimbal_stabilization: bool
    obstacle_avoidance: bool
    weather_resistance: str  # light, moderate, severe


@dataclass
class MissionContext:
    """Context information for mission planning."""
    mission_id: str
    search_target: str
    area_size_km2: float
    terrain_type: str  # urban, rural, mountainous, coastal
    time_of_day: str  # dawn, day, dusk, night
    weather_conditions: Dict
    urgency_level: str  # low, medium, high, critical
    available_drones: List[DroneCapabilities]
    constraints: OptimizationConstraints


@dataclass
class OptimizationResult:
    """Result of mission optimization."""
    success: bool
    optimized_plan: Dict
    confidence_score: float
    estimated_duration: int
    estimated_battery_usage: float
    coverage_percentage: float
    risk_assessment: str
    recommendations: List[str]
    alternative_plans: List[Dict] = field(default_factory=list)


class AdaptivePlanner:
    """
    Advanced adaptive planning system for SAR missions.
    
    Provides intelligent mission optimization that adapts to:
    - Real-time weather conditions
    - Drone performance and battery levels
    - Terrain and environmental factors
    - Mission urgency and constraints
    - Historical performance data
    """

    def __init__(self):
        self.coordination_engine = CoordinationEngine()
        self.optimization_history: List[Dict] = []
        self.performance_models: Dict[str, Any] = {}
        self.learning_enabled = True
        
        # Optimization parameters
        self.optimization_weights = {
            'time_efficiency': 0.3,
            'coverage_quality': 0.25,
            'battery_conservation': 0.2,
            'safety_margin': 0.15,
            'weather_adaptation': 0.1
        }

    async def optimize_mission_plan(
        self,
        mission_context: MissionContext,
        strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE
    ) -> OptimizationResult:
        """
        Optimize a mission plan based on context and strategy.
        
        Args:
            mission_context: Mission context and constraints
            strategy: Optimization strategy to use
            
        Returns:
            OptimizationResult with optimized plan
        """
        try:
            logger.info(f"Starting mission optimization for {mission_context.mission_id}")
            
            # Analyze mission context
            context_analysis = await self._analyze_mission_context(mission_context)
            
            # Generate base plan
            base_plan = await self._generate_base_plan(mission_context, context_analysis)
            
            # Apply optimization strategy
            optimized_plan = await self._apply_optimization_strategy(
                base_plan, mission_context, strategy, context_analysis
            )
            
            # Validate and refine plan
            validated_plan = await self._validate_and_refine_plan(
                optimized_plan, mission_context
            )
            
            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(
                validated_plan, mission_context
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                validated_plan, mission_context, metrics
            )
            
            # Create optimization result
            result = OptimizationResult(
                success=True,
                optimized_plan=validated_plan,
                confidence_score=metrics['confidence_score'],
                estimated_duration=metrics['estimated_duration'],
                estimated_battery_usage=metrics['estimated_battery_usage'],
                coverage_percentage=metrics['coverage_percentage'],
                risk_assessment=metrics['risk_assessment'],
                recommendations=recommendations
            )
            
            # Store optimization history
            await self._store_optimization_history(mission_context, result)
            
            logger.info(f"Mission optimization completed for {mission_context.mission_id}")
            return result
            
        except Exception as e:
            logger.error(f"Mission optimization failed: {e}")
            return OptimizationResult(
                success=False,
                optimized_plan={},
                confidence_score=0.0,
                estimated_duration=0,
                estimated_battery_usage=0.0,
                coverage_percentage=0.0,
                risk_assessment="high",
                recommendations=[f"Optimization failed: {str(e)}"]
            )

    async def _analyze_mission_context(self, context: MissionContext) -> Dict[str, Any]:
        """Analyze mission context for optimization decisions."""
        analysis = {
            'terrain_complexity': self._assess_terrain_complexity(context.terrain_type),
            'weather_impact': self._assess_weather_impact(context.weather_conditions),
            'time_constraints': self._assess_time_constraints(context),
            'drone_capabilities': self._assess_drone_capabilities(context.available_drones),
            'urgency_factors': self._assess_urgency_factors(context.urgency_level),
            'area_characteristics': self._assess_area_characteristics(context.area_size_km2)
        }
        
        # Calculate overall complexity score
        complexity_score = (
            analysis['terrain_complexity'] * 0.25 +
            analysis['weather_impact'] * 0.2 +
            analysis['time_constraints'] * 0.2 +
            analysis['drone_capabilities'] * 0.15 +
            analysis['urgency_factors'] * 0.1 +
            analysis['area_characteristics'] * 0.1
        )
        
        analysis['overall_complexity'] = complexity_score
        return analysis

    def _assess_terrain_complexity(self, terrain_type: str) -> float:
        """Assess terrain complexity (0.0 = simple, 1.0 = complex)."""
        complexity_map = {
            'urban': 0.8,      # Buildings, obstacles
            'mountainous': 0.9, # Elevation changes, wind
            'coastal': 0.6,    # Wind, salt air
            'rural': 0.3,      # Open fields
            'forest': 0.7,     # Trees, limited visibility
            'desert': 0.4      # Sand, heat
        }
        return complexity_map.get(terrain_type, 0.5)

    def _assess_weather_impact(self, weather: Dict) -> float:
        """Assess weather impact on operations (0.0 = ideal, 1.0 = severe)."""
        impact = 0.0
        
        # Wind speed impact
        wind_speed = weather.get('wind_speed', 0)
        if wind_speed > 15:  # m/s
            impact += 0.4
        elif wind_speed > 10:
            impact += 0.2
        
        # Visibility impact
        visibility = weather.get('visibility', 10000)  # meters
        if visibility < 1000:
            impact += 0.3
        elif visibility < 5000:
            impact += 0.1
        
        # Precipitation impact
        precipitation = weather.get('precipitation', 0)
        if precipitation > 5:  # mm/h
            impact += 0.3
        elif precipitation > 1:
            impact += 0.1
        
        return min(impact, 1.0)

    def _assess_time_constraints(self, context: MissionContext) -> float:
        """Assess time constraint pressure (0.0 = relaxed, 1.0 = urgent)."""
        max_duration = context.constraints.max_duration_minutes
        area_size = context.area_size_km2
        
        # Calculate base time requirement
        base_time = math.sqrt(area_size) * 30  # Rough estimate
        
        if max_duration < base_time * 0.5:
            return 1.0  # Very urgent
        elif max_duration < base_time * 0.8:
            return 0.7  # Urgent
        elif max_duration < base_time * 1.2:
            return 0.3  # Moderate
        else:
            return 0.1  # Relaxed

    def _assess_drone_capabilities(self, drones: List[DroneCapabilities]) -> float:
        """Assess overall drone capability (0.0 = limited, 1.0 = excellent)."""
        if not drones:
            return 0.0
        
        total_score = 0.0
        for drone in drones:
            score = 0.0
            
            # Flight time capability
            if drone.max_flight_time > 60:
                score += 0.3
            elif drone.max_flight_time > 30:
                score += 0.2
            else:
                score += 0.1
            
            # Weather resistance
            if drone.weather_resistance == 'severe':
                score += 0.3
            elif drone.weather_resistance == 'moderate':
                score += 0.2
            else:
                score += 0.1
            
            # Advanced features
            if drone.obstacle_avoidance:
                score += 0.2
            if drone.gimbal_stabilization:
                score += 0.1
            if drone.camera_resolution[0] > 1920:
                score += 0.1
            
            total_score += score
        
        return total_score / len(drones)

    def _assess_urgency_factors(self, urgency: str) -> float:
        """Assess urgency level (0.0 = low, 1.0 = critical)."""
        urgency_map = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.6,
            'critical': 1.0
        }
        return urgency_map.get(urgency, 0.3)

    def _assess_area_characteristics(self, area_size_km2: float) -> float:
        """Assess area size complexity (0.0 = small, 1.0 = very large)."""
        if area_size_km2 < 1:
            return 0.1
        elif area_size_km2 < 5:
            return 0.3
        elif area_size_km2 < 20:
            return 0.6
        else:
            return 1.0

    async def _generate_base_plan(
        self,
        context: MissionContext,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a base mission plan."""
        # Select optimal search pattern
        search_pattern = self._select_search_pattern(context, analysis)
        
        # Calculate optimal altitude
        optimal_altitude = self._calculate_optimal_altitude(context, analysis)
        
        # Generate waypoints
        waypoints = await self._generate_waypoints(context, search_pattern, optimal_altitude)
        
        # Assign drones to areas
        drone_assignments = await self._assign_drones_to_areas(
            context.available_drones, waypoints, context
        )
        
        base_plan = {
            'mission_id': context.mission_id,
            'search_pattern': search_pattern.value,
            'optimal_altitude': optimal_altitude,
            'waypoints': waypoints,
            'drone_assignments': drone_assignments,
            'estimated_duration': self._estimate_base_duration(context, waypoints),
            'safety_margins': self._calculate_safety_margins(context, analysis)
        }
        
        return base_plan

    def _select_search_pattern(
        self,
        context: MissionContext,
        analysis: Dict[str, Any]
    ) -> SearchPattern:
        """Select optimal search pattern based on context."""
        complexity = analysis['overall_complexity']
        area_size = context.area_size_km2
        terrain = context.terrain_type
        
        # Simple decision tree for pattern selection
        if complexity > 0.8:
            return SearchPattern.ADAPTIVE
        elif area_size > 10:
            return SearchPattern.GRID
        elif terrain in ['urban', 'mountainous']:
            return SearchPattern.SPIRAL
        elif terrain == 'coastal':
            return SearchPattern.LAWNMOWER
        else:
            return SearchPattern.CONCENTRIC

    def _calculate_optimal_altitude(
        self,
        context: MissionContext,
        analysis: Dict[str, Any]
    ) -> float:
        """Calculate optimal flight altitude."""
        base_altitude = 50.0  # meters
        
        # Adjust for terrain
        if context.terrain_type == 'mountainous':
            base_altitude += 30
        elif context.terrain_type == 'urban':
            base_altitude += 20
        
        # Adjust for weather
        weather_impact = analysis['weather_impact']
        if weather_impact > 0.7:
            base_altitude -= 20  # Lower altitude for stability
        elif weather_impact < 0.3:
            base_altitude += 10  # Higher altitude for efficiency
        
        # Ensure within constraints
        return max(
            context.constraints.min_altitude,
            min(base_altitude, context.constraints.max_altitude)
        )

    async def _generate_waypoints(
        self,
        context: MissionContext,
        pattern: SearchPattern,
        altitude: float
    ) -> List[Dict]:
        """Generate waypoints based on search pattern."""
        if pattern == SearchPattern.GRID:
            return self._generate_grid_waypoints(context, altitude)
        elif pattern == SearchPattern.SPIRAL:
            return self._generate_spiral_waypoints(context, altitude)
        elif pattern == SearchPattern.CONCENTRIC:
            return self._generate_concentric_waypoints(context, altitude)
        elif pattern == SearchPattern.LAWNMOWER:
            return self._generate_lawnmower_waypoints(context, altitude)
        else:
            return self._generate_adaptive_waypoints(context, altitude)

    def _generate_grid_waypoints(self, context: MissionContext, altitude: float) -> List[Dict]:
        """Generate grid pattern waypoints."""
        waypoints = []
        area_size = context.area_size_km2
        
        # Calculate grid dimensions
        grid_size = math.sqrt(area_size)
        num_rows = int(grid_size * 2)  # 500m spacing
        num_cols = int(grid_size * 2)
        
        # Generate waypoints
        for row in range(num_rows):
            for col in range(num_cols):
                lat_offset = (row - num_rows/2) * 0.0045  # ~500m
                lng_offset = (col - num_cols/2) * 0.0045
                
                waypoints.append({
                    'lat': 37.7749 + lat_offset,  # Default center
                    'lng': -122.4194 + lng_offset,
                    'altitude': altitude,
                    'type': 'search',
                    'order': len(waypoints)
                })
        
        return waypoints

    def _generate_spiral_waypoints(self, context: MissionContext, altitude: float) -> List[Dict]:
        """Generate spiral pattern waypoints."""
        waypoints = []
        area_size = context.area_size_km2
        radius_km = math.sqrt(area_size / math.pi)
        
        # Generate spiral waypoints
        num_points = int(radius_km * 4)  # 250m spacing
        for i in range(num_points):
            angle = i * 0.5  # radians
            radius = (i / num_points) * radius_km
            
            lat_offset = radius * math.cos(angle) / 111.32
            lng_offset = radius * math.sin(angle) / (111.32 * math.cos(math.radians(37.7749)))
            
            waypoints.append({
                'lat': 37.7749 + lat_offset,
                'lng': -122.4194 + lng_offset,
                'altitude': altitude,
                'type': 'search',
                'order': i
            })
        
        return waypoints

    def _generate_concentric_waypoints(self, context: MissionContext, altitude: float) -> List[Dict]:
        """Generate concentric circle waypoints."""
        waypoints = []
        area_size = context.area_size_km2
        radius_km = math.sqrt(area_size / math.pi)
        
        # Generate concentric circles
        num_circles = int(radius_km / 0.5)  # 500m spacing
        for circle in range(num_circles):
            circle_radius = (circle + 1) * 0.5
            num_points = max(8, int(circle_radius * 8))  # 8 points per km
            
            for point in range(num_points):
                angle = (2 * math.pi * point) / num_points
                
                lat_offset = circle_radius * math.cos(angle) / 111.32
                lng_offset = circle_radius * math.sin(angle) / (111.32 * math.cos(math.radians(37.7749)))
                
                waypoints.append({
                    'lat': 37.7749 + lat_offset,
                    'lng': -122.4194 + lng_offset,
                    'altitude': altitude,
                    'type': 'search',
                    'order': len(waypoints)
                })
        
        return waypoints

    def _generate_lawnmower_waypoints(self, context: MissionContext, altitude: float) -> List[Dict]:
        """Generate lawnmower pattern waypoints."""
        waypoints = []
        area_size = context.area_size_km2
        
        # Calculate lawnmower pattern
        width_km = math.sqrt(area_size)
        height_km = area_size / width_km
        
        num_strips = int(height_km / 0.5)  # 500m strip width
        for strip in range(num_strips):
            y_offset = (strip - num_strips/2) * 0.0045
            
            # Forward pass
            for x in range(int(width_km * 2)):  # 500m spacing
                x_offset = (x - width_km) * 0.0045
                waypoints.append({
                    'lat': 37.7749 + y_offset,
                    'lng': -122.4194 + x_offset,
                    'altitude': altitude,
                    'type': 'search',
                    'order': len(waypoints)
                })
            
            # Backward pass (if not last strip)
            if strip < num_strips - 1:
                for x in range(int(width_km * 2) - 1, -1, -1):
                    x_offset = (x - width_km) * 0.0045
                    waypoints.append({
                        'lat': 37.7749 + y_offset + 0.0045,
                        'lng': -122.4194 + x_offset,
                        'altitude': altitude,
                        'type': 'search',
                        'order': len(waypoints)
                    })
        
        return waypoints

    def _generate_adaptive_waypoints(self, context: MissionContext, altitude: float) -> List[Dict]:
        """Generate adaptive waypoints based on multiple factors."""
        # Combine multiple patterns based on context
        grid_waypoints = self._generate_grid_waypoints(context, altitude)
        spiral_waypoints = self._generate_spiral_waypoints(context, altitude)
        
        # Select best waypoints based on context
        if context.terrain_type == 'urban':
            return spiral_waypoints  # Better for complex terrain
        else:
            return grid_waypoints  # More efficient for open areas

    async def _assign_drones_to_areas(
        self,
        drones: List[DroneCapabilities],
        waypoints: List[Dict],
        context: MissionContext
    ) -> List[Dict]:
        """Assign drones to search areas."""
        assignments = []
        
        if not drones or not waypoints:
            return assignments
        
        # Calculate area per drone
        waypoints_per_drone = len(waypoints) // len(drones)
        remainder = len(waypoints) % len(drones)
        
        start_idx = 0
        for i, drone in enumerate(drones):
            # Assign waypoints to drone
            end_idx = start_idx + waypoints_per_drone
            if i < remainder:
                end_idx += 1
            
            drone_waypoints = waypoints[start_idx:end_idx]
            
            assignments.append({
                'drone_id': drone.drone_id,
                'assigned_waypoints': drone_waypoints,
                'estimated_duration': self._estimate_drone_duration(drone, drone_waypoints),
                'battery_usage': self._estimate_battery_usage(drone, drone_waypoints),
                'priority': self._calculate_drone_priority(drone, context)
            })
            
            start_idx = end_idx
        
        return assignments

    def _estimate_drone_duration(self, drone: DroneCapabilities, waypoints: List[Dict]) -> int:
        """Estimate duration for drone to complete assigned waypoints."""
        if not waypoints:
            return 0
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            
            # Simple distance calculation
            lat_diff = curr_wp['lat'] - prev_wp['lat']
            lng_diff = curr_wp['lng'] - prev_wp['lng']
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111320  # meters
            
            total_distance += distance
        
        # Calculate time based on cruise speed
        flight_time = total_distance / drone.cruise_speed  # seconds
        return int(flight_time / 60)  # minutes

    def _estimate_battery_usage(self, drone: DroneCapabilities, waypoints: List[Dict]) -> float:
        """Estimate battery usage for drone."""
        duration = self._estimate_drone_duration(drone, waypoints)
        
        # Simple battery usage calculation
        battery_per_minute = 100.0 / drone.max_flight_time
        usage = duration * battery_per_minute
        
        return min(usage, 100.0)

    def _calculate_drone_priority(self, drone: DroneCapabilities, context: MissionContext) -> str:
        """Calculate priority for drone assignment."""
        score = 0.0
        
        # Flight time capability
        if drone.max_flight_time > 60:
            score += 0.3
        elif drone.max_flight_time > 30:
            score += 0.2
        
        # Weather resistance
        if drone.weather_resistance == 'severe':
            score += 0.3
        elif drone.weather_resistance == 'moderate':
            score += 0.2
        
        # Advanced features
        if drone.obstacle_avoidance:
            score += 0.2
        if drone.gimbal_stabilization:
            score += 0.1
        
        # Determine priority
        if score > 0.7:
            return 'high'
        elif score > 0.4:
            return 'medium'
        else:
            return 'low'

    def _estimate_base_duration(self, context: MissionContext, waypoints: List[Dict]) -> int:
        """Estimate base mission duration."""
        if not waypoints:
            return 0
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            
            lat_diff = curr_wp['lat'] - prev_wp['lat']
            lng_diff = curr_wp['lng'] - prev_wp['lng']
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111320
            
            total_distance += distance
        
        # Estimate time based on average speed
        avg_speed = 10.0  # m/s
        flight_time = total_distance / avg_speed  # seconds
        
        # Add safety margins
        safety_margin = 1.2  # 20% margin
        total_time = flight_time * safety_margin
        
        return int(total_time / 60)  # minutes

    def _calculate_safety_margins(self, context: MissionContext, analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate safety margins for the mission."""
        margins = {
            'battery_reserve': 20.0,  # Default 20%
            'time_buffer': 15.0,      # Default 15%
            'altitude_buffer': 10.0,  # Default 10m
            'weather_buffer': 0.0     # Weather-dependent
        }
        
        # Adjust for complexity
        complexity = analysis['overall_complexity']
        if complexity > 0.7:
            margins['battery_reserve'] += 10.0
            margins['time_buffer'] += 10.0
            margins['altitude_buffer'] += 5.0
        
        # Adjust for weather
        weather_impact = analysis['weather_impact']
        margins['weather_buffer'] = weather_impact * 20.0
        
        return margins

    async def _apply_optimization_strategy(
        self,
        base_plan: Dict[str, Any],
        context: MissionContext,
        strategy: OptimizationStrategy,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply optimization strategy to base plan."""
        optimized_plan = base_plan.copy()
        
        if strategy == OptimizationStrategy.TIME_EFFICIENT:
            optimized_plan = await self._optimize_for_time_efficiency(optimized_plan, context)
        elif strategy == OptimizationStrategy.COVERAGE_OPTIMAL:
            optimized_plan = await self._optimize_for_coverage(optimized_plan, context)
        elif strategy == OptimizationStrategy.BATTERY_CONSERVATIVE:
            optimized_plan = await self._optimize_for_battery(optimized_plan, context)
        elif strategy == OptimizationStrategy.ADAPTIVE:
            optimized_plan = await self._optimize_adaptively(optimized_plan, context, analysis)
        
        return optimized_plan

    async def _optimize_for_time_efficiency(self, plan: Dict[str, Any], context: MissionContext) -> Dict[str, Any]:
        """Optimize plan for time efficiency."""
        # Reduce waypoint spacing
        waypoints = plan['waypoints']
        optimized_waypoints = []
        
        for i in range(0, len(waypoints), 2):  # Skip every other waypoint
            optimized_waypoints.append(waypoints[i])
        
        plan['waypoints'] = optimized_waypoints
        plan['optimization_applied'] = 'time_efficiency'
        
        return plan

    async def _optimize_for_coverage(self, plan: Dict[str, Any], context: MissionContext) -> Dict[str, Any]:
        """Optimize plan for maximum coverage."""
        # Increase waypoint density
        waypoints = plan['waypoints']
        optimized_waypoints = []
        
        for i in range(len(waypoints)):
            optimized_waypoints.append(waypoints[i])
            # Add intermediate waypoints for better coverage
            if i < len(waypoints) - 1:
                next_wp = waypoints[i + 1]
                intermediate = {
                    'lat': (waypoints[i]['lat'] + next_wp['lat']) / 2,
                    'lng': (waypoints[i]['lng'] + next_wp['lng']) / 2,
                    'altitude': waypoints[i]['altitude'],
                    'type': 'search',
                    'order': len(optimized_waypoints)
                }
                optimized_waypoints.append(intermediate)
        
        plan['waypoints'] = optimized_waypoints
        plan['optimization_applied'] = 'coverage_optimal'
        
        return plan

    async def _optimize_for_battery(self, plan: Dict[str, Any], context: MissionContext) -> Dict[str, Any]:
        """Optimize plan for battery conservation."""
        # Reduce altitude and optimize flight paths
        waypoints = plan['waypoints']
        optimized_waypoints = []
        
        for wp in waypoints:
            optimized_wp = wp.copy()
            optimized_wp['altitude'] = max(wp['altitude'] - 10, context.constraints.min_altitude)
            optimized_waypoints.append(optimized_wp)
        
        plan['waypoints'] = optimized_waypoints
        plan['optimization_applied'] = 'battery_conservative'
        
        return plan

    async def _optimize_adaptively(
        self,
        plan: Dict[str, Any],
        context: MissionContext,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply adaptive optimization based on multiple factors."""
        # Combine multiple optimization strategies
        time_weight = self.optimization_weights['time_efficiency']
        coverage_weight = self.optimization_weights['coverage_quality']
        battery_weight = self.optimization_weights['battery_conservation']
        
        # Apply weighted optimizations
        if time_weight > 0.3:
            plan = await self._optimize_for_time_efficiency(plan, context)
        
        if coverage_weight > 0.3:
            plan = await self._optimize_for_coverage(plan, context)
        
        if battery_weight > 0.3:
            plan = await self._optimize_for_battery(plan, context)
        
        plan['optimization_applied'] = 'adaptive'
        return plan

    async def _validate_and_refine_plan(
        self,
        plan: Dict[str, Any],
        context: MissionContext
    ) -> Dict[str, Any]:
        """Validate and refine the optimized plan."""
        # Check constraints
        if plan['estimated_duration'] > context.constraints.max_duration_minutes:
            # Reduce waypoints to meet time constraint
            waypoints = plan['waypoints']
            reduction_factor = context.constraints.max_duration_minutes / plan['estimated_duration']
            new_waypoint_count = int(len(waypoints) * reduction_factor)
            plan['waypoints'] = waypoints[:new_waypoint_count]
        
        # Check battery constraints
        for assignment in plan['drone_assignments']:
            if assignment['battery_usage'] > (100 - context.constraints.min_battery_reserve):
                # Reduce waypoints for this drone
                waypoints = assignment['assigned_waypoints']
                reduction_factor = (100 - context.constraints.min_battery_reserve) / assignment['battery_usage']
                new_waypoint_count = int(len(waypoints) * reduction_factor)
                assignment['assigned_waypoints'] = waypoints[:new_waypoint_count]
        
        # Add validation metadata
        plan['validation_passed'] = True
        plan['refinements_applied'] = True
        
        return plan

    async def _calculate_performance_metrics(
        self,
        plan: Dict[str, Any],
        context: MissionContext
    ) -> Dict[str, Any]:
        """Calculate performance metrics for the plan."""
        metrics = {
            'confidence_score': 0.8,  # Base confidence
            'estimated_duration': plan['estimated_duration'],
            'estimated_battery_usage': 0.0,
            'coverage_percentage': 0.0,
            'risk_assessment': 'medium'
        }
        
        # Calculate battery usage
        total_battery = 0.0
        for assignment in plan['drone_assignments']:
            total_battery += assignment['battery_usage']
        metrics['estimated_battery_usage'] = total_battery / len(plan['drone_assignments'])
        
        # Calculate coverage
        total_waypoints = len(plan['waypoints'])
        area_coverage = min(100.0, (total_waypoints / 100) * 100)  # Rough estimate
        metrics['coverage_percentage'] = area_coverage
        
        # Assess risk
        if metrics['estimated_battery_usage'] > 80:
            metrics['risk_assessment'] = 'high'
        elif metrics['estimated_battery_usage'] > 60:
            metrics['risk_assessment'] = 'medium'
        else:
            metrics['risk_assessment'] = 'low'
        
        # Adjust confidence based on factors
        if context.urgency_level == 'critical':
            metrics['confidence_score'] -= 0.1
        if context.terrain_type == 'mountainous':
            metrics['confidence_score'] -= 0.1
        
        metrics['confidence_score'] = max(0.0, min(1.0, metrics['confidence_score']))
        
        return metrics

    async def _generate_recommendations(
        self,
        plan: Dict[str, Any],
        context: MissionContext,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for the plan."""
        recommendations = []
        
        # Battery recommendations
        if metrics['estimated_battery_usage'] > 70:
            recommendations.append("Consider reducing mission scope or using additional drones")
        
        # Weather recommendations
        if context.weather_conditions.get('wind_speed', 0) > 10:
            recommendations.append("Monitor wind conditions closely during flight")
        
        # Terrain recommendations
        if context.terrain_type == 'mountainous':
            recommendations.append("Use drones with obstacle avoidance for mountainous terrain")
        
        # Time recommendations
        if metrics['estimated_duration'] > context.constraints.max_duration_minutes * 0.9:
            recommendations.append("Mission duration is near maximum limit")
        
        # Coverage recommendations
        if metrics['coverage_percentage'] < 80:
            recommendations.append("Consider increasing waypoint density for better coverage")
        
        return recommendations

    async def _store_optimization_history(
        self,
        context: MissionContext,
        result: OptimizationResult
    ) -> None:
        """Store optimization history for learning."""
        history_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'mission_id': context.mission_id,
            'context': {
                'area_size': context.area_size_km2,
                'terrain_type': context.terrain_type,
                'urgency_level': context.urgency_level,
                'weather_conditions': context.weather_conditions
            },
            'result': {
                'success': result.success,
                'confidence_score': result.confidence_score,
                'estimated_duration': result.estimated_duration,
                'coverage_percentage': result.coverage_percentage
            }
        }
        
        self.optimization_history.append(history_entry)
        
        # Keep only last 1000 entries
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-1000:]

    async def get_optimization_history(self, limit: int = 100) -> List[Dict]:
        """Get optimization history for analysis."""
        return self.optimization_history[-limit:]

    async def update_optimization_weights(self, new_weights: Dict[str, float]) -> None:
        """Update optimization weights based on performance."""
        self.optimization_weights.update(new_weights)
        logger.info(f"Updated optimization weights: {self.optimization_weights}")

    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights from optimization history."""
        if not self.optimization_history:
            return {'message': 'No optimization history available'}
        
        # Calculate average performance metrics
        total_entries = len(self.optimization_history)
        avg_confidence = sum(entry['result']['confidence_score'] for entry in self.optimization_history) / total_entries
        avg_duration = sum(entry['result']['estimated_duration'] for entry in self.optimization_history) / total_entries
        avg_coverage = sum(entry['result']['coverage_percentage'] for entry in self.optimization_history) / total_entries
        
        # Calculate success rate
        success_rate = sum(1 for entry in self.optimization_history if entry['result']['success']) / total_entries
        
        return {
            'total_optimizations': total_entries,
            'success_rate': success_rate,
            'average_confidence': avg_confidence,
            'average_duration': avg_duration,
            'average_coverage': avg_coverage,
            'optimization_weights': self.optimization_weights
        }


# Global instance
adaptive_planner = AdaptivePlanner()
