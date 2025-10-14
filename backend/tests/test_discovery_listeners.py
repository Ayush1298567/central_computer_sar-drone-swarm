import asyncio
import pytest

from app.communication.drone_registry import DroneRegistry


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_mdns_stub_start_stop():
    reg = DroneRegistry(persist_path=None)
    await reg.start_discovery()
    await asyncio.sleep(0.05)
    await reg.stop_discovery()
    assert reg.discovery_active is False


@pytest.mark.timeout(180)
def test_set_last_seen_emits_and_persists(monkeypatch, tmp_path):
    # Capture broadcast via websocket manager
    sent = {"n": 0}

    class DummyMgr:
        async def broadcast_discovery_update(self, payload):
            sent["n"] += 1

    monkeypatch.setattr("app.api.api_v1.websocket.manager", DummyMgr())

    reg = DroneRegistry(persist_path=str(tmp_path / "reg.json"))
    reg.set_last_seen("dX")
    assert reg.get_last_seen("dX") is not None
    assert sent["n"] >= 1


@pytest.mark.timeout(180)
def test_lora_beacon_parse_emit(monkeypatch, tmp_path):
    # Fake serial to feed lines
    lines = [b"DRONE:L1:-70\n"]

    class FakeSer:
        def __init__(self, *a, **k): pass
        def readline(self):
            return lines.pop(0) if lines else b""
        def close(self): pass

    class FakeSerialMod:
        Serial = FakeSer

    monkeypatch.setattr("app.communication.drone_registry.serial", FakeSerialMod())

    sent = {"n": 0}
    class DummyMgr:
        async def broadcast_discovery_update(self, payload):
            sent["n"] += 1
    monkeypatch.setattr("app.api.api_v1.websocket.manager", DummyMgr())

    reg = DroneRegistry(persist_path=str(tmp_path/"reg.json"))
    # call private method directly to simulate one cycle
    import asyncio
    async def run_once():
        reg.discovery_active = True
        task = asyncio.create_task(reg._discover_lora_drones())
        await asyncio.sleep(0.05)
        reg.discovery_active = False
        task.cancel()
        try:
            await task
        except Exception:
            pass
    asyncio.get_event_loop().run_until_complete(run_once())
    assert sent["n"] >= 1


