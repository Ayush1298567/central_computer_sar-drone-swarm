"""
Area Division Algorithm for SAR Drone Swarm
Implements real geometric algorithms using Shapely for dividing search areas into zones.
"""

import logging
from typing import List, Tuple, Dict, Any
import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
import math

logger = logging.getLogger(__name__)

class AreaDivider:
    """Real area division using Shapely geometric operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def divide_area_into_zones(self, polygon_coords: List[Tuple[float, float]], 
                             num_zones: int, 
                             overlap_percentage: float = 0.1) -> List[Dict[str, Any]]:
        """
        Divide a polygon into zones for drone coverage using real geometric algorithms.
        
        Args:
            polygon_coords: List of (lng, lat) coordinates defining the search area
            num_zones: Number of zones to create
            overlap_percentage: Overlap between adjacent zones (0.0 to 0.5)
            
        Returns:
            List of zone dictionaries with coordinates and metadata
        """
        try:
            # Create Shapely polygon from coordinates
            polygon = Polygon(polygon_coords)
            
            if not polygon.is_valid:
                self.logger.error("Invalid polygon provided for area division")
                return []
            
            # Calculate bounding box
            minx, miny, maxx, maxy = polygon.bounds
            
            # Calculate grid dimensions
            width = maxx - minx
            height = maxy - miny
            
            # Determine grid layout (prefer square-ish grids)
            aspect_ratio = width / height
            cols = int(math.ceil(math.sqrt(num_zones * aspect_ratio)))
            rows = int(math.ceil(num_zones / cols))
            
            # Calculate cell dimensions with overlap
            cell_width = width / cols
            cell_height = height / rows
            
            # Apply overlap
            overlap_x = cell_width * overlap_percentage
            overlap_y = cell_height * overlap_percentage
            
            zones = []
            zone_id = 0
            
            for row in range(rows):
                for col in range(cols):
                    if zone_id >= num_zones:
                        break
                    
                    # Calculate cell bounds with overlap
                    x1 = minx + (col * cell_width) - overlap_x
                    y1 = miny + (row * cell_height) - overlap_y
                    x2 = minx + ((col + 1) * cell_width) + overlap_x
                    y2 = miny + ((row + 1) * cell_height) + overlap_y
                    
                    # Create cell polygon
                    cell = box(x1, y1, x2, y2)
                    
                    # Intersect with search area polygon
                    zone_polygon = polygon.intersection(cell)
                    
                    # Only include zones with significant area
                    if zone_polygon.area > 0 and zone_polygon.area > (cell.area * 0.01):
                        # Extract coordinates
                        if hasattr(zone_polygon, 'exterior'):
                            coords = list(zone_polygon.exterior.coords)
                        else:
                            # Handle MultiPolygon case
                            coords = []
                            for geom in zone_polygon.geoms:
                                if hasattr(geom, 'exterior'):
                                    coords.extend(list(geom.exterior.coords))
                        
                        if coords:
                            zone_data = {
                                'id': zone_id,
                                'coordinates': coords,
                                'area': zone_polygon.area,
                                'centroid': (zone_polygon.centroid.x, zone_polygon.centroid.y),
                                'bounds': zone_polygon.bounds,
                                'priority': self._calculate_zone_priority(zone_polygon, polygon),
                                'difficulty': self._calculate_zone_difficulty(zone_polygon)
                            }
                            zones.append(zone_data)
                            zone_id += 1
                
                if zone_id >= num_zones:
                    break
            
            self.logger.info(f"Created {len(zones)} zones from polygon with {len(polygon_coords)} vertices")
            return zones
            
        except Exception as e:
            self.logger.error(f"Error dividing area into zones: {e}", exc_info=True)
            return []
    
    def _calculate_zone_priority(self, zone: Polygon, search_area: Polygon) -> float:
        """Calculate priority score for a zone based on geometric properties"""
        try:
            # Factors affecting priority:
            # 1. Distance from search area center
            # 2. Zone area (larger zones get higher priority)
            # 3. Accessibility (how easy it is to reach)
            
            search_center = search_area.centroid
            zone_center = zone.centroid
            
            # Distance from center (normalized)
            max_distance = math.sqrt(search_area.area) / 2
            distance_factor = 1.0 - (search_center.distance(zone_center) / max_distance)
            distance_factor = max(0.0, min(1.0, distance_factor))
            
            # Area factor (normalized)
            area_factor = min(1.0, zone.area / (search_area.area / 10))
            
            # Accessibility factor (based on shape complexity)
            perimeter_area_ratio = zone.length / (zone.area + 1e-10)
            accessibility_factor = 1.0 / (1.0 + perimeter_area_ratio / 1000)
            
            # Combined priority score
            priority = (distance_factor * 0.4 + area_factor * 0.4 + accessibility_factor * 0.2)
            
            return max(0.0, min(1.0, priority))
            
        except Exception as e:
            self.logger.error(f"Error calculating zone priority: {e}")
            return 0.5
    
    def _calculate_zone_difficulty(self, zone: Polygon) -> float:
        """Calculate difficulty score for a zone based on geometric complexity"""
        try:
            # Factors affecting difficulty:
            # 1. Shape complexity (perimeter to area ratio)
            # 2. Number of vertices
            # 3. Aspect ratio (very elongated shapes are harder)
            
            if zone.area <= 0:
                return 1.0
            
            # Perimeter to area ratio
            perimeter_area_ratio = zone.length / zone.area
            
            # Number of vertices (more vertices = more complex)
            vertex_count = len(zone.exterior.coords) - 1
            vertex_factor = min(1.0, vertex_count / 20)
            
            # Aspect ratio (bounding box)
            minx, miny, maxx, maxy = zone.bounds
            width = maxx - minx
            height = maxy - miny
            
            if height > 0:
                aspect_ratio = max(width / height, height / width)
                aspect_factor = min(1.0, (aspect_ratio - 1) / 4)
            else:
                aspect_factor = 1.0
            
            # Combined difficulty score
            difficulty = (perimeter_area_ratio / 1000 * 0.4 + 
                         vertex_factor * 0.3 + 
                         aspect_factor * 0.3)
            
            return max(0.0, min(1.0, difficulty))
            
        except Exception as e:
            self.logger.error(f"Error calculating zone difficulty: {e}")
            return 0.5
    
    def optimize_zone_assignment(self, zones: List[Dict[str, Any]], 
                               drone_capabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize zone assignment to drones based on capabilities and zone properties.
        
        Args:
            zones: List of zone dictionaries
            drone_capabilities: List of drone capability dictionaries
            
        Returns:
            List of zones with assigned drone IDs
        """
        try:
            if not zones or not drone_capabilities:
                return zones
            
            # Sort zones by priority (highest first)
            sorted_zones = sorted(zones, key=lambda z: z['priority'], reverse=True)
            
            # Sort drones by capability score (highest first)
            sorted_drones = sorted(drone_capabilities, 
                                 key=lambda d: d.get('capability_score', 0.5), 
                                 reverse=True)
            
            # Assign zones to drones
            for i, zone in enumerate(sorted_zones):
                drone_index = i % len(sorted_drones)
                zone['assigned_drone_id'] = sorted_drones[drone_index].get('id', f'drone_{drone_index}')
                zone['assignment_score'] = self._calculate_assignment_score(zone, sorted_drones[drone_index])
            
            self.logger.info(f"Assigned {len(zones)} zones to {len(drone_capabilities)} drones")
            return sorted_zones
            
        except Exception as e:
            self.logger.error(f"Error optimizing zone assignment: {e}", exc_info=True)
            return zones
    
    def _calculate_assignment_score(self, zone: Dict[str, Any], drone: Dict[str, Any]) -> float:
        """Calculate how well a drone matches a zone's requirements"""
        try:
            # Factors:
            # 1. Drone capability vs zone difficulty
            # 2. Drone range vs zone distance
            # 3. Drone battery vs zone estimated time
            
            capability_score = drone.get('capability_score', 0.5)
            zone_difficulty = zone.get('difficulty', 0.5)
            
            # Capability match (higher capability should handle higher difficulty)
            capability_match = 1.0 - abs(capability_score - zone_difficulty)
            
            # Range check (if available)
            drone_range = drone.get('max_range', 1000)  # meters
            zone_area = zone.get('area', 0)
            estimated_range_needed = math.sqrt(zone_area) * 2  # rough estimate
            
            range_match = 1.0 if drone_range >= estimated_range_needed else drone_range / estimated_range_needed
            
            # Battery check (if available)
            drone_battery = drone.get('battery_level', 100)
            estimated_time = zone.get('area', 0) / 100  # rough estimate
            battery_match = min(1.0, drone_battery / (estimated_time * 10))
            
            # Combined score
            assignment_score = (capability_match * 0.5 + range_match * 0.3 + battery_match * 0.2)
            
            return max(0.0, min(1.0, assignment_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating assignment score: {e}")
            return 0.5
    
    def validate_zones(self, zones: List[Dict[str, Any]], 
                      search_area: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Validate that zones properly cover the search area.
        
        Args:
            zones: List of zone dictionaries
            search_area: Original search area coordinates
            
        Returns:
            Validation results dictionary
        """
        try:
            search_polygon = Polygon(search_area)
            
            if not search_polygon.is_valid:
                return {
                    'valid': False,
                    'error': 'Invalid search area polygon',
                    'coverage': 0.0
                }
            
            # Create union of all zones
            zone_polygons = []
            for zone in zones:
                coords = zone.get('coordinates', [])
                if coords:
                    zone_poly = Polygon(coords)
                    if zone_poly.is_valid:
                        zone_polygons.append(zone_poly)
            
            if not zone_polygons:
                return {
                    'valid': False,
                    'error': 'No valid zones found',
                    'coverage': 0.0
                }
            
            # Calculate coverage
            union_zones = unary_union(zone_polygons)
            intersection = search_polygon.intersection(union_zones)
            coverage = intersection.area / search_polygon.area
            
            # Check for gaps
            gaps = search_polygon.difference(union_zones)
            gap_area = gaps.area if hasattr(gaps, 'area') else 0
            
            # Check for overlaps
            overlap_area = 0
            for i, zone1 in enumerate(zone_polygons):
                for zone2 in zone_polygons[i+1:]:
                    if zone1.intersects(zone2):
                        overlap = zone1.intersection(zone2)
                        overlap_area += overlap.area
            
            validation_result = {
                'valid': coverage >= 0.95,  # 95% coverage threshold
                'coverage': coverage,
                'gap_area': gap_area,
                'overlap_area': overlap_area,
                'zone_count': len(zones),
                'total_zone_area': sum(zone.get('area', 0) for zone in zones),
                'search_area': search_polygon.area
            }
            
            self.logger.info(f"Zone validation: {coverage:.2%} coverage, {len(zones)} zones")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating zones: {e}", exc_info=True)
            return {
                'valid': False,
                'error': str(e),
                'coverage': 0.0
            }

# Global instance
area_divider = AreaDivider()

# Convenience functions
def divide_area_into_zones(polygon_coords: List[Tuple[float, float]], 
                          num_zones: int, 
                          overlap_percentage: float = 0.1) -> List[Dict[str, Any]]:
    """Convenience function for area division"""
    return area_divider.divide_area_into_zones(polygon_coords, num_zones, overlap_percentage)

def optimize_zone_assignment(zones: List[Dict[str, Any]], 
                           drone_capabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convenience function for zone assignment optimization"""
    return area_divider.optimize_zone_assignment(zones, drone_capabilities)

def validate_zones(zones: List[Dict[str, Any]], 
                  search_area: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Convenience function for zone validation"""
    return area_divider.validate_zones(zones, search_area)