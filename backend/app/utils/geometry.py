"""
Geometric calculations and utilities for SAR drone operations
"""
import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class Coordinate:
    """Geographic coordinate with latitude and longitude"""
    latitude: float
    longitude: float
    altitude: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude
        }


@dataclass
class SearchGrid:
    """Search grid definition"""
    grid_id: str
    coordinates: List[Coordinate]
    area_km2: float
    priority: int = 1


class GeometryCalculator:
    """Geometric calculations for SAR operations"""
    
    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def degrees_to_radians(degrees: float) -> float:
        """Convert degrees to radians"""
        return degrees * math.pi / 180.0
    
    @staticmethod
    def radians_to_degrees(radians: float) -> float:
        """Convert radians to degrees"""
        return radians * 180.0 / math.pi
    
    @classmethod
    def haversine_distance(
        cls,
        coord1: Coordinate,
        coord2: Coordinate
    ) -> float:
        """
        Calculate the great circle distance between two points using Haversine formula
        Returns distance in kilometers
        """
        # Convert to radians
        lat1_rad = cls.degrees_to_radians(coord1.latitude)
        lon1_rad = cls.degrees_to_radians(coord1.longitude)
        lat2_rad = cls.degrees_to_radians(coord2.latitude)
        lon2_rad = cls.degrees_to_radians(coord2.longitude)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return cls.EARTH_RADIUS_KM * c
    
    @classmethod
    def calculate_bearing(
        cls,
        from_coord: Coordinate,
        to_coord: Coordinate
    ) -> float:
        """
        Calculate the initial bearing from one coordinate to another
        Returns bearing in degrees (0-360)
        """
        # Convert to radians
        lat1_rad = cls.degrees_to_radians(from_coord.latitude)
        lat2_rad = cls.degrees_to_radians(to_coord.latitude)
        dlon_rad = cls.degrees_to_radians(to_coord.longitude - from_coord.longitude)
        
        # Calculate bearing
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = cls.radians_to_degrees(bearing_rad)
        
        # Normalize to 0-360 degrees
        return (bearing_deg + 360) % 360
    
    @classmethod
    def calculate_destination(
        cls,
        start_coord: Coordinate,
        bearing_degrees: float,
        distance_km: float
    ) -> Coordinate:
        """
        Calculate destination coordinate given start point, bearing, and distance
        """
        # Convert to radians
        lat1_rad = cls.degrees_to_radians(start_coord.latitude)
        lon1_rad = cls.degrees_to_radians(start_coord.longitude)
        bearing_rad = cls.degrees_to_radians(bearing_degrees)
        
        # Angular distance
        angular_distance = distance_km / cls.EARTH_RADIUS_KM
        
        # Calculate destination
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(angular_distance) +
            math.cos(lat1_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )
        
        lon2_rad = lon1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat1_rad),
            math.cos(angular_distance) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        return Coordinate(
            latitude=cls.radians_to_degrees(lat2_rad),
            longitude=cls.radians_to_degrees(lon2_rad),
            altitude=start_coord.altitude
        )
    
    @classmethod
    def calculate_polygon_area(cls, coordinates: List[Coordinate]) -> float:
        """
        Calculate area of a polygon using the spherical excess method
        Returns area in square kilometers
        """
        if len(coordinates) < 3:
            return 0.0
        
        # Ensure polygon is closed
        coords = coordinates.copy()
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        
        # Convert to radians
        coords_rad = [
            (cls.degrees_to_radians(c.latitude), cls.degrees_to_radians(c.longitude))
            for c in coords
        ]
        
        # Calculate spherical excess
        n = len(coords_rad) - 1
        spherical_excess = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            k = (i + 2) % n
            
            lat1, lon1 = coords_rad[i]
            lat2, lon2 = coords_rad[j]
            lat3, lon3 = coords_rad[k]
            
            # Calculate angle at vertex j
            bearing1 = cls._calculate_bearing_rad(lat2, lon2, lat1, lon1)
            bearing2 = cls._calculate_bearing_rad(lat2, lon2, lat3, lon3)
            angle = bearing2 - bearing1
            
            # Normalize angle
            while angle > math.pi:
                angle -= 2 * math.pi
            while angle < -math.pi:
                angle += 2 * math.pi
            
            spherical_excess += angle
        
        # Calculate area
        area_steradians = abs(spherical_excess) - (n - 2) * math.pi
        area_km2 = area_steradians * cls.EARTH_RADIUS_KM ** 2
        
        return abs(area_km2)
    
    @classmethod
    def _calculate_bearing_rad(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing in radians (internal helper)"""
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        return math.atan2(y, x)
    
    @classmethod
    def generate_search_grid(
        cls,
        boundary_coords: List[Coordinate],
        grid_spacing_km: float = 1.0,
        overlap_percent: float = 20.0
    ) -> List[SearchGrid]:
        """
        Generate search grid within boundary coordinates
        """
        if len(boundary_coords) < 3:
            raise ValueError("Need at least 3 boundary coordinates")
        
        # Calculate bounding box
        min_lat = min(c.latitude for c in boundary_coords)
        max_lat = max(c.latitude for c in boundary_coords)
        min_lon = min(c.longitude for c in boundary_coords)
        max_lon = max(c.longitude for c in boundary_coords)
        
        # Calculate grid dimensions
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        
        # Convert grid spacing to degrees (approximate)
        lat_spacing = grid_spacing_km / 111.0  # 1 degree ≈ 111 km
        lon_spacing = grid_spacing_km / (111.0 * math.cos(math.radians((min_lat + max_lat) / 2)))
        
        # Apply overlap
        overlap_factor = 1.0 - (overlap_percent / 100.0)
        lat_spacing *= overlap_factor
        lon_spacing *= overlap_factor
        
        grids = []
        grid_id = 0
        
        # Generate grid cells
        lat = min_lat
        while lat < max_lat:
            lon = min_lon
            while lon < max_lon:
                # Create grid cell corners
                grid_coords = [
                    Coordinate(lat, lon),
                    Coordinate(lat, lon + lon_spacing),
                    Coordinate(lat + lat_spacing, lon + lon_spacing),
                    Coordinate(lat + lat_spacing, lon),
                    Coordinate(lat, lon)  # Close the polygon
                ]
                
                # Check if grid cell intersects with boundary
                if cls._grid_intersects_boundary(grid_coords[:-1], boundary_coords):
                    area = cls.calculate_polygon_area(grid_coords[:-1])
                    grids.append(SearchGrid(
                        grid_id=f"grid_{grid_id:04d}",
                        coordinates=grid_coords[:-1],  # Don't include closing coordinate
                        area_km2=area
                    ))
                    grid_id += 1
                
                lon += lon_spacing
            lat += lat_spacing
        
        return grids
    
    @classmethod
    def _grid_intersects_boundary(
        cls,
        grid_coords: List[Coordinate],
        boundary_coords: List[Coordinate]
    ) -> bool:
        """Check if grid cell intersects with boundary polygon (simplified)"""
        # Simple check: if any grid corner is inside boundary, consider it intersecting
        for grid_coord in grid_coords:
            if cls._point_in_polygon(grid_coord, boundary_coords):
                return True
        
        # Also check if any boundary point is inside grid
        for boundary_coord in boundary_coords:
            if cls._point_in_polygon(boundary_coord, grid_coords):
                return True
        
        return False
    
    @classmethod
    def _point_in_polygon(cls, point: Coordinate, polygon: List[Coordinate]) -> bool:
        """Ray casting algorithm to check if point is inside polygon"""
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
    
    @classmethod
    def calculate_waypoints(
        cls,
        start_coord: Coordinate,
        end_coord: Coordinate,
        waypoint_distance_km: float = 5.0
    ) -> List[Coordinate]:
        """
        Calculate waypoints between start and end coordinates
        """
        total_distance = cls.haversine_distance(start_coord, end_coord)
        
        if total_distance <= waypoint_distance_km:
            return [start_coord, end_coord]
        
        num_segments = int(math.ceil(total_distance / waypoint_distance_km))
        bearing = cls.calculate_bearing(start_coord, end_coord)
        
        waypoints = [start_coord]
        
        for i in range(1, num_segments):
            distance = (i / num_segments) * total_distance
            waypoint = cls.calculate_destination(start_coord, bearing, distance)
            waypoints.append(waypoint)
        
        waypoints.append(end_coord)
        return waypoints
    
    @classmethod
    def optimize_drone_paths(
        cls,
        grids: List[SearchGrid],
        drone_positions: List[Coordinate],
        max_flight_distance_km: float = 50.0
    ) -> Dict[int, List[SearchGrid]]:
        """
        Optimize grid assignment to drones based on distance and efficiency
        Simple greedy algorithm - can be improved with more sophisticated methods
        """
        if not grids or not drone_positions:
            return {}
        
        # Initialize assignments
        assignments = {i: [] for i in range(len(drone_positions))}
        unassigned_grids = grids.copy()
        
        # Sort grids by priority (higher priority first)
        unassigned_grids.sort(key=lambda g: g.priority, reverse=True)
        
        while unassigned_grids:
            # Find the best drone-grid combination
            best_drone_idx = None
            best_grid = None
            best_distance = float('inf')
            
            for drone_idx, drone_pos in enumerate(drone_positions):
                # Calculate current drone position (last assigned grid or initial position)
                current_pos = drone_pos
                if assignments[drone_idx]:
                    last_grid = assignments[drone_idx][-1]
                    # Use centroid of last grid
                    current_pos = cls._calculate_centroid(last_grid.coordinates)
                
                # Find closest unassigned grid
                for grid in unassigned_grids:
                    grid_centroid = cls._calculate_centroid(grid.coordinates)
                    distance = cls.haversine_distance(current_pos, grid_centroid)
                    
                    # Check if within flight range
                    if distance <= max_flight_distance_km and distance < best_distance:
                        best_distance = distance
                        best_drone_idx = drone_idx
                        best_grid = grid
            
            # Assign best combination or break if no valid assignment
            if best_drone_idx is not None and best_grid is not None:
                assignments[best_drone_idx].append(best_grid)
                unassigned_grids.remove(best_grid)
            else:
                # No more valid assignments possible
                break
        
        return assignments
    
    @classmethod
    def _calculate_centroid(cls, coordinates: List[Coordinate]) -> Coordinate:
        """Calculate centroid of polygon"""
        if not coordinates:
            return Coordinate(0.0, 0.0)
        
        lat_sum = sum(c.latitude for c in coordinates)
        lon_sum = sum(c.longitude for c in coordinates)
        alt_sum = sum(c.altitude for c in coordinates)
        
        n = len(coordinates)
        return Coordinate(
            latitude=lat_sum / n,
            longitude=lon_sum / n,
            altitude=alt_sum / n
        )
    
    @classmethod
    def calculate_flight_time(
        cls,
        path_coordinates: List[Coordinate],
        drone_speed_kmh: float = 50.0
    ) -> float:
        """
        Calculate estimated flight time for a path
        Returns time in hours
        """
        if len(path_coordinates) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(path_coordinates) - 1):
            total_distance += cls.haversine_distance(
                path_coordinates[i],
                path_coordinates[i + 1]
            )
        
        return total_distance / drone_speed_kmh
    
    @classmethod
    def is_coordinate_in_no_fly_zone(
        cls,
        coordinate: Coordinate,
        no_fly_zones: List[List[Coordinate]]
    ) -> bool:
        """
        Check if a coordinate is within any no-fly zone
        """
        for zone in no_fly_zones:
            if cls._point_in_polygon(coordinate, zone):
                return True
        return False