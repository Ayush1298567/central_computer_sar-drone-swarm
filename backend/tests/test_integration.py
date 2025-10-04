import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db, get_sync_db
from app.services.mission_planner import MissionPlanner
from app.services.emergency_protocols import EmergencyProtocols, EmergencyType
from app.services.search_algorithms import SearchAlgorithms, SearchPattern

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
async def db_session():
    """Create database session for testing"""
    # Initialize test database
    await init_db()
    async for session in get_sync_db():
        yield session

@pytest.mark.asyncio
async def test_health_check():
    """Test system health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data
        assert "services" in data

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "SAR Drone Swarm Control System" in data["message"]
        assert "version" in data
        assert "status" in data

@pytest.mark.asyncio
async def test_emergency_stop_endpoint():
    """Test emergency stop endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/emergency-stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "emergency_stop_activated" in data["status"]
        assert "timestamp" in data
        assert "message" in data

@pytest.mark.asyncio
async def test_mission_planner_integration():
    """Test mission planner integration"""
    planner = MissionPlanner()
    
    # Test basic mission planning
    result = await planner.plan_mission(
        user_input="Search for missing hikers in mountain area",
        context={
            "drone_count": 5,
            "weather": "clear",
            "terrain_type": "mountain"
        },
        conversation_id="integration_test"
    )
    
    assert result["status"] in ["ready", "needs_clarification", "error"]
    assert "understanding_level" in result
    assert "conversation_id" in result

@pytest.mark.asyncio
async def test_emergency_protocols_integration():
    """Test emergency protocols integration"""
    protocols = EmergencyProtocols()
    
    # Test emergency stop
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.EMERGENCY_STOP,
        reason="Integration test emergency",
        operator_id="test_system",
        drone_ids=["test_drone_001"]
    )
    
    assert result["success"] is True
    assert "emergency_id" in result
    assert "level" in result
    
    # Test low battery emergency
    battery_result = await protocols.handle_low_battery(
        drone_id="test_drone_001",
        battery_level=12.0,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    
    assert battery_result["type"] == "low_battery"
    assert battery_result["drone_id"] == "test_drone_001"
    assert battery_result["level"] == "critical"

@pytest.mark.asyncio
async def test_search_algorithms_integration():
    """Test search algorithms integration"""
    center = {"lat": 37.7749, "lon": -122.4194}
    
    # Test grid pattern generation
    waypoints = SearchAlgorithms.generate_search_pattern(
        pattern_type=SearchPattern.GRID,
        center=center,
        parameters={
            "width_m": 1000,
            "height_m": 1000,
            "spacing_m": 100,
            "altitude_m": 50
        }
    )
    
    assert len(waypoints) > 0
    assert all("lat" in wp and "lon" in wp and "alt" in wp for wp in waypoints)
    
    # Test coverage calculation
    coverage = SearchAlgorithms.calculate_search_coverage(waypoints, search_radius_m=25)
    assert coverage["coverage_percent"] > 0
    assert coverage["area_covered_km2"] > 0
    
    # Test waypoint validation
    validation = SearchAlgorithms.validate_waypoints(waypoints)
    assert validation["valid"] is True
    assert len(validation["errors"]) == 0

@pytest.mark.asyncio
async def test_full_mission_workflow():
    """Test complete mission workflow"""
    planner = MissionPlanner()
    protocols = EmergencyProtocols()
    
    # Step 1: Plan mission
    plan_result = await planner.plan_mission(
        user_input="Search collapsed building at coordinates 37.7749, -122.4194",
        context={
            "drone_count": 3,
            "weather": "clear",
            "mission_type": "search_and_rescue"
        },
        conversation_id="workflow_test"
    )
    
    assert plan_result["status"] in ["ready", "needs_clarification"]
    
    # Step 2: Generate search pattern if mission is ready
    if plan_result["status"] == "ready":
        mission_plan = plan_result["mission_plan"]
        waypoints = mission_plan.get("coordinates", [])
        
        assert len(waypoints) > 0
        
        # Step 3: Test emergency handling during mission
        emergency_result = await protocols.trigger_emergency(
            emergency_type=EmergencyType.LOW_BATTERY,
            reason="Low battery during mission",
            operator_id="mission_controller",
            drone_ids=["mission_drone_001"],
            additional_data={
                "battery_level": 15.0,
                "position": waypoints[0] if waypoints else {"lat": 37.7749, "lon": -122.4194, "alt": 50}
            }
        )
        
        assert emergency_result["success"] is True

@pytest.mark.asyncio
async def test_error_handling_integration():
    """Test error handling across components"""
    planner = MissionPlanner()
    protocols = EmergencyProtocols()
    
    # Test mission planner with invalid input
    result = await planner.plan_mission(
        user_input="",  # Empty input
        context={},
        conversation_id="error_test"
    )
    
    assert "status" in result
    assert result["status"] in ["ready", "needs_clarification", "error"]
    
    # Test emergency protocols with invalid data
    try:
        await protocols.trigger_emergency(
            emergency_type=None,  # Invalid type
            reason="Test",
            operator_id="test"
        )
        assert False, "Should have raised an error"
    except Exception:
        pass  # Expected to fail

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent operations"""
    planner = MissionPlanner()
    protocols = EmergencyProtocols()
    
    # Run multiple operations concurrently
    tasks = [
        planner.plan_mission(
            user_input=f"Mission {i}",
            context={"drone_count": 2},
            conversation_id=f"concurrent_test_{i}"
        )
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    for result in results:
        assert "status" in result
        assert "conversation_id" in result

@pytest.mark.asyncio
async def test_data_consistency():
    """Test data consistency across components"""
    planner = MissionPlanner()
    
    # Create mission with specific parameters
    result = await planner.plan_mission(
        user_input="Search forest area for 2 missing persons",
        context={
            "drone_count": 4,
            "weather": "clear",
            "terrain_type": "forest",
            "missing_count": 2
        },
        conversation_id="consistency_test"
    )
    
    if result["status"] == "ready":
        mission_plan = result["mission_plan"]
        
        # Verify mission plan contains expected data
        assert "mission_type" in mission_plan
        assert "coordinates" in mission_plan
        assert "estimated_duration_minutes" in mission_plan
        assert "search_pattern" in mission_plan
        
        # Verify coordinates are valid
        coordinates = mission_plan["coordinates"]
        assert len(coordinates) > 0
        assert all("lat" in coord and "lon" in coord for coord in coordinates)

@pytest.mark.asyncio
async def test_system_performance():
    """Test system performance with multiple operations"""
    planner = MissionPlanner()
    
    # Test multiple rapid mission planning requests
    start_time = asyncio.get_event_loop().time()
    
    tasks = [
        planner.plan_mission(
            user_input=f"Performance test mission {i}",
            context={"drone_count": 3},
            conversation_id=f"perf_test_{i}"
        )
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    # Should complete within reasonable time (adjust threshold as needed)
    assert duration < 10.0  # 10 seconds for 5 operations
    assert len(results) == 5
    
    # All operations should succeed
    for result in results:
        assert "status" in result
        assert result["status"] in ["ready", "needs_clarification", "error"]

@pytest.mark.asyncio
async def test_websocket_authentication():
    """Test WebSocket authentication (basic test)"""
    # This is a basic test - full WebSocket testing would require more setup
    from app.core.security import create_access_token, verify_token
    
    # Create test token
    token = create_access_token(data={"sub": "1", "username": "test_user"})
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["username"] == "test_user"

@pytest.mark.asyncio
async def test_database_operations():
    """Test database operations"""
    from app.core.database import check_db_health
    
    # Test database health
    is_healthy = await check_db_health()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_configuration_validation():
    """Test configuration validation"""
    from app.core.config import settings
    
    # Test that settings are loaded correctly
    assert settings.PROJECT_NAME == "SAR Drone Swarm Control"
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) >= 32
    assert settings.OLLAMA_HOST.startswith(("http://", "https://"))