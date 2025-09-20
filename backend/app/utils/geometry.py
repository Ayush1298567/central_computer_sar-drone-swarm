"""
Advanced geometric utilities for SAR Drone Command & Control System.
Provides comprehensive geometric calculations, search grid generation, and navigation algorithms.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

from ..utils.logging import get_mission_logger

logger = get_mission_logger("geometry")


@dataclass
class Coordinate:
    """Represents a geographic coordinate with latitude and longitude."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    
    def __post_init__(self):
        """Validate coordinate values."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
        if self.altitude is not None and self.altitude < 0:
            raise ValueError(f"Altitude must be non-negative, got {self.altitude}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"latitude": self.latitude, "longitude": self.longitude}
        if self.altitude is not None:
            result["altitude"] = self.altitude
        return result
    
    def __str__(self) -> str:
        """String representation."""
        if self.altitude is not None:
            return f"({self.latitude:.6f}, {self.longitude:.6f}, {self.altitude:.1f}m)"
        return f"({self.latitude:.6f}, {self.longitude:.6f})"


@dataclass
class BoundingBox:
    """Represents a rectangular bounding box."""
    north: float
    south: float
    east: float
    west: float
    
    def __post_init__(self):
        """Validate bounding box."""
        if self.north <= self.south:
            raise ValueError("North boundary must be greater than south boundary")
        if self.east <= self.west:
            raise ValueError("East boundary must be greater than west boundary")
    
    def contains(self, coord: Coordinate) -> bool:
        """Check if coordinate is within bounding box."""
        return (self.south <= coord.latitude <= self.north and
                self.west <= coord.longitude <= self.east)
    
    def center(self) -> Coordinate:
        """Get center coordinate of bounding box."""
        return Coordinate(
            latitude=(self.north + self.south) / 2,
            longitude=(self.east + self.west) / 2
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west
        }


class SearchPattern(Enum):
    """Search pattern types for drone missions."""
    GRID = "grid"
    SPIRAL = "spiral"
    RANDOM = "random"
    ADAPTIVE = "adaptive"
    CUSTOM = "custom"


class GeometryCalculator:
    """
    Advanced geometric calculator for SAR operations.
    Provides comprehensive geometric calculations and search pattern generation.
    """
    
    # Earth's radius in meters
    EARTH_RADIUS = 6371000.0
    
    def __init__(self):
        """Initialize geometry calculator."""
        logger.info("GeometryCalculator initialized")
    
    def haversine_distance(self, coord1: Coordinate, coord2: Coordinate) -> float:
        """
        Calculate the great circle distance between two coordinates using the Haversine formula.
        
        Args:
            coord1: First coordinate
            coord2: Second coordinate
            
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = math.radians(coord1.latitude)
        lon1_rad = math.radians(coord1.longitude)
        lat2_rad = math.radians(coord2.latitude)
        lon2_rad = math.radians(coord2.longitude)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = self.EARTH_RADIUS * c
        
        logger.debug(f"Haversine distance calculated: {distance:.2f}m between {coord1} and {coord2}")
        return distance
    
    def calculate_bearing(self, coord1: Coordinate, coord2: Coordinate) -> float:
        """
        Calculate the initial bearing from coord1 to coord2.
        
        Args:
            coord1: Starting coordinate
            coord2: Destination coordinate
            
        Returns:
            Bearing in degrees (0-360)
        """
        # Convert to radians
        lat1_rad = math.radians(coord1.latitude)
        lat2_rad = math.radians(coord2.latitude)
        dlon_rad = math.radians(coord2.longitude - coord1.longitude)
        
        # Calculate bearing
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-360 degrees
        bearing_deg = (bearing_deg + 360) % 360
        
        logger.debug(f"Bearing calculated: {bearing_deg:.2f}° from {coord1} to {coord2}")
        return bearing_deg
    
    def destination_point(self, start: Coordinate, distance: float, bearing: float) -> Coordinate:
        """
        Calculate destination point given start point, distance, and bearing.
        
        Args:
            start: Starting coordinate
            distance: Distance in meters
            bearing: Bearing in degrees
            
        Returns:
            Destination coordinate
        """
        # Convert to radians
        lat1_rad = math.radians(start.latitude)
        lon1_rad = math.radians(start.longitude)
        bearing_rad = math.radians(bearing)
        
        # Angular distance
        angular_distance = distance / self.EARTH_RADIUS
        
        # Calculate destination
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(angular_distance) +
            math.cos(lat1_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1_rad),
            math.cos(angular_distance) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        # Convert back to degrees
        lat2_deg = math.degrees(lat2_rad)
        lon2_deg = math.degrees(lon2_rad)
        
        # Normalize longitude
        lon2_deg = (lon2_deg + 540) % 360 - 180
        
        destination = Coordinate(lat2_deg, lon2_deg, start.altitude)
        
        logger.debug(f"Destination point calculated: {destination} from {start} at {distance:.2f}m, {bearing:.2f}°")
        return destination
    
    def calculate_polygon_area(self, coordinates: List[Coordinate]) -> float:
        """
        Calculate the area of a polygon using the spherical excess formula.
        
        Args:
            coordinates: List of coordinates forming the polygon
            
        Returns:
            Area in square meters
        """
        if len(coordinates) < 3:
            raise ValueError("Polygon must have at least 3 coordinates")
        
        # Ensure polygon is closed
        if coordinates[0] != coordinates[-1]:
            coordinates = coordinates + [coordinates[0]]
        
        # Convert to radians
        coords_rad = [(math.radians(c.latitude), math.radians(c.longitude)) for c in coordinates]
        
        # Calculate spherical excess
        n = len(coords_rad) - 1
        S = -(n - 2) * math.pi
        
        for i in range(n):
            lat1, lon1 = coords_rad[i]
            lat2, lon2 = coords_rad[i + 1]
            
            if i == 0:
                lat0, lon0 = coords_rad[n - 1]
            else:
                lat0, lon0 = coords_rad[i - 1]
            
            # Calculate angle
            E = 2 * math.atan2(
                math.tan((lon2 - lon1) / 2),
                1 / math.cos(lat1) + 1 / math.cos(lat2)
            )
            S += E
        
        # Convert to area
        area = abs(S) * (self.EARTH_RADIUS ** 2)
        
        logger.info(f"Polygon area calculated: {area:.2f} m²")
        return area
    
    def generate_search_grid(
        self,
        boundary: BoundingBox,
        grid_spacing: float,
        pattern: SearchPattern = SearchPattern.GRID,
        overlap: float = 0.1
    ) -> List[List[Coordinate]]:
        """
        Generate search grid waypoints for systematic area coverage.
        
        Args:
            boundary: Search area boundary
            grid_spacing: Spacing between grid lines in meters
            pattern: Search pattern type
            overlap: Overlap percentage between tracks (0.0 to 1.0)
            
        Returns:
            List of tracks, each containing waypoint coordinates
        """
        logger.info(f"Generating {pattern.value} search grid with {grid_spacing}m spacing")
        
        if pattern == SearchPattern.GRID:
            return self._generate_grid_pattern(boundary, grid_spacing, overlap)
        elif pattern == SearchPattern.SPIRAL:
            return self._generate_spiral_pattern(boundary, grid_spacing)
        elif pattern == SearchPattern.RANDOM:
            return self._generate_random_pattern(boundary, grid_spacing)
        else:
            raise ValueError(f"Unsupported search pattern: {pattern}")
    
    def _generate_grid_pattern(
        self,
        boundary: BoundingBox,
        grid_spacing: float,
        overlap: float
    ) -> List[List[Coordinate]]:
        """Generate systematic grid search pattern."""
        tracks = []
        
        # Calculate effective spacing with overlap
        effective_spacing = grid_spacing * (1 - overlap)
        
        # Convert spacing to degrees (approximate)
        lat_spacing = effective_spacing / 111000  # ~111km per degree latitude
        
        # Calculate number of tracks
        lat_range = boundary.north - boundary.south
        num_tracks = max(1, int(lat_range / lat_spacing))
        
        # Generate tracks
        for i in range(num_tracks + 1):
            lat = boundary.south + (lat_range * i / num_tracks)
            
            if i % 2 == 0:  # West to East
                start = Coordinate(lat, boundary.west)
                end = Coordinate(lat, boundary.east)
            else:  # East to West
                start = Coordinate(lat, boundary.east)
                end = Coordinate(lat, boundary.west)
            
            tracks.append([start, end])
        
        logger.info(f"Generated {len(tracks)} grid tracks")
        return tracks
    
    def _generate_spiral_pattern(
        self,
        boundary: BoundingBox,
        grid_spacing: float
    ) -> List[List[Coordinate]]:
        """Generate spiral search pattern."""
        center = boundary.center()
        waypoints = [center]
        
        # Calculate maximum radius
        max_distance = max(
            self.haversine_distance(center, Coordinate(boundary.north, boundary.west)),
            self.haversine_distance(center, Coordinate(boundary.north, boundary.east)),
            self.haversine_distance(center, Coordinate(boundary.south, boundary.west)),
            self.haversine_distance(center, Coordinate(boundary.south, boundary.east))
        )
        
        # Generate spiral
        radius = grid_spacing
        angle = 0
        angle_increment = math.radians(30)  # 30 degrees
        
        while radius < max_distance:
            bearing = math.degrees(angle)
            point = self.destination_point(center, radius, bearing)
            
            if boundary.contains(point):
                waypoints.append(point)
            
            angle += angle_increment
            radius += grid_spacing / (2 * math.pi)  # Gradually increase radius
        
        logger.info(f"Generated spiral pattern with {len(waypoints)} waypoints")
        return [waypoints]
    
    def _generate_random_pattern(
        self,
        boundary: BoundingBox,
        grid_spacing: float,
        num_points: int = 50
    ) -> List[List[Coordinate]]:
        """Generate random search pattern."""
        import random
        
        waypoints = []
        
        for _ in range(num_points):
            lat = random.uniform(boundary.south, boundary.north)
            lon = random.uniform(boundary.west, boundary.east)
            waypoints.append(Coordinate(lat, lon))
        
        logger.info(f"Generated random pattern with {len(waypoints)} waypoints")
        return [waypoints]
    
    def optimize_waypoint_order(self, waypoints: List[Coordinate]) -> List[Coordinate]:
        """
        Optimize waypoint order using nearest neighbor heuristic.
        
        Args:
            waypoints: List of waypoints to optimize
            
        Returns:
            Optimized waypoint order
        """
        if len(waypoints) <= 2:
            return waypoints
        
        logger.info(f"Optimizing order of {len(waypoints)} waypoints")
        
        optimized = [waypoints[0]]  # Start with first waypoint
        remaining = waypoints[1:]
        
        while remaining:
            current = optimized[-1]
            
            # Find nearest remaining waypoint
            nearest_idx = 0
            min_distance = self.haversine_distance(current, remaining[0])
            
            for i, waypoint in enumerate(remaining[1:], 1):
                distance = self.haversine_distance(current, waypoint)
                if distance < min_distance:
                    min_distance = distance
                    nearest_idx = i
            
            # Add nearest waypoint and remove from remaining
            optimized.append(remaining.pop(nearest_idx))
        
        # Calculate total distances
        original_distance = self._calculate_total_distance(waypoints)
        optimized_distance = self._calculate_total_distance(optimized)
        
        improvement = ((original_distance - optimized_distance) / original_distance) * 100
        logger.info(f"Waypoint optimization completed: {improvement:.1f}% distance reduction")
        
        return optimized
    
    def _calculate_total_distance(self, waypoints: List[Coordinate]) -> float:
        """Calculate total distance for a waypoint sequence."""
        if len(waypoints) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(waypoints) - 1):
            total += self.haversine_distance(waypoints[i], waypoints[i + 1])
        
        return total
    
    def calculate_search_time(
        self,
        waypoints: List[Coordinate],
        drone_speed: float,
        hover_time: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate estimated search time for waypoint sequence.
        
        Args:
            waypoints: List of waypoints
            drone_speed: Drone speed in m/s
            hover_time: Time to hover at each waypoint in seconds
            
        Returns:
            Dictionary with time estimates
        """
        total_distance = self._calculate_total_distance(waypoints)
        flight_time = total_distance / drone_speed
        total_hover_time = hover_time * len(waypoints)
        total_time = flight_time + total_hover_time
        
        time_estimates = {
            "total_distance_m": total_distance,
            "flight_time_s": flight_time,
            "hover_time_s": total_hover_time,
            "total_time_s": total_time,
            "total_time_minutes": total_time / 60,
            "average_speed_ms": drone_speed
        }
        
        logger.info(f"Search time calculated: {total_time/60:.1f} minutes for {len(waypoints)} waypoints")
        return time_estimates
    
    def divide_search_area(
        self,
        boundary: BoundingBox,
        num_sections: int,
        method: str = "grid"
    ) -> List[BoundingBox]:
        """
        Divide search area into multiple sections for multi-drone operations.
        
        Args:
            boundary: Original search area
            num_sections: Number of sections to create
            method: Division method ("grid" or "strips")
            
        Returns:
            List of bounding boxes for each section
        """
        logger.info(f"Dividing search area into {num_sections} sections using {method} method")
        
        if method == "grid":
            return self._divide_grid_sections(boundary, num_sections)
        elif method == "strips":
            return self._divide_strip_sections(boundary, num_sections)
        else:
            raise ValueError(f"Unsupported division method: {method}")
    
    def _divide_grid_sections(self, boundary: BoundingBox, num_sections: int) -> List[BoundingBox]:
        """Divide area into grid sections."""
        # Calculate grid dimensions
        cols = int(math.sqrt(num_sections))
        rows = math.ceil(num_sections / cols)
        
        sections = []
        lat_step = (boundary.north - boundary.south) / rows
        lon_step = (boundary.east - boundary.west) / cols
        
        for row in range(rows):
            for col in range(cols):
                if len(sections) >= num_sections:
                    break
                
                south = boundary.south + row * lat_step
                north = boundary.south + (row + 1) * lat_step
                west = boundary.west + col * lon_step
                east = boundary.west + (col + 1) * lon_step
                
                sections.append(BoundingBox(north, south, east, west))
        
        return sections
    
    def _divide_strip_sections(self, boundary: BoundingBox, num_sections: int) -> List[BoundingBox]:
        """Divide area into horizontal strips."""
        sections = []
        lat_step = (boundary.north - boundary.south) / num_sections
        
        for i in range(num_sections):
            south = boundary.south + i * lat_step
            north = boundary.south + (i + 1) * lat_step
            
            sections.append(BoundingBox(north, south, boundary.east, boundary.west))
        
        return sections


# Utility functions
def create_bounding_box_from_coordinates(coordinates: List[Coordinate]) -> BoundingBox:
    """Create bounding box from a list of coordinates."""
    if not coordinates:
        raise ValueError("Cannot create bounding box from empty coordinate list")
    
    lats = [coord.latitude for coord in coordinates]
    lons = [coord.longitude for coord in coordinates]
    
    return BoundingBox(
        north=max(lats),
        south=min(lats),
        east=max(lons),
        west=min(lons)
    )


def validate_search_area(boundary: BoundingBox, max_area_km2: float = 100.0) -> bool:
    """
    Validate that search area is within reasonable limits.
    
    Args:
        boundary: Bounding box to validate
        max_area_km2: Maximum allowed area in square kilometers
        
    Returns:
        True if valid, False otherwise
    """
    calculator = GeometryCalculator()
    
    # Create polygon from bounding box
    corners = [
        Coordinate(boundary.north, boundary.west),
        Coordinate(boundary.north, boundary.east),
        Coordinate(boundary.south, boundary.east),
        Coordinate(boundary.south, boundary.west)
    ]
    
    area_m2 = calculator.calculate_polygon_area(corners)
    area_km2 = area_m2 / 1_000_000
    
    is_valid = area_km2 <= max_area_km2
    
    logger.info(f"Search area validation: {area_km2:.2f} km² {'valid' if is_valid else 'invalid'}")
    return is_valid