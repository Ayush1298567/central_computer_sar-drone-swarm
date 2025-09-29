"""
Mission models for SAR Mission Commander
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base

class MissionStatus(enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MissionType(enum.Enum):
    SEARCH = "search"
    RESCUE = "rescue"
    SURVEY = "survey"
    TRAINING = "training"

class MissionPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Mission(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    status = Column(Enum(MissionStatus), default=MissionStatus.PLANNING)
    mission_type = Column(Enum(MissionType), default=MissionType.SEARCH)
    priority = Column(Enum(MissionPriority), default=MissionPriority.MEDIUM)

    # Location data
    search_area = Column(Text)  # JSON string of coordinates
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    altitude = Column(Float, default=100.0)  # meters
    radius = Column(Float, default=1000.0)  # meters

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Mission parameters
    weather_conditions = Column(Text)  # JSON string
    time_limit_minutes = Column(Integer, default=120)
    max_drones = Column(Integer, default=5)

    # Results
    discoveries_found = Column(Integer, default=0)
    area_covered = Column(Float, default=0.0)  # square meters

    # Relationships
    chat_session_id = Column(String, ForeignKey("chat_sessions.id"))
    chat_session = relationship("ChatSession", back_populates="mission")
    drones = relationship("Drone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")