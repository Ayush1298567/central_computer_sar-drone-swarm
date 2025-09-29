"""
Database models for drone management.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Drone(Base):
    """Drone model for mission coordination."""

    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True)

    # Status and availability
    status = Column(String(50), default="available")  # available, assigned, active, maintenance, offline
    is_connected = Column(Boolean, default=False)

    # Position and telemetry (last known)
    current_lat = Column(Float)
    current_lng = Column(Float)
    altitude = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    battery_level = Column(Float, default=100.0)
    speed = Column(Float, default=0.0)

    # Capabilities
    max_speed = Column(Float, default=20.0)  # m/s
    max_altitude = Column(Float, default=120.0)  # meters
    max_flight_time = Column(Integer, default=30)  # minutes
    camera_resolution = Column(String(20), default="1080p")
    has_thermal = Column(Boolean, default=False)
    has_night_vision = Column(Boolean, default=False)

    # Hardware specs
    weight = Column(Float)  # kg
    dimensions = Column(JSON)  # length, width, height in cm

    # Mission assignment
    current_mission_id = Column(Integer, nullable=True)

    # Maintenance and logs
    last_maintenance = Column(DateTime(timezone=True))
    flight_hours = Column(Float, default=0.0)
    notes = Column(Text)

    # Timestamps
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())