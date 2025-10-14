# backend/tests/test_real_mission_execution.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.services.real_mission_execution import RealMissionExecutionEngine
from app.communication.drone_registry import DroneRegistry

@pytest.mark.timeout(180)
@pytest.mark.asyncio
async def test_assign_mission_to_drones(tmp_path, monkeypatch):
    # Setup registry with two drones
    persist = str(tmp_path/"r.json")
    reg = DroneRegistry(persist_path=persist)
    reg.register_pi_host("d1", "http://127.0.0.1:8000")
    reg.register_pi_host("d2", "http://127.0.0.2:8000")

    engine = RealMissionExecutionEngine()

    # monkeypatch hub send_mission_to_drone
    async def fake_send(drone_id, payload, use_http=True, use_redis=True, timeout=10.0):
        return {"sent_to": drone_id}

    class FakeHub:
        async def send_mission_to_drone(self, drone_id, payload, use_http=True, use_redis=True, timeout=10.0):
            return await fake_send(drone_id, payload, use_http, use_redis, timeout)

    monkeypatch.setattr("app.services.real_mission_execution.get_hub", lambda singleton=True: FakeHub())

    res = await engine.assign_mission_to_drones("m1", ["d1","d2"], {"mission":"x"})
    assert "d1" in res and "d2" in res
    assert res["d1"]["ok"] is True

