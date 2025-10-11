"""
Geometry utilities for SAR Mission Commander
Handles coordinate calculations, search patterns, and area coverage
"""
import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

class GeometryCalculator:
    """Geometric calculations for SAR mission planning."""
    
    @staticmethod
    def calculate_polygon_area(coordinates: List[Tuple[float, float]]) -> float:
        """Calculate the area of a polygon in square kilometers."""
        if len(coordinates) < 3:
            return 0.0
        
        # Simple area calculation using shoelace formula
        area = 0.0
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        area = abs(area) / 2.0
        
        # Convert to km² (approximate)
        area_km_sq = area * (111 * 111)  # Rough conversion
        
        return area_km_sq
    
    @staticmethod
    def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in meters."""
        return _calculate_distance(coord1[0], coord1[1], coord2[0], coord2[1])
    
    @staticmethod
    def generate_search_grid(
        boundary: List[Tuple[float, float]], 
        grid_spacing: float,
        overlap_percentage: float = 20
    ) -> List[Tuple[float, float]]:
        """Generate a systematic search grid within a boundary."""
        if len(boundary) < 3:
            return []
        
        # Simple grid generation
        grid_points = []
        
        # Find bounds
        min_lat = min(coord[0] for coord in boundary)
        max_lat = max(coord[0] for coord in boundary)
        min_lng = min(coord[1] for coord in boundary)
        max_lng = max(coord[1] for coord in boundary)
        
        # Generate grid
        lat_step = grid_spacing / 111000.0  # Convert to degrees
        lng_step = grid_spacing / (111000.0 * math.cos(math.radians((min_lat + max_lat) / 2)))
        
        lat = min_lat
        while lat <= max_lat:
            lng = min_lng
            while lng <= max_lng:
                grid_points.append((lat, lng))
                lng += lng_step
            lat += lat_step
        
        return grid_points
    
    @staticmethod
    def divide_area_for_drones(
        boundary: List[Tuple[float, float]], 
        drone_count: int,
        launch_point: Tuple[float, float]
    ) -> List[Dict]:
        """Divide search area optimally between multiple drones."""
        if drone_count <= 0 or len(boundary) < 3:
            return []
        
        assignments = []
        
        if drone_count == 1:
            # Single drone gets entire area
            return [{
                "drone_id": 1,
                "search_area": boundary,
                "estimated_area": GeometryCalculator.calculate_polygon_area(boundary)
            }]
        
        # For multiple drones, divide the area
        area_per_drone = GeometryCalculator.calculate_polygon_area(boundary) / drone_count
        
        # Simple division - in practice, this would be more sophisticated
        for i in range(drone_count):
            assignments.append({
                "drone_id": i + 1,
                "search_area": boundary,  # Simplified - all drones get same area
                "estimated_area": area_per_drone
            })
        
        return assignments

@dataclass
class Coordinate:
    """Represents a geographic coordinate"""
    latitude: float
    longitude: float
    altitude: float = 0.0

@dataclass
class SearchPattern:
    """Represents a search pattern configuration"""
    pattern_type: str  # "grid", "spiral", "lawnmower", "zigzag"
    spacing: float  # Distance between search lines in meters
    altitude: float  # Search altitude in meters
    start_coordinate: Coordinate
    end_coordinate: Coordinate

def calculate_search_pattern(
    pattern_type: str,
    center_lat: float,
    center_lon: float,
    radius: float,
    altitude: float = 100.0,
    spacing: float = 50.0
) -> List[Coordinate]:
    """
    Calculate search pattern coordinates based on pattern type
    
    Args:
        pattern_type: Type of search pattern ("grid", "spiral", "lawnmower")
        center_lat: Center latitude
        center_lon: Center longitude
        radius: Search radius in meters
        altitude: Search altitude in meters
        spacing: Spacing between search lines in meters
    
    Returns:
        List of coordinates for the search pattern
    """
    coordinates = []
    
    if pattern_type == "grid":
        coordinates = _calculate_grid_pattern(center_lat, center_lon, radius, spacing, altitude)
    elif pattern_type == "spiral":
        coordinates = _calculate_spiral_pattern(center_lat, center_lon, radius, spacing, altitude)
    elif pattern_type == "lawnmower":
        coordinates = _calculate_lawnmower_pattern(center_lat, center_lon, radius, spacing, altitude)
    else:
        # Default to grid pattern
        coordinates = _calculate_grid_pattern(center_lat, center_lon, radius, spacing, altitude)
    
    return coordinates

def _calculate_grid_pattern(
    center_lat: float,
    center_lon: float,
    radius: float,
    spacing: float,
    altitude: float
) -> List[Coordinate]:
    """Calculate grid search pattern"""
    coordinates = []
    
    # Convert radius to degrees (approximate)
    lat_radius = radius / 111000.0  # 1 degree latitude ≈ 111km
    lon_radius = radius / (111000.0 * math.cos(math.radians(center_lat)))
    
    # Calculate grid points
    steps = int(radius * 2 / spacing)
    
    for i in range(steps + 1):
        for j in range(steps + 1):
            lat_offset = (i - steps/2) * spacing / 111000.0
            lon_offset = (j - steps/2) * spacing / (111000.0 * math.cos(math.radians(center_lat)))
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            # Check if within radius
            distance = _calculate_distance(center_lat, center_lon, lat, lon)
            if distance <= radius:
                coordinates.append(Coordinate(lat, lon, altitude))
    
    return coordinates

def _calculate_spiral_pattern(
    center_lat: float,
    center_lon: float,
    radius: float,
    spacing: float,
    altitude: float
) -> List[Coordinate]:
    """Calculate spiral search pattern"""
    coordinates = []
    
    # Convert radius to degrees
    lat_radius = radius / 111000.0
    lon_radius = radius / (111000.0 * math.cos(math.radians(center_lat)))
    
    # Generate spiral points
    max_angle = 8 * math.pi  # 4 full rotations
    angle_step = 0.1
    
    angle = 0
    while angle <= max_angle:
        # Calculate spiral radius
        spiral_radius = (angle / max_angle) * radius
        
        # Convert to lat/lon offsets
        lat_offset = spiral_radius * math.cos(angle) / 111000.0
        lon_offset = spiral_radius * math.sin(angle) / (111000.0 * math.cos(math.radians(center_lat)))
        
        lat = center_lat + lat_offset
        lon = center_lon + lon_offset
        
        coordinates.append(Coordinate(lat, lon, altitude))
        
        angle += angle_step
    
    return coordinates

def _calculate_lawnmower_pattern(
    center_lat: float,
    center_lon: float,
    radius: float,
    spacing: float,
    altitude: float
) -> List[Coordinate]:
    """Calculate lawnmower search pattern"""
    coordinates = []
    
    # Convert radius to degrees
    lat_radius = radius / 111000.0
    lon_radius = radius / (111000.0 * math.cos(math.radians(center_lat)))
    
    # Calculate number of parallel lines
    num_lines = int(radius * 2 / spacing)
    
    for i in range(num_lines + 1):
        lat_offset = (i - num_lines/2) * spacing / 111000.0
        
        # Alternate direction for lawnmower effect
        if i % 2 == 0:
            lon_start = center_lon - lon_radius
            lon_end = center_lon + lon_radius
        else:
            lon_start = center_lon + lon_radius
            lon_end = center_lon - lon_radius
        
        # Generate points along the line
        num_points = 20  # Number of points per line
        for j in range(num_points + 1):
            lon_offset = lon_start + (lon_end - lon_start) * (j / num_points)
            lon_offset -= center_lon
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            # Check if within radius
            distance = _calculate_distance(center_lat, center_lon, lat, lon)
            if distance <= radius:
                coordinates.append(Coordinate(lat, lon, altitude))
    
    return coordinates

def calculate_area_coverage(
    search_area: List[Coordinate],
    drone_speed: float,
    flight_time: float
) -> Dict[str, Any]:
    """
    Calculate area coverage metrics
    
    Args:
        search_area: List of coordinates in search area
        drone_speed: Drone speed in m/s
        flight_time: Available flight time in seconds
    
    Returns:
        Dictionary with coverage metrics
    """
    if not search_area:
        return {
            "total_area": 0,
            "coverage_percentage": 0,
            "estimated_flight_time": 0,
            "coverage_efficiency": 0
        }
    
    # Calculate total search area (simplified)
    total_area = len(search_area) * 100  # Assume 100m² per point
    
    # Calculate distance to cover
    total_distance = 0
    for i in range(len(search_area) - 1):
        coord1 = search_area[i]
        coord2 = search_area[i + 1]
        distance = _calculate_distance(
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        )
        total_distance += distance
    
    # Calculate coverage metrics
    estimated_flight_time = total_distance / drone_speed if drone_speed > 0 else 0
    coverage_percentage = min(100, (flight_time / estimated_flight_time * 100)) if estimated_flight_time > 0 else 0
    coverage_efficiency = total_area / estimated_flight_time if estimated_flight_time > 0 else 0
    
    return {
        "total_area": total_area,
        "coverage_percentage": coverage_percentage,
        "estimated_flight_time": estimated_flight_time,
        "coverage_efficiency": coverage_efficiency,
        "total_distance": total_distance
    }

def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing between two coordinates"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def is_point_in_polygon(point: Coordinate, polygon: List[Coordinate]) -> bool:
    """Check if a point is inside a polygon"""
    x, y = point.longitude, point.latitude
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0].longitude, polygon[0].latitude
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n].longitude, polygon[i % n].latitude
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside