"""
Mission model for SAR operations
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class MissionStatus(enum.Enum):
    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class MissionType(enum.Enum):
    MISSING_PERSON = "missing_person"
    EMERGENCY_RESPONSE = "emergency_response"
    SURVEILLANCE = "surveillance"
    DELIVERY = "delivery"
    MAPPING = "mapping"


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mission_type = Column(Enum(MissionType), nullable=False)
    status = Column(Enum(MissionStatus), default=MissionStatus.PLANNING)
    
    # Location and area
    search_area = Column(JSON)  # {"center": {"lat": 0, "lng": 0}, "radius": 1000}
    priority = Column(Integer, default=5)  # 1-10 scale
    
    # Mission parameters
    max_flight_time = Column(Integer, default=30)  # minutes
    search_altitude = Column(Float, default=100.0)  # meters
    weather_thresholds = Column(JSON)  # wind, visibility limits
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Mission data
    assigned_drones = Column(JSON, default=list)  # List of drone IDs
    progress_percentage = Column(Float, default=0.0)
    discovered_objects = Column(JSON, default=list)
    
    # AI planning data
    search_strategy = Column(JSON)  # AI-generated strategy
    risk_assessment = Column(JSON)  # AI risk analysis
    estimated_duration = Column(Integer)  # minutes
    
    # Relationships
    discoveries = relationship("Discovery", back_populates="mission")
    chat_sessions = relationship("ChatSession", back_populates="mission")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mission_type": self.mission_type.value if self.mission_type else None,
            "status": self.status.value if self.status else None,
            "search_area": self.search_area,
            "priority": self.priority,
            "max_flight_time": self.max_flight_time,
            "search_altitude": self.search_altitude,
            "weather_thresholds": self.weather_thresholds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assigned_drones": self.assigned_drones,
            "progress_percentage": self.progress_percentage,
            "discovered_objects": self.discovered_objects,
            "search_strategy": self.search_strategy,
            "risk_assessment": self.risk_assessment,
            "estimated_duration": self.estimated_duration
        }