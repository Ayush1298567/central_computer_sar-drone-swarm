"""
Drone models for SAR Mission Commander
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base

class DroneStatus(enum.Enum):
    AVAILABLE = "available"
    IN_MISSION = "in_mission"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class DroneType(enum.Enum):
    QUADCOPTER = "quadcopter"
    HEXACOPTER = "hexacopter"
    FIXED_WING = "fixed_wing"
    VTOL = "vtol"

class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String, ForeignKey("drones.id"))

    # Position
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    heading = Column(Float)

    # Status
    battery_level = Column(Float)  # percentage
    speed = Column(Float)  # m/s
    signal_strength = Column(Float)  # percentage

    # Environment
    temperature = Column(Float)  # celsius
    wind_speed = Column(Float)  # m/s
    wind_direction = Column(Float)  # degrees

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    drone = relationship("Drone", back_populates="telemetry")

class Drone(Base):
    __tablename__ = "drones"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    model = Column(String)
    status = Column(Enum(DroneStatus), default=DroneStatus.AVAILABLE)
    drone_type = Column(Enum(DroneType), default=DroneType.QUADCOPTER)

    # Capabilities
    max_altitude = Column(Float, default=120.0)  # meters
    max_speed = Column(Float, default=15.0)  # m/s
    battery_capacity = Column(Float, default=5000.0)  # mAh
    camera_resolution = Column(String, default="4K")
    has_thermal = Column(Boolean, default=False)
    has_night_vision = Column(Boolean, default=False)

    # Current mission
    mission_id = Column(String, ForeignKey("missions.id"), nullable=True)

    # Registration
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mission = relationship("Mission", back_populates="drones")
    telemetry = relationship("TelemetryData", back_populates="drone")