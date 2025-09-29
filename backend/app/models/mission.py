"""
Mission model definitions.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum


class MissionStatus(str, Enum):
    """Mission status enumeration."""
    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EMERGENCY = "emergency"


class Mission(Base):
    """Mission model representing a SAR mission."""

    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=MissionStatus.PLANNING.value, nullable=False)
    priority = Column(Integer, default=3, nullable=False)  # 1-5, 5 being highest
    mission_type = Column(String(50), default="search", nullable=False)  # search, rescue, survey, etc.

    # Location and area
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    search_area = Column(JSON, nullable=False)  # GeoJSON polygon
    search_altitude = Column(Float, default=30.0, nullable=False)

    # Mission parameters
    estimated_duration = Column(Integer, nullable=True)  # minutes
    max_drones = Column(Integer, nullable=False)
    search_pattern = Column(String(50), default="lawnmower", nullable=False)
    overlap_percentage = Column(Float, default=10.0, nullable=False)

    # Timing
    planned_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    planned_end_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)

    # Mission results
    discoveries_count = Column(Integer, default=0, nullable=False)
    area_covered = Column(Float, default=0.0, nullable=False)  # square meters
    progress_percentage = Column(Float, default=0.0, nullable=False)

    # Metadata
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    weather_conditions = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    drones = relationship("MissionDrone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    chat_messages = relationship("ChatMessage", back_populates="mission")

    def __repr__(self):
        return f"<Mission(id={self.id}, mission_id='{self.mission_id}', name='{self.name}', status='{self.status}')>"


# Association table for many-to-many relationship between missions and drones
mission_drone_table = Table(
    "mission_drone",
    Base.metadata,
    Column("mission_id", Integer, ForeignKey("missions.id"), primary_key=True),
    Column("drone_id", Integer, ForeignKey("drones.id"), primary_key=True),
    Column("assigned_area", JSON, nullable=True),  # Assigned search area for this drone
    Column("waypoints", JSON, nullable=True),  # Flight waypoints
    Column("current_waypoint", Integer, default=0, nullable=False),
    Column("status", String(20), default="assigned", nullable=False),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
)


class MissionDrone(Base):
    """Association object for mission-drone relationship."""

    __tablename__ = "mission_drone"

    mission_id = Column(Integer, ForeignKey("missions.id"), primary_key=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), primary_key=True)
    assigned_area = Column(JSON, nullable=True)
    waypoints = Column(JSON, nullable=True)
    current_waypoint = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="assigned", nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    mission = relationship("Mission", back_populates="drones")
    drone = relationship("Drone", back_populates="missions")

    def __repr__(self):
        return f"<MissionDrone(mission_id={self.mission_id}, drone_id={self.drone_id}, status='{self.status}')>"