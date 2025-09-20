"""
Mission data models for the SAR drone system
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MissionStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"

class MissionType(str, Enum):
    MISSING_PERSON = "missing_person"
    DISASTER_RESPONSE = "disaster_response"
    RECONNAISSANCE = "reconnaissance"
    TRAINING = "training"

class MissionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class SearchArea(BaseModel):
    """Search area definition"""
    center_lat: float = Field(..., description="Center latitude")
    center_lng: float = Field(..., description="Center longitude")
    radius_km: float = Field(..., description="Search radius in kilometers")
    boundaries: Optional[List[Dict[str, float]]] = Field(None, description="Polygon boundaries")
    no_fly_zones: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class MissionRequirements(BaseModel):
    """Mission requirements and constraints"""
    max_duration_hours: Optional[float] = Field(default=4.0)
    min_drone_count: Optional[int] = Field(default=1)
    max_drone_count: Optional[int] = Field(default=10)
    required_sensors: Optional[List[str]] = Field(default_factory=list)
    weather_constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    altitude_constraints: Optional[Dict[str, float]] = Field(default_factory=dict)

class DroneAssignment(BaseModel):
    """Drone assignment for a mission"""
    drone_id: str
    search_zone: Dict[str, Any]
    flight_path: List[Dict[str, float]]
    estimated_duration: float
    priority: int = Field(default=1)

class MissionTimeline(BaseModel):
    """Mission timeline and checkpoints"""
    start_time: datetime
    estimated_end_time: datetime
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)

class MissionPlan(BaseModel):
    """Complete mission plan"""
    mission_id: str
    mission_type: MissionType
    priority: MissionPriority
    search_area: SearchArea
    drone_assignments: List[DroneAssignment]
    timeline: MissionTimeline
    success_probability: float
    risk_assessment: Dict[str, Any]
    created_by: str
    created_at: datetime

# SQLAlchemy Models
class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    mission_type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    status = Column(String, default=MissionStatus.PLANNED)
    
    # Mission parameters
    search_area = Column(JSON)
    requirements = Column(JSON)
    drone_assignments = Column(JSON)
    timeline = Column(JSON)
    
    # Metadata
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    success_probability = Column(Float)
    risk_assessment = Column(JSON)
    actual_results = Column(JSON)

# Pydantic Models for API
class MissionCreate(BaseModel):
    name: str = Field(..., description="Mission name")
    description: Optional[str] = Field(None, description="Mission description")
    mission_type: MissionType
    priority: MissionPriority = Field(default=MissionPriority.NORMAL)
    search_area: SearchArea
    requirements: Optional[MissionRequirements] = Field(default_factory=MissionRequirements)
    created_by: str = Field(..., description="User who created the mission")

class MissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[MissionPriority] = None
    status: Optional[MissionStatus] = None
    requirements: Optional[MissionRequirements] = None

class MissionResponse(BaseModel):
    id: int
    mission_id: str
    name: str
    description: Optional[str]
    mission_type: MissionType
    priority: MissionPriority
    status: MissionStatus
    search_area: SearchArea
    requirements: Optional[MissionRequirements]
    drone_assignments: Optional[List[DroneAssignment]]
    timeline: Optional[MissionTimeline]
    created_by: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    success_probability: Optional[float]
    risk_assessment: Optional[Dict[str, Any]]
    actual_results: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class MissionListResponse(BaseModel):
    missions: List[MissionResponse]
    total: int
    page: int
    per_page: int
    pages: int