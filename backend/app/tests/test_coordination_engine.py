"""
Tests for the coordination engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.coordination_engine import (
    CoordinationEngine,
    DroneState,
    MissionState,
    CoordinationCommand,
    CoordinationPriority,
    DroneStatus
)


@pytest.fixture
def coordination_engine():
    """Create a coordination engine instance for testing."""
    return CoordinationEngine()


@pytest.fixture
def sample_drone():
    """Create a sample drone state for testing."""
    return DroneState(
        drone_id="test-drone-1",
        status=DroneStatus.ONLINE,
        position=(40.7128, -74.0060, 30.0),
        battery_level=85.0,
        heading=0.0,
        speed=0.0
    )


@pytest.fixture
def sample_mission():
    """Create a sample mission state for testing."""
    return MissionState(
        mission_id="test-mission-1",
        status="active",
        drones=[],
        search_areas=[
            {
                "coordinates": [[
                    [40.7128, -74.0060],
                    [40.7589, -74.0060],
                    [40.7589, -73.9851],
                    [40.7128, -73.9851],
                    [40.7128, -74.0060]
                ]],
                "altitude": 30.0
            }
        ]
    )


class TestDroneRegistration:
    """Test drone registration functionality."""

    def test_register_drone(self, coordination_engine, sample_drone):
        """Test registering a drone with the coordination engine."""
        asyncio.run(coordination_engine.register_drone(sample_drone))

        assert sample_drone.drone_id in coordination_engine.drone_states
        assert coordination_engine.drone_states[sample_drone.drone_id] == sample_drone

    def test_unregister_drone(self, coordination_engine, sample_drone):
        """Test unregistering a drone from the coordination engine."""
        # First register the drone
        asyncio.run(coordination_engine.register_drone(sample_drone))
        assert sample_drone.drone_id in coordination_engine.drone_states

        # Then unregister it
        asyncio.run(coordination_engine.unregister_drone(sample_drone.drone_id))
        assert sample_drone.drone_id not in coordination_engine.drone_states


class TestMissionCoordination:
    """Test mission coordination functionality."""

    def test_start_mission(self, coordination_engine, sample_mission):
        """Test starting a mission coordination."""
        commands = asyncio.run(coordination_engine.start_mission(sample_mission.mission_id))

        # Should generate initial commands
        assert len(commands) > 0
        assert sample_mission.mission_id in coordination_engine.active_missions

    def test_update_drone_state(self, coordination_engine, sample_drone):
        """Test updating drone state and triggering coordination."""
        # Register drone first
        asyncio.run(coordination_engine.register_drone(sample_drone))

        # Update drone state
        updates = {"battery_level": 15.0}  # Low battery
        commands = asyncio.run(coordination_engine.update_drone_state(sample_drone.drone_id, updates))

        # Should generate return-to-home command due to low battery
        assert len(commands) > 0
        assert any(cmd.command_type == "return_to_home" for cmd in commands)


class TestBatteryManagement:
    """Test battery level management."""

    def test_low_battery_return_to_home(self, coordination_engine, sample_drone):
        """Test that drones with low battery return to home."""
        # Register drone with low battery
        sample_drone.battery_level = 15.0
        asyncio.run(coordination_engine.register_drone(sample_drone))

        # Check battery levels should trigger return command
        commands = asyncio.run(coordination_engine._check_battery_levels())

        assert len(commands) > 0
        assert commands[0].command_type == "return_to_home"
        assert commands[0].priority == CoordinationPriority.CRITICAL


class TestDroneSeparation:
    """Test drone separation and collision avoidance."""

    def test_drone_separation_check(self, coordination_engine):
        """Test checking and maintaining safe drone separation."""
        # Create two drones close to each other
        drone1 = DroneState(
            drone_id="drone-1",
            status=DroneStatus.FLYING,
            position=(40.7128, -74.0060, 30.0),
            battery_level=85.0,
            heading=0.0,
            speed=10.0
        )

        drone2 = DroneState(
            drone_id="drone-2",
            status=DroneStatus.FLYING,
            position=(40.7129, -74.0060, 30.0),  # Very close to drone1
            battery_level=90.0,
            heading=0.0,
            speed=10.0
        )

        asyncio.run(coordination_engine.register_drone(drone1))
        asyncio.run(coordination_engine.register_drone(drone2))

        # Check separation should detect the close proximity
        commands = asyncio.run(coordination_engine._check_drone_separation())

        # Should generate avoidance commands
        assert len(commands) > 0

    def test_avoidance_maneuver_calculation(self, coordination_engine):
        """Test calculation of avoidance maneuvers."""
        drone1 = DroneState(
            drone_id="drone-1",
            status=DroneStatus.FLYING,
            position=(40.7128, -74.0060, 30.0),
            battery_level=85.0,
            heading=0.0,
            speed=10.0
        )

        drone2 = DroneState(
            drone_id="drone-2",
            status=DroneStatus.FLYING,
            position=(40.7129, -74.0060, 30.0),
            battery_level=90.0,
            heading=0.0,
            speed=10.0
        )

        command = asyncio.run(
            coordination_engine._calculate_avoidance_maneuver(drone1, drone2, 10.0)
        )

        assert command is not None
        assert command.command_type == "adjust_position"
        assert command.priority == CoordinationPriority.HIGH


class TestWeatherIntegration:
    """Test weather-based coordination adjustments."""

    @patch('app.services.coordination_engine.weather_service')
    def test_high_wind_adjustment(self, mock_weather_service, coordination_engine):
        """Test altitude reduction in high wind conditions."""
        # Mock weather service to return high wind
        mock_weather = Mock()
        mock_weather.wind_speed = 15.0  # High wind
        mock_weather_service.get_current_weather.return_value = mock_weather

        # Create mission with weather conditions
        mission = MissionState(
            mission_id="test-mission",
            status="active",
            weather_conditions={"wind_speed": 15.0}
        )

        # Add flying drone to mission
        drone = DroneState(
            drone_id="drone-1",
            status=DroneStatus.FLYING,
            position=(40.7128, -74.0060, 30.0),
            battery_level=85.0
        )
        mission.drones.append(drone)

        coordination_engine.active_missions[mission.mission_id] = mission

        # Check weather impact should generate altitude adjustment
        commands = asyncio.run(coordination_engine._check_weather_impact())

        assert len(commands) > 0
        assert commands[0].command_type == "adjust_altitude"


class TestCommandPrioritization:
    """Test command prioritization and filtering."""

    def test_command_prioritization(self, coordination_engine):
        """Test that commands are properly prioritized."""
        commands = [
            CoordinationCommand(
                drone_id="drone-1",
                command_type="navigate",
                parameters={},
                priority=CoordinationPriority.LOW,
                reason="Low priority command"
            ),
            CoordinationCommand(
                drone_id="drone-2",
                command_type="return_to_home",
                parameters={},
                priority=CoordinationPriority.CRITICAL,
                reason="Emergency return"
            )
        ]

        prioritized = coordination_engine._prioritize_commands(commands)

        # Critical command should come first
        assert prioritized[0].priority == CoordinationPriority.CRITICAL
        assert prioritized[1].priority == CoordinationPriority.LOW


class TestDistanceCalculation:
    """Test distance calculation functionality."""

    def test_calculate_distance_3d(self, coordination_engine):
        """Test 3D distance calculation between two points."""
        pos1 = (40.7128, -74.0060, 30.0)
        pos2 = (40.7129, -74.0061, 35.0)

        distance = coordination_engine._calculate_distance(pos1, pos2)

        # Should calculate a reasonable distance
        assert distance > 0
        assert isinstance(distance, float)


class TestSearchPatternGeneration:
    """Test search pattern and waypoint generation."""

    def test_generate_search_waypoints(self, coordination_engine):
        """Test generation of search waypoints for an area."""
        search_area = {
            "coordinates": [[
                [40.7128, -74.0060],
                [40.7589, -74.0060],
                [40.7589, -73.9851],
                [40.7128, -73.9851],
                [40.7128, -74.0060]
            ]],
            "altitude": 30.0
        }

        waypoints = coordination_engine._generate_search_waypoints(search_area)

        # Should generate waypoints for the search area
        assert len(waypoints) > 0
        assert all(isinstance(wp, tuple) and len(wp) == 3 for wp in waypoints)


if __name__ == "__main__":
    pytest.main([__file__])