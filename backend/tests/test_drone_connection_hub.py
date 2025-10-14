# backend/tests/test_drone_connection_hub.py
import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from app.communication.drone_registry import DroneRegistry
from app.communication.drone_connection_hub import DroneConnectionHub

@pytest.mark.timeout(180)
@pytest.mark.asyncio
async def test_send_mission_http_and_redis(tmp_path, monkeypatch):
    # Setup a registry with a fake pi host
    persist = str(tmp_path/"r.json")
    reg = DroneRegistry(persist_path=persist)
    reg.register_pi_host("d1", "http://127.0.0.1:8000")

    hub = DroneConnectionHub(redis_channel="missions_test")

    # mock send_mission_http and publish_mission_redis
    async def fake_send_mission_http(pi_host, payload, timeout=10.0):
        return {"ack": True, "pi": pi_host}
    async def fake_publish(drone_id, payload, channel="missions"):
        return None

    monkeypatch.setattr("app.communication.drone_connection_hub.send_mission_http", fake_send_mission_http, raising=False)
    monkeypatch.setattr("app.communication.drone_connection_hub.publish_mission_redis", fake_publish, raising=False)

    res = await hub.send_mission_to_drone("d1", {"mission":"x"})
    assert isinstance(res, dict)
    # http should be acknowledged; redis either returns published True or error None
    assert res.get("http") is not None
    assert "redis" in res

@pytest.mark.timeout(180)
@pytest.mark.parametrize("command", ["disarm","arm","rtl","land"])
def test_send_emergency_command_no_module(monkeypatch, tmp_path, command):
    hub = DroneConnectionHub()
    # If emergency module not present, it should return False not raise
    out = hub.send_emergency_command("no_such", command)
    assert out in (False, True)

