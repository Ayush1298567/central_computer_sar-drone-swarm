"""
Discovery Model

Defines the structure for discovery/detection data.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Discovery(Base):
    """Discovery model for SAR detections."""

    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)

    # Location fields using backend naming convention
    lat = Column(Float, nullable=False)  # Discovery latitude
    lng = Column(Float, nullable=False)  # Discovery longitude
    altitude = Column(Float, nullable=False)  # Discovery altitude in meters

    # Detection details
    discovery_type = Column(String, nullable=False)  # human, vehicle, debris, etc.
    confidence = Column(Float, nullable=False)  # Confidence score (0-100)
    description = Column(Text)

    # Evidence and metadata
    evidence_data = Column(JSON)  # Additional evidence data
    image_url = Column(String)  # URL to evidence image
    video_url = Column(String)  # URL to evidence video

    # Classification
    classification = Column(String)  # confirmed, potential, false_positive
    priority = Column(String, default="medium")  # low, medium, high, critical

    # Mission context
    mission_id = Column(Integer, nullable=False)
    drone_id = Column(Integer, nullable=False)

    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String)  # User ID who verified
    verification_notes = Column(Text)

    # Environmental context
    weather_at_time = Column(String)
    lighting_conditions = Column(String)
    terrain_type = Column(String)

    # Metadata
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert discovery to dictionary."""
        return {
            'id': self.id,
            'lat': self.lat,
            'lng': self.lng,
            'altitude': self.altitude,
            'discovery_type': self.discovery_type,
            'confidence': self.confidence,
            'description': self.description,
            'evidence_data': self.evidence_data,
            'image_url': self.image_url,
            'video_url': self.video_url,
            'classification': self.classification,
            'priority': self.priority,
            'mission_id': self.mission_id,
            'drone_id': self.drone_id,
            'is_verified': self.is_verified,
            'verified_by': self.verified_by,
            'verification_notes': self.verification_notes,
            'weather_at_time': self.weather_at_time,
            'lighting_conditions': self.lighting_conditions,
            'terrain_type': self.terrain_type,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }