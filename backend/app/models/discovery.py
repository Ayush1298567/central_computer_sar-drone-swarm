"""
Discovery model definitions.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum


class DiscoveryStatus(str, Enum):
    """Discovery status enumeration."""
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    INVESTIGATING = "investigating"
    INVESTIGATED = "investigated"
    FALSE_POSITIVE = "false_positive"
    REQUIRES_ACTION = "requires_action"


class DiscoveryPriority(str, Enum):
    """Discovery priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class Discovery(Base):
    """Discovery model representing detected objects or points of interest."""

    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    discovery_id = Column(String(50), unique=True, index=True, nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)  # meters

    # Detection details
    discovery_type = Column(String(50), nullable=False)  # person, vehicle, structure, etc.
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    detection_method = Column(String(50), nullable=False)  # thermal, visual, AI, etc.
    detected_by_drone = Column(String(50), nullable=True)

    # Status and priority
    status = Column(String(20), default=DiscoveryStatus.DETECTED.value, nullable=False)
    priority = Column(String(20), default=DiscoveryPriority.MEDIUM.value, nullable=False)
    requires_investigation = Column(Boolean, default=True, nullable=False)

    # Investigation details
    investigation_radius = Column(Float, default=100.0, nullable=False)  # meters
    assigned_drone_id = Column(String(50), nullable=True)
    investigated_at = Column(DateTime(timezone=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)

    # Additional data
    metadata = Column(JSON, nullable=True)  # Additional detection data
    image_urls = Column(JSON, nullable=True)  # URLs to captured images
    video_url = Column(String(500), nullable=True)  # URL to investigation video

    # Timing
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    mission = relationship("Mission", back_populates="discoveries")
    evidence_files = relationship("EvidenceFile", back_populates="discovery")

    def __repr__(self):
        return f"<Discovery(id={self.id}, discovery_id='{self.discovery_id}', type='{self.discovery_type}', status='{self.status}')>"


class EvidenceFile(Base):
    """Evidence files associated with discoveries."""

    __tablename__ = "evidence_files"

    id = Column(Integer, primary_key=True, index=True)
    discovery_id = Column(Integer, ForeignKey("discoveries.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, video, audio, document
    file_size = Column(Integer, nullable=False)  # bytes
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Relationships
    discovery = relationship("Discovery", back_populates="evidence_files")

    def __repr__(self):
        return f"<EvidenceFile(id={self.id}, file_name='{self.file_name}', type='{self.file_type}')>"