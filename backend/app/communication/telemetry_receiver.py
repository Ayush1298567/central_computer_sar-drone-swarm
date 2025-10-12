"""
Telemetry Receiver: subscribes to Redis telemetry channel and caches last state.
Optional Redis integration; safe imports; persist last N messages.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional, Deque, List
from collections import deque

from app.core.config import settings

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
    def __init__(
        self,
        channel: str = "telemetry",
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        client_factory: Optional[Any] = None,
        persist_limit: Optional[int] = None,
        redis_enabled: Optional[bool] = None,
    ):
        self.channel = channel
        self.host = host or os.getenv("REDIS_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.cache = TelemetryCache()
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._client_factory = client_factory
        self._hb_task: Optional[asyncio.Task] = None
        self._persist_limit: int = persist_limit or settings.TELEMETRY_PERSIST_N
        self._messages: Deque[Dict[str, Any]] = deque(maxlen=self._persist_limit)
        # If redis_enabled not explicitly provided, rely on global setting
        self._redis_enabled: bool = settings.REDIS_ENABLED if redis_enabled is None else bool(redis_enabled)

    def _on_message(self, data: Dict[str, Any]) -> None:
        drone_id = data.get("drone_id") or data.get("id")
        telemetry = data.get("telemetry") or data.get("payload") or {}
        if not drone_id:
            return
        self.cache.update(drone_id, telemetry)
        self._messages.append({"drone_id": drone_id, "telemetry": telemetry})
        # Update registry heartbeat/status
        try:
            from app.communication.drone_registry import get_registry
            reg = get_registry()
            reg.set_last_seen(drone_id)
        except Exception:
            logger.exception("Registry heartbeat update failed")
        # Increment telemetry metric if available
        try:
            from app.monitoring.metrics import inc_telemetry_updates
            inc_telemetry_updates(1)
        except Exception:
            pass

    async def _subscribe_loop(self):
        # Only subscribe when Redis is enabled or a client_factory is provided (tests)
        if not self._redis_enabled and self._client_factory is None:
            logger.info("Redis telemetry disabled; subscribe loop not started")
            return

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
                        raw = message["data"]
                        if isinstance(raw, (bytes, bytearray)):
                            raw = raw.decode("utf-8")
                        data = json.loads(raw)
                        self._on_message(data)
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
                    # Update drones_online gauge if metrics available
                    try:
                        from app.monitoring.metrics import set_drones_online
                        online = 0
                        for drone_id in reg.list_drones():
                            if (reg.get_status(drone_id) or "").lower() != "offline":
                                online += 1
                        set_drones_online(online)
                    except Exception:
                        pass
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

    def recent_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None or limit >= len(self._messages):
            return list(self._messages)
        # Return the most recent 'limit' messages
        return list(self._messages)[-limit:]


_telemetry_singleton: Optional[TelemetryReceiver] = None


def get_telemetry_receiver(singleton: bool = True) -> TelemetryReceiver:
    global _telemetry_singleton
    if singleton:
        if _telemetry_singleton is None:
            _telemetry_singleton = TelemetryReceiver()
        return _telemetry_singleton
    return TelemetryReceiver()

"""
Legacy helpers kept for backward compatibility and tests
 - _handle_message: parse a JSON payload and update _last_cache
 - start_redis_listener: optional Redis subscription (disabled if redis lib missing)
"""
import asyncio as _asyncio
import json as _json
from typing import Dict as _Dict, Any as _Any, Optional as _Optional

try:  # Optional import to keep module import-safe when redis isn't installed
    from redis import asyncio as aioredis  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    aioredis = None  # type: ignore

REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
TELEMETRY_CHANNEL = "telemetry"
_last_cache: _Dict[str, _Dict[str, _Any]] = {}

async def _handle_message(payload: str):
    try:
        obj = _json.loads(payload)
        drone_id = obj.get("drone_id") or obj.get("id")
        if not drone_id:
            logger.debug("telemetry without drone_id: %s", obj)
            return
        _last_cache[drone_id] = obj
        # also count this as a telemetry update in metrics if available
        try:
            from app.monitoring.metrics import inc_telemetry_updates
            inc_telemetry_updates(1)
        except Exception:
            pass
    except Exception as e:
        logger.exception("Failed to parse telemetry message: %s", e)

async def start_redis_listener(stop_event: _asyncio.Event):
    if not settings.REDIS_ENABLED:
        logger.info("Redis telemetry disabled; listener not started")
        return
    if aioredis is None:
        logger.warning("redis asyncio client not available; listener not started")
        return
    r = aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(TELEMETRY_CHANNEL)
    logger.info("Subscribed to telemetry channel")
    try:
        while not stop_event.is_set():
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg:
                data = msg["data"]
                if isinstance(data, (bytes, bytearray)):
                    data = data.decode()
                await _handle_message(data)
            await _asyncio.sleep(0)
    finally:
        try:
            await pubsub.unsubscribe(TELEMETRY_CHANNEL)
            await r.close()
        except Exception:
            pass

def get_last_telemetry(drone_id: str) -> _Optional[_Dict[str, _Any]]:
    return _last_cache.get(drone_id)

