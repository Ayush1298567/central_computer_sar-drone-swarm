"""
Comprehensive Mission Lifecycle Tests
Tests full mission orchestration with multi-drone scenarios
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.real_mission_execution import (
    RealMissionExecutionEngine,
    MissionPhase,
    DroneState,
    MissionState
)


@pytest.mark.asyncio
async def test_mission_engine_start_stop():
    """Test mission engine lifecycle"""
    engine = RealMissionExecutionEngine()
    
    # Start engine
    started = await engine.start()
    assert started is True
    assert engine._running is True
    
    # Stop engine
    stopped = await engine.stop()
    assert stopped is True
    assert engine._running is False


@pytest.mark.asyncio
async def test_execute_mission_initialization():
    """Test mission initialization creates proper state"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    # Mock hub to prevent actual command sending
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    # Mock registry
    mock_registry = Mock()
    mock_registry.get_drone = Mock(return_value=Mock(drone_id="drone_1"))
    engine.registry = mock_registry
    
    # Execute mission
    result = await engine.execute_mission(
        mission_id="test_mission_001",
        drone_ids=["drone_1", "drone_2"],
        waypoints=[
            {"lat": 40.7128, "lon": -74.0060, "alt": 50},
            {"lat": 40.7130, "lon": -74.0062, "alt": 50}
        ],
        parameters={"altitude": 50, "speed": 5}
    )
    
    assert result["success"] is True
    assert result["mission_id"] == "test_mission_001"
    assert len(result["drones"]) == 2
    
    # Verify mission state was created
    assert "test_mission_001" in engine._running_missions
    mission = engine._running_missions["test_mission_001"]
    
    assert mission.mission_id == "test_mission_001"
    assert mission.status == "RUNNING"
    assert len(mission.drones) == 2
    assert len(mission.waypoints) == 2
    
    # Verify drone states initialized
    for drone_id in ["drone_1", "drone_2"]:
        assert drone_id in mission.drones
        drone_state = mission.drones[drone_id]
        assert drone_state.phase == MissionPhase.PREPARE
        assert drone_state.progress == 0.0
        assert drone_state.total_waypoints == 2
    
    await engine.stop()


@pytest.mark.asyncio
async def test_mission_abort():
    """Test mission abortion functionality"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    # Mock dependencies
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    # Create a mission
    mission = MissionState(
        mission_id="abort_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.5,
                current_waypoint=5,
                total_waypoints=10,
                battery_level=80.0,
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.5,
        current_phase=MissionPhase.SEARCH
    )
    
    engine._running_missions["abort_test"] = mission
    
    # Abort mission
    success = await engine.abort_mission("abort_test", "Test abort")
    
    assert success is True
    assert mission.status == "ABORTED"
    assert mission.current_phase == MissionPhase.ABORTED
    assert mission.emergency_triggered is True
    assert mission.end_time is not None
    
    # Verify RTL command was sent
    mock_hub.send_command.assert_called_once()
    call_kwargs = mock_hub.send_command.call_args[1]
    assert call_kwargs["command_type"] == "return_home"
    assert call_kwargs["priority"] == 3
    
    await engine.stop()


@pytest.mark.asyncio
async def test_mission_pause_resume():
    """Test mission pause and resume"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    # Create mission
    mission = MissionState(
        mission_id="pause_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.5,
                current_waypoint=5,
                total_waypoints=10,
                battery_level=80.0,
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.5,
        current_phase=MissionPhase.SEARCH
    )
    
    engine._running_missions["pause_test"] = mission
    
    # Pause mission
    paused = await engine.pause_mission("pause_test")
    assert paused is True
    assert mission.status == "PAUSED"
    
    # Resume mission
    resumed = await engine.resume_mission("pause_test")
    assert resumed is True
    assert mission.status == "RUNNING"
    
    await engine.stop()


@pytest.mark.asyncio
async def test_mission_progress_calculation():
    """Test overall mission progress calculation"""
    engine = RealMissionExecutionEngine()
    
    mission = MissionState(
        mission_id="progress_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.3,
                current_waypoint=3,
                total_waypoints=10,
                battery_level=80.0,
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            ),
            "drone_2": DroneState(
                drone_id="drone_2",
                phase=MissionPhase.SEARCH,
                progress=0.7,
                current_waypoint=7,
                total_waypoints=10,
                battery_level=60.0,
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.0,
        current_phase=MissionPhase.SEARCH
    )
    
    engine._calculate_progress(mission)
    
    # Average of 0.3 and 0.7 = 0.5
    assert mission.overall_progress == 0.5


@pytest.mark.asyncio
async def test_battery_monitoring_triggers_rtl():
    """Test that low battery automatically triggers RTL"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    # Create mission with low battery drone
    mission = MissionState(
        mission_id="battery_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.5,
                current_waypoint=5,
                total_waypoints=10,
                battery_level=20.0,  # Below 25% threshold
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.5,
        current_phase=MissionPhase.SEARCH
    )
    
    engine._running_missions["battery_test"] = mission
    
    # Check emergency conditions
    await engine._check_emergency_conditions(mission)
    
    # Verify RTL was triggered
    mock_hub.send_command.assert_called_once()
    call_kwargs = mock_hub.send_command.call_args[1]
    assert call_kwargs["command_type"] == "return_home"
    assert "Low battery" in call_kwargs["parameters"]["reason"]
    
    # Verify drone phase changed to RETURN
    assert mission.drones["drone_1"].phase == MissionPhase.RETURN
    
    await engine.stop()


@pytest.mark.asyncio
async def test_critical_battery_triggers_emergency_land():
    """Test that critical battery triggers emergency landing"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    # Create mission with critical battery
    mission = MissionState(
        mission_id="critical_battery_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.5,
                current_waypoint=5,
                total_waypoints=10,
                battery_level=10.0,  # Below 15% critical threshold
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.5,
        current_phase=MissionPhase.SEARCH
    )
    
    engine._running_missions["critical_battery_test"] = mission
    
    # Check emergency conditions
    await engine._check_emergency_conditions(mission)
    
    # Verify emergency land was triggered
    mock_hub.send_command.assert_called_once()
    call_kwargs = mock_hub.send_command.call_args[1]
    assert call_kwargs["command_type"] == "emergency_land"
    assert call_kwargs["priority"] == 3
    
    # Verify drone phase changed to ABORTED
    assert mission.drones["drone_1"].phase == MissionPhase.ABORTED
    
    await engine.stop()


@pytest.mark.asyncio
async def test_get_mission_status():
    """Test retrieving mission status"""
    engine = RealMissionExecutionEngine()
    
    # Create mission
    mission = MissionState(
        mission_id="status_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.TRANSIT,
                progress=0.4,
                current_waypoint=0,
                total_waypoints=5,
                battery_level=85.0,
                altitude=50.0,
                position={"lat": 40.0, "lon": -74.0, "alt": 50.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.4,
        current_phase=MissionPhase.TRANSIT
    )
    
    engine._running_missions["status_test"] = mission
    
    # Get status
    status = engine.get_mission_status("status_test")
    
    assert status is not None
    assert status["mission_id"] == "status_test"
    assert status["status"] == "RUNNING"
    assert status["current_phase"] == "transit"
    assert status["overall_progress"] == 0.4
    assert status["drones_count"] == 1
    assert "drone_1" in status["drones"]


@pytest.mark.asyncio
async def test_multi_drone_mission_coordination():
    """Test coordinating a mission with multiple drones"""
    engine = RealMissionExecutionEngine()
    await engine.start()
    
    # Mock dependencies
    mock_hub = Mock()
    mock_hub.send_command = AsyncMock(return_value=True)
    engine.hub = mock_hub
    
    mock_registry = Mock()
    mock_registry.get_drone = Mock(return_value=Mock(drone_id="test"))
    engine.registry = mock_registry
    
    # Create mission with 3 drones
    result = await engine.execute_mission(
        mission_id="multi_drone_test",
        drone_ids=["drone_1", "drone_2", "drone_3"],
        waypoints=[
            {"lat": 40.7128, "lon": -74.0060, "alt": 50},
            {"lat": 40.7130, "lon": -74.0062, "alt": 50},
            {"lat": 40.7132, "lon": -74.0064, "alt": 50}
        ],
        parameters={"altitude": 50, "speed": 5}
    )
    
    assert result["success"] is True
    
    # Wait for mission to progress through some phases
    await asyncio.sleep(0.5)
    
    mission = engine._running_missions["multi_drone_test"]
    
    # Verify all 3 drones have state
    assert len(mission.drones) == 3
    for drone_id in ["drone_1", "drone_2", "drone_3"]:
        assert drone_id in mission.drones
        assert isinstance(mission.drones[drone_id], DroneState)
    
    await engine.stop()


@pytest.mark.asyncio
async def test_mission_phases_enum():
    """Test MissionPhase enum values"""
    assert MissionPhase.PREPARE.value == "prepare"
    assert MissionPhase.TAKEOFF.value == "takeoff"
    assert MissionPhase.TRANSIT.value == "transit"
    assert MissionPhase.SEARCH.value == "search"
    assert MissionPhase.RETURN.value == "return"
    assert MissionPhase.LAND.value == "land"
    assert MissionPhase.COMPLETE.value == "complete"
    assert MissionPhase.ABORTED.value == "aborted"
    assert MissionPhase.FAILED.value == "failed"


@pytest.mark.asyncio
async def test_telemetry_integration():
    """Test that mission engine updates from telemetry"""
    engine = RealMissionExecutionEngine()
    
    # Mock telemetry receiver
    mock_receiver = Mock()
    mock_cache = Mock()
    mock_cache.get = Mock(return_value={
        "battery_level": 75.0,
        "position": {"lat": 40.7128, "lon": -74.0060, "alt": 55.0}
    })
    mock_receiver.cache = mock_cache
    
    # Create mission
    mission = MissionState(
        mission_id="telemetry_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.SEARCH,
                progress=0.5,
                current_waypoint=5,
                total_waypoints=10,
                battery_level=100.0,  # Will be updated
                altitude=50.0,  # Will be updated
                position={"lat": 0.0, "lon": 0.0, "alt": 0.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.5,
        current_phase=MissionPhase.SEARCH
    )
    
    # Update from telemetry
    with patch('app.communication.telemetry_receiver.get_telemetry_receiver', return_value=mock_receiver):
        await engine._update_from_telemetry(mission)
    
    # Verify drone state was updated
    drone_state = mission.drones["drone_1"]
    assert drone_state.battery_level == 75.0
    assert drone_state.altitude == 55.0
    assert drone_state.position["lat"] == 40.7128


@pytest.mark.asyncio
async def test_mission_complete_flow():
    """Test mission completion updates state correctly"""
    engine = RealMissionExecutionEngine()
    
    mission = MissionState(
        mission_id="complete_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.LAND,
                progress=0.95,
                current_waypoint=10,
                total_waypoints=10,
                battery_level=40.0,
                altitude=0.0,
                position={"lat": 0.0, "lon": 0.0, "alt": 0.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.95,
        current_phase=MissionPhase.LAND
    )
    
    engine._running_missions["complete_test"] = mission
    
    # Mock WebSocket
    with patch('app.api.websocket.connection_manager'):
        await engine._complete_mission("complete_test")
    
    # Verify mission completed
    assert mission.status == "COMPLETED"
    assert mission.current_phase == MissionPhase.COMPLETE
    assert mission.overall_progress == 1.0
    assert mission.end_time is not None
    
    # Verify drone completed
    assert mission.drones["drone_1"].phase == MissionPhase.COMPLETE
    assert mission.drones["drone_1"].progress == 1.0


@pytest.mark.asyncio
async def test_mission_fail_flow():
    """Test mission failure updates state correctly"""
    engine = RealMissionExecutionEngine()
    
    mission = MissionState(
        mission_id="fail_test",
        status="RUNNING",
        start_time=datetime.utcnow(),
        end_time=None,
        drones={
            "drone_1": DroneState(
                drone_id="drone_1",
                phase=MissionPhase.TAKEOFF,
                progress=0.2,
                current_waypoint=0,
                total_waypoints=10,
                battery_level=90.0,
                altitude=10.0,
                position={"lat": 0.0, "lon": 0.0, "alt": 10.0},
                last_update=datetime.utcnow()
            )
        },
        waypoints=[],
        parameters={},
        overall_progress=0.2,
        current_phase=MissionPhase.TAKEOFF
    )
    
    engine._running_missions["fail_test"] = mission
    
    # Mock WebSocket
    with patch('app.api.websocket.connection_manager'):
        await engine._fail_mission("fail_test", "Takeoff timeout")
    
    # Verify mission failed
    assert mission.status == "FAILED"
    assert mission.current_phase == MissionPhase.FAILED
    assert mission.end_time is not None
    
    # Verify drone failed with error message
    assert mission.drones["drone_1"].phase == MissionPhase.FAILED
    assert mission.drones["drone_1"].error_message == "Takeoff timeout"


@pytest.mark.asyncio
async def test_get_all_missions():
    """Test retrieving all mission statuses"""
    engine = RealMissionExecutionEngine()
    
    # Create multiple missions
    for i in range(3):
        mission = MissionState(
            mission_id=f"mission_{i}",
            status="RUNNING",
            start_time=datetime.utcnow(),
            end_time=None,
            drones={},
            waypoints=[],
            parameters={},
            overall_progress=i * 0.3,
            current_phase=MissionPhase.SEARCH
        )
        engine._running_missions[f"mission_{i}"] = mission
    
    # Get all missions
    all_missions = engine.get_all_missions()
    
    assert len(all_missions) == 3
    assert all(m is not None for m in all_missions)


def test_mission_system_coverage():
    """Verify all required mission orchestration components exist"""
    from app.services import real_mission_execution
    
    required_classes = [
        'RealMissionExecutionEngine',
        'MissionPhase',
        'DroneState',
        'MissionState'
    ]
    
    for class_name in required_classes:
        assert hasattr(real_mission_execution, class_name), f"Missing class: {class_name}"
    
    required_methods = [
        'execute_mission',
        'abort_mission',
        'pause_mission',
        'resume_mission',
        'get_mission_status',
        'get_all_missions'
    ]
    
    engine = RealMissionExecutionEngine()
    for method_name in required_methods:
        assert hasattr(engine, method_name), f"Missing method: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

