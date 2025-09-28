"""
Comprehensive tests for area calculation and geometric utilities.
Tests polygon area calculation, distance calculations, waypoint generation, and area division.
"""

import pytest
import math
from unittest.mock import Mock, patch
from shapely.geometry import Polygon, Point
import numpy as np

from ..utils.geometry import GeometryCalculator


class TestGeometryCalculator:
    """Test suite for geometric calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = GeometryCalculator()

        # Test coordinates (Manhattan area approximation)
        self.test_polygon = [
            [40.7128, -74.0060],  # Lower left
            [40.7589, -74.0060],  # Upper left
            [40.7589, -73.9352],  # Upper right
            [40.7128, -73.9352],  # Lower right
            [40.7128, -74.0060]   # Back to start
        ]

        self.test_centroid = [40.7358, -73.9706]  # Approximate center of Manhattan

    def test_calculate_polygon_area_valid(self):
        """Test area calculation for valid polygon."""
        area = self.calculator.calculate_polygon_area(self.test_polygon)

        assert area > 0, "Valid polygon should have positive area"
        assert isinstance(area, float), "Area should be float"

        # Manhattan area should be approximately 87 km²
        assert 80 < area < 100, f"Expected area around 87 km², got {area}"

    def test_calculate_polygon_area_edge_cases(self):
        """Test area calculation for edge cases."""
        # Empty polygon
        assert self.calculator.calculate_polygon_area([]) == 0.0

        # Single point
        assert self.calculator.calculate_polygon_area([[0, 0]]) == 0.0

        # Two points (not a polygon)
        assert self.calculator.calculate_polygon_area([[0, 0], [1, 1]]) == 0.0

        # Three points (valid triangle)
        triangle = [[0, 0], [1, 0], [0.5, 1], [0, 0]]
        area = self.calculator.calculate_polygon_area(triangle)
        assert area > 0, "Triangle should have positive area"

    def test_calculate_distance_valid(self):
        """Test distance calculation between valid coordinates."""
        coord1 = [40.7128, -74.0060]  # NYC
        coord2 = [34.0522, -118.2437]  # LA

        distance = self.calculator.calculate_distance(coord1, coord2)

        assert distance > 0, "Distance should be positive"
        assert isinstance(distance, float), "Distance should be float"
        # NYC to LA is approximately 3940 km
        assert 3900 < distance < 4000, f"Expected ~3940km, got {distance}"

    def test_calculate_distance_edge_cases(self):
        """Test distance calculation edge cases."""
        coord1 = [0, 0]
        coord2 = [0, 0]

        # Same point should be 0 distance
        distance = self.calculator.calculate_distance(coord1, coord2)
        assert distance == 0, "Distance between same points should be 0"

        # Very close points
        close_coord1 = [40.7128, -74.0060]
        close_coord2 = [40.7129, -74.0061]  # ~10m apart

        close_distance = self.calculator.calculate_distance(close_coord1, close_coord2)
        assert 0 < close_distance < 20, f"Close points should have small distance, got {close_distance}"

    def test_generate_search_grid_valid(self):
        """Test search grid generation for valid polygon."""
        grid_spacing = 100  # 100 meters
        overlap = 20  # 20% overlap

        grid_points = self.calculator.generate_search_grid(
            self.test_polygon,
            grid_spacing,
            overlap
        )

        assert len(grid_points) > 0, "Should generate grid points"
        assert all(isinstance(point, tuple) and len(point) == 2 for point in grid_points)

        # All points should be within reasonable bounds
        latitudes = [p[0] for p in grid_points]
        longitudes = [p[1] for p in grid_points]

        assert min(latitudes) >= 40.7, "Latitudes should be in valid range"
        assert max(latitudes) <= 40.8, "Latitudes should be in valid range"
        assert min(longitudes) >= -74.1, "Longitudes should be in valid range"
        assert max(longitudes) <= -73.9, "Longitudes should be in valid range"

    def test_generate_search_grid_edge_cases(self):
        """Test search grid generation edge cases."""
        # Empty boundary
        grid_points = self.calculator.generate_search_grid([], 100, 20)
        assert grid_points == [], "Empty boundary should return empty grid"

        # Invalid boundary (too few points)
        grid_points = self.calculator.generate_search_grid([[0, 0], [1, 1]], 100, 20)
        assert grid_points == [], "Invalid boundary should return empty grid"

        # Very small spacing
        grid_points = self.calculator.generate_search_grid(self.test_polygon, 1, 0)
        assert len(grid_points) > 100, "Small spacing should generate many points"

        # Zero spacing
        grid_points = self.calculator.generate_search_grid(self.test_polygon, 0, 0)
        assert grid_points == [], "Zero spacing should return empty grid"

    def test_divide_area_for_drones_single_drone(self):
        """Test area division for single drone."""
        launch_point = [40.7128, -74.0060]

        assignments = self.calculator.divide_area_for_drones(
            self.test_polygon,
            1,
            launch_point
        )

        assert len(assignments) == 1, "Should have one assignment for single drone"

        assignment = assignments[0]
        assert assignment["drone_id"] == 1
        assert "search_area" in assignment
        assert "navigation_waypoints" in assignment
        assert "estimated_area" in assignment
        assert assignment["estimated_area"] > 0

    def test_divide_area_for_drones_multiple_drones(self):
        """Test area division for multiple drones."""
        launch_point = [40.7128, -74.0060]
        drone_count = 4

        assignments = self.calculator.divide_area_for_drones(
            self.test_polygon,
            drone_count,
            launch_point
        )

        assert len(assignments) == drone_count, f"Should have {drone_count} assignments"

        for i, assignment in enumerate(assignments):
            assert assignment["drone_id"] == i + 1
            assert "search_area" in assignment
            assert "navigation_waypoints" in assignment
            assert "estimated_area" in assignment
            assert assignment["estimated_area"] > 0

        # Total area should be preserved (approximately)
        total_area = sum(a["estimated_area"] for a in assignments)
        original_area = self.calculator.calculate_polygon_area(self.test_polygon)
        assert abs(total_area - original_area) / original_area < 0.1, "Total area should be preserved"

    def test_divide_area_for_drones_edge_cases(self):
        """Test area division edge cases."""
        launch_point = [40.7128, -74.0060]

        # Zero drones
        assignments = self.calculator.divide_area_for_drones(self.test_polygon, 0, launch_point)
        assert assignments == [], "Zero drones should return empty list"

        # Negative drones
        assignments = self.calculator.divide_area_for_drones(self.test_polygon, -1, launch_point)
        assert assignments == [], "Negative drones should return empty list"

        # Invalid polygon
        assignments = self.calculator.divide_area_for_drones([], 2, launch_point)
        assert assignments == [], "Invalid polygon should return empty list"

    def test_calculate_navigation_waypoints_short_distance(self):
        """Test waypoint calculation for short distance."""
        launch_point = [40.7128, -74.0060]
        search_area = [
            [40.7130, -74.0060],
            [40.7130, -74.0050],
            [40.7120, -74.0050],
            [40.7120, -74.0060]
        ]

        waypoints = self.calculator._calculate_approach_waypoints(launch_point, search_area)

        assert len(waypoints) >= 2, "Should have at least takeoff and search waypoints"
        assert all(len(wp) == 3 for wp in waypoints), "Each waypoint should have lat, lng, alt"
        assert waypoints[0][2] > 0, "Takeoff waypoint should have positive altitude"
        assert waypoints[-1][2] > 0, "Search waypoint should have positive altitude"

    def test_calculate_navigation_waypoints_long_distance(self):
        """Test waypoint calculation for long distance."""
        launch_point = [40.7128, -74.0060]  # NYC
        search_area = [
            [34.0522, -118.2437],  # LA area
            [34.0622, -118.2437],
            [34.0622, -118.2337],
            [34.0522, -118.2337]
        ]

        waypoints = self.calculator._calculate_approach_waypoints(launch_point, search_area)

        assert len(waypoints) >= 3, "Long distance should have intermediate waypoint"
        assert all(len(wp) == 3 for wp in waypoints), "Each waypoint should have lat, lng, alt"

        # Should have increasing then decreasing altitude pattern
        altitudes = [wp[2] for wp in waypoints]
        assert altitudes[0] > 0, "Takeoff altitude should be positive"
        assert max(altitudes) > altitudes[0], "Should have higher cruise altitude"
        assert altitudes[-1] > 0, "Search altitude should be positive"

    def test_calculate_bearing_valid(self):
        """Test bearing calculation between points."""
        coord1 = [0, 0]  # Equator, Prime Meridian
        coord2 = [0, 1]  # East of coord1

        bearing = self.calculator.calculate_bearing(coord1, coord2)

        assert 0 <= bearing <= 360, "Bearing should be between 0 and 360 degrees"
        assert abs(bearing - 90) < 1, f"Expected ~90° (east), got {bearing}"

    def test_calculate_bearing_edge_cases(self):
        """Test bearing calculation edge cases."""
        coord1 = [40.7128, -74.0060]

        # Same point
        bearing = self.calculator.calculate_bearing(coord1, coord1)
        assert bearing == 0, "Same point should have 0 bearing"

        # North
        north_coord = [40.7228, -74.0060]
        bearing = self.calculator.calculate_bearing(coord1, north_coord)
        assert abs(bearing - 0) < 1 or abs(bearing - 360) < 1, f"Expected ~0° (north), got {bearing}"

        # South
        south_coord = [40.7028, -74.0060]
        bearing = self.calculator.calculate_bearing(coord1, south_coord)
        assert abs(bearing - 180) < 1, f"Expected ~180° (south), got {bearing}"

    def test_calculate_destination_point_valid(self):
        """Test destination point calculation."""
        start_point = [40.7128, -74.0060]
        bearing = 90  # East
        distance = 1000  # 1km

        dest_point = self.calculator.calculate_destination_point(start_point, bearing, distance)

        assert len(dest_point) == 2, "Should return lat, lng tuple"
        assert isinstance(dest_point[0], float), "Latitude should be float"
        assert isinstance(dest_point[1], float), "Longitude should be float"
        assert dest_point != start_point, "Destination should be different from start"

    def test_calculate_destination_point_edge_cases(self):
        """Test destination point calculation edge cases."""
        start_point = [40.7128, -74.0060]

        # Zero distance
        dest_point = self.calculator.calculate_destination_point(start_point, 90, 0)
        assert dest_point == start_point, "Zero distance should return start point"

        # Very small distance
        dest_point = self.calculator.calculate_destination_point(start_point, 90, 0.1)
        assert dest_point != start_point, "Small distance should return different point"

        # North pole (edge case)
        north_pole = [89.9, 0]
        dest_point = self.calculator.calculate_destination_point(north_pole, 0, 1000)
        assert len(dest_point) == 2, "Should handle polar regions"

    def test_grid_spacing_and_overlap_interaction(self):
        """Test interaction between grid spacing and overlap percentage."""
        base_spacing = 100

        # No overlap
        grid_0 = self.calculator.generate_search_grid(self.test_polygon, base_spacing, 0)
        assert len(grid_0) > 0

        # 50% overlap (should generate more points)
        grid_50 = self.calculator.generate_search_grid(self.test_polygon, base_spacing, 50)
        assert len(grid_50) > len(grid_0), "Higher overlap should generate more points"

        # 90% overlap (should generate significantly more points)
        grid_90 = self.calculator.generate_search_grid(self.test_polygon, base_spacing, 90)
        assert len(grid_90) > len(grid_50), "Very high overlap should generate many more points"

    def test_polygon_complexity_impact(self):
        """Test how polygon complexity affects calculations."""
        # Simple rectangle
        simple_rect = [
            [0, 0], [1, 0], [1, 1], [0, 1], [0, 0]
        ]

        # Complex irregular polygon
        complex_poly = [
            [0, 0], [0.5, 0.2], [1, 0], [1.2, 0.8], [1, 1.2],
            [0.8, 1], [0.3, 1.1], [0.1, 0.7], [0, 0]
        ]

        # Both should calculate areas successfully
        simple_area = self.calculator.calculate_polygon_area(simple_rect)
        complex_area = self.calculator.calculate_polygon_area(complex_poly)

        assert simple_area > 0, "Simple polygon should have positive area"
        assert complex_area > 0, "Complex polygon should have positive area"
        assert isinstance(simple_area, float), "Simple area should be float"
        assert isinstance(complex_area, float), "Complex area should be float"

    def test_coordinate_precision_handling(self):
        """Test handling of high-precision coordinates."""
        # High precision coordinates
        precise_coord1 = [40.712812345, -74.006012345]
        precise_coord2 = [40.712912345, -74.006112345]

        distance = self.calculator.calculate_distance(precise_coord1, precise_coord2)

        assert distance > 0, "Should handle high precision coordinates"
        assert isinstance(distance, float), "Distance should be float"
        assert distance < 20, f"Very close points should have small distance, got {distance}"


class TestGeometricIntegration:
    """Integration tests for geometric calculations."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.calculator = GeometryCalculator()

        # Realistic mission scenario
        self.mission_area = [
            [40.7128, -74.0060],  # NYC Financial District
            [40.7200, -74.0060],
            [40.7200, -73.9950],
            [40.7128, -73.9950],
            [40.7128, -74.0060]
        ]

        self.launch_point = [40.7100, -74.0100]  # Nearby launch location

    def test_complete_mission_planning_workflow(self):
        """Test complete workflow from area to drone assignments."""
        # 1. Calculate area
        area = self.calculator.calculate_polygon_area(self.mission_area)
        assert area > 0

        # 2. Generate search grid
        grid_points = self.calculator.generate_search_grid(self.mission_area, 50, 10)
        assert len(grid_points) > 0

        # 3. Divide area for multiple drones
        assignments = self.calculator.divide_area_for_drones(
            self.mission_area, 3, self.launch_point
        )
        assert len(assignments) == 3

        # 4. Verify each drone has valid waypoints
        for assignment in assignments:
            waypoints = assignment["navigation_waypoints"]
            assert len(waypoints) > 0
            assert all(len(wp) == 3 for wp in waypoints)  # lat, lng, alt

        # 5. Verify total area is preserved
        total_assigned_area = sum(a["estimated_area"] for a in assignments)
        assert abs(total_assigned_area - area) / area < 0.2  # Within 20% tolerance

    def test_large_area_handling(self):
        """Test handling of large geographic areas."""
        # Large area (several square kilometers)
        large_area = [
            [40.7, -74.0],
            [40.8, -74.0],
            [40.8, -73.9],
            [40.7, -73.9],
            [40.7, -74.0]
        ]

        # Should handle large areas without issues
        area = self.calculator.calculate_polygon_area(large_area)
        assert area > 10, "Large area should be > 10 km²"

        assignments = self.calculator.divide_area_for_drones(large_area, 5, [40.75, -73.95])
        assert len(assignments) == 5

    def test_tiny_area_handling(self):
        """Test handling of very small areas."""
        # Tiny area (tens of square meters)
        tiny_area = [
            [40.7128, -74.0060],
            [40.7129, -74.0060],
            [40.7129, -74.0059],
            [40.7128, -74.0059],
            [40.7128, -74.0060]
        ]

        # Should handle tiny areas
        area = self.calculator.calculate_polygon_area(tiny_area)
        assert 0 < area < 0.01, "Tiny area should be < 0.01 km²"

        assignments = self.calculator.divide_area_for_drones(tiny_area, 1, [40.7128, -74.0060])
        assert len(assignments) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])