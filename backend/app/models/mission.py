"""
Database models for SAR missions.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Mission(Base):
    """SAR Mission model."""

    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="planning")  # planning, active, completed, cancelled

    # Location and area
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    area_size_km2 = Column(Float, nullable=False)
    search_altitude = Column(Float, default=50.0)  # meters

    # Mission parameters
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    weather_conditions = Column(JSON)  # Store weather data
    estimated_duration = Column(Integer)  # minutes

    # AI planning data
    ai_plan = Column(JSON)  # Store AI-generated mission plan
    user_approved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    drones = relationship("Drone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    chat_messages = relationship("ChatMessage", back_populates="mission")


class Drone(Base):
    """Drone model for mission coordination."""

    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    status = Column(String(50), default="available")  # available, assigned, active, maintenance

    # Position and telemetry
    current_lat = Column(Float)
    current_lng = Column(Float)
    altitude = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    battery_level = Column(Float, default=100.0)
    speed = Column(Float, default=0.0)

    # Capabilities
    max_speed = Column(Float, default=20.0)  # m/s
    max_altitude = Column(Float, default=120.0)  # meters
    camera_resolution = Column(String(20), default="1080p")

    # Mission assignment
    mission_id = Column(Integer, ForeignKey("missions.id"))

    # Timestamps
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    mission = relationship("Mission", back_populates="drones")
    discoveries = relationship("Discovery", back_populates="drone")


class Discovery(Base):
    """Discovery or point of interest found during mission."""

    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"))

    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    altitude = Column(Float, default=0.0)

    # Discovery details
    discovery_type = Column(String(50), nullable=False)  # person, vehicle, structure, etc.
    confidence = Column(Float, default=0.0)  # AI confidence score 0-1
    description = Column(Text)

    # Status and workflow
    status = Column(String(50), default="new")  # new, investigating, confirmed, false_positive
    priority = Column(String(20), default="normal")  # low, normal, high, critical

    # Evidence
    image_path = Column(String(500))  # Path to saved image
    video_path = Column(String(500))  # Path to saved video clip

    # Investigation
    investigation_notes = Column(Text)
    response_required = Column(Boolean, default=False)

    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    investigated_at = Column(DateTime(timezone=True))

    # Relationships
    mission = relationship("Mission", back_populates="discoveries")
    drone = relationship("Drone", back_populates="discoveries")