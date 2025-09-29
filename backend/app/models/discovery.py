"""
Discovery models for SAR Mission Commander
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base

class DiscoveryType(enum.Enum):
    PERSON = "person"
    VEHICLE = "vehicle"
    AIRCRAFT = "aircraft"
    STRUCTURE = "structure"
    ANIMAL = "animal"
    OTHER = "other"

class ConfidenceLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String, ForeignKey("missions.id"))

    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)

    # Discovery details
    discovery_type = Column(Enum(DiscoveryType), default=DiscoveryType.OTHER)
    description = Column(Text)
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.MEDIUM)

    # Status
    verified = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    priority = Column(Integer, default=5)  # 1-10 scale

    # Media
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)

    # Timing
    discovered_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # AI analysis
    ai_analysis = Column(Text)  # JSON string with AI insights

    # Relationships
    mission = relationship("Mission", back_populates="discoveries")