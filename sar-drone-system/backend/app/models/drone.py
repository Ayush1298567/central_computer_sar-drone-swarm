"""
Drone model for fleet management
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum, Boolean
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class DroneStatus(enum.Enum):
    IDLE = "idle"
    CHARGING = "charging"
    READY = "ready"
    IN_FLIGHT = "in_flight"
    LANDING = "landing"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"


class DroneType(enum.Enum):
    SEARCH = "search"
    DELIVERY = "delivery"
    SURVEILLANCE = "surveillance"
    MULTI_PURPOSE = "multi_purpose"


class Drone(Base):
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    drone_type = Column(Enum(DroneType), nullable=False)
    status = Column(Enum(DroneStatus), default=DroneStatus.IDLE)
    
    # Physical specifications
    max_flight_time = Column(Integer, default=30)  # minutes
    max_speed = Column(Float, default=50.0)  # km/h
    max_altitude = Column(Float, default=120.0)  # meters
    payload_capacity = Column(Float, default=2.0)  # kg
    
    # Current status
    battery_level = Column(Float, default=100.0)  # percentage
    current_location = Column(JSON)  # {"lat": 0, "lng": 0, "altitude": 0}
    assigned_mission_id = Column(Integer, default=None)
    
    # Capabilities
    has_camera = Column(Boolean, default=True)
    has_thermal_camera = Column(Boolean, default=False)
    has_gps = Column(Boolean, default=True)
    has_autopilot = Column(Boolean, default=True)
    
    # Performance metrics
    total_flight_time = Column(Integer, default=0)  # minutes
    total_missions = Column(Integer, default=0)
    last_maintenance = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))
    
    # Configuration
    configuration = Column(JSON, default=dict)  # Custom settings
    health_status = Column(JSON, default=dict)  # System health data

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "drone_type": self.drone_type.value if self.drone_type else None,
            "status": self.status.value if self.status else None,
            "max_flight_time": self.max_flight_time,
            "max_speed": self.max_speed,
            "max_altitude": self.max_altitude,
            "payload_capacity": self.payload_capacity,
            "battery_level": self.battery_level,
            "current_location": self.current_location,
            "assigned_mission_id": self.assigned_mission_id,
            "has_camera": self.has_camera,
            "has_thermal_camera": self.has_thermal_camera,
            "has_gps": self.has_gps,
            "has_autopilot": self.has_autopilot,
            "total_flight_time": self.total_flight_time,
            "total_missions": self.total_missions,
            "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "configuration": self.configuration,
            "health_status": self.health_status
        }

    def is_available(self):
        """Check if drone is available for assignment"""
        return self.status in [DroneStatus.IDLE, DroneStatus.READY] and self.battery_level > 20

    def can_handle_mission(self, mission):
        """Check if drone can handle the given mission"""
        if not self.is_available():
            return False
        
        # Check flight time
        if mission.max_flight_time > self.max_flight_time:
            return False
            
        # Check altitude requirements
        if mission.search_altitude > self.max_altitude:
            return False
            
        return True