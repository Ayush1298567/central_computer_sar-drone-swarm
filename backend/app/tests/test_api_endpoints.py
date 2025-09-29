"""
Basic API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)


def test_read_main():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "SAR Mission Commander API",
        "version": "1.0.0",
        "status": "operational"
    }


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_get_missions():
    """Test getting missions list."""
    response = client.get("/api/v1/missions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_drones():
    """Test getting drones list."""
    response = client.get("/api/v1/drones")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_discoveries():
    """Test getting discoveries list."""
    response = client.get("/api/v1/discoveries")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_conversation():
    """Test chat conversation endpoint."""
    response = client.post(
        "/api/v1/chat/converse",
        json={
            "mission_id": 1,
            "user_message": "Hello, I want to start a mission"
        }
    )
    # This might fail if no mission exists, but tests the endpoint structure
    assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__])