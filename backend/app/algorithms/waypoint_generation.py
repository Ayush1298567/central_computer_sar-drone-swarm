"""
Waypoint Generation Algorithm for SAR Drone Swarm
Implements real geometric algorithms using Shapely for generating efficient search patterns.
"""

import logging
import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.affinity import rotate

logger = logging.getLogger(__name__)

class WaypointGenerator:
    """Real waypoint generation using Shapely geometric operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_lawnmower_pattern(self, zone_coords: List[Tuple[float, float]], 
                                 altitude: float = 50.0, 
                                 spacing: float = 10.0,
                                 direction: float = 0.0) -> List[Dict[str, Any]]:
        """
        Generate lawnmower pattern waypoints for a zone using real geometric algorithms.
        
        Args:
            zone_coords: List of (lng, lat) coordinates defining the zone
            altitude: Flight altitude in meters
            spacing: Distance between parallel lines in meters
            direction: Direction of the pattern in degrees (0 = North)
            
        Returns:
            List of waypoint dictionaries with lat, lng, alt, and metadata
        """
        try:
            # Create Shapely polygon from coordinates
            zone_polygon = Polygon(zone_coords)
            
            if not zone_polygon.is_valid:
                self.logger.error("Invalid zone polygon provided for waypoint generation")
                return []
            
            # Get bounding box
            minx, miny, maxx, maxy = zone_polygon.bounds
            
            # Calculate number of lines needed
            width = maxx - minx
            height = maxy - miny
            diagonal = math.sqrt(width**2 + height**2)
            
            # Convert spacing from meters to degrees (approximate)
            # 1 degree latitude ≈ 111,320 meters
            # 1 degree longitude ≈ 111,320 * cos(latitude) meters
            center_lat = (miny + maxy) / 2
            lat_spacing = spacing / 111320.0
            lng_spacing = spacing / (111320.0 * math.cos(math.radians(center_lat)))
            
            # Generate parallel lines
            lines = []
            y = miny
            
            while y <= maxy:
                # Create horizontal line
                line = LineString([(minx, y), (maxx, y)])
                
                # Intersect line with zone polygon
                intersection = zone_polygon.intersection(line)
                
                if not intersection.is_empty:
                    # Extract waypoints from intersection
                    if hasattr(intersection, 'coords'):
                        coords = list(intersection.coords)
                    else:
                        # Handle MultiLineString case
                        coords = []
                        for geom in intersection.geoms:
                            coords.extend(list(geom.coords))
                    
                    if coords:
                        lines.append({
                            'line': intersection,
                            'y': y,
                            'coords': coords
                        })
                
                y += lat_spacing
            
            # Generate waypoints from lines
            waypoints = []
            waypoint_id = 0
            
            for line_data in lines:
                coords = line_data['coords']
                
                # Sort coordinates by longitude for proper order
                coords.sort(key=lambda c: c[0])
                
                # Create waypoints
                for i, (lng, lat) in enumerate(coords):
                    waypoint = {
                        'id': waypoint_id,
                        'lat': lat,
                        'lng': lng,
                        'alt': altitude,
                        'sequence': waypoint_id,
                        'line_id': lines.index(line_data),
                        'position_in_line': i,
                        'type': 'search',
                        'metadata': {
                            'pattern': 'lawnmower',
                            'spacing': spacing,
                            'direction': direction,
                            'zone_area': zone_polygon.area
                        }
                    }
                    waypoints.append(waypoint)
                    waypoint_id += 1
            
            # Apply rotation if specified
            if direction != 0:
                waypoints = self._rotate_waypoints(waypoints, direction, zone_polygon.centroid)
            
            # Optimize waypoint order for efficiency
            waypoints = self._optimize_waypoint_order(waypoints)
            
            self.logger.info(f"Generated {len(waypoints)} waypoints for zone with {len(zone_coords)} vertices")
            return waypoints
            
        except Exception as e:
            self.logger.error(f"Error generating lawnmower pattern: {e}", exc_info=True)
            return []
    
    def generate_spiral_pattern(self, zone_coords: List[Tuple[float, float]], 
                              altitude: float = 50.0, 
                              spacing: float = 10.0,
                              center: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Generate spiral pattern waypoints for a zone.
        
        Args:
            zone_coords: List of (lng, lat) coordinates defining the zone
            altitude: Flight altitude in meters
            spacing: Distance between spiral turns in meters
            center: Center point for spiral (if None, uses zone centroid)
            
        Returns:
            List of waypoint dictionaries
        """
        try:
            zone_polygon = Polygon(zone_coords)
            
            if not zone_polygon.is_valid:
                self.logger.error("Invalid zone polygon for spiral pattern")
                return []
            
            # Use provided center or calculate centroid
            if center is None:
                center = (zone_polygon.centroid.x, zone_polygon.centroid.y)
            
            center_lng, center_lat = center
            
            # Convert spacing to degrees
            lat_spacing = spacing / 111320.0
            lng_spacing = spacing / (111320.0 * math.cos(math.radians(center_lat)))
            
            waypoints = []
            waypoint_id = 0
            
            # Generate spiral points
            max_radius = max(zone_polygon.bounds[2] - zone_polygon.bounds[0],
                           zone_polygon.bounds[3] - zone_polygon.bounds[1]) / 2
            
            radius = 0
            angle = 0
            
            while radius < max_radius:
                # Calculate spiral point
                lng = center_lng + radius * math.cos(angle) * lng_spacing
                lat = center_lat + radius * math.sin(angle) * lat_spacing
                
                point = Point(lng, lat)
                
                # Check if point is within zone
                if zone_polygon.contains(point):
                    waypoint = {
                        'id': waypoint_id,
                        'lat': lat,
                        'lng': lng,
                        'alt': altitude,
                        'sequence': waypoint_id,
                        'radius': radius,
                        'angle': math.degrees(angle),
                        'type': 'search',
                        'metadata': {
                            'pattern': 'spiral',
                            'spacing': spacing,
                            'center': center
                        }
                    }
                    waypoints.append(waypoint)
                    waypoint_id += 1
                
                # Increment angle and radius
                angle += 0.1  # radians
                radius = spacing * angle / (2 * math.pi)
            
            self.logger.info(f"Generated {len(waypoints)} spiral waypoints")
            return waypoints
            
        except Exception as e:
            self.logger.error(f"Error generating spiral pattern: {e}", exc_info=True)
            return []
    
    def generate_grid_pattern(self, zone_coords: List[Tuple[float, float]], 
                            altitude: float = 50.0, 
                            spacing: float = 10.0,
                            angle: float = 0.0) -> List[Dict[str, Any]]:
        """
        Generate grid pattern waypoints for a zone.
        
        Args:
            zone_coords: List of (lng, lat) coordinates defining the zone
            altitude: Flight altitude in meters
            spacing: Distance between grid points in meters
            angle: Rotation angle for the grid in degrees
            
        Returns:
            List of waypoint dictionaries
        """
        try:
            zone_polygon = Polygon(zone_coords)
            
            if not zone_polygon.is_valid:
                self.logger.error("Invalid zone polygon for grid pattern")
                return []
            
            # Get bounding box
            minx, miny, maxx, maxy = zone_polygon.bounds
            
            # Convert spacing to degrees
            center_lat = (miny + maxy) / 2
            lat_spacing = spacing / 111320.0
            lng_spacing = spacing / (111320.0 * math.cos(math.radians(center_lat)))
            
            waypoints = []
            waypoint_id = 0
            
            # Generate grid points
            y = miny
            while y <= maxy:
                x = minx
                while x <= maxx:
                    point = Point(x, y)
                    
                    # Check if point is within zone
                    if zone_polygon.contains(point):
                        waypoint = {
                            'id': waypoint_id,
                            'lat': y,
                            'lng': x,
                            'alt': altitude,
                            'sequence': waypoint_id,
                            'grid_x': x,
                            'grid_y': y,
                            'type': 'search',
                            'metadata': {
                                'pattern': 'grid',
                                'spacing': spacing,
                                'angle': angle
                            }
                        }
                        waypoints.append(waypoint)
                        waypoint_id += 1
                    
                    x += lng_spacing
                y += lat_spacing
            
            # Apply rotation if specified
            if angle != 0:
                waypoints = self._rotate_waypoints(waypoints, angle, zone_polygon.centroid)
            
            self.logger.info(f"Generated {len(waypoints)} grid waypoints")
            return waypoints
            
        except Exception as e:
            self.logger.error(f"Error generating grid pattern: {e}", exc_info=True)
            return []
    
    def _rotate_waypoints(self, waypoints: List[Dict[str, Any]], 
                         angle_degrees: float, 
                         center: Tuple[float, float]) -> List[Dict[str, Any]]:
        """Rotate waypoints around a center point"""
        try:
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            center_lng, center_lat = center
            
            for waypoint in waypoints:
                # Translate to origin
                x = waypoint['lng'] - center_lng
                y = waypoint['lat'] - center_lat
                
                # Rotate
                new_x = x * cos_a - y * sin_a
                new_y = x * sin_a + y * cos_a
                
                # Translate back
                waypoint['lng'] = new_x + center_lng
                waypoint['lat'] = new_y + center_lat
            
            return waypoints
            
        except Exception as e:
            self.logger.error(f"Error rotating waypoints: {e}")
            return waypoints
    
    def _optimize_waypoint_order(self, waypoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize waypoint order to minimize travel distance using nearest neighbor"""
        try:
            if len(waypoints) <= 1:
                return waypoints
            
            # Simple nearest neighbor optimization
            optimized = [waypoints[0]]  # Start with first waypoint
            remaining = waypoints[1:].copy()
            
            while remaining:
                current = optimized[-1]
                current_point = Point(current['lng'], current['lat'])
                
                # Find nearest remaining waypoint
                min_distance = float('inf')
                nearest_index = 0
                
                for i, waypoint in enumerate(remaining):
                    waypoint_point = Point(waypoint['lng'], waypoint['lat'])
                    distance = current_point.distance(waypoint_point)
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_index = i
                
                # Add nearest waypoint
                nearest = remaining.pop(nearest_index)
                nearest['sequence'] = len(optimized)
                optimized.append(nearest)
            
            self.logger.info(f"Optimized waypoint order for {len(waypoints)} waypoints")
            return optimized
            
        except Exception as e:
            self.logger.error(f"Error optimizing waypoint order: {e}")
            return waypoints
    
    def calculate_waypoint_distances(self, waypoints: List[Dict[str, Any]]) -> List[float]:
        """Calculate distances between consecutive waypoints"""
        try:
            distances = []
            
            for i in range(len(waypoints) - 1):
                wp1 = waypoints[i]
                wp2 = waypoints[i + 1]
                
                # Use Haversine formula for accurate distance calculation
                distance = self._haversine_distance(
                    wp1['lat'], wp1['lng'],
                    wp2['lat'], wp2['lng']
                )
                
                distances.append(distance)
            
            return distances
            
        except Exception as e:
            self.logger.error(f"Error calculating waypoint distances: {e}")
            return []
    
    def _haversine_distance(self, lat1: float, lng1: float, 
                           lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        try:
            # Earth's radius in meters
            R = 6371000
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lng1_rad = math.radians(lng1)
            lat2_rad = math.radians(lat2)
            lng2_rad = math.radians(lng2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlng = lng2_rad - lng1_rad
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            
            return R * c
            
        except Exception as e:
            self.logger.error(f"Error calculating Haversine distance: {e}")
            return 0.0
    
    def estimate_flight_time(self, waypoints: List[Dict[str, Any]], 
                           speed: float = 5.0) -> Dict[str, Any]:
        """Estimate total flight time for waypoints"""
        try:
            distances = self.calculate_waypoint_distances(waypoints)
            total_distance = sum(distances)
            
            # Add time for altitude changes
            altitude_changes = 0
            for i in range(len(waypoints) - 1):
                alt_change = abs(waypoints[i+1]['alt'] - waypoints[i]['alt'])
                altitude_changes += alt_change
            
            # Estimate time (distance/speed + altitude change time)
            flight_time = (total_distance / speed) + (altitude_changes / 2.0)  # 2 m/s vertical speed
            
            return {
                'total_distance': total_distance,
                'flight_time': flight_time,
                'average_speed': speed,
                'waypoint_count': len(waypoints),
                'altitude_changes': altitude_changes
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating flight time: {e}")
            return {
                'total_distance': 0,
                'flight_time': 0,
                'average_speed': speed,
                'waypoint_count': len(waypoints),
                'altitude_changes': 0
            }

# Global instance
waypoint_generator = WaypointGenerator()

# Convenience functions
def generate_lawnmower_pattern(zone_coords: List[Tuple[float, float]], 
                             altitude: float = 50.0, 
                             spacing: float = 10.0,
                             direction: float = 0.0) -> List[Dict[str, Any]]:
    """Convenience function for lawnmower pattern generation"""
    return waypoint_generator.generate_lawnmower_pattern(zone_coords, altitude, spacing, direction)

def generate_spiral_pattern(zone_coords: List[Tuple[float, float]], 
                          altitude: float = 50.0, 
                          spacing: float = 10.0,
                          center: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
    """Convenience function for spiral pattern generation"""
    return waypoint_generator.generate_spiral_pattern(zone_coords, altitude, spacing, center)

def generate_grid_pattern(zone_coords: List[Tuple[float, float]], 
                        altitude: float = 50.0, 
                        spacing: float = 10.0,
                        angle: float = 0.0) -> List[Dict[str, Any]]:
    """Convenience function for grid pattern generation"""
    return waypoint_generator.generate_grid_pattern(zone_coords, altitude, spacing, angle)