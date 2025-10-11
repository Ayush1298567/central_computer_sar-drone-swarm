from __future__ import annotations

import json
import os
import threading
import time
from typing import Optional

import redis

from backend.app.schemas.telemetry import TelemetryMessage


def _get_redis_client() -> redis.Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return redis.Redis(host=host, port=port, db=0)


def process_one_telemetry_message(timeout_seconds: float = 2.0) -> bool:
    """Subscribe to the telemetry channel, process a single message, then return.

    Returns True if a message was processed, False on timeout.
    """
    client = _get_redis_client()
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("telemetry")

    start = time.time()
    try:
        while time.time() - start < timeout_seconds:
            message = pubsub.get_message(timeout=0.05)
            if not message:
                time.sleep(0.01)
                continue

            try:
                raw = message["data"]
                payload = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
                telemetry = TelemetryMessage.model_validate_json(payload)
                key = TelemetryMessage.redis_last_key(telemetry.drone_id)
                # Store the original JSON blob for debugging transparency
                client.set(key, payload)
                return True
            except Exception:
                # Best-effort: skip bad messages, keep listening until timeout
                continue
        return False
    finally:
        try:
            pubsub.unsubscribe()
            pubsub.close()
        except Exception:
            pass


def run_consumer_forever(sleep_seconds: float = 0.05) -> None:
    """Run a simple forever-loop consumer that mirrors last telemetry into a Redis key."""
    client = _get_redis_client()
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("telemetry")
    try:
        for message in pubsub.listen():
            if not message:
                time.sleep(sleep_seconds)
                continue
            try:
                raw = message["data"]
                payload = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
                telemetry = TelemetryMessage.model_validate_json(payload)
                key = TelemetryMessage.redis_last_key(telemetry.drone_id)
                client.set(key, payload)
            except Exception:
                # Skip malformed messages
                continue
    finally:
        try:
            pubsub.unsubscribe()
            pubsub.close()
        except Exception:
            pass


def start_background_single_shot(timeout_seconds: float = 2.0) -> threading.Thread:
    """Start a background thread to process a single telemetry message."""
    thread = threading.Thread(target=process_one_telemetry_message, args=(timeout_seconds,), daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    run_consumer_forever()
