from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Mission(Base):
    """
    Core mission data model representing a search and rescue operation.

    This model stores all information about a mission including:
    - Basic mission metadata (name, description, status)
    - Geographic search area (stored as GeoJSON polygon)
    - Mission parameters and configuration
    - Timing information (created, started, completed)
    - Results and performance metrics
    """
    __tablename__ = "missions"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Mission status tracking
    status = Column(String(50), nullable=False, default="planning")  # planning, active, paused, completed, aborted

    # Geographic data
    search_area = Column(JSON)  # GeoJSON polygon defining search boundaries
    launch_point = Column(JSON)  # GPS coordinates of drone launch location

    # Mission parameters
    search_altitude = Column(Float)  # Preferred search altitude in meters
    search_speed = Column(String(20))  # "fast" or "thorough"
    search_target = Column(String(100))  # What to search for (person, debris, etc.)
    recording_mode = Column(String(20))  # "continuous" or "event_triggered"

    # Operational data
    assigned_drone_count = Column(Integer, default=0)
    estimated_duration = Column(Integer)  # Estimated duration in minutes
    actual_duration = Column(Integer)  # Actual duration in minutes
    coverage_percentage = Column(Float, default=0.0)

    # Mission context and AI parameters
    mission_context = Column(JSON)  # Complete mission context for drones
    ai_confidence = Column(Float)  # AI confidence in mission plan (0-1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    drone_assignments = relationship("DroneAssignment", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    chat_history = relationship("ChatMessage", back_populates="mission")

    def to_dict(self):
        """Convert mission to dictionary for API responses."""
        return {
            "id": str(self.id),
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

class DroneAssignment(Base):
    """
    Tracks which drones are assigned to which missions and their specific areas.
    """
    __tablename__ = "drone_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    drone_id = Column(String(50), ForeignKey("drones.id"), nullable=False)

    # Assigned search area for this drone
    assigned_area = Column(JSON)  # GeoJSON polygon for this drone's search area
    navigation_waypoints = Column(JSON)  # GPS waypoints to reach search area

    # Mission parameters specific to this drone
    priority_level = Column(Integer, default=1)  # 1=normal, 2=high, 3=critical
    estimated_coverage_time = Column(Integer)  # Minutes to cover assigned area

    # Status tracking
    status = Column(String(50), default="assigned")  # assigned, navigating, searching, completed
    progress_percentage = Column(Float, default=0.0)

    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    mission = relationship("Mission", back_populates="drone_assignments")
    drone = relationship("Drone", back_populates="mission_assignments")

class ChatMessage(Base):
    """
    Stores conversational mission planning dialogue between user and AI.
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)

    # Message content
    sender = Column(String(10), nullable=False)  # "user" or "ai"
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, question, confirmation, etc.

    # AI-specific data
    ai_confidence = Column(Float)  # AI confidence in its response (0-1)
    processing_time = Column(Float)  # Time taken to generate response (seconds)

    # Context and attachments
    attachments = Column(JSON)  # Map updates, mission previews, etc.
    conversation_context = Column(JSON)  # Conversation state at time of message

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mission = relationship("Mission", back_populates="chat_history")