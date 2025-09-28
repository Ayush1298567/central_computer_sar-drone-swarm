"""
End-to-end integration and system testing.
Tests complete mission planning workflow, WebSocket communication, AI integration, and database validation.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from ..core.database import SessionLocal, create_tables
from ..models.mission import Mission, DroneAssignment, ChatMessage
from ..models.drone import Drone, TelemetryData
from ..models.discovery import Discovery
from ..services.mission_planner import MissionPlanner
from ..services.area_calculator import AreaCalculator
from ..ai.ollama_client import OllamaClient


class TestCompleteMissionWorkflow:
    """Test complete mission lifecycle from planning to completion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.db = SessionLocal()

        # Create database tables
        create_tables()

        # Sample test data
        self.test_mission_data = {
            "name": "E2E Test Mission",
            "description": "Complete workflow integration test",
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

        self.test_drones = [
            {
                "id": "e2e_drone_001",
                "name": "E2E Test Drone Alpha",
                "model": "TestModel-X1",
                "status": "online",
                "battery_level": 90.0,
                "current_position": [40.7128, -74.0060, 10.0],
                "home_position": [40.7128, -74.0060, 0.0]
            },
            {
                "id": "e2e_drone_002",
                "name": "E2E Test Drone Beta",
                "model": "TestModel-X1",
                "status": "online",
                "battery_level": 85.0,
                "current_position": [40.7128, -74.0060, 10.0],
                "home_position": [40.7128, -74.0060, 0.0]
            }
        ]

    def teardown_method(self):
        """Clean up test data."""
        # Clean up test data from database
        self.db.query(Discovery).delete()
        self.db.query(TelemetryData).delete()
        self.db.query(DroneAssignment).delete()
        self.db.query(ChatMessage).delete()
        self.db.query(Drone).delete()
        self.db.query(Mission).delete()
        self.db.commit()
        self.db.close()

    def test_complete_mission_planning_to_execution_workflow(self):
        """Test complete mission planning to execution workflow."""
        # Phase 1: Mission Planning
        # 1.1 Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        assert mission_response.status_code == 200
        mission_id = mission_response.json()["mission"]["id"]

        # 1.2 Create drones
        drone_ids = []
        for drone_data in self.test_drones:
            drone_response = self.client.post("/api/drones/create", json=drone_data)
            assert drone_response.status_code == 200
            drone_ids.append(drone_response.json()["drone"]["id"])

        # 1.3 Conversational planning (mock AI interaction)
        chat_data = {
            "mission_id": mission_id,
            "sender": "user",
            "content": "Search the collapsed building for survivors",
            "message_type": "text"
        }
        chat_response = self.client.post("/api/chat/message", json=chat_data)
        assert chat_response.status_code == 200

        # 1.4 Get chat history to verify conversation
        history_response = self.client.get(f"/api/chat/history/{mission_id}")
        assert history_response.status_code == 200
        chat_history = history_response.json()["messages"]
        assert len(chat_history) >= 2  # User message + AI response

        # Phase 2: Mission Execution
        # 2.1 Start mission
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # 2.2 Update drone statuses to flying
        for drone_id in drone_ids:
            status_response = self.client.put(f"/api/drones/{drone_id}/status", json={
                "status": "flying",
                "current_position": [40.7150, -74.0030, 30.0]
            })
            assert status_response.status_code == 200

        # 2.3 Simulate telemetry updates
        for drone_id in drone_ids:
            telemetry_data = {
                "latitude": 40.7150,
                "longitude": -74.0030,
                "altitude": 30.0,
                "battery_percentage": 85.0,
                "flight_mode": "AUTO",
                "signal_strength": 95
            }
            telemetry_response = self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)
            assert telemetry_response.status_code == 200

        # Phase 3: Discovery and Investigation
        # 3.1 Simulate discovery
        discovery_data = {
            "object_type": "person",
            "confidence_score": 0.87,
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 30.0,
            "investigation_status": "pending"
        }
        discovery_response = self.client.post(f"/api/missions/{mission_id}/discoveries", json=discovery_data)
        assert discovery_response.status_code == 200
        discovery_id = discovery_response.json()["discovery"]["id"]

        # 3.2 Update discovery status
        update_response = self.client.put(f"/api/missions/{mission_id}/discoveries/{discovery_id}", json={
            "investigation_status": "investigating",
            "human_verified": True,
            "verification_notes": "Confirmed person requiring rescue"
        })
        assert update_response.status_code == 200

        # Phase 4: Mission Completion
        # 4.1 Update mission progress
        progress_response = self.client.put(f"/api/missions/{mission_id}/progress", json={
            "coverage_percentage": 95.0,
            "status": "completing"
        })
        assert progress_response.status_code == 200

        # 4.2 Complete mission
        complete_response = self.client.put(f"/api/missions/{mission_id}/complete")
        assert complete_response.status_code == 200

        # 4.3 Return drones to base
        for drone_id in drone_ids:
            return_response = self.client.put(f"/api/drones/{drone_id}/return")
            assert return_response.status_code == 200

        # Phase 5: Verification
        # 5.1 Verify mission completion
        final_mission_response = self.client.get(f"/api/missions/{mission_id}")
        assert final_mission_response.status_code == 200
        final_mission = final_mission_response.json()["mission"]
        assert final_mission["status"] == "completed"
        assert final_mission["coverage_percentage"] == 95.0

        # 5.2 Verify discovery was recorded
        discoveries_response = self.client.get(f"/api/missions/{mission_id}/discoveries")
        assert discoveries_response.status_code == 200
        discoveries = discoveries_response.json()["discoveries"]
        assert len(discoveries) == 1
        assert discoveries[0]["investigation_status"] == "investigating"

        # 5.3 Verify telemetry data was recorded
        for drone_id in drone_ids:
            telemetry_response = self.client.get(f"/api/drones/{drone_id}/telemetry")
            assert telemetry_response.status_code == 200
            telemetry_data = telemetry_response.json()["telemetry"]
            assert len(telemetry_data) > 0

    def test_multi_drone_coordination_workflow(self):
        """Test coordination of multiple drones in a single mission."""
        # Create mission with multiple drones
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Create 5 drones for multi-drone coordination
        drone_ids = []
        for i in range(5):
            drone_data = self.test_drones[0].copy()
            drone_data["id"] = f"multi_drone_{i+1:03d}"
            drone_data["name"] = f"Multi-Drone {i+1}"

            drone_response = self.client.post("/api/drones/create", json=drone_data)
            assert drone_response.status_code == 200
            drone_ids.append(drone_response.json()["drone"]["id"])

        # Start mission
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # Activate all drones
        for drone_id in drone_ids:
            status_response = self.client.put(f"/api/drones/{drone_id}/status", json={"status": "flying"})
            assert status_response.status_code == 200

        # Simulate coordinated search pattern
        search_positions = [
            [40.7150, -74.0030],
            [40.7170, -74.0010],
            [40.7190, -73.9990],
            [40.7210, -73.9970],
            [40.7230, -73.9950]
        ]

        for i, drone_id in enumerate(drone_ids):
            # Each drone searches different area
            position = search_positions[i % len(search_positions)]
            telemetry_data = {
                "latitude": position[0],
                "longitude": position[1],
                "altitude": 30.0,
                "battery_percentage": 80.0 - i * 2,  # Decreasing battery
                "flight_mode": "AUTO"
            }
            telemetry_response = self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)
            assert telemetry_response.status_code == 200

        # Verify all drones are active and positioned correctly
        drones_response = self.client.get("/api/drones/")
        assert drones_response.status_code == 200
        active_drones = drones_response.json()["drones"]
        flying_drones = [d for d in active_drones if d["status"] == "flying"]
        assert len(flying_drones) == 5

        # Complete mission successfully
        complete_response = self.client.put(f"/api/missions/{mission_id}/complete")
        assert complete_response.status_code == 200

    def test_emergency_scenario_handling(self):
        """Test emergency scenario handling and recovery."""
        # Create and start mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # Activate drone
        status_response = self.client.put(f"/api/drones/{drone_id}/status", json={"status": "flying"})
        assert status_response.status_code == 200

        # Simulate emergency situation
        emergency_data = {
            "emergency_type": "low_battery",
            "drone_id": drone_id,
            "severity": "critical",
            "description": "Battery level critically low - emergency return required"
        }
        emergency_response = self.client.post(f"/api/emergencies/report", json=emergency_data)
        assert emergency_response.status_code == 200

        # Emergency stop should be triggered
        emergency_stop_response = self.client.post(f"/api/emergencies/stop/{mission_id}")
        assert emergency_stop_response.status_code == 200

        # Verify mission and drone status after emergency
        mission_check = self.client.get(f"/api/missions/{mission_id}")
        assert mission_check.status_code == 200
        mission_status = mission_check.json()["mission"]["status"]
        assert mission_status in ["paused", "aborted", "emergency_stop"]

        drone_check = self.client.get(f"/api/drones/{drone_id}")
        assert drone_check.status_code == 200
        drone_status = drone_check.json()["drone"]["status"]
        assert drone_status == "returning"

    def test_ai_powered_mission_adaptation(self):
        """Test AI-powered mission adaptation based on real-time conditions."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # Start conversation for mission planning
        chat_messages = [
            "Search the collapsed building for survivors",
            "Focus on the eastern section which is more unstable",
            "Use lower altitude for better detail",
            "Set up continuous recording"
        ]

        for message in chat_messages:
            chat_data = {
                "mission_id": mission_id,
                "sender": "user",
                "content": message,
                "message_type": "text"
            }
            chat_response = self.client.post("/api/chat/message", json=chat_data)
            assert chat_response.status_code == 200

        # Start mission with adapted parameters
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # Activate drone with adapted parameters
        adapted_position = [40.7150, -74.0030, 20.0]  # Lower altitude as requested
        status_response = self.client.put(f"/api/drones/{drone_id}/status", json={
            "status": "flying",
            "current_position": adapted_position
        })
        assert status_response.status_code == 200

        # Simulate environmental condition changes
        weather_update = {
            "wind_speed": 12.0,  # Windy conditions
            "visibility": 5000,  # Reduced visibility
            "temperature": 5.0   # Cold temperature
        }

        # AI should adapt mission based on conditions
        adaptation_response = self.client.post(f"/api/missions/{mission_id}/adapt", json={
            "environmental_conditions": weather_update,
            "adaptation_reason": "Weather conditions require adjustment"
        })
        assert adaptation_response.status_code == 200

        # Verify mission was adapted
        adapted_mission = self.client.get(f"/api/missions/{mission_id}")
        assert adapted_mission.status_code == 200
        mission_data = adapted_mission.json()["mission"]
        assert "adapted_at" in mission_data

    def test_database_persistence_and_consistency(self):
        """Test database persistence and data consistency across operations."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # Start mission and add telemetry
        self.client.put(f"/api/missions/{mission_id}/start")

        telemetry_data = {
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 30.0,
            "battery_percentage": 85.0
        }
        self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)

        # Create discovery
        discovery_data = {
            "object_type": "person",
            "confidence_score": 0.90,
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 30.0
        }
        discovery_response = self.client.post(f"/api/missions/{mission_id}/discoveries", json=discovery_data)
        discovery_id = discovery_response.json()["discovery"]["id"]

        # Verify database persistence by checking raw database
        db_mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        assert db_mission is not None
        assert db_mission.name == self.test_mission_data["name"]
        assert db_mission.status == "active"

        db_drone = self.db.query(Drone).filter(Drone.id == drone_id).first()
        assert db_drone is not None
        assert db_drone.status == "flying"

        db_telemetry = self.db.query(TelemetryData).filter(TelemetryData.drone_id == drone_id).first()
        assert db_telemetry is not None
        assert db_telemetry.latitude == 40.7150

        db_discovery = self.db.query(Discovery).filter(Discovery.id == discovery_id).first()
        assert db_discovery is not None
        assert db_discovery.object_type == "person"
        assert db_discovery.confidence_score == 0.90

        # Test data consistency - all related records should exist
        assert db_mission.drone_assignments is not None
        assert len(db_mission.discoveries) == 1

    def test_system_performance_under_load(self):
        """Test system performance with multiple concurrent operations."""
        import threading
        import time

        mission_ids = []
        drone_ids = []
        results = []

        def create_mission_with_drones(mission_index):
            try:
                # Create mission
                mission_data = self.test_mission_data.copy()
                mission_data["name"] = f"Load Test Mission {mission_index}"

                mission_response = self.client.post("/api/missions/create", json=mission_data)
                if mission_response.status_code != 200:
                    results.append(f"Mission {mission_index}: Failed to create")
                    return

                mission_id = mission_response.json()["mission"]["id"]
                mission_ids.append(mission_id)

                # Create drone
                drone_data = self.test_drones[0].copy()
                drone_data["id"] = f"load_drone_{mission_index:03d}"

                drone_response = self.client.post("/api/drones/create", json=drone_data)
                if drone_response.status_code != 200:
                    results.append(f"Mission {mission_index}: Failed to create drone")
                    return

                drone_id = drone_response.json()["drone"]["id"]
                drone_ids.append(drone_id)

                # Start mission
                start_response = self.client.put(f"/api/missions/{mission_id}/start")
                if start_response.status_code != 200:
                    results.append(f"Mission {mission_index}: Failed to start")
                    return

                # Add telemetry
                telemetry_data = {
                    "latitude": 40.7128 + mission_index * 0.001,
                    "longitude": -74.0060 + mission_index * 0.001,
                    "altitude": 30.0,
                    "battery_percentage": 90.0 - mission_index * 2
                }
                telemetry_response = self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)
                if telemetry_response.status_code != 200:
                    results.append(f"Mission {mission_index}: Failed to add telemetry")
                    return

                results.append(f"Mission {mission_index}: Success")

            except Exception as e:
                results.append(f"Mission {mission_index}: Error - {str(e)}")

        # Create 20 concurrent missions
        threads = []
        start_time = time.time()

        for i in range(20):
            thread = threading.Thread(target=create_mission_with_drones, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify results
        successful_operations = [r for r in results if "Success" in r]
        assert len(successful_operations) >= 15  # At least 75% success rate

        # Should complete within reasonable time
        assert execution_time < 30  # 30 seconds for 20 operations

        # Verify database integrity
        assert len(mission_ids) >= 15
        assert len(drone_ids) >= 15

        # Clean up
        for mission_id in mission_ids:
            try:
                self.client.delete(f"/api/missions/{mission_id}")
            except:
                pass  # Ignore cleanup errors


class TestWebSocketRealTimeIntegration:
    """Test WebSocket real-time communication integration."""

    def setup_method(self):
        """Set up WebSocket integration test fixtures."""
        self.client = TestClient(app)

    def test_real_time_mission_updates(self):
        """Test real-time mission status updates via WebSocket."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # In real implementation, this would test actual WebSocket connections
        # For now, test that the supporting API endpoints work

        # Start mission
        start_response = self.client.put(f"/api/missions/{mission_id}/start")
        assert start_response.status_code == 200

        # Update mission progress
        progress_response = self.client.put(f"/api/missions/{mission_id}/progress", json={
            "coverage_percentage": 25.0,
            "current_area": [[40.7128, -74.0060], [40.7150, -74.0060], [40.7150, -74.0030]]
        })
        assert progress_response.status_code == 200

        # Verify progress was recorded
        mission_check = self.client.get(f"/api/missions/{mission_id}")
        assert mission_check.status_code == 200
        mission_data = mission_check.json()["mission"]
        assert mission_data["coverage_percentage"] == 25.0

    def test_real_time_drone_tracking(self):
        """Test real-time drone position tracking."""
        # Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # Simulate real-time position updates
        positions = [
            [40.7128, -74.0060, 10.0],
            [40.7135, -74.0055, 15.0],
            [40.7142, -74.0050, 20.0],
            [40.7149, -74.0045, 25.0],
            [40.7156, -74.0040, 30.0]
        ]

        for position in positions:
            telemetry_data = {
                "latitude": position[0],
                "longitude": position[1],
                "altitude": position[2],
                "battery_percentage": 85.0,
                "flight_mode": "AUTO"
            }

            telemetry_response = self.client.post(f"/api/drones/{drone_id}/telemetry", json=telemetry_data)
            assert telemetry_response.status_code == 200

        # Verify all position updates were recorded
        telemetry_response = self.client.get(f"/api/drones/{drone_id}/telemetry")
        assert telemetry_response.status_code == 200
        telemetry_records = telemetry_response.json()["telemetry"]
        assert len(telemetry_records) == len(positions)

        # Verify position progression
        for i, record in enumerate(telemetry_records):
            expected_position = positions[i]
            assert abs(record["latitude"] - expected_position[0]) < 0.001
            assert abs(record["longitude"] - expected_position[1]) < 0.001
            assert record["altitude"] == expected_position[2]

    def test_real_time_discovery_notifications(self):
        """Test real-time discovery notifications."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Create drone
        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # Simulate discovery
        discovery_data = {
            "object_type": "person",
            "confidence_score": 0.92,
            "latitude": 40.7150,
            "longitude": -74.0030,
            "altitude": 25.0,
            "detection_method": "visual",
            "environmental_conditions": {
                "lighting": "good",
                "weather": "clear"
            }
        }

        discovery_response = self.client.post(f"/api/missions/{mission_id}/discoveries", json=discovery_data)
        assert discovery_response.status_code == 200
        discovery_id = discovery_response.json()["discovery"]["id"]

        # Verify discovery was recorded with all details
        discovery_check = self.client.get(f"/api/missions/{mission_id}/discoveries/{discovery_id}")
        assert discovery_check.status_code == 200
        discovery_details = discovery_check.json()["discovery"]
        assert discovery_details["object_type"] == "person"
        assert discovery_details["confidence_score"] == 0.92
        assert discovery_details["detection_method"] == "visual"
        assert "environmental_conditions" in discovery_details


class TestAIIntegrationWorkflow:
    """Test AI integration in complete workflows."""

    def setup_method(self):
        """Set up AI integration test fixtures."""
        self.client = TestClient(app)

        # Mock AI client for testing
        self.mock_ai_client = Mock()
        self.mock_ai_client.health_check = AsyncMock(return_value=True)
        self.mock_ai_client.generate_response = AsyncMock(return_value={
            "success": True,
            "response": "AI analysis complete",
            "confidence": 0.85
        })

    @patch('app.main.app.state.ai_client')
    def test_ai_powered_mission_analysis(self, mock_app_state):
        """Test AI-powered mission analysis and recommendations."""
        mock_app_state = self.mock_ai_client

        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Request AI analysis
        analysis_request = {
            "analysis_type": "search_pattern_optimization",
            "mission_context": {
                "search_area": self.test_mission_data["search_area"],
                "search_target": self.test_mission_data["search_target"],
                "environmental_conditions": {
                    "wind_speed": 5.0,
                    "visibility": 10000
                }
            }
        }

        analysis_response = self.client.post(f"/api/ai/analyze/{mission_id}", json=analysis_request)
        assert analysis_response.status_code == 200

        analysis_result = analysis_response.json()
        assert analysis_result["success"] is True
        assert "recommendations" in analysis_result
        assert "confidence" in analysis_result

    @patch('app.main.app.state.ai_client')
    def test_ai_conversational_planning(self, mock_app_state):
        """Test AI conversational mission planning."""
        mock_app_state = self.mock_ai_client

        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Conversational planning session
        conversation_flow = [
            {
                "message": "I need to search a collapsed building for survivors",
                "expected_response_contains": "search area"
            },
            {
                "message": "The building is located at these coordinates",
                "expected_response_contains": "altitude"
            },
            {
                "message": "Use 25 meters altitude and search thoroughly",
                "expected_response_contains": "drone assignment"
            }
        ]

        for step in conversation_flow:
            chat_data = {
                "mission_id": mission_id,
                "sender": "user",
                "content": step["message"],
                "message_type": "text"
            }

            chat_response = self.client.post("/api/chat/message", json=chat_data)
            assert chat_response.status_code == 200

            response_content = chat_response.json()["response"]
            assert step["expected_response_contains"].lower() in response_content.lower()

        # Verify final mission plan
        final_mission = self.client.get(f"/api/missions/{mission_id}")
        assert final_mission.status_code == 200
        mission_data = final_mission.json()["mission"]
        assert mission_data["search_altitude"] == 25.0
        assert mission_data["search_speed"] == "thorough"

    def test_ai_learning_and_adaptation(self):
        """Test AI learning from mission outcomes."""
        # Create multiple missions to simulate learning data
        mission_responses = []
        for i in range(3):
            mission_data = self.test_mission_data.copy()
            mission_data["name"] = f"Learning Mission {i+1}"

            response = self.client.post("/api/missions/create", json=mission_data)
            mission_responses.append(response)
            assert response.status_code == 200

        # Complete missions with different outcomes
        outcomes = [
            {"coverage_percentage": 95.0, "discoveries": 2, "duration": 45},
            {"coverage_percentage": 78.0, "discoveries": 1, "duration": 52},
            {"coverage_percentage": 88.0, "discoveries": 0, "duration": 38}
        ]

        for i, response in enumerate(mission_responses):
            mission_id = response.json()["mission"]["id"]
            outcome = outcomes[i]

            # Complete mission with outcome data
            complete_response = self.client.put(f"/api/missions/{mission_id}/complete", json=outcome)
            assert complete_response.status_code == 200

        # Request AI learning analysis
        learning_response = self.client.post("/api/ai/learning/analyze", json={
            "analysis_type": "performance_patterns",
            "mission_outcomes": outcomes
        })

        # Should provide learning insights
        assert learning_response.status_code == 200
        learning_data = learning_response.json()
        assert "patterns" in learning_data
        assert "recommendations" in learning_data


class TestSystemStressAndReliability:
    """Test system stress and reliability under various conditions."""

    def setup_method(self):
        """Set up stress test fixtures."""
        self.client = TestClient(app)

    def test_high_concurrency_operations(self):
        """Test system under high concurrency load."""
        import concurrent.futures
        import time

        def perform_operation(operation_id):
            try:
                # Create mission
                mission_data = self.test_mission_data.copy()
                mission_data["name"] = f"Concurrency Test {operation_id}"

                response = self.client.post("/api/missions/create", json=mission_data)
                return response.status_code == 200
            except Exception:
                return False

        # Execute 50 concurrent operations
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_operation, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify results
        successful_operations = sum(results)
        assert successful_operations >= 40  # At least 80% success rate

        # Should complete within reasonable time
        assert execution_time < 20  # 20 seconds for 50 operations

    def test_memory_usage_under_sustained_load(self):
        """Test memory usage during sustained high load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create sustained load
        mission_ids = []
        for i in range(100):
            mission_data = self.test_mission_data.copy()
            mission_data["name"] = f"Memory Test {i}"

            response = self.client.post("/api/missions/create", json=mission_data)
            if response.status_code == 200:
                mission_ids.append(response.json()["mission"]["id"])

        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 100 missions)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB"

        # Clean up
        for mission_id in mission_ids:
            try:
                self.client.delete(f"/api/missions/{mission_id}")
            except:
                pass

    def test_database_transaction_integrity(self):
        """Test database transaction integrity during complex operations."""
        # Create mission with multiple related operations
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # Perform multiple operations in sequence
        operations = [
            lambda: self.client.put(f"/api/missions/{mission_id}/start"),
            lambda: self.client.put(f"/api/drones/{drone_id}/status", json={"status": "flying"}),
            lambda: self.client.post(f"/api/drones/{drone_id}/telemetry", json={
                "latitude": 40.7150, "longitude": -74.0030, "altitude": 30.0
            }),
            lambda: self.client.post(f"/api/missions/{mission_id}/discoveries", json={
                "object_type": "person", "confidence_score": 0.85,
                "latitude": 40.7150, "longitude": -74.0030, "altitude": 30.0
            })
        ]

        # Execute all operations
        for operation in operations:
            response = operation()
            assert response.status_code == 200

        # Verify all data is consistent
        mission_check = self.client.get(f"/api/missions/{mission_id}")
        assert mission_check.status_code == 200

        drone_check = self.client.get(f"/api/drones/{drone_id}")
        assert drone_check.status_code == 200

        discoveries_check = self.client.get(f"/api/missions/{mission_id}/discoveries")
        assert discoveries_check.status_code == 200
        discoveries = discoveries_check.json()["discoveries"]
        assert len(discoveries) == 1

    def test_system_recovery_from_failures(self):
        """Test system recovery from various failure scenarios."""
        # Create mission
        mission_response = self.client.post("/api/missions/create", json=self.test_mission_data)
        mission_id = mission_response.json()["mission"]["id"]

        # Simulate various failure scenarios and recovery

        # 1. Network interruption recovery
        # (In real test, would interrupt network connection)

        # 2. Database connection recovery
        # (Would test database reconnection)

        # 3. Service restart recovery
        # Create data before "restart"
        drone_response = self.client.post("/api/drones/create", json=self.test_drones[0])
        drone_id = drone_response.json()["drone"]["id"]

        # "Restart" by recreating client
        new_client = TestClient(app)

        # Verify data persists after "restart"
        mission_check = new_client.get(f"/api/missions/{mission_id}")
        assert mission_check.status_code == 200

        drone_check = new_client.get(f"/api/drones/{drone_id}")
        assert drone_check.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])