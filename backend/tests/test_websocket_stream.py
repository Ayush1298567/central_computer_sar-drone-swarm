# backend/tests/test_websocket_stream.py
import pytest

from app.api.api_v1.websocket import handle_telemetry_request, manager
from app.communication.drone_registry import DroneRegistry


class DummyWebSocket:
    def __init__(self):
        self.sent = []
    async def send_text(self, text):
        self.sent.append(text)


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_websocket_telemetry_includes_status(monkeypatch, tmp_path):
    # Prepare registry entry
    reg = DroneRegistry(persist_path=str(tmp_path/"reg.json"))
    reg.register_pi_host("d1", "http://pi")
    reg.set_last_seen("d1")
    reg.set_mission_status("d1", "m1", "accepted")

    # Fake telemetry receiver snapshot
    class FakeRecv:
        def __init__(self):
            self.cache = type("C", (), {"snapshot": lambda self=None: {"d1": {"battery": 88}}})()
        def start(self):
            pass

    # Patch the provider used by handler
    monkeypatch.setattr("app.communication.telemetry_receiver.get_telemetry_receiver", lambda *a, **k: FakeRecv(), raising=True)

    # Capture send via manager
    ws = DummyWebSocket()
    cid = "conn-test"
    manager.active_connections[cid] = ws

    await handle_telemetry_request(cid, type("U", (), {"id":1, "username":"t"})())
    assert manager.active_connections[cid].sent, "No message sent"
    body = manager.active_connections[cid].sent[-1]
    # Expect a telemetry payload JSON containing our fields
    assert "\"drones\":" in body
    assert "status" in body or "mission_status" in body


