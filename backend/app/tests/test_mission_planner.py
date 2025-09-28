"""
Comprehensive tests for mission planning logic.
Tests mission creation, area calculation, drone assignment, and planning validation.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from ..services.mission_planner import MissionPlanner
from ..services.area_calculator import AreaCalculator
from ..models.mission import Mission, DroneAssignment
from ..models.drone import Drone
from ..core.database import SessionLocal


class TestMissionPlanner:
    """Test suite for mission planning functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mission_planner = MissionPlanner()
        self.area_calculator = AreaCalculator()

        # Sample test data
        self.sample_search_area = [
            [40.7128, -74.0060],  # New York coordinates
            [40.7589, -74.0060],
            [40.7589, -73.9352],
            [40.7128, -73.9352],
            [40.7128, -74.0060]
        ]

        self.sample_launch_point = [40.7128, -74.0060]

        self.sample_drones = [
            {
                "id": "drone_1",
                "name": "Test Drone 1",
                "status": "online",
                "battery_level": 85.0,
                "coverage_rate": 0.15,
                "max_flight_time": 25
            },
            {
                "id": "drone_2",
                "name": "Test Drone 2",
                "status": "online",
                "battery_level": 92.0,
                "coverage_rate": 0.12,
                "max_flight_time": 30
            }
        ]

    def test_calculate_search_area(self):
        """Test search area calculation from polygon coordinates."""
        area_km2 = self.area_calculator.calculate_polygon_area(self.sample_search_area)

        assert area_km2 > 0, "Area calculation should return positive value"
        assert isinstance(area_km2, float), "Area should be returned as float"

        # Test with empty/invalid coordinates
        assert self.area_calculator.calculate_polygon_area([]) == 0.0
        assert self.area_calculator.calculate_polygon_area([[0, 0]]) == 0.0

    def test_calculate_distance_between_points(self):
        """Test distance calculation between GPS coordinates."""
        coord1 = [40.7128, -74.0060]  # NYC
        coord2 = [34.0522, -118.2437]  # LA

        distance = self.area_calculator.calculate_distance(coord1, coord2)

        assert distance > 0, "Distance should be positive"
        assert isinstance(distance, float), "Distance should be float"
        assert distance > 3900000, "Distance between NYC and LA should be ~3900km"

    def test_generate_search_grid(self):
        """Test generation of systematic search grid."""
        grid_spacing = 100  # meters
        overlap = 20  # percentage

        grid_points = self.area_calculator.generate_search_grid(
            self.sample_search_area,
            grid_spacing,
            overlap
        )

        assert len(grid_points) > 0, "Grid should contain points"
        assert all(isinstance(point, tuple) and len(point) == 2 for point in grid_points)

        # Test with invalid inputs
        assert self.area_calculator.generate_search_grid([], grid_spacing) == []
        assert self.area_calculator.generate_search_grid([[0, 0], [1, 1]], grid_spacing) == []

    def test_divide_area_for_drones(self):
        """Test optimal area division between multiple drones."""
        drone_count = 2
        launch_point = self.sample_launch_point

        assignments = self.area_calculator.divide_area_for_drones(
            self.sample_search_area,
            drone_count,
            launch_point
        )

        assert len(assignments) == drone_count, f"Should have {drone_count} assignments"

        for assignment in assignments:
            assert "drone_id" in assignment
            assert "search_area" in assignment
            assert "navigation_waypoints" in assignment
            assert "estimated_area" in assignment
            assert assignment["estimated_area"] > 0

    def test_calculate_navigation_waypoints(self):
        """Test waypoint calculation for drone navigation."""
        search_area = self.sample_search_area
        launch_point = self.sample_launch_point

        waypoints = self.area_calculator._calculate_approach_waypoints(launch_point, search_area)

        assert len(waypoints) > 0, "Should generate waypoints"
        assert all(len(wp) == 3 for wp in waypoints), "Each waypoint should have lat, lng, alt"
        assert all(wp[2] > 0 for wp in waypoints), "All waypoints should have positive altitude"

    def test_estimate_mission_duration(self):
        """Test mission duration estimation based on area and drone capabilities."""
        search_area = self.sample_search_area
        drones = self.sample_drones

        # Mock mission planner method
        duration = self.mission_planner._estimate_mission_duration(search_area, drones)

        assert duration > 0, "Duration should be positive"
        assert isinstance(duration, (int, float)), "Duration should be numeric"

    def test_validate_mission_safety(self):
        """Test mission safety validation."""
        mission_data = {
            "search_area": self.sample_search_area,
            "search_altitude": 50.0,  # meters
            "weather_conditions": {
                "wind_speed": 5.0,  # m/s (safe)
                "visibility": 10000  # meters (good)
            }
        }

        # Mock safety validation
        is_safe = self.mission_planner._validate_mission_safety(mission_data)

        assert is_safe is True, "Mission should be considered safe"

        # Test unsafe conditions
        unsafe_mission = mission_data.copy()
        unsafe_mission["weather_conditions"]["wind_speed"] = 25.0  # Too windy

        is_unsafe = self.mission_planner._validate_mission_safety(unsafe_mission)
        assert is_unsafe is False, "Mission should be considered unsafe"

    def test_calculate_coverage_efficiency(self):
        """Test coverage efficiency calculation."""
        mission_data = {
            "search_area": self.sample_search_area,
            "estimated_duration": 45,  # minutes
            "drone_count": 2
        }

        efficiency = self.mission_planner._calculate_coverage_efficiency(mission_data)

        assert efficiency > 0, "Efficiency should be positive"
        assert isinstance(efficiency, (int, float)), "Efficiency should be numeric"

    def test_generate_mission_context(self):
        """Test generation of complete mission context for drones."""
        mission_data = {
            "name": "Test SAR Mission",
            "search_area": self.sample_search_area,
            "launch_point": self.sample_launch_point,
            "search_target": "person",
            "search_altitude": 30.0,
            "search_speed": "thorough",
            "recording_mode": "continuous"
        }

        context = self.mission_planner._generate_mission_context(mission_data, self.sample_drones)

        assert "mission_id" in context
        assert "search_area" in context
        assert "launch_point" in context
        assert "drone_assignments" in context
        assert len(context["drone_assignments"]) == len(self.sample_drones)

    @pytest.mark.asyncio
    async def test_create_mission_plan(self):
        """Test complete mission plan creation."""
        mission_request = {
            "name": "Emergency SAR Mission",
            "description": "Search for missing person in urban area",
            "search_area": self.sample_search_area,
            "launch_point": self.sample_launch_point,
            "search_target": "person",
            "priority": "high"
        }

        plan = await self.mission_planner.create_mission_plan(mission_request, self.sample_drones)

        assert plan["success"] is True
        assert "mission_context" in plan
        assert "estimated_duration" in plan
        assert "drone_assignments" in plan
        assert plan["estimated_duration"] > 0

    @pytest.mark.asyncio
    async def test_update_mission_plan(self):
        """Test mission plan updates based on new information."""
        original_plan = {
            "mission_id": "test_mission_123",
            "search_area": self.sample_search_area,
            "estimated_duration": 45
        }

        updates = {
            "search_altitude": 40.0,
            "weather_conditions": {"wind_speed": 8.0}
        }

        updated_plan = await self.mission_planner.update_mission_plan(original_plan, updates)

        assert updated_plan["success"] is True
        assert "updated_at" in updated_plan
        assert updated_plan["estimated_duration"] != original_plan["estimated_duration"]

    def test_calculate_bearing_and_destination(self):
        """Test bearing calculation and destination point calculation."""
        start_point = [40.7128, -74.0060]
        bearing = 90  # East
        distance = 1000  # 1km

        dest_point = self.area_calculator.calculate_destination_point(start_point, bearing, distance)

        assert len(dest_point) == 2
        assert isinstance(dest_point[0], float)
        assert isinstance(dest_point[1], float)
        assert dest_point != start_point  # Should be different point

    def test_area_division_edge_cases(self):
        """Test area division with edge cases."""
        # Single drone
        assignments = self.area_calculator.divide_area_for_drones(
            self.sample_search_area, 1, self.sample_launch_point
        )
        assert len(assignments) == 1

        # Zero drones
        assignments = self.area_calculator.divide_area_for_drones(
            self.sample_search_area, 0, self.sample_launch_point
        )
        assert len(assignments) == 0

        # Invalid area
        assignments = self.area_calculator.divide_area_for_drones(
            [], 2, self.sample_launch_point
        )
        assert len(assignments) == 0

    def test_mission_plan_validation(self):
        """Test comprehensive mission plan validation."""
        valid_plan = {
            "name": "Valid Mission",
            "search_area": self.sample_search_area,
            "launch_point": self.sample_launch_point,
            "search_altitude": 30.0,
            "drone_count": 2
        }

        invalid_plan = {
            "name": "",  # Invalid: empty name
            "search_area": [],  # Invalid: no area
            "launch_point": None,  # Invalid: no launch point
            "search_altitude": -10.0,  # Invalid: negative altitude
            "drone_count": 0  # Invalid: no drones
        }

        # Mock validation method
        is_valid = self.mission_planner._validate_mission_plan(valid_plan)
        assert is_valid is True

        is_invalid = self.mission_planner._validate_mission_plan(invalid_plan)
        assert is_invalid is False


class TestDatabaseIntegration:
    """Test database operations for mission planning."""

    def setup_method(self):
        """Set up database test session."""
        self.db = SessionLocal()

    def teardown_method(self):
        """Clean up test session."""
        self.db.close()

    def test_mission_creation_in_database(self):
        """Test creating mission in database."""
        mission = Mission(
            name="Test Mission",
            description="Database integration test",
            search_area=json.dumps(self.sample_search_area),
            launch_point=json.dumps(self.sample_launch_point),
            search_target="person",
            search_altitude=30.0,
            status="planning"
        )

        self.db.add(mission)
        self.db.commit()

        # Verify mission was created
        saved_mission = self.db.query(Mission).filter(Mission.name == "Test Mission").first()
        assert saved_mission is not None
        assert saved_mission.status == "planning"

    def test_drone_assignment_creation(self):
        """Test creating drone assignments in database."""
        # Create test mission
        mission = Mission(
            name="Test Assignment Mission",
            search_area=json.dumps(self.sample_search_area),
            launch_point=json.dumps(self.sample_launch_point)
        )
        self.db.add(mission)
        self.db.commit()

        # Create test drone
        drone = Drone(
            id="test_drone_123",
            name="Test Assignment Drone",
            status="online"
        )
        self.db.add(drone)
        self.db.commit()

        # Create assignment
        assignment = DroneAssignment(
            mission_id=mission.id,
            drone_id=drone.id,
            assigned_area=json.dumps(self.sample_search_area[:3]),  # Partial area
            status="assigned"
        )
        self.db.add(assignment)
        self.db.commit()

        # Verify assignment
        saved_assignment = self.db.query(DroneAssignment).filter(
            DroneAssignment.mission_id == mission.id
        ).first()
        assert saved_assignment is not None
        assert saved_assignment.status == "assigned"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])