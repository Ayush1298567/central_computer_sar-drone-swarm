from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from ..core.database import Base


class MissionStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ABORTED = "aborted"


class Mission(Base):
    """Core mission data model representing a search and rescue operation."""
    __tablename__ = "missions"

    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Mission status tracking
    status = Column(String(50), nullable=False, default="planning")
    mission_type = Column(String(50), default="search")
    priority = Column(Integer, default=3)

    # Geographic data
    search_area = Column(JSON)  # GeoJSON polygon
    center_lat = Column(Float)
    center_lng = Column(Float)
    altitude = Column(Float)
    radius = Column(Float)

    # Mission parameters
    search_altitude = Column(Float, default=30.0)
    search_pattern = Column(String(50), default="lawnmower")
    overlap_percentage = Column(Float, default=10.0)

    # Operational data
    max_drones = Column(Integer, default=1)
    estimated_duration = Column(Integer)
    discoveries_count = Column(Integer, default=0)
    area_covered = Column(Float, default=0.0)
    progress_percentage = Column(Float, default=0.0)

    # Weather and timing
    weather_conditions = Column(JSON)
    time_limit_minutes = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    planned_start_time = Column(DateTime)
    planned_end_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)

    # User tracking
    created_by = Column(String(100))
    
    # Relationships
    drone_assignments = relationship("MissionDrone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    chat_sessions = relationship("ChatSession", back_populates="mission")
    
    def to_dict(self):
        """Convert mission to dictionary for API responses."""
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "mission_type": self.mission_type,
            "priority": self.priority,
            "search_area": self.search_area,
            "center_lat": self.center_lat,
            "center_lng": self.center_lng,
            "altitude": self.altitude,
            "radius": self.radius,
            "search_altitude": self.search_altitude,
            "search_pattern": self.search_pattern,
            "overlap_percentage": self.overlap_percentage,
            "max_drones": self.max_drones,
            "estimated_duration": self.estimated_duration,
            "discoveries_count": self.discoveries_count,
            "area_covered": self.area_covered,
            "progress_percentage": self.progress_percentage,
            "weather_conditions": self.weather_conditions,
            "time_limit_minutes": self.time_limit_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "planned_start_time": self.planned_start_time.isoformat() if self.planned_start_time else None,
            "planned_end_time": self.planned_end_time.isoformat() if self.planned_end_time else None,
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_end_time": self.actual_end_time.isoformat() if self.actual_end_time else None,
            "created_by": self.created_by
        }


class MissionDrone(Base):
    """Junction table tracking drone assignments to missions."""
    __tablename__ = "mission_drone"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)

    # Assignment details
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(String(100))
    status = Column(String(50), default="assigned")

    # Area assignment and waypoints
    assigned_area = Column(JSON)
    current_waypoint = Column(JSON)

    # Relationships
    mission = relationship("Mission", back_populates="drone_assignments")
    drone = relationship("Drone", back_populates="mission_assignments")


class MissionLog(Base):
    """Append-only mission log for persistence and recovery."""
    __tablename__ = "mission_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # state_update, discovery, command, error
    message = Column(Text)
    payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

