# backend/app/communication/pi_communication.py
"""
High-level communication utilities for talking to drone Raspberry Pis over 5G.
Supports:
 - HTTP REST push (POST /api/mission)
 - Redis pub/sub (publish 'missions' channel)
 - Build mission payloads
"""
from typing import Any, Dict, Optional
import json
import logging
import asyncio

import httpx
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
HTTP_TIMEOUT = 10.0
MISSIONS_CHANNEL = "missions"

async def send_mission_http(pi_host: str, mission_payload: Dict[str, Any], timeout: float = HTTP_TIMEOUT) -> Dict[str, Any]:
    url = f"{pi_host.rstrip('/')}/api/mission"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=mission_payload)
        r.raise_for_status()
        return r.json()

async def publish_mission_redis(drone_id: str, mission_payload: Dict[str, Any], channel: str = MISSIONS_CHANNEL):
    r = aioredis.from_url(REDIS_URL)
    message = json.dumps({"drone_id": drone_id, "mission": mission_payload})
    await r.publish(channel, message)
    await r.close()

def build_mission_payload(waypoints: list, mission_id: str, priority: int = 1, meta: Optional[Dict]=None) -> Dict[str, Any]:
    payload = {
        "mission_id": mission_id,
        "priority": priority,
        "waypoints": waypoints,
        "meta": meta or {}
    }
    return payload

def send_mission_http_sync(pi_host: str, mission_payload: Dict[str, Any], timeout: float = HTTP_TIMEOUT) -> Dict[str, Any]:
    import requests
    url = f"{pi_host.rstrip('/')}/api/mission"
    r = requests.post(url, json=mission_payload, timeout=timeout)
    r.raise_for_status()
    return r.json()
