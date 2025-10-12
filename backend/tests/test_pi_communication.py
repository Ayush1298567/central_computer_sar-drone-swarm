# backend/tests/test_pi_communication.py
import asyncio
import json
import pytest

from app.communication.pi_communication import build_mission_payload, send_mission_http, publish_mission_redis


def test_build_mission_payload():
    p = build_mission_payload("m1", {"k": 1})
    assert p["mission_id"] == "m1" and p["payload"]["k"] == 1


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_send_mission_http(monkeypatch):
    async def fake_to_thread(func, *args, **kwargs):
        # direct call for speed
        return func(*args, **kwargs)

    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)

    # Monkeypatch private sync post function to avoid network
    def fake_post(url, data_json, timeout):
        return {"status": 200, "body": {"echo": data_json}}

    monkeypatch.setattr("app.communication.pi_communication._http_post", fake_post)

    res = await send_mission_http("http://example/mission", {"a": 1})
    assert res["status"] == 200 and res["body"]["echo"]["a"] == 1


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_publish_mission_redis(monkeypatch):
    sent = {}

    async def fake_pub(channel, message, *, host, port, db):
        sent["channel"] = channel
        sent["message"] = json.loads(message)

    await publish_mission_redis(
        "d1",
        {"m": 2},
        channel="missions_test",
        host="127.0.0.1",
        port=6379,
        publisher=fake_pub,
    )
    assert sent["channel"] == "missions_test"
    assert sent["message"]["drone_id"] == "d1"
    assert sent["message"]["mission"]["m"] == 2

# backend/tests/test_pi_communication.py
import pytest
import asyncio
import json
from backend.app.communication.pi_communication import build_mission_payload, publish_mission_redis

@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_build_payload_and_publish():
    payload = build_mission_payload("m1", {"waypoints": [[1,2,3]]})
    assert payload["mission_id"] == "m1" and payload["payload"]["waypoints"][0] == [1,2,3]
    # ensure publish function can be called with fake publisher
    called = {}
    async def fake_pub(channel, message, *, host, port, db):
        called["ok"] = True
    await publish_mission_redis("drone-001", payload, publisher=fake_pub)
    assert called.get("ok") is True
