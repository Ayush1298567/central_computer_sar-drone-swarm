# backend/tests/test_telemetry_registry_integration.py
import asyncio
import pytest

from app.communication.telemetry_receiver import TelemetryReceiver
from app.communication.drone_registry import DroneRegistry


class FakePubSub:
    def __init__(self):
        self._messages = asyncio.Queue()
    async def subscribe(self, channel):
        return None
    async def unsubscribe(self, channel):
        return None
    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        try:
            return await asyncio.wait_for(self._messages.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    async def close(self):
        pass
    async def inject(self, channel, data):
        import json
        await self._messages.put({"type": "message", "channel": channel, "data": json.dumps(data).encode("utf-8")})


class FakeRedis:
    def __init__(self):
        self._pubsub = FakePubSub()
    def pubsub(self):
        return self._pubsub
    async def close(self):
        pass


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_telemetry_updates_registry(tmp_path):
    # Isolated registry persistence
    reg = DroneRegistry(persist_path=str(tmp_path / "reg.json"))
    reg.register_pi_host("d1", "http://pi")

    fake = FakeRedis()

    def factory(host=None, port=None, db=None):
        return fake

    recv = TelemetryReceiver(channel="tel_test", client_factory=factory)
    recv.start()

    # Inject telemetry
    await fake._pubsub.inject("tel_test", {"drone_id": "d1", "telemetry": {"battery": 50}})

    # Await heartbeat write
    ok = False
    for _ in range(50):
        if reg.get_last_seen("d1"):
            ok = True
            break
        await asyncio.sleep(0.02)
    assert ok is True

    # Simulate staleness
    reg.set_last_seen("d1", "2000-01-01T00:00:00")
    await asyncio.sleep(0.05)
    await recv.stop()
    # Manually run offline check
    reg.mark_offline_if_stale(threshold_seconds=0.0)
    assert reg.get_status("d1") == "offline"


