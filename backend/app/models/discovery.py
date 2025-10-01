from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Discovery(Base):
    """Represents objects or persons of interest discovered during missions."""
    __tablename__ = "discoveries"
    
    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    
    # Detection information
    object_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    detection_method = Column(String(50))
    
    # Geographic location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    location_accuracy = Column(Float)
    
    # Visual evidence
    primary_image_url = Column(String(500))
    video_clip_url = Column(String(500))
    thermal_image_url = Column(String(500))
    
    # Detection context
    environmental_conditions = Column(JSON)
    detection_context = Column(JSON)
    sensor_data = Column(JSON)
    
    # Investigation status
    investigation_status = Column(String(50), default="pending")
    priority_level = Column(Integer, default=1)
    human_verified = Column(Boolean, default=False)
    verification_notes = Column(Text)
    
    # Follow-up actions
    action_required = Column(String(100))
    ground_team_notified = Column(Boolean, default=False)
    emergency_services_contacted = Column(Boolean, default=False)
    
    # Chain of custody
    discovered_by_operator = Column(String(100))
    verified_by_operator = Column(String(100))
    evidence_secured = Column(Boolean, default=False)
    legal_chain_maintained = Column(Boolean, default=True)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    investigated_at = Column(DateTime)
    verified_at = Column(DateTime)
    closed_at = Column(DateTime)
    
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
            "object_type": self.object_type,
            "confidence_score": self.confidence_score,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "investigation_status": self.investigation_status,
            "priority_level": self.priority_level,
            "human_verified": self.human_verified,
            "discovered_at": self.discovered_at.isoformat(),
            "primary_image_url": self.primary_image_url,
            "video_clip_url": self.video_clip_url
        }
    
    def calculate_priority(self):
        """Calculate priority level based on object type and confidence."""
        if self.object_type == "person" and self.confidence_score > 0.8:
            return 4  # Critical
        elif self.object_type == "person" and self.confidence_score > 0.6:
            return 3  # High
        elif self.object_type in ["vehicle", "debris"] and self.confidence_score > 0.7:
            return 2  # Medium
        else:
            return 1  # Low


class EvidenceFile(Base):
    """Stores evidence files associated with discoveries."""
    __tablename__ = "evidence_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    discovery_id = Column(Integer, ForeignKey("discoveries.id"), nullable=False)
    
    file_type = Column(String(50))  # image, video, thermal, etc.
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100))
    
    # Relationships
    discovery = relationship("Discovery", back_populates="evidence_files")
