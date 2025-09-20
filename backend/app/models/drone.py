"""
Drone data models for the SAR drone system
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DroneStatus(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    ACTIVE = "active"
    RETURNING = "returning"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class DroneType(str, Enum):
    QUADCOPTER = "quadcopter"
    FIXED_WING = "fixed_wing"
    HYBRID = "hybrid"
    CUSTOM = "custom"

class HealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class DroneCapabilities(BaseModel):
    """Drone capabilities and specifications"""
    max_flight_time_minutes: float = Field(..., description="Maximum flight time in minutes")
    max_speed_ms: float = Field(..., description="Maximum speed in m/s")
    max_altitude_m: float = Field(..., description="Maximum altitude in meters")
    camera_resolution: Optional[str] = Field(None, description="Camera resolution")
    has_thermal_camera: bool = Field(default=False)
    has_lidar: bool = Field(default=False)
    has_gps: bool = Field(default=True)
    payload_capacity_kg: float = Field(default=0.0, description="Payload capacity in kg")
    weather_resistance: str = Field(default="basic", description="Weather resistance level")

class TelemetryData(BaseModel):
    """Real-time telemetry data from drone"""
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: float
    speed_ms: float
    heading_deg: float
    battery_percent: float
    signal_strength: int = Field(..., ge=0, le=100)
    gps_satellites: int
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None

class DroneHealth(BaseModel):
    """Drone health assessment"""
    overall_status: HealthStatus
    battery_health: int = Field(..., ge=0, le=100)
    motor_health: int = Field(..., ge=0, le=100)
    sensor_health: int = Field(..., ge=0, le=100)
    communication_health: int = Field(..., ge=0, le=100)
    last_maintenance: Optional[datetime] = None
    next_maintenance_due: Optional[datetime] = None
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class DroneCommand(BaseModel):
    """Command to send to drone"""
    command_type: str = Field(..., description="Type of command")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)
    timeout_seconds: int = Field(default=30)

# SQLAlchemy Models
class Drone(Base):
    __tablename__ = "drones"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    drone_type = Column(String, nullable=False)
    status = Column(String, default=DroneStatus.OFFLINE)
    
    # Network information
    ip_address = Column(String)
    port = Column(Integer)
    mac_address = Column(String)
    
    # Capabilities
    capabilities = Column(JSON)
    
    # Current state
    current_mission_id = Column(String)
    last_telemetry = Column(JSON)
    health_status = Column(JSON)
    
    # Metadata
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    firmware_version = Column(String)
    hardware_version = Column(String)
    
    # Statistics
    total_flight_time_minutes = Column(Float, default=0.0)
    total_missions = Column(Integer, default=0)
    successful_missions = Column(Integer, default=0)

# Pydantic Models for API
class DroneRegister(BaseModel):
    drone_id: str = Field(..., description="Unique drone identifier")
    name: str = Field(..., description="Human-readable drone name")
    drone_type: DroneType
    ip_address: Optional[str] = None
    port: Optional[int] = None
    mac_address: Optional[str] = None
    capabilities: DroneCapabilities
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None

class DroneUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[DroneStatus] = None
    capabilities: Optional[DroneCapabilities] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None

class DroneResponse(BaseModel):
    id: int
    drone_id: str
    name: str
    drone_type: DroneType
    status: DroneStatus
    ip_address: Optional[str]
    port: Optional[int]
    mac_address: Optional[str]
    capabilities: Optional[DroneCapabilities]
    current_mission_id: Optional[str]
    last_telemetry: Optional[TelemetryData]
    health_status: Optional[DroneHealth]
    registered_at: datetime
    last_seen: datetime
    firmware_version: Optional[str]
    hardware_version: Optional[str]
    total_flight_time_minutes: float
    total_missions: int
    successful_missions: int

    class Config:
        from_attributes = True

class DroneListResponse(BaseModel):
    drones: List[DroneResponse]
    total: int
    page: int
    per_page: int
    pages: int

class TelemetryResponse(BaseModel):
    drone_id: str
    telemetry: TelemetryData
    received_at: datetime

class HealthCheckResponse(BaseModel):
    drone_id: str
    health: DroneHealth
    checked_at: datetime

class CommandResponse(BaseModel):
    command_id: str
    drone_id: str
    command: DroneCommand
    status: str
    sent_at: datetime
    response: Optional[Dict[str, Any]] = None