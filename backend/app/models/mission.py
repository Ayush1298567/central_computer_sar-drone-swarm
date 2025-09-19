"""
Mission database models.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base

class MissionStatus(enum.Enum):
    """Mission status enumeration."""
    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"

class MissionPriority(enum.Enum):
    """Mission priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Mission(Base):
    """Mission model representing SAR operations."""
    
    __tablename__ = "missions"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Mission status and timing
    status = Column(SQLEnum(MissionStatus), default=MissionStatus.PLANNING, nullable=False)
    priority = Column(SQLEnum(MissionPriority), default=MissionPriority.MEDIUM, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Mission parameters (stored as JSON for flexibility)
    parameters = Column(JSON, nullable=False)
    
    # Search area information
    search_area_name = Column(String(200))
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    area_size_km2 = Column(Float)
    boundary_coordinates = Column(JSON)  # GeoJSON polygon
    
    # Target information
    target_description = Column(Text)
    target_type = Column(String(100))
    last_known_latitude = Column(Float)
    last_known_longitude = Column(Float)
    last_known_timestamp = Column(DateTime(timezone=True))
    
    # Resource allocation
    assigned_drones = Column(JSON)  # List of drone IDs
    num_drones = Column(Integer, default=1)
    search_altitude = Column(Float, default=100.0)
    
    # Environmental conditions
    weather_conditions = Column(JSON)
    terrain_type = Column(String(100))
    visibility_km = Column(Float)
    wind_speed_ms = Column(Float)
    
    # Mission constraints
    max_duration_hours = Column(Float, default=4.0)
    battery_reserve_percentage = Column(Float, default=25.0)
    max_wind_speed_ms = Column(Float, default=15.0)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    area_covered_km2 = Column(Float, default=0.0)
    flight_time_minutes = Column(Float, default=0.0)
    
    # AI and automation
    ai_recommendations = Column(JSON)
    autonomous_decisions = Column(JSON)
    conversation_history = Column(JSON)
    
    # Results and outcomes
    discoveries_count = Column(Integer, default=0)
    success_rating = Column(Float)  # 0.0 to 1.0
    lessons_learned = Column(JSON)
    
    # Contact information
    operator_name = Column(String(200))
    operator_contact = Column(String(200))
    emergency_contact = Column(String(200))
    
    # Relationships
    # discoveries = relationship("Discovery", back_populates="mission")
    # learning_entries = relationship("AILearningEntry", back_populates="mission")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mission to dictionary."""
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parameters": self.parameters or {},
            "search_area": {
                "name": self.search_area_name,
                "center": {
                    "latitude": self.center_latitude,
                    "longitude": self.center_longitude
                } if self.center_latitude and self.center_longitude else None,
                "size_km2": self.area_size_km2,
                "boundary": self.boundary_coordinates
            },
            "target": {
                "description": self.target_description,
                "type": self.target_type,
                "last_known_location": {
                    "latitude": self.last_known_latitude,
                    "longitude": self.last_known_longitude,
                    "timestamp": self.last_known_timestamp.isoformat() if self.last_known_timestamp else None
                } if self.last_known_latitude and self.last_known_longitude else None
            },
            "resources": {
                "assigned_drones": self.assigned_drones or [],
                "num_drones": self.num_drones,
                "search_altitude": self.search_altitude
            },
            "environment": {
                "weather_conditions": self.weather_conditions or {},
                "terrain_type": self.terrain_type,
                "visibility_km": self.visibility_km,
                "wind_speed_ms": self.wind_speed_ms
            },
            "constraints": {
                "max_duration_hours": self.max_duration_hours,
                "battery_reserve_percentage": self.battery_reserve_percentage,
                "max_wind_speed_ms": self.max_wind_speed_ms
            },
            "progress": {
                "percentage": self.progress_percentage,
                "area_covered_km2": self.area_covered_km2,
                "flight_time_minutes": self.flight_time_minutes,
                "discoveries_count": self.discoveries_count
            },
            "ai_data": {
                "recommendations": self.ai_recommendations or {},
                "autonomous_decisions": self.autonomous_decisions or [],
                "conversation_history": self.conversation_history or []
            },
            "results": {
                "success_rating": self.success_rating,
                "lessons_learned": self.lessons_learned or []
            },
            "contacts": {
                "operator_name": self.operator_name,
                "operator_contact": self.operator_contact,
                "emergency_contact": self.emergency_contact
            }
        }
    
    def update_progress(self, percentage: float, area_covered: float = None, flight_time: float = None):
        """Update mission progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        if area_covered is not None:
            self.area_covered_km2 = area_covered
        if flight_time is not None:
            self.flight_time_minutes = flight_time
        self.updated_at = datetime.utcnow()
    
    def add_discovery(self):
        """Increment discovery count."""
        self.discoveries_count += 1
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if mission is currently active."""
        return self.status == MissionStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if mission is completed."""
        return self.status in [MissionStatus.COMPLETED, MissionStatus.ABORTED, MissionStatus.FAILED]
    
    def get_duration_hours(self) -> Optional[float]:
        """Get mission duration in hours."""
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return duration.total_seconds() / 3600
        elif self.started_at:
            duration = datetime.utcnow() - self.started_at
            return duration.total_seconds() / 3600
        return None
    
    def get_efficiency_score(self) -> Optional[float]:
        """Calculate mission efficiency score."""
        if not self.area_covered_km2 or not self.flight_time_minutes:
            return None
        
        # Simple efficiency: area covered per flight hour
        flight_hours = self.flight_time_minutes / 60
        if flight_hours > 0:
            return self.area_covered_km2 / flight_hours
        return None

class MissionParameters(Base):
    """Detailed mission parameters model for complex configurations."""
    
    __tablename__ = "mission_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String(50), index=True, nullable=False)
    
    # Search pattern configuration
    search_pattern_type = Column(String(50), default="grid")  # grid, spiral, random, adaptive
    overlap_percentage = Column(Float, default=20.0)
    flight_speed_ms = Column(Float, default=10.0)
    camera_angle_degrees = Column(Float, default=-90.0)  # Gimbal angle
    
    # Image capture settings
    image_interval_seconds = Column(Float, default=2.0)
    image_resolution = Column(String(20), default="4K")
    image_format = Column(String(10), default="JPEG")
    enable_raw_capture = Column(Boolean, default=False)
    
    # Video recording settings
    enable_video_recording = Column(Boolean, default=True)
    video_resolution = Column(String(20), default="1080p")
    video_bitrate_mbps = Column(Float, default=10.0)
    
    # AI processing settings
    enable_realtime_ai = Column(Boolean, default=True)
    ai_confidence_threshold = Column(Float, default=0.7)
    object_detection_classes = Column(JSON)  # List of classes to detect
    
    # Communication settings
    telemetry_interval_seconds = Column(Float, default=1.0)
    video_stream_quality = Column(String(20), default="medium")
    enable_mesh_networking = Column(Boolean, default=True)
    
    # Safety settings
    return_to_home_battery = Column(Float, default=20.0)
    max_altitude_agl = Column(Float, default=120.0)  # Above ground level
    geofence_enabled = Column(Boolean, default=True)
    geofence_coordinates = Column(JSON)
    
    # Weather thresholds
    max_wind_gusts_ms = Column(Float, default=20.0)
    min_visibility_m = Column(Float, default=1000.0)
    max_precipitation_mm = Column(Float, default=5.0)
    
    # Advanced settings
    adaptive_altitude = Column(Boolean, default=False)
    terrain_following = Column(Boolean, default=False)
    night_vision_mode = Column(Boolean, default=False)
    thermal_imaging = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary."""
        return {
            "mission_id": self.mission_id,
            "search_pattern": {
                "type": self.search_pattern_type,
                "overlap_percentage": self.overlap_percentage,
                "flight_speed_ms": self.flight_speed_ms,
                "camera_angle_degrees": self.camera_angle_degrees
            },
            "imaging": {
                "image_interval_seconds": self.image_interval_seconds,
                "image_resolution": self.image_resolution,
                "image_format": self.image_format,
                "enable_raw_capture": self.enable_raw_capture,
                "enable_video_recording": self.enable_video_recording,
                "video_resolution": self.video_resolution,
                "video_bitrate_mbps": self.video_bitrate_mbps
            },
            "ai_processing": {
                "enable_realtime_ai": self.enable_realtime_ai,
                "confidence_threshold": self.ai_confidence_threshold,
                "detection_classes": self.object_detection_classes or []
            },
            "communication": {
                "telemetry_interval_seconds": self.telemetry_interval_seconds,
                "video_stream_quality": self.video_stream_quality,
                "enable_mesh_networking": self.enable_mesh_networking
            },
            "safety": {
                "return_to_home_battery": self.return_to_home_battery,
                "max_altitude_agl": self.max_altitude_agl,
                "geofence_enabled": self.geofence_enabled,
                "geofence_coordinates": self.geofence_coordinates or []
            },
            "weather_limits": {
                "max_wind_gusts_ms": self.max_wind_gusts_ms,
                "min_visibility_m": self.min_visibility_m,
                "max_precipitation_mm": self.max_precipitation_mm
            },
            "advanced": {
                "adaptive_altitude": self.adaptive_altitude,
                "terrain_following": self.terrain_following,
                "night_vision_mode": self.night_vision_mode,
                "thermal_imaging": self.thermal_imaging
            }
        }