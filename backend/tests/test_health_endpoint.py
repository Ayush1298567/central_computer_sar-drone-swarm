import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.communication.drone_registry import get_registry


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


def test_health_endpoint_basic():
    app = build_app()
    client = TestClient(app)

    # Ensure at least one drone entry for counting
    reg = get_registry()
    reg.register_pi_host("health-drone", "http://pi")
    reg.set_status("health-drone", "online")

    r = client.get(f"{settings.API_V1_STR}/health")
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"status", "drones_online", "ai_enabled"}
    assert data["status"] in ("ok", "degraded")
    assert isinstance(data["drones_online"], int)
    assert isinstance(data["ai_enabled"], bool)
