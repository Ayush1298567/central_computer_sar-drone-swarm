# backend/tests/test_telemetry_receiver.py
import asyncio
import json
import pytest
import sys

from app.communication.telemetry_receiver import TelemetryReceiver


class FakePubSub:
    def __init__(self):
        self._messages = asyncio.Queue()
        self._subscribed = set()

    async def subscribe(self, channel):
        self._subscribed.add(channel)

    async def unsubscribe(self, channel):
        self._subscribed.discard(channel)

    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        try:
            return await asyncio.wait_for(self._messages.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self):
        pass

    async def inject(self, channel, data: dict):
        await self._messages.put({"type": "message", "channel": channel, "data": json.dumps(data).encode("utf-8")})


class FakeRedis:
    def __init__(self, host=None, port=None, db=None):
        self._pubsub = FakePubSub()

    def pubsub(self):
        return self._pubsub

    async def close(self):
        pass


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_telemetry_receiver_monkeypatched(monkeypatch):
    fake = FakeRedis()

    async def fake_constructor(**kwargs):
        return fake

    # use injectable client factory instead of monkeypatching module
    def factory(host=None, port=None, db=None):
        return fake

    recv = TelemetryReceiver(channel="tel_test", client_factory=factory)
    recv.start()

    # Inject a message
    await fake._pubsub.inject("tel_test", {"drone_id": "d1", "telemetry": {"battery": 77}})
    # Wait up to ~1s for async loop to process
    ok = False
    for _ in range(50):
        snap = recv.cache.snapshot()
        if snap.get("d1", {}).get("battery") == 77:
            ok = True
            break
        await asyncio.sleep(0.02)
    assert ok is True

    await recv.stop()


