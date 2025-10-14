from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional

from app.communication.telemetry_receiver import get_telemetry_receiver

router = APIRouter()

@router.post("/telemetry")
async def ingest_telemetry(body: Dict[str, Any]):
    """HTTP telemetry ingestion fallback when Redis is disabled.
    Accepts flexible payload shapes and updates the TelemetryCache.
    """
    recv = get_telemetry_receiver()
    # Extract drone id and telemetry payload
    drone_id: Optional[str] = body.get("drone_id") or body.get("id")
    telemetry: Dict[str, Any] = body.get("telemetry") or body.get("payload") or body
    if not drone_id:
        raise HTTPException(status_code=400, detail="drone_id is required")

    await recv.cache.update(drone_id, telemetry)
    return {"status": "ok"}
