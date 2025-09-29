"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_sar_missions.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_drone_data():
    """Sample drone data for testing."""
    return {
        "drone_id": "test-drone-1",
        "name": "Test Drone 1",
        "battery_level": 85.0,
        "position_lat": 40.7128,
        "position_lng": -74.0060,
        "position_alt": 30.0
    }


class TestDroneEndpoints:
    """Test drone-related endpoints."""

    def test_get_drones_empty(self, client):
        """Test getting drones when none exist."""
        response = client.get("/api/v1/drones")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_drone(self, client, sample_drone_data):
        """Test creating a new drone."""
        response = client.post("/api/v1/drones", json=sample_drone_data)
        assert response.status_code == 200

        data = response.json()
        assert data["drone_id"] == sample_drone_data["drone_id"]
        assert data["name"] == sample_drone_data["name"]
        assert data["battery_level"] == sample_drone_data["battery_level"]

    def test_get_drones_with_data(self, client, sample_drone_data):
        """Test getting drones after creating one."""
        # Create a drone first
        client.post("/api/v1/drones", json=sample_drone_data)

        # Get all drones
        response = client.get("/api/v1/drones")
        assert response.status_code == 200

        drones = response.json()
        assert len(drones) == 1
        assert drones[0]["drone_id"] == sample_drone_data["drone_id"]

    def test_get_drone_by_id(self, client, sample_drone_data):
        """Test getting a specific drone by ID."""
        # Create a drone first
        create_response = client.post("/api/v1/drones", json=sample_drone_data)
        drone_id = create_response.json()["id"]

        # Get the drone by ID
        response = client.get(f"/api/v1/drones/{drone_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["drone_id"] == sample_drone_data["drone_id"]

    def test_get_drone_not_found(self, client):
        """Test getting a drone that doesn't exist."""
        response = client.get("/api/v1/drones/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Drone not found"

    def test_update_drone(self, client, sample_drone_data):
        """Test updating a drone."""
        # Create a drone first
        create_response = client.post("/api/v1/drones", json=sample_drone_data)
        drone_id = create_response.json()["id"]

        # Update the drone
        update_data = {"battery_level": 75.0, "name": "Updated Drone Name"}
        response = client.put(f"/api/v1/drones/{drone_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["battery_level"] == 75.0
        assert data["name"] == "Updated Drone Name"

    def test_delete_drone(self, client, sample_drone_data):
        """Test deleting a drone."""
        # Create a drone first
        create_response = client.post("/api/v1/drones", json=sample_drone_data)
        drone_id = create_response.json()["id"]

        # Delete the drone
        response = client.delete(f"/api/v1/drones/{drone_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Drone deleted successfully"

        # Verify it's deleted
        get_response = client.get(f"/api/v1/drones/{drone_id}")
        assert get_response.status_code == 404


class TestMissionEndpoints:
    """Test mission-related endpoints."""

    def test_get_missions_empty(self, client):
        """Test getting missions when none exist."""
        response = client.get("/api/v1/missions")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_mission(self, client):
        """Test creating a new mission."""
        mission_data = {
            "mission_id": "test-mission-1",
            "name": "Test Mission",
            "priority": "high",
            "search_area": {
                "coordinates": [[
                    [40.7128, -74.0060],
                    [40.7589, -74.0060],
                    [40.7589, -73.9851],
                    [40.7128, -73.9851],
                    [40.7128, -74.0060]
                ]],
                "altitude": 30.0,
                "pattern": "lawnmower"
            },
            "center_lat": 40.7128,
            "center_lng": -74.0060,
            "estimated_duration": 120
        }

        response = client.post("/api/v1/missions", json=mission_data)
        assert response.status_code == 200

        data = response.json()
        assert data["mission_id"] == mission_data["mission_id"]
        assert data["name"] == mission_data["name"]

    def test_start_mission(self, client):
        """Test starting a mission."""
        # Create a mission first
        mission_data = {
            "mission_id": "test-mission-2",
            "name": "Test Mission 2",
            "priority": "medium",
            "search_area": {
                "coordinates": [[
                    [40.7128, -74.0060],
                    [40.7589, -74.0060],
                    [40.7589, -73.9851],
                    [40.7128, -73.9851],
                    [40.7128, -74.0060]
                ]],
                "altitude": 30.0,
                "pattern": "lawnmower"
            },
            "center_lat": 40.7128,
            "center_lng": -74.0060,
            "estimated_duration": 120
        }

        create_response = client.post("/api/v1/missions", json=mission_data)
        mission_id = create_response.json()["id"]

        # Start the mission
        response = client.post(f"/api/v1/missions/{mission_id}/start")
        assert response.status_code == 200

        data = response.json()
        assert "commands" in data
        assert len(data["commands"]) > 0


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


if __name__ == "__main__":
    pytest.main([__file__])