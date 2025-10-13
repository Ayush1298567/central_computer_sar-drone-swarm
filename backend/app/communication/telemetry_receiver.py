"""
Telemetry Receiver and Cache

- Async-safe TelemetryCache with history and normalized snapshots
- Redis subscription when enabled; HTTP fallback is exposed via API router
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelemetryCache:
    """Async-safe in-memory telemetry store with bounded history per drone."""

    def __init__(self, history_size: Optional[int] = None):
        try:
            from app.core.config import settings
            default_size = settings.TELEMETRY_HISTORY_SIZE
        except Exception:
            default_size = 50
        self._history_size: int = history_size or default_size
        self._latest_by_drone: Dict[str, Dict[str, Any]] = {}
        self._history_by_drone: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

    async def update(self, drone_id: str, payload: Dict[str, Any]) -> None:
        """Update latest normalized telemetry for a drone and append to history."""
        if not drone_id:
            return
        normalized = self._normalize(drone_id, payload)
        async with self._lock:
            self._latest_by_drone[drone_id] = normalized
            dq = self._history_by_drone.get(drone_id)
            if dq is None:
                dq = deque(maxlen=self._history_size)
                self._history_by_drone[drone_id] = dq
            dq.append({**normalized, "_raw": payload})

        # Opportunistically bump registry last_seen
        try:
            from app.communication.drone_registry import get_registry
            reg = get_registry()
            reg.set_last_seen(drone_id)
        except Exception:
            # registry unavailable should not break telemetry
            pass

    async def get(self, drone_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            value = self._latest_by_drone.get(drone_id)
            return dict(value) if value else None

    async def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Return normalized snapshot keyed by drone id, enriched with registry status."""
        async with self._lock:
            snapshot = {k: dict(v) for k, v in self._latest_by_drone.items()}

        # Merge status/last_seen from registry when available
        try:
            from app.communication.drone_registry import get_registry
            reg = get_registry()
            for did, rec in snapshot.items():
                rec.setdefault("status", reg.get_status(did))
                rec.setdefault("last_seen", reg.get_last_seen(did))
        except Exception:
            pass
        return snapshot

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Non-async compatibility snapshot used by legacy tests/handlers."""
        return dict(self._latest_by_drone)

    def _normalize(self, drone_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        now_iso = datetime.utcnow().isoformat()
        # Extract lat/lon/alt possibly nested
        lat = payload.get("lat") or payload.get("latitude")
        lon = payload.get("lon") or payload.get("lng") or payload.get("longitude")
        alt = payload.get("alt") or payload.get("altitude")
        position = payload.get("position") or payload.get("gps") or payload.get("location") or {}
        if lat is None:
            lat = position.get("lat") or position.get("latitude")
        if lon is None:
            lon = position.get("lon") or position.get("lng") or position.get("longitude")
        if alt is None:
            alt = position.get("alt") or position.get("altitude")

        battery = (
            payload.get("battery")
            or payload.get("battery_level")
            or payload.get("batteryPercent")
            or payload.get("battery_level_pct")
        )
        status = payload.get("status")

        def _to_float(value: Any) -> Optional[float]:
            try:
                return float(value)
            except Exception:
                return None

        return {
            "id": drone_id,
            "lat": _to_float(lat),
            "lon": _to_float(lon),
            "alt": _to_float(alt),
            "battery": _to_float(battery),
            "status": status,
            "last_seen": now_iso,
        }


class TelemetryReceiver:
    """Receives telemetry via Redis pubsub when enabled and updates TelemetryCache."""

    def __init__(
        self,
        channel: Optional[str] = None,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        client_factory: Optional[Any] = None,
        history_size: Optional[int] = None,
    ):
        try:
            from app.core.config import settings
            self.channel = channel or settings.TELEMETRY_CHANNEL
            self.host = host or settings.REDIS_HOST
            self.port = port or settings.REDIS_PORT
            self.db = settings.REDIS_DB if db is None else db
            self.redis_enabled = bool(settings.REDIS_ENABLED)
        except Exception:
            self.channel = channel or os.getenv("TELEMETRY_CHANNEL", "telemetry")
            self.host = host or os.getenv("REDIS_HOST", "127.0.0.1")
            self.port = port or int(os.getenv("REDIS_PORT", "6379"))
            self.db = int(os.getenv("REDIS_DB", "0")) if db is None else db
            self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"

        self.cache = TelemetryCache(history_size=history_size)
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._client_factory = client_factory
        self._hb_task: Optional[asyncio.Task] = None

    async def _subscribe_loop(self) -> None:
        if not self.redis_enabled:
            # No Redis, idle loop
            while not self._stop.is_set():
                await asyncio.sleep(0.1)
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
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8")
                        data = json.loads(raw)
                        drone_id = data.get("drone_id") or data.get("id")
                        telemetry = data.get("telemetry") or data.get("payload") or data
                        if drone_id:
                            await self.cache.update(drone_id, telemetry)
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

    async def _heartbeat_loop(self) -> None:
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

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        if self._task is None or self._task.done():
            _loop = loop or asyncio.get_event_loop()
            self._stop.clear()
            self._task = _loop.create_task(self._subscribe_loop())
            self._hb_task = _loop.create_task(self._heartbeat_loop())

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
"""

