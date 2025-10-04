import pytest
import asyncio
from datetime import datetime
from app.services.emergency_protocols import EmergencyProtocols, EmergencyType, EmergencyLevel

@pytest.mark.asyncio
async def test_emergency_stop():
    """Test emergency stop protocol"""
    protocols = EmergencyProtocols()
    
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.EMERGENCY_STOP,
        reason="Test emergency stop",
        operator_id="test_operator",
        drone_ids=["drone_001", "drone_002"]
    )
    
    assert result["success"] is True
    assert "emergency_id" in result
    assert result["level"] == EmergencyLevel.CRITICAL.value
    assert "results" in result

@pytest.mark.asyncio
async def test_low_battery_emergency():
    """Test low battery emergency handling"""
    protocols = EmergencyProtocols()
    
    result = await protocols.handle_low_battery(
        drone_id="drone_001",
        battery_level=15.0,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    
    assert result["type"] == "low_battery"
    assert result["drone_id"] == "drone_001"
    assert result["battery_level"] == 15.0
    assert result["level"] == EmergencyLevel.CRITICAL.value
    assert result["action"] == "immediate_rtl"

@pytest.mark.asyncio
async def test_communication_loss():
    """Test communication loss emergency"""
    protocols = EmergencyProtocols()
    
    last_contact = datetime.utcnow()
    result = await protocols.handle_communication_loss(
        drone_id="drone_001",
        last_contact=last_contact,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    
    assert result["type"] == "communication_loss"
    assert result["drone_id"] == "drone_001"
    assert "time_since_contact" in result
    assert result["severity"] in ["medium", "high", "critical"]

@pytest.mark.asyncio
async def test_weather_emergency():
    """Test weather emergency handling"""
    protocols = EmergencyProtocols()
    
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.WEATHER_EMERGENCY,
        reason="Severe weather detected",
        operator_id="weather_system",
        drone_ids=["drone_001", "drone_002"],
        additional_data={
            "weather": {
                "wind_speed": 20,
                "visibility": 0.5,
                "precipitation": "heavy"
            }
        }
    )
    
    assert result["success"] is True
    assert result["level"] == EmergencyLevel.HIGH.value

@pytest.mark.asyncio
async def test_collision_risk():
    """Test collision risk emergency"""
    protocols = EmergencyProtocols()
    
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.COLLISION_RISK,
        reason="Obstacle detected",
        operator_id="collision_system",
        drone_ids=["drone_001"],
        additional_data={
            "obstacle": {
                "type": "building",
                "distance": 10,
                "bearing": 45
            }
        }
    )
    
    assert result["success"] is True
    assert result["level"] == EmergencyLevel.CRITICAL.value

@pytest.mark.asyncio
async def test_system_failure():
    """Test system failure emergency"""
    protocols = EmergencyProtocols()
    
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.SYSTEM_FAILURE,
        reason="GPS failure detected",
        operator_id="system_monitor",
        drone_ids=["drone_001"],
        additional_data={
            "failure_type": "gps",
            "severity": "critical"
        }
    )
    
    assert result["success"] is True
    assert result["level"] == EmergencyLevel.HIGH.value

@pytest.mark.asyncio
async def test_emergency_level_determination():
    """Test emergency level determination"""
    protocols = EmergencyProtocols()
    
    # Test different emergency types and their levels
    test_cases = [
        (EmergencyType.EMERGENCY_STOP, EmergencyLevel.CRITICAL),
        (EmergencyType.COMMUNICATION_LOSS, EmergencyLevel.HIGH),
        (EmergencyType.WEATHER_EMERGENCY, EmergencyLevel.HIGH),
        (EmergencyType.SYSTEM_FAILURE, EmergencyLevel.HIGH),
        (EmergencyType.MANUAL_OVERRIDE, EmergencyLevel.MEDIUM)
    ]
    
    for emergency_type, expected_level in test_cases:
        level = protocols._determine_emergency_level(emergency_type, {})
        assert level == expected_level.value

@pytest.mark.asyncio
async def test_battery_level_classification():
    """Test battery level classification"""
    protocols = EmergencyProtocols()
    
    # Test critical battery
    result = await protocols.handle_low_battery(
        drone_id="drone_001",
        battery_level=8.0,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    assert result["level"] == EmergencyLevel.CRITICAL.value
    assert result["action"] == "immediate_rtl"
    
    # Test high battery warning
    result = await protocols.handle_low_battery(
        drone_id="drone_001",
        battery_level=18.0,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    assert result["level"] == EmergencyLevel.HIGH.value
    assert result["action"] == "rtl_soon"
    
    # Test medium battery warning
    result = await protocols.handle_low_battery(
        drone_id="drone_001",
        battery_level=25.0,
        position={"lat": 37.7749, "lon": -122.4194, "alt": 50}
    )
    assert result["level"] == EmergencyLevel.MEDIUM.value
    assert result["action"] == "reduce_mission"

@pytest.mark.asyncio
async def test_active_emergencies_tracking():
    """Test active emergencies tracking"""
    protocols = EmergencyProtocols()
    
    # Trigger multiple emergencies
    result1 = await protocols.trigger_emergency(
        emergency_type=EmergencyType.LOW_BATTERY,
        reason="Battery low",
        operator_id="test_operator",
        drone_ids=["drone_001"]
    )
    
    result2 = await protocols.trigger_emergency(
        emergency_type=EmergencyType.COMMUNICATION_LOSS,
        reason="Comm lost",
        operator_id="test_operator",
        drone_ids=["drone_002"]
    )
    
    # Check active emergencies
    active = await protocols.get_active_emergencies()
    assert len(active) >= 2
    
    # Resolve one emergency
    await protocols.resolve_emergency(
        emergency_id=result1["emergency_id"],
        resolution="Battery replaced",
        operator_id="test_operator"
    )
    
    # Check active emergencies after resolution
    active_after = await protocols.get_active_emergencies()
    assert len(active_after) == len(active) - 1

@pytest.mark.asyncio
async def test_emergency_history():
    """Test emergency history tracking"""
    protocols = EmergencyProtocols()
    
    # Trigger emergency
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.EMERGENCY_STOP,
        reason="Test emergency",
        operator_id="test_operator",
        drone_ids=["drone_001"]
    )
    
    # Check history
    history = await protocols.get_emergency_history(limit=10)
    assert len(history) >= 1
    
    # Find our emergency in history
    emergency_found = any(
        e["id"] == result["emergency_id"] for e in history
    )
    assert emergency_found

@pytest.mark.asyncio
async def test_emergency_status_check():
    """Test emergency system status check"""
    protocols = EmergencyProtocols()
    
    status = await protocols.emergency_status_check()
    
    assert "active_emergencies" in status
    assert "total_logged" in status
    assert "system_status" in status
    assert "last_check" in status
    assert status["system_status"] in ["operational", "emergency_active"]

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in emergency protocols"""
    protocols = EmergencyProtocols()
    
    # Test with invalid emergency type
    try:
        await protocols.trigger_emergency(
            emergency_type=None,  # Invalid type
            reason="Test",
            operator_id="test_operator"
        )
        assert False, "Should have raised an error"
    except Exception:
        pass  # Expected to fail

@pytest.mark.asyncio
async def test_callback_registration():
    """Test custom emergency callback registration"""
    protocols = EmergencyProtocols()
    
    callback_called = False
    
    async def custom_callback(emergency):
        nonlocal callback_called
        callback_called = True
        return {"custom": "response"}
    
    # Register custom callback
    await protocols.register_emergency_callback(
        EmergencyType.MANUAL_OVERRIDE,
        custom_callback
    )
    
    # Trigger emergency
    result = await protocols.trigger_emergency(
        emergency_type=EmergencyType.MANUAL_OVERRIDE,
        reason="Test override",
        operator_id="test_operator"
    )
    
    assert callback_called
    assert result["success"] is True