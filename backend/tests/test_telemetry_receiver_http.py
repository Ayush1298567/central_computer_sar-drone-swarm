import json
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_http_telemetry_updates_cache(monkeypatch):
    # Stub heavy startup/shutdown tasks in lifespan
    async def ok_async(*args, **kwargs):
        return None

    async def ok_true(*args, **kwargs):
        return True

    monkeypatch.setattr("app.core.database.init_db", ok_async, raising=True)
    monkeypatch.setattr("app.core.database.close_db", ok_async, raising=True)
    monkeypatch.setattr("app.core.database.check_db_health", ok_true, raising=True)
    monkeypatch.setattr("app.communication.drone_connection_hub.drone_connection_hub.start", ok_true, raising=True)
    monkeypatch.setattr("app.communication.drone_connection_hub.drone_connection_hub.stop", ok_async, raising=True)
    monkeypatch.setattr("app.services.real_mission_execution.real_mission_execution_engine.start", ok_true, raising=True)
    monkeypatch.setattr("app.services.real_mission_execution.real_mission_execution_engine.stop", ok_async, raising=True)

    with TestClient(app) as client:
        body = {
            "drone_id": "drone-001",
            "telemetry": {"lat": 1.0, "lon": 2.0, "alt": 3.0, "battery": 95, "status": "flying"},
        }
        resp = client.post("/api/v1/telemetry", json=body)
        assert resp.status_code == 200

        from app.communication.telemetry_receiver import get_telemetry_receiver

        recv = get_telemetry_receiver()
        snap = recv.cache.snapshot()
        assert "drone-001" in snap
        rec = snap["drone-001"]
        assert rec["lat"] == 1.0 and rec["lon"] == 2.0 and rec["alt"] == 3.0
