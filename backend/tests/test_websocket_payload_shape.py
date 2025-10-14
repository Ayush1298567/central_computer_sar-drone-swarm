import json
import pytest

from app.api.api_v1.websocket import manager, broadcast_telemetry_snapshot_once


class DummyWebSocket:
    def __init__(self):
        self.sent = []
    async def send_text(self, text):
        self.sent.append(text)


@pytest.mark.asyncio
async def test_websocket_payload_shape(monkeypatch):
    class FakeCache:
        async def get_all(self):
            return {
                "drone-001": {
                    "id": "drone-001",
                    "lat": 1.23,
                    "lon": 4.56,
                    "alt": 7.89,
                    "battery": 88.0,
                    "status": "flying",
                    "last_seen": "2024-01-01T00:00:00",
                }
            }

    class FakeRecv:
        def __init__(self):
            self.cache = FakeCache()
        def start(self):
            pass

    monkeypatch.setattr(
        "app.communication.telemetry_receiver.get_telemetry_receiver",
        lambda *a, **k: FakeRecv(),
        raising=True,
    )

    ws = DummyWebSocket()
    cid = "conn-test"
    manager.active_connections[cid] = ws
    manager.subscriptions[cid] = {"telemetry"}

    await broadcast_telemetry_snapshot_once()

    assert ws.sent, "No message was sent to client"
    payload = json.loads(ws.sent[-1])
    assert payload.get("type") == "telemetry"
    drones = payload.get("payload", {}).get("drones")
    assert isinstance(drones, list) and len(drones) == 1
    drone = drones[0]
    for key in ["id", "lat", "lon", "alt", "battery", "status", "last_seen"]:
        assert key in drone

