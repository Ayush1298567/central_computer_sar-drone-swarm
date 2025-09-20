"""
Comprehensive test suite for all API endpoints
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_sar_missions.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override database dependency
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import after setting up test database
from app.main import app
from app.core.database import get_db, Base

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test tables
Base.metadata.create_all(bind=test_engine)

# Create test client
client = TestClient(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAPIEndpoints:
    """Comprehensive API endpoint tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear test data
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        
        # Test data
        self.test_mission_data = {
            "name": "Test SAR Mission",
            "description": "Test mission for API validation",
            "mission_type": "missing_person",
            "priority": "high",
            "search_area": {
                "center_lat": 34.0522,
                "center_lng": -118.2437,
                "radius_km": 5.0,
                "boundaries": None,
                "no_fly_zones": []
            },
            "requirements": {
                "max_duration_hours": 3.0,
                "min_drone_count": 1,
                "max_drone_count": 3,
                "required_sensors": ["camera", "gps"],
                "weather_constraints": {},
                "altitude_constraints": {}
            },
            "created_by": "test_user"
        }
        
        self.test_drone_data = {
            "drone_id": "test_drone_001",
            "name": "Test Drone Alpha",
            "drone_type": "quadcopter",
            "ip_address": "192.168.1.100",
            "port": 8080,
            "capabilities": {
                "max_flight_time_minutes": 30.0,
                "max_speed_ms": 15.0,
                "max_altitude_m": 500.0,
                "camera_resolution": "4K",
                "has_thermal_camera": True,
                "has_lidar": False,
                "has_gps": True,
                "payload_capacity_kg": 2.0,
                "weather_resistance": "good"
            },
            "firmware_version": "1.2.3",
            "hardware_version": "v2.1"
        }
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        logger.info("✅ Root endpoint test passed")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        logger.info("✅ Health check test passed")
    
    def test_api_info(self):
        """Test API info endpoint"""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "version" in data
        assert "endpoints" in data
        logger.info("✅ API info test passed")
    
    # Mission API Tests
    def test_create_mission(self):
        """Test mission creation"""
        response = client.post("/api/v1/missions/", json=self.test_mission_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == self.test_mission_data["name"]
        assert data["mission_type"] == self.test_mission_data["mission_type"]
        assert data["priority"] == self.test_mission_data["priority"]
        assert data["status"] == "planned"
        assert "mission_id" in data
        assert "drone_assignments" in data
        assert "timeline" in data
        
        self.created_mission_id = data["mission_id"]
        logger.info(f"✅ Mission creation test passed - ID: {self.created_mission_id}")
        return data
    
    def test_list_missions(self):
        """Test mission listing"""
        # Create a mission first
        self.test_create_mission()
        
        response = client.get("/api/v1/missions/")
        assert response.status_code == 200
        
        data = response.json()
        assert "missions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["missions"]) >= 1
        logger.info("✅ Mission listing test passed")
    
    def test_get_mission(self):
        """Test getting specific mission"""
        # Create a mission first
        created_mission = self.test_create_mission()
        mission_id = created_mission["mission_id"]
        
        response = client.get(f"/api/v1/missions/{mission_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["mission_id"] == mission_id
        assert data["name"] == self.test_mission_data["name"]
        logger.info(f"✅ Get mission test passed - ID: {mission_id}")
    
    def test_update_mission(self):
        """Test mission update"""
        # Create a mission first
        created_mission = self.test_create_mission()
        mission_id = created_mission["mission_id"]
        
        update_data = {
            "name": "Updated Test Mission",
            "priority": "urgent"
        }
        
        response = client.patch(f"/api/v1/missions/{mission_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["priority"] == update_data["priority"]
        logger.info(f"✅ Mission update test passed - ID: {mission_id}")
    
    def test_mission_lifecycle(self):
        """Test complete mission lifecycle"""
        # Create mission
        created_mission = self.test_create_mission()
        mission_id = created_mission["mission_id"]
        
        # Start mission
        response = client.post(f"/api/v1/missions/{mission_id}/start")
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Pause mission
        response = client.post(f"/api/v1/missions/{mission_id}/pause")
        assert response.status_code == 200
        
        # Resume mission
        response = client.post(f"/api/v1/missions/{mission_id}/resume")
        assert response.status_code == 200
        
        # Abort mission
        response = client.post(f"/api/v1/missions/{mission_id}/abort?reason=Test%20abort")
        assert response.status_code == 200
        
        logger.info(f"✅ Mission lifecycle test passed - ID: {mission_id}")
    
    # Drone API Tests
    def test_drone_discovery(self):
        """Test drone discovery"""
        response = client.post("/api/v1/drones/discover?discovery_method=network_scan&timeout_seconds=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "drones" in data
        assert "discovery_method" in data
        logger.info("✅ Drone discovery test passed")
    
    def test_register_drone(self):
        """Test drone registration"""
        response = client.post("/api/v1/drones/register", json=self.test_drone_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["drone_id"] == self.test_drone_data["drone_id"]
        assert data["name"] == self.test_drone_data["name"]
        assert data["drone_type"] == self.test_drone_data["drone_type"]
        assert data["status"] == "idle"
        
        self.registered_drone_id = data["drone_id"]
        logger.info(f"✅ Drone registration test passed - ID: {self.registered_drone_id}")
        return data
    
    def test_list_drones(self):
        """Test drone listing"""
        # Register a drone first
        self.test_register_drone()
        
        response = client.get("/api/v1/drones/")
        assert response.status_code == 200
        
        data = response.json()
        assert "drones" in data
        assert "total" in data
        assert len(data["drones"]) >= 1
        logger.info("✅ Drone listing test passed")
    
    def test_get_drone(self):
        """Test getting specific drone"""
        # Register a drone first
        registered_drone = self.test_register_drone()
        drone_id = registered_drone["drone_id"]
        
        response = client.get(f"/api/v1/drones/{drone_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["drone_id"] == drone_id
        assert data["name"] == self.test_drone_data["name"]
        logger.info(f"✅ Get drone test passed - ID: {drone_id}")
    
    def test_update_drone(self):
        """Test drone update"""
        # Register a drone first
        registered_drone = self.test_register_drone()
        drone_id = registered_drone["drone_id"]
        
        update_data = {
            "name": "Updated Test Drone",
            "status": "maintenance"
        }
        
        response = client.patch(f"/api/v1/drones/{drone_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        logger.info(f"✅ Drone update test passed - ID: {drone_id}")
    
    def test_drone_telemetry(self):
        """Test drone telemetry submission"""
        # Register a drone first
        registered_drone = self.test_register_drone()
        drone_id = registered_drone["drone_id"]
        
        telemetry_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": 34.0522,
            "longitude": -118.2437,
            "altitude_m": 100.0,
            "speed_ms": 5.0,
            "heading_deg": 90.0,
            "battery_percent": 85.0,
            "signal_strength": 95,
            "gps_satellites": 12
        }
        
        response = client.post(f"/api/v1/drones/{drone_id}/telemetry", json=telemetry_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["drone_id"] == drone_id
        assert "telemetry" in data
        assert "received_at" in data
        logger.info(f"✅ Drone telemetry test passed - ID: {drone_id}")
    
    def test_drone_health_check(self):
        """Test drone health check"""
        # Register a drone first
        registered_drone = self.test_register_drone()
        drone_id = registered_drone["drone_id"]
        
        response = client.post(f"/api/v1/drones/{drone_id}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["drone_id"] == drone_id
        assert "health" in data
        assert "checked_at" in data
        logger.info(f"✅ Drone health check test passed - ID: {drone_id}")
    
    def test_drone_command(self):
        """Test sending command to drone"""
        # Register a drone first
        registered_drone = self.test_register_drone()
        drone_id = registered_drone["drone_id"]
        
        command_data = {
            "command_type": "takeoff",
            "parameters": {"altitude": 50},
            "priority": 5,
            "timeout_seconds": 30
        }
        
        response = client.post(f"/api/v1/drones/{drone_id}/command", json=command_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["drone_id"] == drone_id
        assert "command_id" in data
        assert data["status"] == "sent"
        logger.info(f"✅ Drone command test passed - ID: {drone_id}")
    
    # Chat API Tests
    def test_create_chat_session(self):
        """Test chat session creation"""
        session_data = {
            "user_id": "test_user",
            "initial_message": "I need to plan a search and rescue mission"
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["user_id"] == session_data["user_id"]
        assert data["status"] == "active"
        assert "session_id" in data
        assert "current_stage" in data
        
        self.created_session_id = data["session_id"]
        logger.info(f"✅ Chat session creation test passed - ID: {self.created_session_id}")
        return data
    
    def test_list_chat_sessions(self):
        """Test chat session listing"""
        # Create a session first
        self.test_create_chat_session()
        
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        logger.info("✅ Chat session listing test passed")
    
    def test_get_conversation(self):
        """Test getting conversation"""
        # Create a session first
        created_session = self.test_create_chat_session()
        session_id = created_session["session_id"]
        
        response = client.get(f"/api/v1/chat/sessions/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "session" in data
        assert "messages" in data
        assert data["session"]["session_id"] == session_id
        logger.info(f"✅ Get conversation test passed - ID: {session_id}")
    
    def test_send_message(self):
        """Test sending message in chat"""
        # Create a session first
        created_session = self.test_create_chat_session()
        session_id = created_session["session_id"]
        
        message_data = {
            "content": "I need to plan a missing person search mission with high priority",
            "metadata": {"test": True}
        }
        
        response = client.post(f"/api/v1/chat/sessions/{session_id}/messages", json=message_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["content"] == message_data["content"]
        assert data["role"] == "user"
        logger.info(f"✅ Send message test passed - ID: {session_id}")
    
    def test_planning_progress(self):
        """Test getting planning progress"""
        # Create a session first
        created_session = self.test_create_chat_session()
        session_id = created_session["session_id"]
        
        response = client.get(f"/api/v1/chat/sessions/{session_id}/progress")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert "current_stage" in data
        assert "progress_percentage" in data
        assert "context" in data
        logger.info(f"✅ Planning progress test passed - ID: {session_id}")
    
    # WebSocket Connection Tests
    def test_websocket_connection_info(self):
        """Test WebSocket connection information"""
        response = client.get("/api/v1/ws/connections")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_connections" in data
        assert "connections" in data
        assert "mission_subscribers" in data
        assert "drone_subscribers" in data
        logger.info("✅ WebSocket connection info test passed")
    
    def test_websocket_broadcast(self):
        """Test WebSocket broadcast functionality"""
        broadcast_data = {
            "message_type": "test_message",
            "data": {"test": "data", "timestamp": datetime.utcnow().isoformat()},
            "target_type": "notifications"
        }
        
        response = client.post("/api/v1/ws/broadcast", json=broadcast_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "recipients" in data
        logger.info("✅ WebSocket broadcast test passed")
    
    # Error Handling Tests
    def test_mission_not_found(self):
        """Test mission not found error"""
        response = client.get("/api/v1/missions/nonexistent_mission")
        assert response.status_code == 404
        logger.info("✅ Mission not found error test passed")
    
    def test_drone_not_found(self):
        """Test drone not found error"""
        response = client.get("/api/v1/drones/nonexistent_drone")
        assert response.status_code == 404
        logger.info("✅ Drone not found error test passed")
    
    def test_chat_session_not_found(self):
        """Test chat session not found error"""
        response = client.get("/api/v1/chat/sessions/nonexistent_session")
        assert response.status_code == 404
        logger.info("✅ Chat session not found error test passed")
    
    def test_invalid_mission_data(self):
        """Test invalid mission data"""
        invalid_data = {
            "name": "",  # Empty name
            "mission_type": "invalid_type",  # Invalid type
            "created_by": ""  # Empty creator
        }
        
        response = client.post("/api/v1/missions/", json=invalid_data)
        assert response.status_code == 422  # Validation error
        logger.info("✅ Invalid mission data error test passed")
    
    def test_duplicate_drone_registration(self):
        """Test duplicate drone registration"""
        # Register drone first time
        self.test_register_drone()
        
        # Try to register same drone again
        response = client.post("/api/v1/drones/register", json=self.test_drone_data)
        assert response.status_code == 400
        logger.info("✅ Duplicate drone registration error test passed")

def run_comprehensive_tests():
    """Run all API endpoint tests"""
    logger.info("🚀 Starting comprehensive API endpoint tests...")
    
    test_instance = TestAPIEndpoints()
    
    # Test categories
    test_methods = [
        # Basic endpoints
        ("Basic Endpoints", [
            test_instance.test_root_endpoint,
            test_instance.test_health_check,
            test_instance.test_api_info
        ]),
        
        # Mission API
        ("Mission API", [
            test_instance.test_create_mission,
            test_instance.test_list_missions,
            test_instance.test_get_mission,
            test_instance.test_update_mission,
            test_instance.test_mission_lifecycle
        ]),
        
        # Drone API
        ("Drone API", [
            test_instance.test_drone_discovery,
            test_instance.test_register_drone,
            test_instance.test_list_drones,
            test_instance.test_get_drone,
            test_instance.test_update_drone,
            test_instance.test_drone_telemetry,
            test_instance.test_drone_health_check,
            test_instance.test_drone_command
        ]),
        
        # Chat API
        ("Chat API", [
            test_instance.test_create_chat_session,
            test_instance.test_list_chat_sessions,
            test_instance.test_get_conversation,
            test_instance.test_send_message,
            test_instance.test_planning_progress
        ]),
        
        # WebSocket API
        ("WebSocket API", [
            test_instance.test_websocket_connection_info,
            test_instance.test_websocket_broadcast
        ]),
        
        # Error Handling
        ("Error Handling", [
            test_instance.test_mission_not_found,
            test_instance.test_drone_not_found,
            test_instance.test_chat_session_not_found,
            test_instance.test_invalid_mission_data,
            test_instance.test_duplicate_drone_registration
        ])
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category_name, tests in test_methods:
        logger.info(f"\n📋 Testing {category_name}:")
        for test_method in tests:
            total_tests += 1
            try:
                test_instance.setup_method()  # Reset for each test
                test_method()
                passed_tests += 1
            except Exception as e:
                failed_tests.append((test_method.__name__, str(e)))
                logger.error(f"❌ {test_method.__name__} failed: {str(e)}")
    
    # Print summary
    logger.info(f"\n📊 TEST SUMMARY:")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        logger.info(f"\n❌ Failed tests:")
        for test_name, error in failed_tests:
            logger.info(f"  - {test_name}: {error}")
    else:
        logger.info(f"\n🎉 All tests passed!")
    
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    return passed_tests, len(failed_tests), success_rate

if __name__ == "__main__":
    run_comprehensive_tests()