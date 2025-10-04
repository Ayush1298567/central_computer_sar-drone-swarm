import pytest
import asyncio
from datetime import datetime
from app.services.mission_planner import MissionPlanner

@pytest.mark.asyncio
async def test_mission_planning_basic():
    """Test basic mission planning functionality"""
    planner = MissionPlanner()
    
    result = await planner.plan_mission(
        user_input="Search collapsed building at coordinates 37.7749, -122.4194",
        context={"drone_count": 5, "weather": "clear"},
        conversation_id="test123"
    )
    
    assert result["status"] in ["ready", "needs_clarification", "error"]
    assert "understanding_level" in result
    assert result["understanding_level"] >= 0.0
    assert "conversation_id" in result
    assert result["conversation_id"] == "test123"

@pytest.mark.asyncio
async def test_mission_planning_conversation():
    """Test conversation-based mission planning"""
    planner = MissionPlanner()
    conversation_id = f"test_conv_{datetime.now().timestamp()}"
    
    # First message
    result1 = await planner.plan_mission(
        user_input="I need to search for missing hikers",
        context={"drone_count": 3, "weather": "clear"},
        conversation_id=conversation_id
    )
    
    assert result1["status"] in ["ready", "needs_clarification"]
    
    # Follow-up message
    result2 = await planner.plan_mission(
        user_input="The area is mountainous terrain near coordinates 37.7, -122.4",
        context={"drone_count": 3, "weather": "clear"},
        conversation_id=conversation_id
    )
    
    assert result2["status"] in ["ready", "needs_clarification"]
    assert result2["understanding_level"] >= result1["understanding_level"]

@pytest.mark.asyncio
async def test_coordinate_generation():
    """Test coordinate generation functionality"""
    planner = MissionPlanner()
    
    coords = await planner._generate_coordinates({
        "area": {
            "bounds": {
                "north": 37.8,
                "south": 37.7,
                "east": -122.4,
                "west": -122.5
            }
        },
        "density": "medium",
        "altitude": 50,
        "search_pattern": "grid"
    })
    
    assert len(coords) > 100  # Should generate substantial grid
    assert all("lat" in c and "lon" in c for c in coords)
    assert all("altitude" in c for c in coords)
    
    # Check coordinate bounds
    lats = [c["lat"] for c in coords]
    lons = [c["lon"] for c in coords]
    
    assert min(lats) >= 37.7
    assert max(lats) <= 37.8
    assert min(lons) >= -122.5
    assert max(lons) <= -122.4

@pytest.mark.asyncio
async def test_parameter_extraction():
    """Test parameter extraction from AI responses"""
    planner = MissionPlanner()
    
    # Test terrain detection
    params = await planner._extract_parameters(
        "Search in forest area for missing person",
        {"mission_type": "search_and_rescue"}
    )
    
    assert "terrain_type" in params
    assert params["terrain_type"] == "forest"
    
    # Test mission type detection
    params = await planner._extract_parameters(
        "Rescue operation for 3 missing people",
        {}
    )
    
    assert "mission_type" in params
    assert "missing_count" in params

@pytest.mark.asyncio
async def test_understanding_calculation():
    """Test understanding level calculation"""
    planner = MissionPlanner()
    
    # Test with minimal parameters
    understanding1 = planner._calculate_understanding({
        "mission_type": "search_and_rescue"
    })
    
    # Test with more parameters
    understanding2 = planner._calculate_understanding({
        "mission_type": "search_and_rescue",
        "terrain_type": "forest",
        "missing_count": 2,
        "priority": "high"
    })
    
    assert understanding2 > understanding1
    assert understanding2 <= 1.0
    assert understanding1 >= 0.0

@pytest.mark.asyncio
async def test_conversation_state_management():
    """Test conversation state management"""
    planner = MissionPlanner()
    conversation_id = f"test_state_{datetime.now().timestamp()}"
    
    # Start conversation
    await planner.plan_mission(
        user_input="Test message",
        context={},
        conversation_id=conversation_id
    )
    
    # Check state exists
    state = await planner.get_conversation_history(conversation_id)
    assert "messages" in state
    assert len(state["messages"]) >= 2  # User message + AI response
    
    # Clear conversation
    await planner.clear_conversation(conversation_id)
    
    # Check state is cleared
    state_after = await planner.get_conversation_history(conversation_id)
    assert state_after == {}

@pytest.mark.asyncio
async def test_duration_estimation():
    """Test mission duration estimation"""
    planner = MissionPlanner()
    
    # Test with different coordinate counts
    coords_short = [{"lat": 37.7, "lon": -122.4, "alt": 50} for _ in range(10)]
    coords_long = [{"lat": 37.7, "lon": -122.4, "alt": 50} for _ in range(100)]
    
    duration_short = planner._estimate_duration(coords_short, {"speed": 5})
    duration_long = planner._estimate_duration(coords_long, {"speed": 5})
    
    assert duration_long > duration_short
    assert duration_short > 0
    assert duration_long > 0

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in mission planning"""
    planner = MissionPlanner()
    
    # Test with invalid input
    result = await planner.plan_mission(
        user_input="",
        context={},
        conversation_id="error_test"
    )
    
    assert "status" in result
    assert result["status"] in ["ready", "needs_clarification", "error"]

@pytest.mark.asyncio
async def test_fallback_response():
    """Test fallback response when AI is unavailable"""
    planner = MissionPlanner()
    
    # Test fallback response
    response = planner._get_fallback_response("search mission", {"drone_count": 5})
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert "search" in response.lower() or "mission" in response.lower()

@pytest.mark.asyncio
async def test_area_calculation():
    """Test area calculation functionality"""
    planner = MissionPlanner()
    
    area = planner._calculate_area(37.7, 37.8, -122.5, -122.4)
    
    assert area > 0
    assert isinstance(area, float)