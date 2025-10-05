"""
Area calculation service for mission planning.
"""

import logging
import math
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class AreaCalculator:
    """Calculates search areas and mission coverage."""

    @staticmethod
    def calculate_area_bounds(center_lat: float, center_lng: float, area_km2: float) -> Dict:
        """Calculate bounding box for a given area."""
        # Approximate conversion: 1 degree ≈ 111 km
        km_per_degree = 111

        # Calculate side length in degrees
        side_length_deg = math.sqrt(area_km2) / km_per_degree

        bounds = {
            "north": center_lat + side_length_deg,
            "south": center_lat - side_length_deg,
            "east": center_lng + side_length_deg,
            "west": center_lng - side_length_deg,
            "center_lat": center_lat,
            "center_lng": center_lng,
            "area_km2": area_km2
        }

        return bounds

    @staticmethod
    def calculate_drone_coverage_area(drone_altitude: float, camera_fov: float = 60) -> float:
        """Calculate area covered by a single drone pass."""
        # Simple calculation: area = 2 * altitude * tan(fov/2) * flight_distance
        # For estimation, assume 1km flight distance
        flight_distance_km = 1.0

        # Convert altitude to km
        altitude_km = drone_altitude / 1000

        # Calculate swath width in km
        fov_radians = math.radians(camera_fov)
        swath_width_km = 2 * altitude_km * math.tan(fov_radians / 2)

        # Calculate coverage area
        coverage_area_km2 = swath_width_km * flight_distance_km

        return coverage_area_km2

    @staticmethod
    def calculate_optimal_drone_count(area_km2: float, drone_altitude: float, overlap_percent: float = 20) -> int:
        """Calculate optimal number of drones for area coverage."""
        # Calculate single drone coverage
        single_coverage = AreaCalculator.calculate_drone_coverage_area(drone_altitude)

        # Account for overlap
        effective_coverage = single_coverage * (1 - overlap_percent / 100)

        # Calculate required drones
        required_drones = math.ceil(area_km2 / effective_coverage)

        # Cap at reasonable maximum
        return min(required_drones, 10)

    @staticmethod
    def calculate_flight_path_length(area_bounds: Dict, pattern: str = "lawnmower") -> float:
        """Calculate total flight path length for an area."""
        width_km = abs(area_bounds["east"] - area_bounds["west"]) * 111  # Convert to km
        height_km = abs(area_bounds["north"] - area_bounds["south"]) * 111  # Convert to km

        if pattern == "lawnmower":
            # Back and forth pattern
            num_passes = max(1, int(height_km / 0.1))  # Assume 100m spacing
            total_distance = num_passes * width_km + (num_passes - 1) * height_km
            return total_distance

        elif pattern == "spiral":
            # Spiral pattern (approximate)
            radius_km = math.sqrt(width_km * height_km / math.pi)
            num_turns = 3
            total_distance = 2 * math.pi * radius_km * num_turns
            return total_distance

        else:
            # Default to area perimeter
            return 2 * (width_km + height_km)

    @staticmethod
    def calculate_search_time(area_km2: float, drone_speed_kmh: float = 15, efficiency: float = 0.8) -> int:
        """Calculate estimated search time in minutes."""
        # Base calculation
        flight_distance_km = area_km2 * 3  # Assume 3km flight per km2 searched
        flight_time_hours = flight_distance_km / drone_speed_kmh

        # Account for efficiency (maneuvering, camera operation, etc.)
        adjusted_time_hours = flight_time_hours / efficiency

        # Convert to minutes
        search_time_minutes = int(adjusted_time_hours * 60)

        return search_time_minutes

    @staticmethod
    def optimize_altitude_for_coverage(target_resolution: float = 5) -> float:
        """Calculate optimal altitude for desired ground resolution in cm/pixel."""
        # This is a simplified calculation
        # Real implementation would depend on camera specs

        # Assume we want target_resolution cm/pixel
        # Optimal altitude = (sensor_size * focal_length * 100) / (target_resolution * image_width_pixels)

        # For now, return a reasonable altitude based on common use cases
        altitude_map = {
            1: 30,   # Very high resolution
            5: 50,   # Standard resolution
            10: 80,  # Lower resolution, larger coverage
            25: 120  # Maximum altitude
        }

        return altitude_map.get(target_resolution, 50)

    @staticmethod
    def validate_search_area(area_bounds: Dict, restrictions: List[Dict] = None) -> List[str]:
        """Validate search area against restrictions (airspace, terrain, etc.)."""
        warnings = []

        # Check for common restrictions
        if restrictions:
            for restriction in restrictions:
                restriction_type = restriction.get("type", "")

                if restriction_type == "no_fly_zone":
                    # Check if area overlaps with no-fly zone
                    if AreaCalculator._areas_overlap(area_bounds, restriction.get("bounds", {})):
                        warnings.append(f"Search area overlaps with {restriction.get('name', 'restricted area')}")

                elif restriction_type == "altitude_limit":
                    max_alt = restriction.get("max_altitude", 120)
                    warnings.append(f"Altitude restricted to {max_alt}m in this area")

        # Check area size reasonableness
        area_km2 = area_bounds.get("area_km2", 0)
        if area_km2 > 100:
            warnings.append("Large search area may require multiple missions or additional resources")

        if area_km2 < 0.01:
            warnings.append("Very small search area - consider if this is appropriate for drone operations")

        return warnings

    @staticmethod
    def _areas_overlap(bounds1: Dict, bounds2: Dict) -> bool:
        """Check if two bounding boxes overlap."""
        return not (
            bounds1["east"] < bounds2["west"] or
            bounds1["west"] > bounds2["east"] or
            bounds1["north"] < bounds2["south"] or
            bounds1["south"] > bounds2["north"]
        )


# Global instance
area_calculator = AreaCalculator()