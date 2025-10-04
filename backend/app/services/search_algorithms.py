import logging
from typing import List, Dict, Any, Tuple, Optional
import math
from enum import Enum
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchPattern(Enum):
    GRID = "grid"
    SPIRAL = "spiral"
    EXPANDING_SQUARE = "expanding_square"
    SECTOR = "sector"
    PARALLEL_TRACK = "parallel_track"
    CREEPING_LINE = "creeping_line"
    CONTOUR = "contour"

class SearchAlgorithms:
    """Advanced search pattern algorithms for SAR missions"""
    
    @staticmethod
    def generate_search_pattern(
        pattern_type: SearchPattern,
        center: Dict[str, float],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, float]]:
        """
        Generate search pattern waypoints based on pattern type
        """
        try:
            if pattern_type == SearchPattern.GRID:
                return SearchAlgorithms.generate_grid_pattern(
                    center,
                    parameters.get('width_m', 1000),
                    parameters.get('height_m', 1000),
                    parameters.get('spacing_m', 50),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.SPIRAL:
                return SearchAlgorithms.generate_spiral_pattern(
                    center,
                    parameters.get('max_radius_m', 500),
                    parameters.get('spacing_m', 30),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.EXPANDING_SQUARE:
                return SearchAlgorithms.generate_expanding_square(
                    center,
                    parameters.get('max_size_m', 800),
                    parameters.get('step_m', 100),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.SECTOR:
                return SearchAlgorithms.generate_sector_pattern(
                    center,
                    parameters.get('radius_m', 400),
                    parameters.get('sectors', 8),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.PARALLEL_TRACK:
                return SearchAlgorithms.generate_parallel_track(
                    center,
                    parameters.get('width_m', 1000),
                    parameters.get('height_m', 1000),
                    parameters.get('track_spacing_m', 100),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.CREEPING_LINE:
                return SearchAlgorithms.generate_creeping_line(
                    center,
                    parameters.get('length_m', 1000),
                    parameters.get('width_m', 200),
                    parameters.get('spacing_m', 50),
                    parameters.get('altitude_m', 50)
                )
            elif pattern_type == SearchPattern.CONTOUR:
                return SearchAlgorithms.generate_contour_pattern(
                    center,
                    parameters.get('radius_m', 300),
                    parameters.get('contour_spacing_m', 50),
                    parameters.get('altitude_m', 50)
                )
            else:
                raise ValueError(f"Unknown search pattern: {pattern_type}")
                
        except Exception as e:
            logger.error(f"Search pattern generation failed: {e}")
            raise
    
    @staticmethod
    def generate_grid_pattern(
        center: Dict[str, float],
        width_m: float,
        height_m: float,
        spacing_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate grid search pattern waypoints"""
        waypoints = []
        
        # Convert meters to degrees (approximate)
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        half_width = width_m / 2
        half_height = height_m / 2
        
        # Calculate grid dimensions
        rows = int(height_m / spacing_m) + 1
        cols = int(width_m / spacing_m) + 1
        
        # Generate grid with serpentine pattern
        for row in range(rows):
            y = -half_height + (row * spacing_m)
            
            if row % 2 == 0:
                # Left to right
                for col in range(cols):
                    x = -half_width + (col * spacing_m)
                    waypoints.append({
                        'lat': center['lat'] + (y * lat_per_m),
                        'lon': center['lon'] + (x * lon_per_m),
                        'alt': altitude_m,
                        'index': len(waypoints),
                        'pattern': 'grid'
                    })
            else:
                # Right to left
                for col in range(cols - 1, -1, -1):
                    x = -half_width + (col * spacing_m)
                    waypoints.append({
                        'lat': center['lat'] + (y * lat_per_m),
                        'lon': center['lon'] + (x * lon_per_m),
                        'alt': altitude_m,
                        'index': len(waypoints),
                        'pattern': 'grid'
                    })
        
        logger.info(f"Generated {len(waypoints)} waypoints for grid pattern")
        return waypoints
    
    @staticmethod
    def generate_spiral_pattern(
        center: Dict[str, float],
        max_radius_m: float,
        spacing_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate spiral search pattern (Archimedean spiral)"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        # Spiral parameters
        a = spacing_m / (2 * math.pi)  # Distance between turns
        theta = 0
        max_theta = max_radius_m / a * 2 * math.pi
        theta_step = 0.1
        
        while theta <= max_theta:
            r = a * theta
            
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            
            waypoints.append({
                'lat': center['lat'] + (y * lat_per_m),
                'lon': center['lon'] + (x * lon_per_m),
                'alt': altitude_m,
                'index': len(waypoints),
                'pattern': 'spiral'
            })
            
            theta += theta_step
        
        logger.info(f"Generated {len(waypoints)} waypoints for spiral pattern")
        return waypoints
    
    @staticmethod
    def generate_expanding_square(
        center: Dict[str, float],
        max_size_m: float,
        step_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate expanding square search pattern"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        size = step_m
        
        while size <= max_size_m:
            half = size / 2
            
            # Generate square perimeter
            square_points = [
                # Top edge (left to right)
                *[(center['lat'] + (half * lat_per_m), center['lon'] + (x * lon_per_m)) 
                  for x in np.arange(-half, half + step_m, step_m)],
                # Right edge (top to bottom)
                *[(center['lat'] + (y * lat_per_m), center['lon'] + (half * lon_per_m)) 
                  for y in np.arange(half, -half - step_m, -step_m)],
                # Bottom edge (right to left)
                *[(center['lat'] + (-half * lat_per_m), center['lon'] + (x * lon_per_m)) 
                  for x in np.arange(half, -half - step_m, -step_m)],
                # Left edge (bottom to top)
                *[(center['lat'] + (y * lat_per_m), center['lon'] + (-half * lon_per_m)) 
                  for y in np.arange(-half, half + step_m, step_m)]
            ]
            
            for lat, lon in square_points:
                waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'alt': altitude_m,
                    'index': len(waypoints),
                    'pattern': 'expanding_square',
                    'square_size': size
                })
            
            size += step_m
        
        logger.info(f"Generated {len(waypoints)} waypoints for expanding square")
        return waypoints
    
    @staticmethod
    def generate_sector_pattern(
        center: Dict[str, float],
        radius_m: float,
        sectors: int,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate sector search pattern"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        # Generate radial lines for each sector
        for sector in range(sectors):
            angle = (2 * math.pi * sector) / sectors
            
            # Generate points along radial line
            for distance in np.arange(50, radius_m + 50, 50):  # 50m intervals
                x = distance * math.cos(angle)
                y = distance * math.sin(angle)
                
                waypoints.append({
                    'lat': center['lat'] + (y * lat_per_m),
                    'lon': center['lon'] + (x * lon_per_m),
                    'alt': altitude_m,
                    'index': len(waypoints),
                    'pattern': 'sector',
                    'sector': sector,
                    'distance': distance
                })
        
        logger.info(f"Generated {len(waypoints)} waypoints for sector pattern")
        return waypoints
    
    @staticmethod
    def generate_parallel_track(
        center: Dict[str, float],
        width_m: float,
        height_m: float,
        track_spacing_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate parallel track search pattern"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        half_width = width_m / 2
        half_height = height_m / 2
        
        # Generate parallel tracks
        track_count = int(height_m / track_spacing_m) + 1
        
        for track in range(track_count):
            y = -half_height + (track * track_spacing_m)
            
            # Generate waypoints along track
            for x in np.arange(-half_width, half_width + 50, 50):
                waypoints.append({
                    'lat': center['lat'] + (y * lat_per_m),
                    'lon': center['lon'] + (x * lon_per_m),
                    'alt': altitude_m,
                    'index': len(waypoints),
                    'pattern': 'parallel_track',
                    'track': track
                })
        
        logger.info(f"Generated {len(waypoints)} waypoints for parallel track pattern")
        return waypoints
    
    @staticmethod
    def generate_creeping_line(
        center: Dict[str, float],
        length_m: float,
        width_m: float,
        spacing_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate creeping line search pattern"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        half_length = length_m / 2
        half_width = width_m / 2
        
        # Generate creeping line pattern
        line_count = int(width_m / spacing_m) + 1
        
        for line in range(line_count):
            y_offset = -half_width + (line * spacing_m)
            
            # Generate waypoints along line
            for x in np.arange(-half_length, half_length + 25, 25):
                waypoints.append({
                    'lat': center['lat'] + (y_offset * lat_per_m),
                    'lon': center['lon'] + (x * lon_per_m),
                    'alt': altitude_m,
                    'index': len(waypoints),
                    'pattern': 'creeping_line',
                    'line': line
                })
        
        logger.info(f"Generated {len(waypoints)} waypoints for creeping line pattern")
        return waypoints
    
    @staticmethod
    def generate_contour_pattern(
        center: Dict[str, float],
        radius_m: float,
        contour_spacing_m: float,
        altitude_m: float = 50
    ) -> List[Dict[str, float]]:
        """Generate contour search pattern"""
        waypoints = []
        
        lat_per_m = 1 / 111000
        lon_per_m = 1 / (111000 * math.cos(math.radians(center['lat'])))
        
        # Generate concentric circles
        for radius in np.arange(contour_spacing_m, radius_m + contour_spacing_m, contour_spacing_m):
            # Generate points around circle
            for angle in np.arange(0, 2 * math.pi, 0.1):
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                waypoints.append({
                    'lat': center['lat'] + (y * lat_per_m),
                    'lon': center['lon'] + (x * lon_per_m),
                    'alt': altitude_m,
                    'index': len(waypoints),
                    'pattern': 'contour',
                    'radius': radius
                })
        
        logger.info(f"Generated {len(waypoints)} waypoints for contour pattern")
        return waypoints
    
    @staticmethod
    def optimize_waypoint_order(
        waypoints: List[Dict[str, float]],
        start_position: Dict[str, float]
    ) -> List[Dict[str, float]]:
        """Optimize waypoint order using nearest neighbor (simple TSP approximation)"""
        if not waypoints:
            return []
        
        optimized = []
        remaining = waypoints.copy()
        current = start_position
        
        while remaining:
            # Find nearest waypoint
            nearest_idx = 0
            nearest_dist = float('inf')
            
            for i, wp in enumerate(remaining):
                dist = math.sqrt(
                    (wp['lat'] - current['lat']) ** 2 +
                    (wp['lon'] - current['lon']) ** 2
                )
                
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_idx = i
            
            nearest = remaining.pop(nearest_idx)
            optimized.append(nearest)
            current = nearest
        
        logger.info(f"Optimized {len(waypoints)} waypoints")
        return optimized
    
    @staticmethod
    def calculate_search_coverage(
        waypoints: List[Dict[str, float]],
        search_radius_m: float = 25
    ) -> Dict[str, Any]:
        """Calculate search coverage statistics"""
        if not waypoints:
            return {"coverage_percent": 0, "area_covered_km2": 0}
        
        # Calculate total area covered
        total_area_km2 = len(waypoints) * math.pi * (search_radius_m / 1000) ** 2
        
        # Calculate bounding box
        lats = [wp['lat'] for wp in waypoints]
        lons = [wp['lon'] for wp in waypoints]
        
        lat_min, lat_max = min(lats), max(lats)
        lon_min, lon_max = min(lons), max(lons)
        
        # Calculate bounding box area
        lat_diff = lat_max - lat_min
        lon_diff = lon_max - lon_min
        
        # Convert to km²
        lat_km = lat_diff * 111
        lon_km = lon_diff * 111 * math.cos(math.radians((lat_min + lat_max) / 2))
        bounding_area_km2 = lat_km * lon_km
        
        # Calculate coverage percentage
        coverage_percent = min(100, (total_area_km2 / bounding_area_km2) * 100) if bounding_area_km2 > 0 else 0
        
        return {
            "coverage_percent": coverage_percent,
            "area_covered_km2": total_area_km2,
            "bounding_area_km2": bounding_area_km2,
            "waypoint_count": len(waypoints),
            "search_radius_m": search_radius_m
        }
    
    @staticmethod
    def validate_waypoints(waypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        """Validate waypoint data"""
        if not waypoints:
            return {"valid": False, "errors": ["No waypoints provided"]}
        
        errors = []
        
        for i, wp in enumerate(waypoints):
            # Check required fields
            if 'lat' not in wp or 'lon' not in wp:
                errors.append(f"Waypoint {i}: Missing lat/lon")
                continue
            
            # Check latitude range
            if not (-90 <= wp['lat'] <= 90):
                errors.append(f"Waypoint {i}: Invalid latitude {wp['lat']}")
            
            # Check longitude range
            if not (-180 <= wp['lon'] <= 180):
                errors.append(f"Waypoint {i}: Invalid longitude {wp['lon']}")
            
            # Check altitude
            if 'alt' in wp and (wp['alt'] < 0 or wp['alt'] > 500):
                errors.append(f"Waypoint {i}: Invalid altitude {wp['alt']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "waypoint_count": len(waypoints)
        }

# Global instance
search_algorithms = SearchAlgorithms()