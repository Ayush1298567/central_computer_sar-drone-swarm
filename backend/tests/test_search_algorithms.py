import pytest
import math
from app.services.search_algorithms import SearchAlgorithms, SearchPattern

def test_grid_pattern_generation():
    """Test grid search pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_grid_pattern(
        center=center,
        width_m=1000,
        height_m=1000,
        spacing_m=100,
        altitude_m=50
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 50 for wp in waypoints)
    assert all(wp["pattern"] == "grid" for wp in waypoints)

def test_spiral_pattern_generation():
    """Test spiral search pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_spiral_pattern(
        center=center,
        max_radius_m=500,
        spacing_m=50,
        altitude_m=60
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 60 for wp in waypoints)
    assert all(wp["pattern"] == "spiral" for wp in waypoints)

def test_expanding_square_pattern():
    """Test expanding square pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_expanding_square(
        center=center,
        max_size_m=400,
        step_m=100,
        altitude_m=40
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 40 for wp in waypoints)
    assert all(wp["pattern"] == "expanding_square" for wp in waypoints)

def test_sector_pattern_generation():
    """Test sector search pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_sector_pattern(
        center=center,
        radius_m=300,
        sectors=8,
        altitude_m=55
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 55 for wp in waypoints)
    assert all(wp["pattern"] == "sector" for wp in waypoints)

def test_parallel_track_pattern():
    """Test parallel track pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_parallel_track(
        center=center,
        width_m=800,
        height_m=600,
        track_spacing_m=150,
        altitude_m=45
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 45 for wp in waypoints)
    assert all(wp["pattern"] == "parallel_track" for wp in waypoints)

def test_creeping_line_pattern():
    """Test creeping line pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_creeping_line(
        center=center,
        length_m=1000,
        width_m=200,
        spacing_m=50,
        altitude_m=35
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 35 for wp in waypoints)
    assert all(wp["pattern"] == "creeping_line" for wp in waypoints)

def test_contour_pattern():
    """Test contour pattern generation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_contour_pattern(
        center=center,
        radius_m=250,
        contour_spacing_m=50,
        altitude_m=65
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    assert all(wp["alt"] == 65 for wp in waypoints)
    assert all(wp["pattern"] == "contour" for wp in waypoints)

def test_waypoint_optimization():
    """Test waypoint order optimization"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    # Generate some waypoints
    waypoints = SearchAlgorithms.generate_grid_pattern(
        center=center,
        width_m=200,
        height_m=200,
        spacing_m=50,
        altitude_m=50
    )
    
    # Optimize order
    start_position = {"lat": 37.7750, "lon": -122.4195}
    optimized = SearchAlgorithms.optimize_waypoint_order(waypoints, start_position)
    
    assert len(optimized) == len(waypoints)
    assert optimized[0]["lat"] != waypoints[0]["lat"] or optimized[0]["lon"] != waypoints[0]["lon"]

def test_search_coverage_calculation():
    """Test search coverage calculation"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_grid_pattern(
        center=center,
        width_m=1000,
        height_m=1000,
        spacing_m=100,
        altitude_m=50
    )
    
    coverage = SearchAlgorithms.calculate_search_coverage(waypoints, search_radius_m=25)
    
    assert "coverage_percent" in coverage
    assert "area_covered_km2" in coverage
    assert "bounding_area_km2" in coverage
    assert "waypoint_count" in coverage
    assert "search_radius_m" in coverage
    
    assert coverage["coverage_percent"] > 0
    assert coverage["area_covered_km2"] > 0
    assert coverage["waypoint_count"] == len(waypoints)
    assert coverage["search_radius_m"] == 25

def test_waypoint_validation():
    """Test waypoint validation"""
    # Valid waypoints
    valid_waypoints = [
        {"lat": 37.7749, "lon": -122.4194, "alt": 50},
        {"lat": 37.7750, "lon": -122.4195, "alt": 60}
    ]
    
    validation = SearchAlgorithms.validate_waypoints(valid_waypoints)
    assert validation["valid"] is True
    assert len(validation["errors"]) == 0
    assert validation["waypoint_count"] == 2
    
    # Invalid waypoints
    invalid_waypoints = [
        {"lat": 91, "lon": -122.4194, "alt": 50},  # Invalid latitude
        {"lat": 37.7749, "lon": 181, "alt": 50},   # Invalid longitude
        {"lat": 37.7750, "lon": -122.4195, "alt": -10}  # Invalid altitude
    ]
    
    validation = SearchAlgorithms.validate_waypoints(invalid_waypoints)
    assert validation["valid"] is False
    assert len(validation["errors"]) > 0

def test_empty_waypoints():
    """Test handling of empty waypoint lists"""
    # Empty waypoints
    validation = SearchAlgorithms.validate_waypoints([])
    assert validation["valid"] is False
    assert "No waypoints provided" in validation["errors"]
    
    # Coverage calculation with empty waypoints
    coverage = SearchAlgorithms.calculate_search_coverage([], search_radius_m=25)
    assert coverage["coverage_percent"] == 0
    assert coverage["area_covered_km2"] == 0

def test_pattern_generation_with_parameters():
    """Test pattern generation with different parameters"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    # Test different search patterns
    patterns = [
        SearchPattern.GRID,
        SearchPattern.SPIRAL,
        SearchPattern.EXPANDING_SQUARE,
        SearchPattern.SECTOR,
        SearchPattern.PARALLEL_TRACK,
        SearchPattern.CREEPING_LINE,
        SearchPattern.CONTOUR
    ]
    
    for pattern in patterns:
        waypoints = SearchAlgorithms.generate_search_pattern(
            pattern_type=pattern,
            center=center,
            parameters={
                "width_m": 500,
                "height_m": 500,
                "spacing_m": 50,
                "altitude_m": 50,
                "max_radius_m": 250,
                "sectors": 6,
                "track_spacing_m": 100,
                "length_m": 800,
                "contour_spacing_m": 40
            }
        )
        
        assert len(waypoints) > 0
        assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)

def test_coordinate_bounds():
    """Test that generated coordinates are within expected bounds"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    waypoints = SearchAlgorithms.generate_grid_pattern(
        center=center,
        width_m=1000,
        height_m=1000,
        spacing_m=100,
        altitude_m=50
    )
    
    # Check that all waypoints are within reasonable bounds
    lats = [wp["lat"] for wp in waypoints]
    lons = [wp["lon"] for wp in waypoints]
    
    # Should be within ~5km of center (roughly 0.05 degrees)
    assert all(abs(lat - center["lat"]) < 0.05 for lat in lats)
    assert all(abs(lon - center["lon"]) < 0.05 for lon in lons)

def test_altitude_consistency():
    """Test that altitude is consistent across waypoints"""
    center = {"lat": 37.7749, "lon": -122.4194}
    test_altitude = 75
    
    waypoints = SearchAlgorithms.generate_spiral_pattern(
        center=center,
        max_radius_m=300,
        spacing_m=30,
        altitude_m=test_altitude
    )
    
    assert all(wp["alt"] == test_altitude for wp in waypoints)

def test_pattern_specific_attributes():
    """Test pattern-specific attributes"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    # Test sector pattern attributes
    waypoints = SearchAlgorithms.generate_sector_pattern(
        center=center,
        radius_m=200,
        sectors=6,
        altitude_m=50
    )
    
    assert all("sector" in wp for wp in waypoints)
    assert all("distance" in wp for wp in waypoints)
    assert all(0 <= wp["sector"] < 6 for wp in waypoints)
    
    # Test expanding square attributes
    waypoints = SearchAlgorithms.generate_expanding_square(
        center=center,
        max_size_m=300,
        step_m=50,
        altitude_m=50
    )
    
    assert all("square_size" in wp for wp in waypoints)