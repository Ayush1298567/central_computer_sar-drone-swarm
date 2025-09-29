"""
Database models for discoveries and points of interest.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Discovery(Base):
    """Discovery or point of interest found during mission."""

    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"))

    # Location (where discovery was made)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    altitude = Column(Float, default=0.0)

    # Discovery details
    discovery_type = Column(String(50), nullable=False)  # person, vehicle, structure, debris, etc.
    confidence = Column(Float, default=0.0)  # AI confidence score 0-1
    description = Column(Text)

    # Classification
    category = Column(String(50), default="unknown")  # human, vehicle, structure, natural, other
    subcategory = Column(String(50))  # For more specific classification

    # Status and workflow
    status = Column(String(50), default="new")  # new, investigating, confirmed, false_positive, resolved
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    urgency = Column(String(20), default="medium")  # low, medium, high, immediate

    # Evidence and media
    image_path = Column(String(500))  # Path to saved image
    video_path = Column(String(500))  # Path to saved video clip
    audio_path = Column(String(500))  # Path to saved audio clip
    media_metadata = Column(JSON)  # EXIF data, timestamps, etc.

    # Investigation and response
    investigation_notes = Column(Text)
    response_required = Column(Boolean, default=False)
    response_type = Column(String(50))  # medical, evacuation, investigation, etc.
    response_status = Column(String(50), default="pending")  # pending, dispatched, on_scene, resolved

    # Environmental context
    weather_conditions = Column(JSON)  # Weather at time of discovery
    lighting_conditions = Column(String(50))  # daylight, twilight, night, artificial
    visibility = Column(String(20), default="good")  # poor, fair, good, excellent

    # AI analysis
    ai_analysis = Column(JSON)  # Detailed AI analysis results
    suggested_actions = Column(JSON)  # AI-suggested response actions

    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    investigated_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships will be defined in mission.py to avoid circular imports