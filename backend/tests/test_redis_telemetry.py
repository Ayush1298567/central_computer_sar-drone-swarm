# backend/tests/test_redis_telemetry.py
import pytest
import asyncio
import json
from redis import asyncio as aioredis
from backend.app.communication.telemetry_receiver import _last_cache, _handle_message

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_redis_telemetry_store(tmp_path, monkeypatch):
    client = aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
    # ensure cache empty
    _last_cache.clear()
    sample = {"drone_id": "drone-001", "lat": 37.33, "lon": -121.88, "battery": 95}
    await _handle_message(json.dumps(sample))
    assert "drone-001" in _last_cache
    assert _last_cache["drone-001"]["battery"] == 95
    await client.close()
