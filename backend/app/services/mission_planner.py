"""
Mission planning service for creating and optimizing search patterns.
"""

import logging
import math
from typing import Dict, List, Tuple, Optional
from ..models import Mission, Drone

logger = logging.getLogger(__name__)


class MissionPlanner:
    """Creates and optimizes drone mission plans."""

    def __init__(self):
        self.search_patterns = {
            "lawnmower": self._generate_lawnmower_pattern,
            "spiral": self._generate_spiral_pattern,
            "grid": self._generate_grid_pattern,
            "adaptive": self._generate_adaptive_pattern
        }

    def create_mission_plan(self, mission: Mission, available_drones: List[Drone]) -> Dict:
        """Create a comprehensive mission plan."""
        try:
            # Calculate mission parameters
            area_bounds = self._calculate_area_bounds(mission)
            drone_assignments = self._assign_drones_to_areas(available_drones, area_bounds)
            flight_paths = self._generate_flight_paths(mission, drone_assignments)

            # Calculate mission metrics
            total_distance = sum(path["distance"] for path in flight_paths.values())
            estimated_duration = self._calculate_mission_duration(mission, total_distance)
            coverage_area = mission.area_size_km2

            mission_plan = {
                "mission_id": mission.id,
                "mission_name": mission.name,
                "search_pattern": "adaptive",
                "area_bounds": area_bounds,
                "drone_assignments": drone_assignments,
                "flight_paths": flight_paths,
                "mission_metrics": {
                    "total_distance_km": round(total_distance, 2),
                    "estimated_duration_minutes": estimated_duration,
                    "coverage_area_km2": round(coverage_area, 2),
                    "drones_assigned": len(available_drones),
                    "search_altitude_m": mission.search_altitude,
                    "overlap_percentage": 20  # Configurable overlap for thorough coverage
                },
                "safety_parameters": {
                    "max_altitude": 120,
                    "min_altitude": 10,
                    "max_speed": 20,
                    "weather_considerations": mission.weather_conditions or {}
                },
                "emergency_procedures": {
                    "return_home_altitude": 50,
                    "emergency_landing_zones": self._identify_emergency_zones(area_bounds),
                    "communication_checkpoints": self._generate_communication_checkpoints(flight_paths)
                }
            }

            logger.info(f"Created mission plan for {mission.name} with {len(available_drones)} drones")
            return mission_plan

        except Exception as e:
            logger.error(f"Error creating mission plan: {e}")
            raise

    def _calculate_area_bounds(self, mission: Mission) -> Dict:
        """Calculate the bounding box for the search area."""
        # Simple square area calculation for now
        # In a real implementation, this would handle complex polygons
        center_lat = mission.center_lat
        center_lng = mission.center_lng
        area_km = math.sqrt(mission.area_size_km2)  # Approximate side length

        # Convert km to approximate degrees (rough approximation)
        km_to_deg = 0.009  # 1 km ≈ 0.009 degrees at equator

        half_side = (area_km / 2) * km_to_deg

        bounds = {
            "north": center_lat + half_side,
            "south": center_lat - half_side,
            "east": center_lng + half_side,
            "west": center_lng - half_side,
            "center": {"lat": center_lat, "lng": center_lng},
            "width_km": area_km,
            "height_km": area_km
        }

        return bounds

    def _assign_drones_to_areas(self, drones: List[Drone], area_bounds: Dict) -> Dict:
        """Assign drones to specific areas within the search zone."""
        assignments = {}

        if not drones:
            return assignments

        # Simple assignment: divide area into equal parts
        num_drones = len(drones)
        area_width = area_bounds["east"] - area_bounds["west"]
        area_height = area_bounds["north"] - area_bounds["south"]

        section_width = area_width / num_drones

        for i, drone in enumerate(drones):
            section_start = area_bounds["west"] + (i * section_width)
            section_end = section_start + section_width

            assignments[drone.id] = {
                "drone_name": drone.name,
                "area_bounds": {
                    "north": area_bounds["north"],
                    "south": area_bounds["south"],
                    "east": section_end,
                    "west": section_start
                },
                "search_pattern": "lawnmower",
                "priority": "normal"
            }

        return assignments

    def _generate_flight_paths(self, mission: Mission, drone_assignments: Dict) -> Dict:
        """Generate flight paths for each drone."""
        flight_paths = {}

        for drone_id, assignment in drone_assignments.items():
            area_bounds = assignment["area_bounds"]
            search_pattern = assignment["search_pattern"]

            # Generate waypoints for the assigned area
            if search_pattern in self.search_patterns:
                waypoints = self.search_patterns[search_pattern](area_bounds, mission.search_altitude)
            else:
                waypoints = self._generate_default_pattern(area_bounds, mission.search_altitude)

            # Calculate path distance
            distance = self._calculate_path_distance(waypoints)

            flight_paths[drone_id] = {
                "waypoints": waypoints,
                "distance_km": round(distance, 2),
                "estimated_time_minutes": int(distance * 3),  # Assume 3 minutes per km
                "search_pattern": search_pattern
            }

        return flight_paths

    def _generate_lawnmower_pattern(self, bounds: Dict, altitude: float) -> List[Dict]:
        """Generate lawnmower (zigzag) search pattern."""
        waypoints = []

        # Simple back-and-forth pattern
        num_passes = 10  # Number of parallel passes
        pass_spacing = (bounds["north"] - bounds["south"]) / num_passes

        for i in range(num_passes + 1):
            lat = bounds["south"] + (i * pass_spacing)

            if i % 2 == 0:
                # Left to right
                waypoints.append({"lat": lat, "lng": bounds["west"], "alt": altitude, "type": "waypoint"})
                waypoints.append({"lat": lat, "lng": bounds["east"], "alt": altitude, "type": "waypoint"})
            else:
                # Right to left
                waypoints.append({"lat": lat, "lng": bounds["east"], "alt": altitude, "type": "waypoint"})
                waypoints.append({"lat": lat, "lng": bounds["west"], "alt": altitude, "type": "waypoint"})

        return waypoints

    def _generate_spiral_pattern(self, bounds: Dict, altitude: float) -> List[Dict]:
        """Generate spiral search pattern."""
        waypoints = []
        center_lat = (bounds["north"] + bounds["south"]) / 2
        center_lng = (bounds["east"] + bounds["west"]) / 2

        # Simple outward spiral
        num_turns = 5
        points_per_turn = 8

        for turn in range(num_turns):
            radius = (turn + 1) * 0.001  # Increasing radius in degrees

            for point in range(points_per_turn):
                angle = (point / points_per_turn) * 2 * math.pi
                lat = center_lat + (radius * math.sin(angle))
                lng = center_lng + (radius * math.cos(angle))

                waypoints.append({
                    "lat": lat,
                    "lng": lng,
                    "alt": altitude,
                    "type": "waypoint"
                })

        return waypoints

    def _generate_grid_pattern(self, bounds: Dict, altitude: float) -> List[Dict]:
        """Generate grid search pattern."""
        waypoints = []

        # Create a grid of waypoints
        grid_spacing = 0.001  # Degrees between grid points
        num_rows = int((bounds["north"] - bounds["south"]) / grid_spacing) + 1
        num_cols = int((bounds["east"] - bounds["west"]) / grid_spacing) + 1

        for row in range(num_rows):
            lat = bounds["south"] + (row * grid_spacing)

            for col in range(num_cols):
                lng = bounds["west"] + (col * grid_spacing)

                waypoints.append({
                    "lat": lat,
                    "lng": lng,
                    "alt": altitude,
                    "type": "waypoint"
                })

        return waypoints

    def _generate_adaptive_pattern(self, bounds: Dict, altitude: float) -> List[Dict]:
        """Generate adaptive search pattern based on terrain/conditions."""
        # For now, use lawnmower pattern as adaptive
        # In a real implementation, this would analyze terrain data
        return self._generate_lawnmower_pattern(bounds, altitude)

    def _generate_default_pattern(self, bounds: Dict, altitude: float) -> List[Dict]:
        """Generate default search pattern."""
        return self._generate_lawnmower_pattern(bounds, altitude)

    def _calculate_path_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total distance of a waypoint path."""
        if len(waypoints) < 2:
            return 0.0

        total_distance = 0.0

        for i in range(len(waypoints) - 1):
            current = waypoints[i]
            next_wp = waypoints[i + 1]

            # Simple Euclidean distance (not accurate for lat/lng, but fine for estimation)
            distance = math.sqrt(
                (next_wp["lat"] - current["lat"]) ** 2 +
                (next_wp["lng"] - current["lng"]) ** 2
            ) * 111  # Rough km conversion

            total_distance += distance

        return total_distance

    def _calculate_mission_duration(self, mission: Mission, total_distance: float) -> int:
        """Calculate estimated mission duration."""
        # Base calculation
        base_speed_kmh = 15  # 15 km/h average speed
        flight_time_hours = total_distance / base_speed_kmh

        # Add time for takeoff, landing, and transitions
        transition_time_hours = 0.2  # 12 minutes for transitions

        # Add buffer for safety and weather
        buffer_multiplier = 1.2  # 20% buffer

        total_time_hours = (flight_time_hours + transition_time_hours) * buffer_multiplier
        total_time_minutes = int(total_time_hours * 60)

        return min(total_time_minutes, 180)  # Cap at 3 hours

    def _identify_emergency_zones(self, area_bounds: Dict) -> List[Dict]:
        """Identify potential emergency landing zones."""
        # Simple identification of open areas
        zones = [
            {
                "lat": area_bounds["center"]["lat"],
                "lng": area_bounds["center"]["lng"],
                "type": "primary",
                "description": "Central open area"
            }
        ]

        return zones

    def _generate_communication_checkpoints(self, flight_paths: Dict) -> List[Dict]:
        """Generate communication checkpoint locations."""
        checkpoints = []

        for drone_id, path in flight_paths.items():
            if path["waypoints"]:
                # Add checkpoint at start and middle of path
                checkpoints.append({
                    "drone_id": drone_id,
                    "location": path["waypoints"][0],
                    "type": "start"
                })

                mid_point = len(path["waypoints"]) // 2
                if mid_point > 0:
                    checkpoints.append({
                        "drone_id": drone_id,
                        "location": path["waypoints"][mid_point],
                        "type": "midpoint"
                    })

        return checkpoints

    def optimize_for_weather(self, mission: Mission, weather_data: Dict) -> Dict:
        """Optimize mission plan based on weather conditions."""
        optimizations = {
            "altitude_adjustment": 0,
            "speed_reduction": 0,
            "pattern_modification": None,
            "warnings": []
        }

        wind_speed = weather_data.get("wind_speed", 0)
        visibility = weather_data.get("visibility", 10)
        precipitation = weather_data.get("precipitation", 0)

        # Adjust for wind
        if wind_speed > 20:  # km/h
            optimizations["speed_reduction"] = 0.3  # 30% speed reduction
            optimizations["warnings"].append(f"High winds ({wind_speed} km/h) - reducing speed by 30%")

        # Adjust for visibility
        if visibility < 5:  # km
            optimizations["altitude_adjustment"] = 10  # Lower altitude for better visibility
            optimizations["warnings"].append(f"Low visibility ({visibility} km) - reducing altitude by 10m")

        # Adjust for precipitation
        if precipitation > 5:  # mm/h
            optimizations["warnings"].append(f"Heavy precipitation ({precipitation} mm/h) - consider delaying mission")

        return optimizations

    def validate_safety_constraints(self, mission_plan: Dict) -> List[str]:
        """Validate mission plan against safety constraints."""
        warnings = []

        for drone_id, path in mission_plan["flight_paths"].items():
            max_alt = max(wp["alt"] for wp in path["waypoints"])
            min_alt = min(wp["alt"] for wp in path["waypoints"])

            if max_alt > mission_plan["safety_parameters"]["max_altitude"]:
                warnings.append(f"Drone path exceeds maximum altitude: {max_alt}m > {mission_plan['safety_parameters']['max_altitude']}m")

            if min_alt < mission_plan["safety_parameters"]["min_altitude"]:
                warnings.append(f"Drone path below minimum altitude: {min_alt}m < {mission_plan['safety_parameters']['min_altitude']}m")

        return warnings


# Global instance
mission_planner = MissionPlanner()