import pytest
import asyncio
from datetime import datetime, timedelta

from app.ai.ai_monitor import ai_monitor
from app.api.api_v1.websocket import manager
from app.communication.drone_registry import drone_registry
from app.core.config import settings
from app.core.database import init_db


class _Capture:
    def __init__(self):
        self.messages = []

    async def broadcast_to_topic(self, message, topic):
        self.messages.append((topic, message))


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_ai_monitor_triggers_low_battery_and_stale(monkeypatch):
    await init_db()

    cap = _Capture()
    monkeypatch.setattr(manager, "broadcast_to_topic", cap.broadcast_to_topic, raising=True)

    # Arrange a drone entry with stale heartbeat and low battery and off-route
    drone_id = "test-drone-1"
    drone_registry.register_pi_host(drone_id, "http://pi")
    old = (datetime.utcnow() - timedelta(seconds=settings.COMMUNICATION_TIMEOUT + 5)).isoformat()
    drone_registry.set_last_seen(drone_id, old)
    # inject meta and position
    entry = drone_registry._store[drone_id]
    entry.setdefault("meta", {})["battery_level"] = settings.LOW_BATTERY_THRESHOLD - 5
    entry["position"] = {"lat": 10.0, "lon": 10.0}
    entry.setdefault("missions", {})["m1"] = {"status": "active", "updated_at": datetime.utcnow().isoformat()}
    entry["meta"]["planned_center"] = {"lat": 10.001, "lon": 10.001}

    # Act
    await ai_monitor._scan()

    # Assert decisions were broadcast
    topics = [t for (t, _m) in cap.messages]
    assert any(t == "ai_decisions" for t in topics), "No ai_decisions topic broadcast"
    payloads = [m["payload"] for (_t, m) in cap.messages if _t == "ai_decisions"]
    types = {p.get("type") for p in payloads}
    assert {"low_battery", "stale_heartbeat"}.issubset(types)
    # off_route may or may not trigger depending on haversine, allow optional
    for p in payloads:
        assert all(k in p for k in ("decision_id", "type", "reasoning", "confidence_score", "severity"))
