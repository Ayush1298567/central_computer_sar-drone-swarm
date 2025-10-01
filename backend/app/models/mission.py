from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Mission(Base):
    """Core mission data model representing a search and rescue operation."""
    __tablename__ = "missions"
    
    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Mission status tracking
    status = Column(String(50), nullable=False, default="planning")
    
    # Geographic data
    search_area = Column(JSON)  # GeoJSON polygon
    launch_point = Column(JSON)  # GPS coordinates
    
    # Mission parameters
    search_altitude = Column(Float)
    search_speed = Column(String(20))
    search_target = Column(String(100))
    recording_mode = Column(String(20))
    
    # Operational data
    assigned_drone_count = Column(Integer, default=0)
    estimated_duration = Column(Integer)
    actual_duration = Column(Integer)
    coverage_percentage = Column(Float, default=0.0)
    
    # Mission context and AI parameters
    mission_context = Column(JSON)
    ai_confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    drone_assignments = relationship("MissionDrone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    chat_history = relationship("ChatMessageDB", back_populates="mission")
    
    def to_dict(self):
        """Convert mission to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "search_area": self.search_area,
            "launch_point": self.launch_point,
            "search_altitude": self.search_altitude,
            "search_speed": self.search_speed,
            "search_target": self.search_target,
            "assigned_drone_count": self.assigned_drone_count,
            "estimated_duration": self.estimated_duration,
            "coverage_percentage": self.coverage_percentage,
            "ai_confidence": self.ai_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class MissionDrone(Base):
    """Junction table tracking drone assignments to missions."""
    __tablename__ = "mission_drones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    
    # Assigned search area
    assigned_area = Column(JSON)
    navigation_waypoints = Column(JSON)
    
    # Status tracking
    status = Column(String(50), default="assigned")
    progress_percentage = Column(Float, default=0.0)
    
    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    mission = relationship("Mission", back_populates="drone_assignments")
    drone = relationship("Drone", back_populates="mission_assignments")


class ChatMessageDB(Base):
    """Stores conversational mission planning dialogue."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    
    # Message content
    sender = Column(String(10), nullable=False)  # "user" or "ai"
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    
    # AI-specific data
    ai_confidence = Column(Float)
    processing_time = Column(Float)
    
    # Context and attachments
    attachments = Column(JSON)
    conversation_context = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mission = relationship("Mission", back_populates="chat_history")
