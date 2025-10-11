"""
Pydantic schemas for API request/response models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Drone schemas
class DroneBase(BaseModel):
    """Base drone schema."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    drone_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=50)
    max_flight_time: int = Field(..., gt=0)
    max_altitude: float = Field(..., gt=0)
    max_speed: Optional[float] = Field(None, gt=0)
    cruise_speed: float = Field(default=10.0, gt=0)
    max_range: float = Field(default=5000.0, gt=0)
    coverage_rate: float = Field(default=0.1, gt=0)
    capabilities: Optional[Dict[str, Any]] = None


class DroneCreate(DroneBase):
    """Schema for creating a drone."""
    pass


class DroneUpdate(BaseModel):
    """Schema for updating a drone."""
    model_config = ConfigDict(protected_namespaces=())
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None
    connection_status: Optional[str] = None
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    position_lat: Optional[float] = None
    position_lng: Optional[float] = None
    position_alt: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None
    is_active: Optional[bool] = None
    serial_number: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    max_flight_time: Optional[int] = Field(None, gt=0)
    max_altitude: Optional[float] = Field(None, gt=0)
    max_speed: Optional[float] = Field(None, gt=0)
    cruise_speed: Optional[float] = Field(None, gt=0)
    max_range: Optional[float] = Field(None, gt=0)
    coverage_rate: Optional[float] = Field(None, gt=0)
    signal_strength: Optional[int] = None
    ip_address: Optional[str] = None
    flight_controller: Optional[str] = None


class DroneResponse(DroneBase):
    """Schema for drone responses."""
    id: int
    status: str
    connection_status: str
    battery_level: float
    position_lat: Optional[float]
    position_lng: Optional[float]
    position_alt: Optional[float]
    heading: float
    speed: float
    altitude: float
    is_active: bool
    serial_number: Optional[str]
    cruise_speed: Optional[float] = None
    max_range: Optional[float] = None
    coverage_rate: Optional[float] = None
    signal_strength: Optional[int] = None
    last_heartbeat: Optional[datetime]
    ip_address: Optional[str]
    flight_controller: Optional[str]
    total_flight_hours: Optional[float] = None
    missions_completed: Optional[int] = None
    average_performance_score: Optional[float] = None
    last_maintenance: Optional[datetime]
    next_maintenance_due: Optional[datetime]
    maintenance_notes: Optional[str]
    first_connected: Optional[datetime] = None
    last_seen: Optional[datetime]


# Mission schemas
class MissionBase(BaseModel):
    """Base mission schema."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: str = Field(default="medium")
    search_area: Dict[str, Any]  # GeoJSON-like structure
    estimated_duration: Optional[int] = None
    weather_conditions: Optional[Dict[str, Any]] = None


class MissionCreate(MissionBase):
    """Schema for creating a mission."""
    pass


class MissionUpdate(BaseModel):
    """Schema for updating a mission."""
    model_config = ConfigDict(protected_namespaces=())
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    search_area: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None
    weather_conditions: Optional[Dict[str, Any]] = None


class MissionResponse(MissionBase):
    """Schema for mission responses."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    progress_percentage: Optional[float] = None


# Discovery schemas
class DiscoveryBase(BaseModel):
    """Base discovery schema."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    mission_id: int
    drone_id: int
    discovery_type: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(..., ge=0, le=100)
    location_lat: float
    location_lng: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    priority: str = Field(default="medium")


class DiscoveryCreate(DiscoveryBase):
    """Schema for creating a discovery."""
    pass


class DiscoveryUpdate(BaseModel):
    """Schema for updating a discovery."""
    model_config = ConfigDict(protected_namespaces=())
    discovery_type: Optional[str] = Field(None, min_length=1, max_length=50)
    confidence: Optional[float] = Field(None, ge=0, le=100)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    investigation_notes: Optional[str] = None


class DiscoveryResponse(DiscoveryBase):
    """Schema for discovery responses."""
    id: int
    status: str
    investigation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# Chat schemas
class ChatMessage(BaseModel):
    """Schema for chat messages."""
    model_config = ConfigDict(protected_namespaces=())
    session_id: str
    message: str
    message_type: str = Field(default="user")  # user, assistant, system
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat responses."""
    model_config = ConfigDict(protected_namespaces=())
    session_id: str
    message: str
    message_type: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# Analytics schemas
class AnalyticsData(BaseModel):
    """Schema for analytics data."""
    model_config = ConfigDict(protected_namespaces=())
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    """Schema for analytics responses."""
    model_config = ConfigDict(protected_namespaces=())
    data: List[AnalyticsData]
    summary: Dict[str, Any]


# Weather schemas
class WeatherData(BaseModel):
    """Schema for weather data."""
    model_config = ConfigDict(protected_namespaces=())
    location_lat: float
    location_lng: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    conditions: Optional[str] = None
    timestamp: datetime


# Task schemas
class TaskBase(BaseModel):
    """Base task schema."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    mission_id: int
    drone_id: int
    task_type: str
    description: str
    priority: str = Field(default="medium")
    coordinates: Dict[str, float]  # lat, lng
    estimated_duration: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    model_config = ConfigDict(protected_namespaces=())
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    estimated_duration: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema for task responses."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
