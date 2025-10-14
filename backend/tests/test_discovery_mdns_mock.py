import pytest
import asyncio
from app.communication.drone_registry import DroneRegistry


@pytest.mark.asyncio
async def test_mdns_register_callback(monkeypatch, tmp_path):
    reg = DroneRegistry(persist_path=str(tmp_path/"reg.json"))

    calls = []
    class FakeScanner:
        async def start(self, cb):
            # simulate a found service
            await asyncio.sleep(0)
            cb("drone-001._drone._tcp.local.", "drone-001.local", {"id": "d001", "port": "8080"})
            calls.append("started")
            return True
        async def stop(self):
            calls.append("stopped")

    monkeypatch.setattr("app.communication.drone_registry.MDNSScanner", FakeScanner)

    await reg.start_discovery()
    # Give event loop time
    await asyncio.sleep(0)
    assert "d001" in reg.list_drones()
    await reg.stop_discovery()

