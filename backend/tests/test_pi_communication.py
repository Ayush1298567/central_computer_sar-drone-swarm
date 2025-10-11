# backend/tests/test_pi_communication.py
import pytest
import asyncio
import json
from backend.app.communication.pi_communication import build_mission_payload, publish_mission_redis
from redis import asyncio as aioredis

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_build_payload_and_publish():
    payload = build_mission_payload(waypoints=[[1,2,3]], mission_id="m1")
    assert payload["mission_id"] == "m1"
    # test redis publish (will not assert delivery, just ensure no exception)
    r = aioredis.from_url("redis://localhost:6379/0")
    await publish_mission_redis("drone-001", payload)
    await r.close()
