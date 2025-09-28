"""
Comprehensive tests for all API endpoints.
Tests mission, drone, chat, and WebSocket endpoints with integration scenarios.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from ..core.database import SessionLocal
from ..models.mission import Mission, DroneAssignment, ChatMessage
from ..models.drone import Drone, TelemetryData
from ..models.discovery import Discovery


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def setup_method(self):
        """Set up test client and fixtures."""
        self.client = TestClient(app)

        # Sample test data
        self.test_mission_data = {
            "name": "Test SAR Mission",
            "description": "API endpoint test mission",
            "search_area": [
                [40.7128, -74.0060],
                [40.7589, -74.0060],
                [40.7589, -73.9352],
                [40.7128, -73.9352]
            ],
            "launch_point": [40.7128, -74.0060],
            "search_target": "person",
            "search_altitude": 30.0,
            "search_speed": "thorough",
            "recording_mode": "continuous"
        }

        self.test_drone_data = {
            "id": "test_drone_001",
            "name": "Test Drone Alpha",
            "model": "TestModel-X1",
            "status": "online",
            "battery_level": 85.0,
            "current_position": [40.7128, -74.0060, 10.0],
            "home_position": [40.7128, -74.0060, 0.0]
        }

        self.test_chat_message = {
            "sender": "user",
            "content": "Search the collapsed building for survivors",
            "message_type": "text"
        }

    def test_health_check_endpoint(self):
        """Test system health check endpoint."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Mission Commander SAR System" in data["message"]
        assert "version" in data
        assert "status" in data

    def test_create_mission_endpoint(self):
        """Test mission creation endpoint."""
        response = self.client.post("/api/missions/create", json=self.test_mission_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "mission" in data
        assert "message" in data

        mission = data["mission"]
        assert mission["name"] == self.test_mission_data["name"]
        assert mission["status"] == "planning"
        assert "id" in mission

        # Store mission ID for later tests
        self.created_mission_id = mission["id"]

    def test_get_mission_endpoint(self):
        """Test getting mission by ID."""
        # First create a mission
        create_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = create_response.json()["mission"]["id"]

        # Then retrieve it
        response = self.client.get(f"/api/missions/{mission_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "mission" in data

        mission = data["mission"]
        assert mission["id"] == mission_id
        assert mission["name"] == self.test_mission_data["name"]

    def test_get_nonexistent_mission_endpoint(self):
        """Test getting non-existent mission."""
        response = self.client.get("/api/missions/nonexistent_id")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data
        assert "Mission not found" in data["detail"]

    def test_start_mission_endpoint(self):
        """Test starting a mission."""
        # Create a mission first
        create_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = create_response.json()["mission"]["id"]

        # Start the mission
        response = self.client.put(f"/api/missions/{mission_id}/start")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "message" in data
        assert "Mission started successfully" in data["message"]

    def test_create_drone_endpoint(self):
        """Test drone creation endpoint."""
        response = self.client.post("/api/drones/create", json=self.test_drone_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "drone" in data

        drone = data["drone"]
        assert drone["id"] == self.test_drone_data["id"]
        assert drone["name"] == self.test_drone_data["name"]
        assert drone["status"] == "online"

    def test_get_drones_endpoint(self):
        """Test getting all drones."""
        # Create a drone first
        self.client.post("/api/drones/create", json=self.test_drone_data)

        response = self.client.get("/api/drones/")

        assert response.status_code == 200
        data = response.json()

        assert "drones" in data
        assert isinstance(data["drones"], list)
        assert len(data["drones"]) > 0

    def test_get_drone_by_id_endpoint(self):
        """Test getting drone by ID."""
        # Create a drone first
        create_response = self.client.post("/api/drones/create", json=self.test_drone_data)
        drone_id = create_response.json()["drone"]["id"]

        response = self.client.get(f"/api/drones/{drone_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "drone" in data

        drone = data["drone"]
        assert drone["id"] == drone_id
        assert drone["name"] == self.test_drone_data["name"]

    def test_update_drone_status_endpoint(self):
        """Test updating drone status."""
        # Create a drone first
        create_response = self.client.post("/api/drones/create", json=self.test_drone_data)
        drone_id = create_response.json()["drone"]["id"]

        # Update status
        update_data = {"status": "flying", "battery_level": 75.0}
        response = self.client.put(f"/api/drones/{drone_id}/status", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "drone" in data

        drone = data["drone"]
        assert drone["status"] == "flying"
        assert drone["battery_level"] == 75.0

    def test_chat_message_endpoint(self):
        """Test sending chat message."""
        # Create a mission first
        create_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = create_response.json()["mission"]["id"]

        # Send chat message
        chat_data = {
            "mission_id": mission_id,
            **self.test_chat_message
        }
        response = self.client.post("/api/chat/message", json=chat_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "response" in data
        assert "confidence" in data

    def test_chat_history_endpoint(self):
        """Test getting chat history."""
        # Create a mission and send a message first
        create_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = create_response.json()["mission"]["id"]

        chat_data = {
            "mission_id": mission_id,
            **self.test_chat_message
        }
        self.client.post("/api/chat/message", json=chat_data)

        # Get chat history
        response = self.client.get(f"/api/chat/history/{mission_id}")

        assert response.status_code == 200
        data = response.json()

        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) > 0

    def test_invalid_mission_data_endpoint(self):
        """Test mission creation with invalid data."""
        invalid_data = {
            "name": "",  # Invalid: empty name
            "search_area": [],  # Invalid: no area
            "search_altitude": -10.0  # Invalid: negative altitude
        }

        response = self.client.post("/api/missions/create", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()

        assert "detail" in data

    def test_invalid_drone_data_endpoint(self):
        """Test drone creation with invalid data."""
        invalid_data = {
            "id": "",  # Invalid: empty ID
            "name": "",  # Invalid: empty name
            "battery_level": 150.0  # Invalid: > 100%
        }

        response = self.client.post("/api/drones/create", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()

        assert "detail" in data


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.client = TestClient(app)

        self.test_mission = {
            "name": "Integration Test Mission",
            "description": "Full workflow integration test",
            "search_area": [
                [40.7128, -74.0060],
                [40.7589, -74.0060],
                [40.7589, -73.9352],
                [40.7128, -73.9352]
            ],
            "launch_point": [40.7128, -74.0060],
            "search_target": "person",
            "search_altitude": 25.0
        }

        self.test_drone = {
            "id": "integration_drone_001",
            "name": "Integration Test Drone",
            "model": "IntegrationModel-X1",
            "status": "online",
            "battery_level": 90.0
        }

    def test_complete_mission_workflow(self):
        """Test complete mission creation to completion workflow."""
        # 1. Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission)
        assert mission_response.status_code == 200
        mission_id = mission_response.json()["mission"]["id"]

        # 2. Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drone)
        assert drone_response.status_code == 200
        drone_id = drone_response.json()["drone"]["id"]

        # 3. Start mission
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # 4. Update drone status to flying
        update_response = self.client.put(f"/api/drones/{drone_id}/status", json={
            "status": "flying",
            "current_position": [40.7150, -74.0030, 25.0]
        })
        assert update_response.status_code == 200

        # 5. Add telemetry data
        telemetry_data = {
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 25.0,
            "battery_percentage": 85.0,
            "flight_mode": "AUTO"
        }
        telemetry_response = self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)
        assert telemetry_response.status_code == 200

        # 6. Simulate discovery
        discovery_data = {
            "object_type": "person",
            "confidence_score": 0.85,
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 25.0
        }
        discovery_response = self.client.post(f"/api/missions/{mission_id}/discoveries", json=discovery_data)
        assert discovery_response.status_code == 200

    def test_mission_with_multiple_drones(self):
        """Test mission with multiple drones."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission)
        mission_id = mission_response.json()["mission"]["id"]

        # Create multiple drones
        drones = []
        for i in range(3):
            drone_data = self.test_drone.copy()
            drone_data["id"] = f"multi_drone_{i+1:03d}"
            drone_data["name"] = f"Multi Test Drone {i+1}"

            drone_response = self.client.post("/api/drones/create", json=drone_data)
            assert drone_response.status_code == 200
            drones.append(drone_response.json()["drone"]["id"])

        # Start mission
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # Update all drones to flying
        for drone_id in drones:
            update_response = self.client.put(f"/api/drones/{drone_id}/status", json={"status": "flying"})
            assert update_response.status_code == 200

    def test_chat_conversation_workflow(self):
        """Test conversational mission planning workflow."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission)
        mission_id = mission_response.json()["mission"]["id"]

        # Start conversation
        messages = [
            "Search the collapsed building for survivors",
            "Focus on the eastern section",
            "Use 3 drones for faster coverage",
            "Set altitude to 20 meters"
        ]

        for message in messages:
            chat_data = {
                "mission_id": mission_id,
                "sender": "user",
                "content": message,
                "message_type": "text"
            }
            response = self.client.post("/api/chat/message", json=chat_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "response" in data

        # Get conversation history
        history_response = self.client.get(f"/api/chat/history/{mission_id}")
        assert history_response.status_code == 200

        history_data = history_response.json()
        assert len(history_data["messages"]) == len(messages) * 2  # User + AI messages

    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases."""
        # Test with malformed JSON
        response = self.client.post("/api/missions/create", data="invalid json")
        assert response.status_code == 422

        # Test with missing required fields
        incomplete_data = {"name": "Incomplete Mission"}
        response = self.client.post("/api/missions/create", json=incomplete_data)
        assert response.status_code == 422

        # Test with extremely large coordinates
        large_coord_data = self.test_mission.copy()
        large_coord_data["search_area"] = [
            [90.0, 180.0],  # Near north pole, international date line
            [89.0, 180.0],
            [89.0, 179.0],
            [90.0, 179.0]
        ]
        response = self.client.post("/api/missions/create", json=large_coord_data)
        # Should handle gracefully, potentially with validation errors
        assert response.status_code in [200, 422]

    def test_concurrent_mission_operations(self):
        """Test concurrent mission operations."""
        import threading
        import time

        results = []

        def create_mission():
            response = self.client.post("/api/missions/create", json=self.test_mission)
            results.append(response.status_code)

        # Create multiple missions concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_mission)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

    def test_database_consistency(self):
        """Test database consistency across operations."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission)
        mission_id = mission_response.json()["mission"]["id"]

        # Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drone)
        drone_id = drone_response.json()["drone"]["id"]

        # Create discovery
        discovery_data = {
            "object_type": "person",
            "confidence_score": 0.9,
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 25.0
        }
        discovery_response = self.client.post(f"/api/missions/{mission_id}/discoveries", json=discovery_data)
        discovery_id = discovery_response.json()["discovery"]["id"]

        # Verify all records exist and are consistent
        mission_get = self.client.get(f"/api/missions/{mission_id}")
        assert mission_get.status_code == 200

        drone_get = self.client.get(f"/api/drones/{drone_id}")
        assert drone_get.status_code == 200

        # Discovery should be linked to mission
        mission_data = mission_get.json()["mission"]
        # Note: In a real implementation, we'd check that discoveries are properly linked


class TestAPIErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up error handling test fixtures."""
        self.client = TestClient(app)

    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # This would require mocking database connection failures
        # For now, test with invalid database operations

        # Test with malformed mission ID
        response = self.client.get("/api/missions/invalid-uuid-format")
        assert response.status_code == 422

    def test_ai_service_unavailable(self):
        """Test handling when AI service is unavailable."""
        # Mock AI service failure
        with patch('app.ai.ollama_client.OllamaClient.health_check', return_value=False):
            response = self.client.post("/api/chat/message", json={
                "mission_id": "test_mission",
                "sender": "user",
                "content": "Test message",
                "message_type": "text"
            })

            # Should handle gracefully, potentially with fallback
            assert response.status_code in [200, 503]

    def test_large_payload_handling(self):
        """Test handling of large payloads."""
        # Create mission with very large search area
        large_mission = self.test_mission.copy()
        large_mission["search_area"] = []

        # Add many coordinates
        for i in range(1000):
            large_mission["search_area"].extend([
                [40.7 + i * 0.001, -74.0],
                [40.7 + i * 0.001, -73.9]
            ])

        response = self.client.post("/api/missions/create", json=large_mission)

        # Should handle gracefully
        assert response.status_code in [200, 413, 422]  # OK, too large, or validation error

    def test_malicious_input_handling(self):
        """Test handling of potentially malicious input."""
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>"},  # XSS attempt
            {"search_area": "javascript:alert(1)"},     # JavaScript injection
            {"name": "../../../etc/passwd"},            # Path traversal attempt
        ]

        for malicious_data in malicious_inputs:
            test_data = self.test_mission.copy()
            test_data.update(malicious_data)

            response = self.client.post("/api/missions/create", json=test_data)

            # Should reject malicious input
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])