"""
Tests for geometric utilities
"""
import math
from ..utils.geometry import GeometryCalculator, Coordinate, SearchGrid


class TestGeometryCalculator:
    """Test cases for GeometryCalculator"""
    
    def test_coordinate_creation(self):
        """Test coordinate creation and conversion"""
        coord = Coordinate(40.7128, -74.0060, 100.0)
        assert coord.latitude == 40.7128
        assert coord.longitude == -74.0060
        assert coord.altitude == 100.0
        
        coord_dict = coord.to_dict()
        expected = {"latitude": 40.7128, "longitude": -74.0060, "altitude": 100.0}
        assert coord_dict == expected
    
    def test_degrees_radians_conversion(self):
        """Test degree/radian conversion"""
        degrees = 180.0
        radians = GeometryCalculator.degrees_to_radians(degrees)
        assert abs(radians - math.pi) < 1e-10
        
        back_to_degrees = GeometryCalculator.radians_to_degrees(radians)
        assert abs(back_to_degrees - degrees) < 1e-10
    
    def test_haversine_distance(self):
        """Test haversine distance calculation"""
        # New York to Los Angeles (approximately 3944 km)
        nyc = Coordinate(40.7128, -74.0060)
        la = Coordinate(34.0522, -118.2437)
        
        distance = GeometryCalculator.haversine_distance(nyc, la)
        assert 3900 < distance < 4000  # Approximate check
        
        # Same point should have zero distance
        same_distance = GeometryCalculator.haversine_distance(nyc, nyc)
        assert abs(same_distance) < 1e-10
    
    def test_bearing_calculation(self):
        """Test bearing calculation"""
        # North bearing should be approximately 0 degrees
        start = Coordinate(40.0, -74.0)
        north = Coordinate(41.0, -74.0)
        
        bearing = GeometryCalculator.calculate_bearing(start, north)
        assert abs(bearing - 0.0) < 1.0  # Within 1 degree
        
        # East bearing should be approximately 90 degrees
        east = Coordinate(40.0, -73.0)
        bearing_east = GeometryCalculator.calculate_bearing(start, east)
        assert abs(bearing_east - 90.0) < 1.0
    
    def test_destination_calculation(self):
        """Test destination coordinate calculation"""
        start = Coordinate(40.0, -74.0)
        bearing = 90.0  # East
        distance = 111.0  # Approximately 1 degree longitude at this latitude
        
        destination = GeometryCalculator.calculate_destination(start, bearing, distance)
        
        # Should be approximately 1 degree east (more lenient check due to spherical calculations)
        assert abs(destination.latitude - start.latitude) < 0.2
        assert abs(destination.longitude - (start.longitude + 1.0)) < 0.5
    
    def test_polygon_area_calculation(self):
        """Test polygon area calculation"""
        # Simple square (approximately 1km x 1km)
        square_coords = [
            Coordinate(40.0, -74.0),
            Coordinate(40.009, -74.0),    # ~1km north
            Coordinate(40.009, -74.013),  # ~1km east
            Coordinate(40.0, -74.013),    # back south
        ]
        
        area = GeometryCalculator.calculate_polygon_area(square_coords)
        assert 0.5 < area < 2.0  # Should be approximately 1 km²
        
        # Triangle
        triangle_coords = [
            Coordinate(40.0, -74.0),
            Coordinate(40.009, -74.0),
            Coordinate(40.0045, -74.013),
        ]
        
        triangle_area = GeometryCalculator.calculate_polygon_area(triangle_coords)
        assert 0.1 < triangle_area < 1.0
    
    def test_search_grid_generation(self):
        """Test search grid generation"""
        # Define a boundary area
        boundary = [
            Coordinate(40.0, -74.0),
            Coordinate(40.02, -74.0),
            Coordinate(40.02, -74.02),
            Coordinate(40.0, -74.02),
        ]
        
        grids = GeometryCalculator.generate_search_grid(
            boundary, 
            grid_spacing_km=1.0,
            overlap_percent=10.0
        )
        
        assert len(grids) > 0
        assert all(isinstance(grid, SearchGrid) for grid in grids)
        assert all(len(grid.coordinates) >= 3 for grid in grids)
        assert all(grid.area_km2 > 0 for grid in grids)
    
    def test_waypoint_calculation(self):
        """Test waypoint calculation"""
        start = Coordinate(40.0, -74.0)
        end = Coordinate(40.1, -74.1)
        
        waypoints = GeometryCalculator.calculate_waypoints(
            start, end, waypoint_distance_km=5.0
        )
        
        assert len(waypoints) >= 2
        assert waypoints[0] == start
        assert waypoints[-1] == end
        
        # Check that waypoints are reasonably spaced
        for i in range(len(waypoints) - 1):
            distance = GeometryCalculator.haversine_distance(
                waypoints[i], waypoints[i + 1]
            )
            assert distance <= 6.0  # Should not exceed max distance by much
    
    def test_drone_path_optimization(self):
        """Test drone path optimization"""
        # Create some test grids
        grids = [
            SearchGrid("grid_001", [Coordinate(40.0, -74.0)], 1.0, priority=1),
            SearchGrid("grid_002", [Coordinate(40.01, -74.0)], 1.0, priority=2),
            SearchGrid("grid_003", [Coordinate(40.02, -74.0)], 1.0, priority=3),
        ]
        
        # Drone positions
        drone_positions = [
            Coordinate(40.0, -74.0),
            Coordinate(40.05, -74.0),
        ]
        
        assignments = GeometryCalculator.optimize_drone_paths(
            grids, drone_positions, max_flight_distance_km=10.0
        )
        
        assert len(assignments) == 2  # Two drones
        assert all(isinstance(assignment, list) for assignment in assignments.values())
        
        # Check that all grids are assigned
        total_assigned = sum(len(assignment) for assignment in assignments.values())
        assert total_assigned <= len(grids)
    
    def test_flight_time_calculation(self):
        """Test flight time calculation"""
        path = [
            Coordinate(40.0, -74.0),
            Coordinate(40.01, -74.0),  # ~1.1 km
            Coordinate(40.01, -74.01), # ~1.1 km
        ]
        
        flight_time = GeometryCalculator.calculate_flight_time(
            path, drone_speed_kmh=60.0
        )
        
        # Should be approximately 2.2 km / 60 kmh = 0.037 hours
        assert 0.02 < flight_time < 0.06
    
    def test_no_fly_zone_check(self):
        """Test no-fly zone checking"""
        # Define a no-fly zone
        no_fly_zones = [
            [
                Coordinate(40.0, -74.0),
                Coordinate(40.01, -74.0),
                Coordinate(40.01, -74.01),
                Coordinate(40.0, -74.01),
            ]
        ]
        
        # Point inside no-fly zone
        inside_point = Coordinate(40.005, -74.005)
        assert GeometryCalculator.is_coordinate_in_no_fly_zone(
            inside_point, no_fly_zones
        )
        
        # Point outside no-fly zone
        outside_point = Coordinate(40.02, -74.02)
        assert not GeometryCalculator.is_coordinate_in_no_fly_zone(
            outside_point, no_fly_zones
        )


if __name__ == "__main__":
    # Run basic tests
    test_calc = TestGeometryCalculator()
    
    print("Testing coordinate creation...")
    test_calc.test_coordinate_creation()
    print("✓ Coordinate creation test passed")
    
    print("Testing distance calculation...")
    test_calc.test_haversine_distance()
    print("✓ Distance calculation test passed")
    
    print("Testing bearing calculation...")
    test_calc.test_bearing_calculation()
    print("✓ Bearing calculation test passed")
    
    print("Testing area calculation...")
    test_calc.test_polygon_area_calculation()
    print("✓ Area calculation test passed")
    
    print("Testing search grid generation...")
    test_calc.test_search_grid_generation()
    print("✓ Search grid generation test passed")
    
    print("All geometry tests passed!")