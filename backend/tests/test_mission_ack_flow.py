# backend/tests/test_mission_ack_flow.py
import pytest

from app.communication.drone_registry import DroneRegistry
from app.communication.drone_connection_hub import DroneConnectionHub


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_mission_ack_and_stale(tmp_path, monkeypatch):
    reg = DroneRegistry(persist_path=str(tmp_path / "reg.json"))
    reg.register_pi_host("d1", "http://pi")

    hub = DroneConnectionHub()

    async def fake_http(pi_host, payload, timeout=10.0):
        return {"status": "accepted", "mission_id": payload.get("mission_id", "m1")}

    # Patch through the module where it's looked up (globals or import)
    monkeypatch.setattr("app.communication.pi_communication.send_mission_http", fake_http)

    res = await hub.send_mission_to_drone("d1", {"mission_id": "m1"})
    assert res["http"]["status"] == "accepted"
    ms = hub.get_mission_status("d1")
    assert ms and ms["mission_id"] == "m1" and ms["status"] in ("accepted", "ack")

    # Mark stale via registry helper
    reg.mark_missions_stale(threshold_seconds=0.0)
    ms2 = hub.get_mission_status("d1")
    assert ms2 and ms2["status"] == "stale"


