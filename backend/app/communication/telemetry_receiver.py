"""
Telemetry Receiver: subscribes to Redis telemetry channel and caches last state.
Lazy imports, minimal deps; easy to mock in tests.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelemetryCache:
    def __init__(self):
        self._state: Dict[str, Dict[str, Any]] = {}

    def update(self, drone_id: str, telemetry: Dict[str, Any]) -> None:
        self._state[drone_id] = telemetry

    def get(self, drone_id: str) -> Optional[Dict[str, Any]]:
        return self._state.get(drone_id)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._state)


class TelemetryReceiver:
    def __init__(self, channel: str = "telemetry", *, host: Optional[str] = None, port: Optional[int] = None, db: int = 0, client_factory: Optional[Any] = None):
        self.channel = channel
        self.host = host or os.getenv("REDIS_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.cache = TelemetryCache()
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._client_factory = client_factory
        self._hb_task: Optional[asyncio.Task] = None

    async def _subscribe_loop(self):
        client = None
        if self._client_factory is not None:
            try:
                client = self._client_factory(host=self.host, port=self.port, db=self.db)
            except Exception:
                logger.exception("client_factory failed")
                return
        else:
            try:
                import redis.asyncio as redis  # type: ignore
                client = redis.Redis(host=self.host, port=self.port, db=self.db)
            except Exception:
                logger.exception("redis.asyncio not available for telemetry")
                return
        pubsub = client.pubsub()
        await pubsub.subscribe(self.channel)

        try:
            while not self._stop.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    try:
                        data = json.loads(message["data"].decode("utf-8"))
                        drone_id = data.get("drone_id") or data.get("id")
                        telemetry = data.get("telemetry") or data.get("payload") or {}
                        if drone_id:
                            self.cache.update(drone_id, telemetry)
                            # Update registry heartbeat/status
                            try:
                                from app.communication.drone_registry import get_registry
                                reg = get_registry()
                                reg.set_last_seen(drone_id)
                            except Exception:
                                logger.exception("Registry heartbeat update failed")
                    except Exception:
                        logger.exception("Failed to parse telemetry message")
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.unsubscribe(self.channel)
                await pubsub.close()
                await client.close()
            except Exception:
                pass

    async def _heartbeat_loop(self):
        try:
            while not self._stop.is_set():
                try:
                    from app.communication.drone_registry import get_registry
                    reg = get_registry()
                    reg.mark_offline_if_stale(threshold_seconds=30.0)
                except Exception:
                    logger.exception("Registry offline check failed")
                await asyncio.sleep(10.0)
        except asyncio.CancelledError:
            pass

    def start(self) -> None:
        if self._task is None or self._task.done():
            loop = asyncio.get_event_loop()
            self._stop.clear()
            self._task = loop.create_task(self._subscribe_loop())
            self._hb_task = loop.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except Exception:
                pass
        if self._hb_task:
            try:
                await asyncio.wait_for(self._hb_task, timeout=2.0)
            except Exception:
                pass


_telemetry_singleton: Optional[TelemetryReceiver] = None


def get_telemetry_receiver(singleton: bool = True) -> TelemetryReceiver:
    global _telemetry_singleton
    if singleton:
        if _telemetry_singleton is None:
            _telemetry_singleton = TelemetryReceiver()
        return _telemetry_singleton
    return TelemetryReceiver()

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

