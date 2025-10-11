from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Geospatial position in WGS84 with altitude in meters."""

    lat: float = Field(..., description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")
    alt_m: float = Field(..., description="Altitude above MSL in meters")


class Battery(BaseModel):
    """Battery state of charge and optional telemetry."""

    percent: float = Field(..., ge=0, le=100, description="Battery level (%)")
    voltage: Optional[float] = Field(None, description="Battery voltage (V)")
    current: Optional[float] = Field(None, description="Battery current (A)")


class TelemetryMessage(BaseModel):
    """Canonical drone telemetry message contract used across the system."""

    drone_id: str = Field(..., description="Unique drone identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of the reading")
    position: Position = Field(..., description="Current geospatial position")
    velocity_m_s: Optional[float] = Field(None, description="Ground speed (m/s)")
    heading_deg: Optional[float] = Field(None, description="Heading degrees (0-360)")
    battery: Battery = Field(..., description="Battery state")
    state: Optional[str] = Field(
        None, description='Operational state e.g. "armed", "flying", "rtl", "landed"'
    )
    diagnostics: Optional[Dict[str, Any]] = Field(
        None, description="Opaque diagnostics map for additional data"
    )

    @staticmethod
    def redis_last_key(drone_id: str) -> str:
        """Return the Redis key used to store the last telemetry blob for a drone."""
        return f"drone:{drone_id}:last_telemetry"
