"""
Operational log models for missions and drone state history.
"""
from sqlalchemy import Column, String, DateTime, Float, JSON, Integer
from datetime import datetime
from ..core.database import Base


class MissionLog(Base):
    """High-level mission event log for auditability and replay."""
    __tablename__ = "mission_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String(50), index=True, nullable=False)
    event_type = Column(String(50), index=True, nullable=False)  # ai_decision, mission_update, emergency
    payload = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class DroneStateHistory(Base):
    """Per-second telemetry snapshot for active drones during missions."""
    __tablename__ = "drone_state_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(String(50), index=True, nullable=False)
    mission_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    battery_percentage = Column(Float)
    flight_mode = Column(String(50))
    status = Column(String(50))
    signal_strength = Column(Float)
    payload = Column(JSON)  # raw snapshot if needed
