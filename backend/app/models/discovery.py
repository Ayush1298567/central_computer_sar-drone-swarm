from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from ..core.database import Base

class DiscoveryType(PyEnum):
    PERSON = "person"
    VEHICLE = "vehicle"
    STRUCTURE = "structure"
    DEBRIS = "debris"
    HAZARD = "hazard"
    PERSONAL_ITEM = "personal_item"
    ANIMAL = "animal"
    UNKNOWN = "unknown"

class DiscoveryConfidence(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Discovery(Base):
    """Represents objects or persons of interest discovered during missions."""
    __tablename__ = "discoveries"

    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)

    # Geographic location (required for database compatibility)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)

    # Detection information
    discovery_type = Column(String(100), nullable=False)
    description = Column(Text)
    confidence = Column(Float)  # Note: stored as VARCHAR in DB but we'll handle as float

    # Status and verification
    verified = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    priority = Column(Integer, default=1)

    # Media and evidence
    image_url = Column(String(500))
    video_url = Column(String(500))
    ai_analysis = Column(Text)

    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    evidence_secured = Column(Boolean, default=False)
    legal_chain_maintained = Column(Boolean, default=True)
    
    # Relationships
    mission = relationship("Mission", back_populates="discoveries")
    drone = relationship("Drone", back_populates="discoveries")
    evidence_files = relationship("EvidenceFile", back_populates="discovery")
    
    def to_dict(self):
        """Convert discovery to dictionary for API responses."""
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "drone_id": self.drone_id,
            "discovery_type": self.discovery_type,
            "description": self.description,
            "confidence": float(self.confidence) if self.confidence else 0.0,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "verified": self.verified,
            "false_positive": self.false_positive,
            "priority": self.priority,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "ai_analysis": self.ai_analysis,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None
        }
    
    def calculate_priority(self):
        """Calculate priority level based on discovery type and confidence."""
        confidence_score = float(self.confidence) if self.confidence else 0.0
        if self.discovery_type == "person" and confidence_score > 0.8:
            return 4  # Critical
        elif self.discovery_type == "person" and confidence_score > 0.6:
            return 3  # High
        elif self.discovery_type in ["vehicle", "debris"] and confidence_score > 0.7:
            return 2  # Medium
        else:
            return 1  # Low


class EvidenceFile(Base):
    """Stores evidence files associated with discoveries."""
    __tablename__ = "evidence_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discovery_id = Column(Integer, ForeignKey("discoveries.id"), nullable=False)

    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # image, video, thermal, etc.
    file_size = Column(Integer)
    original_filename = Column(String(255))
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100))
    processed = Column(Boolean, default=False)
    thumbnail_path = Column(String(500))

    # Relationships
    discovery = relationship("Discovery", back_populates="evidence_files")
