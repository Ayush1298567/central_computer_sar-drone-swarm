# backend/app/communication/telemetry_receiver.py
"""
Telemetry receiver: subscribes to Redis channel 'telemetry' and caches latest per drone.
"""
import json
import asyncio
from typing import Dict, Any, Optional
from redis import asyncio as aioredis
import logging

logger = logging.getLogger(__name__)
REDIS_URL = "redis://localhost:6379/0"
TELEMETRY_CHANNEL = "telemetry"
_last_cache: Dict[str, Dict[str, Any]] = {}

async def _handle_message(payload: str):
    try:
        obj = json.loads(payload)
        drone_id = obj.get("drone_id") or obj.get("id")
        if not drone_id:
            logger.debug("telemetry without drone_id: %s", obj)
            return
        _last_cache[drone_id] = obj
    except Exception as e:
        logger.exception("Failed to parse telemetry message: %s", e)

async def start_redis_listener(stop_event: asyncio.Event):
    r = aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(TELEMETRY_CHANNEL)
    logger.info("Subscribed to telemetry channel")
    try:
        while not stop_event.is_set():
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg:
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                await _handle_message(data)
            await asyncio.sleep(0)
    finally:
        await pubsub.unsubscribe(TELEMETRY_CHANNEL)
        await r.close()

def get_last_telemetry(drone_id: str) -> Optional[Dict[str, Any]]:
    return _last_cache.get(drone_id)

