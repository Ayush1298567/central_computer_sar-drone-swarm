"""
Pi communication helpers (HTTP + Redis) with lazy imports and minimal deps.

Exposes:
- build_mission_payload(mission_id, payload)
- send_mission_http(pi_host, payload, timeout=10.0)
- publish_mission_redis(drone_id, payload, channel="missions")

All heavy deps are optional and loaded lazily. Functions are designed to be
easily monkeypatched in tests (_http_post, _redis_publish).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def build_mission_payload(mission_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"mission_id": mission_id, "payload": payload}


def _http_post(url: str, data_json: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """Synchronous HTTP POST implemented with urllib; used via asyncio.to_thread."""
    import urllib.request
    import urllib.error

    req = urllib.request.Request(
        url,
        data=json.dumps(data_json).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8") or "{}"
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return {"status": resp.status, "body": parsed}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = str(e)
        return {"error": f"HTTP {e.code}", "body": body}
    except Exception as e:
        return {"error": str(e)}


async def send_mission_http(pi_host: str, payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
    """Asynchronously send mission to Pi via HTTP JSON POST.

    The pi_host may be a full URL (e.g., http://host:port/api/mission). This function
    does not assume a specific path to keep it flexible.
    """
    logger.debug("send_mission_http -> %s", pi_host)
    return await asyncio.to_thread(_http_post, pi_host, payload, timeout)


async def _redis_publish(channel: str, message: str, *, host: str, port: int, db: int) -> None:
    """Publish a message to Redis using redis.asyncio if available."""
    try:
        import redis.asyncio as redis  # type: ignore
    except Exception as e:
        raise RuntimeError("redis.asyncio not available") from e

    r = redis.Redis(host=host, port=port, db=db)
    await r.publish(channel, message)
    await r.close()


async def publish_mission_redis(
    drone_id: str,
    payload: Dict[str, Any],
    *,
    channel: str = "missions",
    host: str | None = None,
    port: int | None = None,
    db: int = 0,
    publisher: Any | None = None,
) -> None:
    """Publish mission payload for a drone to Redis channel.

    Host/port default from env REDIS_HOST/REDIS_PORT or localhost:6379.
    """
    host = host or os.getenv("REDIS_HOST", "127.0.0.1")
    port = port or int(os.getenv("REDIS_PORT", "6379"))
    message = json.dumps({"drone_id": drone_id, "mission": payload})
    if publisher is not None:
        await publisher(channel, message, host=host, port=port, db=db)
        return
    pub = globals().get("_redis_publish")
    if callable(pub):
        await pub(channel, message, host=host, port=port, db=db)
    else:
        logger.warning("Redis publisher not available; skipping publish")

