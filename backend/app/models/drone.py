"""
Drone database models.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base

class DroneStatus(enum.Enum):
    """Drone operational status."""
    OFFLINE = "offline"
    IDLE = "idle"
    PREFLIGHT = "preflight"
    ACTIVE = "active"
    RETURNING = "returning"
    LANDING = "landing"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    EMERGENCY = "emergency"

class DroneType(enum.Enum):
    """Types of drones in the fleet."""
    QUADCOPTER = "quadcopter"
    HEXACOPTER = "hexacopter"
    OCTOCOPTER = "octocopter"
    FIXED_WING = "fixed_wing"
    HYBRID = "hybrid"

class Drone(Base):
    """Drone model representing individual aircraft."""
    
    __tablename__ = "drones"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    
    # Drone specifications
    drone_type = Column(SQLEnum(DroneType), nullable=False)
    manufacturer = Column(String(100))
    firmware_version = Column(String(50))
    
    # Current status
    status = Column(SQLEnum(DroneStatus), default=DroneStatus.OFFLINE, nullable=False)
    last_seen = Column(DateTime(timezone=True))
    last_heartbeat = Column(DateTime(timezone=True))
    
    # Location and movement
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    current_altitude = Column(Float)
    home_latitude = Column(Float)
    home_longitude = Column(Float)
    home_altitude = Column(Float)
    
    # Flight dynamics
    heading_degrees = Column(Float)
    ground_speed_ms = Column(Float)
    vertical_speed_ms = Column(Float)
    wind_speed_ms = Column(Float)
    wind_direction_degrees = Column(Float)
    
    # Power and battery
    battery_percentage = Column(Float)
    battery_voltage = Column(Float)
    battery_current = Column(Float)
    battery_temperature = Column(Float)
    remaining_flight_time_minutes = Column(Float)
    
    # Mission assignment
    assigned_mission_id = Column(String(50))
    current_task = Column(String(200))
    task_progress_percentage = Column(Float, default=0.0)
    
    # Capabilities and equipment
    capabilities = Column(JSON)  # DroneCapabilities as JSON
    payload_weight_kg = Column(Float)
    max_payload_kg = Column(Float)
    
    # Performance metrics
    total_flight_hours = Column(Float, default=0.0)
    total_missions = Column(Integer, default=0)
    successful_missions = Column(Integer, default=0)
    
    # Health and maintenance
    health_score = Column(Float, default=1.0)  # 0.0 to 1.0
    maintenance_due = Column(Boolean, default=False)
    last_maintenance = Column(DateTime(timezone=True))
    next_maintenance = Column(DateTime(timezone=True))
    
    # Communication
    signal_strength = Column(Float)  # dBm
    data_link_quality = Column(Float)  # 0.0 to 1.0
    video_link_quality = Column(Float)  # 0.0 to 1.0
    
    # Environmental sensors
    ambient_temperature = Column(Float)
    humidity_percentage = Column(Float)
    barometric_pressure = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    activated_at = Column(DateTime(timezone=True))
    
    # Error tracking
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    critical_alerts = Column(JSON)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert drone to dictionary."""
        return {
            "id": self.id,
            "drone_id": self.drone_id,
            "name": self.name,
            "model": self.model,
            "serial_number": self.serial_number,
            "type": self.drone_type.value if self.drone_type else None,
            "manufacturer": self.manufacturer,
            "firmware_version": self.firmware_version,
            "status": {
                "current": self.status.value if self.status else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
            },
            "location": {
                "current": {
                    "latitude": self.current_latitude,
                    "longitude": self.current_longitude,
                    "altitude": self.current_altitude
                } if self.current_latitude and self.current_longitude else None,
                "home": {
                    "latitude": self.home_latitude,
                    "longitude": self.home_longitude,
                    "altitude": self.home_altitude
                } if self.home_latitude and self.home_longitude else None
            },
            "flight_dynamics": {
                "heading_degrees": self.heading_degrees,
                "ground_speed_ms": self.ground_speed_ms,
                "vertical_speed_ms": self.vertical_speed_ms,
                "wind_speed_ms": self.wind_speed_ms,
                "wind_direction_degrees": self.wind_direction_degrees
            },
            "power": {
                "battery_percentage": self.battery_percentage,
                "battery_voltage": self.battery_voltage,
                "battery_current": self.battery_current,
                "battery_temperature": self.battery_temperature,
                "remaining_flight_time_minutes": self.remaining_flight_time_minutes
            },
            "mission": {
                "assigned_mission_id": self.assigned_mission_id,
                "current_task": self.current_task,
                "task_progress_percentage": self.task_progress_percentage
            },
            "capabilities": self.capabilities or {},
            "payload": {
                "current_weight_kg": self.payload_weight_kg,
                "max_weight_kg": self.max_payload_kg
            },
            "performance": {
                "total_flight_hours": self.total_flight_hours,
                "total_missions": self.total_missions,
                "successful_missions": self.successful_missions,
                "success_rate": self.successful_missions / max(1, self.total_missions) if self.total_missions else 0
            },
            "health": {
                "score": self.health_score,
                "maintenance_due": self.maintenance_due,
                "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None,
                "next_maintenance": self.next_maintenance.isoformat() if self.next_maintenance else None
            },
            "communication": {
                "signal_strength": self.signal_strength,
                "data_link_quality": self.data_link_quality,
                "video_link_quality": self.video_link_quality
            },
            "environment": {
                "temperature": self.ambient_temperature,
                "humidity": self.humidity_percentage,
                "pressure": self.barometric_pressure
            },
            "errors": {
                "last_error": self.last_error,
                "error_count": self.error_count,
                "critical_alerts": self.critical_alerts or []
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "activated_at": self.activated_at.isoformat() if self.activated_at else None
            }
        }
    
    def update_location(self, latitude: float, longitude: float, altitude: float):
        """Update drone location."""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.current_altitude = altitude
        self.last_seen = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_battery(self, percentage: float, voltage: float = None, current: float = None):
        """Update battery information."""
        self.battery_percentage = max(0.0, min(100.0, percentage))
        if voltage is not None:
            self.battery_voltage = voltage
        if current is not None:
            self.battery_current = current
        self.updated_at = datetime.utcnow()
    
    def set_mission(self, mission_id: str, task: str = None):
        """Assign drone to a mission."""
        self.assigned_mission_id = mission_id
        self.current_task = task
        self.task_progress_percentage = 0.0
        self.updated_at = datetime.utcnow()
    
    def clear_mission(self):
        """Clear mission assignment."""
        self.assigned_mission_id = None
        self.current_task = None
        self.task_progress_percentage = 0.0
        self.updated_at = datetime.utcnow()
    
    def add_flight_time(self, hours: float):
        """Add flight time to total."""
        self.total_flight_hours += hours
        self.updated_at = datetime.utcnow()
    
    def complete_mission(self, successful: bool = True):
        """Mark mission as completed."""
        self.total_missions += 1
        if successful:
            self.successful_missions += 1
        self.clear_mission()
    
    def is_available(self) -> bool:
        """Check if drone is available for assignment."""
        return self.status in [DroneStatus.IDLE] and not self.maintenance_due
    
    def is_operational(self) -> bool:
        """Check if drone is operational."""
        return self.status not in [DroneStatus.OFFLINE, DroneStatus.MAINTENANCE, DroneStatus.ERROR, DroneStatus.EMERGENCY]
    
    def needs_maintenance(self) -> bool:
        """Check if drone needs maintenance."""
        return self.maintenance_due or self.health_score < 0.7
    
    def get_distance_from_home(self) -> Optional[float]:
        """Calculate distance from home position in meters."""
        if not all([self.current_latitude, self.current_longitude, 
                   self.home_latitude, self.home_longitude]):
            return None
        
        # Simple haversine distance calculation
        import math
        
        lat1, lon1 = math.radians(self.current_latitude), math.radians(self.current_longitude)
        lat2, lon2 = math.radians(self.home_latitude), math.radians(self.home_longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        
        return c * r

class DroneCapabilities(Base):
    """Detailed drone capabilities and equipment specifications."""
    
    __tablename__ = "drone_capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(50), index=True, nullable=False)
    
    # Flight capabilities
    max_speed_ms = Column(Float, default=15.0)
    max_altitude_m = Column(Float, default=500.0)
    max_flight_time_minutes = Column(Float, default=30.0)
    max_range_km = Column(Float, default=5.0)
    wind_resistance_ms = Column(Float, default=10.0)
    
    # Camera capabilities
    has_camera = Column(Boolean, default=True)
    camera_resolution = Column(String(20))  # e.g., "4K", "1080p"
    camera_zoom = Column(Float, default=1.0)
    has_gimbal = Column(Boolean, default=True)
    gimbal_range_degrees = Column(Float, default=180.0)
    
    # Imaging modes
    has_thermal_camera = Column(Boolean, default=False)
    has_night_vision = Column(Boolean, default=False)
    has_multispectral = Column(Boolean, default=False)
    has_lidar = Column(Boolean, default=False)
    
    # AI and processing
    has_onboard_ai = Column(Boolean, default=False)
    ai_processing_power = Column(String(50))  # e.g., "NVIDIA Jetson"
    object_detection = Column(Boolean, default=False)
    face_recognition = Column(Boolean, default=False)
    
    # Communication
    communication_range_km = Column(Float, default=2.0)
    has_mesh_networking = Column(Boolean, default=False)
    has_satellite_comm = Column(Boolean, default=False)
    video_streaming_quality = Column(String(20), default="1080p")
    
    # Navigation and positioning
    gps_accuracy_m = Column(Float, default=3.0)
    has_rtk_gps = Column(Boolean, default=False)
    has_obstacle_avoidance = Column(Boolean, default=True)
    autonomous_flight = Column(Boolean, default=True)
    
    # Environmental resistance
    waterproof_rating = Column(String(10))  # e.g., "IP65"
    operating_temp_min = Column(Float, default=-10.0)
    operating_temp_max = Column(Float, default=50.0)
    
    # Payload and attachments
    payload_bay_volume_cm3 = Column(Float)
    has_cargo_release = Column(Boolean, default=False)
    has_spotlight = Column(Boolean, default=False)
    has_speaker = Column(Boolean, default=False)
    
    # Special features
    special_features = Column(JSON)  # List of special capabilities
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to dictionary."""
        return {
            "drone_id": self.drone_id,
            "flight": {
                "max_speed_ms": self.max_speed_ms,
                "max_altitude_m": self.max_altitude_m,
                "max_flight_time_minutes": self.max_flight_time_minutes,
                "max_range_km": self.max_range_km,
                "wind_resistance_ms": self.wind_resistance_ms
            },
            "camera": {
                "has_camera": self.has_camera,
                "resolution": self.camera_resolution,
                "zoom": self.camera_zoom,
                "has_gimbal": self.has_gimbal,
                "gimbal_range_degrees": self.gimbal_range_degrees
            },
            "imaging": {
                "thermal": self.has_thermal_camera,
                "night_vision": self.has_night_vision,
                "multispectral": self.has_multispectral,
                "lidar": self.has_lidar
            },
            "ai": {
                "onboard_processing": self.has_onboard_ai,
                "processing_power": self.ai_processing_power,
                "object_detection": self.object_detection,
                "face_recognition": self.face_recognition
            },
            "communication": {
                "range_km": self.communication_range_km,
                "mesh_networking": self.has_mesh_networking,
                "satellite_comm": self.has_satellite_comm,
                "video_quality": self.video_streaming_quality
            },
            "navigation": {
                "gps_accuracy_m": self.gps_accuracy_m,
                "rtk_gps": self.has_rtk_gps,
                "obstacle_avoidance": self.has_obstacle_avoidance,
                "autonomous_flight": self.autonomous_flight
            },
            "environmental": {
                "waterproof_rating": self.waterproof_rating,
                "operating_temp_range": {
                    "min": self.operating_temp_min,
                    "max": self.operating_temp_max
                }
            },
            "payload": {
                "bay_volume_cm3": self.payload_bay_volume_cm3,
                "cargo_release": self.has_cargo_release,
                "spotlight": self.has_spotlight,
                "speaker": self.has_speaker
            },
            "special_features": self.special_features or []
        }
    
    def is_suitable_for_mission(self, mission_requirements: Dict[str, Any]) -> bool:
        """Check if drone capabilities meet mission requirements."""
        # Check flight requirements
        if mission_requirements.get("max_altitude", 0) > self.max_altitude_m:
            return False
        
        if mission_requirements.get("flight_time", 0) > self.max_flight_time_minutes:
            return False
        
        if mission_requirements.get("range", 0) > self.max_range_km:
            return False
        
        # Check imaging requirements
        if mission_requirements.get("thermal_imaging", False) and not self.has_thermal_camera:
            return False
        
        if mission_requirements.get("night_vision", False) and not self.has_night_vision:
            return False
        
        # Check AI requirements
        if mission_requirements.get("object_detection", False) and not self.object_detection:
            return False
        
        return True
    
    def get_capability_score(self, mission_requirements: Dict[str, Any]) -> float:
        """Calculate capability match score for mission requirements (0.0 to 1.0)."""
        score = 0.0
        total_weight = 0.0
        
        # Flight capability scoring
        if "max_altitude" in mission_requirements:
            weight = 0.2
            total_weight += weight
            if self.max_altitude_m >= mission_requirements["max_altitude"]:
                score += weight
        
        if "flight_time" in mission_requirements:
            weight = 0.2
            total_weight += weight
            if self.max_flight_time_minutes >= mission_requirements["flight_time"]:
                score += weight
        
        if "range" in mission_requirements:
            weight = 0.15
            total_weight += weight
            if self.max_range_km >= mission_requirements["range"]:
                score += weight
        
        # Imaging capability scoring
        imaging_features = ["thermal_imaging", "night_vision", "multispectral"]
        for feature in imaging_features:
            if mission_requirements.get(feature, False):
                weight = 0.15
                total_weight += weight
                if getattr(self, f"has_{feature.replace('_imaging', '_camera')}", False):
                    score += weight
        
        # AI capability scoring
        if mission_requirements.get("object_detection", False):
            weight = 0.1
            total_weight += weight
            if self.object_detection:
                score += weight
        
        return score / max(total_weight, 1.0)