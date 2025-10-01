"""
Discovery model for found objects during SAR missions
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class DiscoveryType(enum.Enum):
    PERSON = "person"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    STRUCTURE = "structure"
    UNKNOWN = "unknown"
    FALSE_POSITIVE = "false_positive"


class DiscoveryStatus(enum.Enum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    
    # Discovery details
    discovery_type = Column(Enum(DiscoveryType), nullable=False)
    status = Column(Enum(DiscoveryStatus), default=DiscoveryStatus.DETECTED)
    confidence_score = Column(Float, nullable=False)  # AI confidence 0-1
    
    # Location
    location = Column(JSON, nullable=False)  # {"lat": 0, "lng": 0, "altitude": 0}
    detection_method = Column(String(100))  # "computer_vision", "thermal", "manual"
    
    # Visual data
    image_path = Column(String(500))  # Path to saved image
    thermal_image_path = Column(String(500))  # Path to thermal image
    video_path = Column(String(500))  # Path to video clip
    
    # AI analysis
    ai_description = Column(Text)  # AI-generated description
    detected_objects = Column(JSON)  # YOLO detection results
    risk_assessment = Column(JSON)  # AI risk analysis
    
    # Investigation
    investigation_notes = Column(Text)
    investigator_drone_id = Column(Integer)  # Which drone investigated
    investigation_result = Column(Text)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional metadata
    weather_conditions = Column(JSON)  # Weather at time of detection
    drone_telemetry = Column(JSON)  # Drone data at detection time
    
    # Relationships
    mission = relationship("Mission", back_populates="discoveries")

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "discovery_type": self.discovery_type.value if self.discovery_type else None,
            "status": self.status.value if self.status else None,
            "confidence_score": self.confidence_score,
            "location": self.location,
            "detection_method": self.detection_method,
            "image_path": self.image_path,
            "thermal_image_path": self.thermal_image_path,
            "video_path": self.video_path,
            "ai_description": self.ai_description,
            "detected_objects": self.detected_objects,
            "risk_assessment": self.risk_assessment,
            "investigation_notes": self.investigation_notes,
            "investigator_drone_id": self.investigator_drone_id,
            "investigation_result": self.investigation_result,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "weather_conditions": self.weather_conditions,
            "drone_telemetry": self.drone_telemetry
        }

    def is_high_confidence(self):
        """Check if discovery has high confidence score"""
        return self.confidence_score >= 0.8

    def needs_investigation(self):
        """Check if discovery needs further investigation"""
        return self.status in [DiscoveryStatus.DETECTED, DiscoveryStatus.CONFIRMED]

    def is_resolved(self):
        """Check if discovery is resolved"""
        return self.status in [DiscoveryStatus.RESOLVED, DiscoveryStatus.DISMISSED]