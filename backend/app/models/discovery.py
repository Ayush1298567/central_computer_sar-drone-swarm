from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .mission import Base

class Discovery(Base):
    """
    Represents objects or persons of interest discovered during missions.
    """
    __tablename__ = "discoveries"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    drone_id = Column(String(50), ForeignKey("drones.id"), nullable=False)
    
    # Detection information
    object_type = Column(String(100), nullable=False)  # person, vehicle, debris, etc.
    confidence_score = Column(Float, nullable=False)  # AI confidence (0-1)
    detection_method = Column(String(50))  # visual, thermal, lidar, etc.
    
    # Geographic location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)  # Altitude when detected
    location_accuracy = Column(Float)  # GPS accuracy in meters
    
    # Visual evidence
    primary_image_url = Column(String(500))  # Primary detection image
    video_clip_url = Column(String(500))  # Video clip of detection
    thermal_image_url = Column(String(500))  # Thermal image if available
    
    # Detection context
    environmental_conditions = Column(JSON)  # Weather, lighting, etc.
    detection_context = Column(JSON)  # Surrounding objects, terrain
    sensor_data = Column(JSON)  # Raw sensor readings
    
    # Investigation status
    investigation_status = Column(String(50), default="pending")  # pending, investigating, verified, false_positive
    priority_level = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=critical
    human_verified = Column(Boolean, default=False)
    verification_notes = Column(Text)
    
    # Follow-up actions
    action_required = Column(String(100))  # rescue_needed, investigation_required, etc.
    ground_team_notified = Column(Boolean, default=False)
    emergency_services_contacted = Column(Boolean, default=False)
    
    # Chain of custody
    discovered_by_operator = Column(String(100))  # Operator who was monitoring
    verified_by_operator = Column(String(100))  # Operator who verified
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
    
    def to_dict(self):
        """Convert discovery to dictionary for API responses."""
        return {
            "id": str(self.id),
            "mission_id": str(self.mission_id),
            "drone_id": self.drone_id,
            "object_type": self.object_type,
            "confidence_score": self.confidence_score,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "investigation_status": self.investigation_status,
            "priority_level": self.priority_level,
            "human_verified": self.human_verified,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
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