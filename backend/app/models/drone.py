"""
Drone model definitions.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Drone(Base):
    """Drone model representing a SAR drone."""

    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    model = Column(String(50), nullable=False)
    status = Column(String(20), default="offline", nullable=False)
    battery_level = Column(Float, default=100.0, nullable=False)
    position_lat = Column(Float, nullable=True)
    position_lng = Column(Float, nullable=True)
    position_alt = Column(Float, nullable=True)
    heading = Column(Float, default=0.0, nullable=False)
    speed = Column(Float, default=0.0, nullable=False)
    altitude = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    capabilities = Column(JSON, nullable=True)  # Camera, sensors, etc.
    max_flight_time = Column(Integer, nullable=False)  # minutes
    max_altitude = Column(Float, nullable=False)  # meters
    max_speed = Column(Float, nullable=False)  # m/s
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    missions = relationship("MissionDrone", back_populates="drone")
    telemetry_data = relationship("DroneTelemetry", back_populates="drone")

    def __repr__(self):
        return f"<Drone(id={self.id}, drone_id='{self.drone_id}', name='{self.name}', status='{self.status}')>"


class DroneTelemetry(Base):
    """Drone telemetry data model."""

    __tablename__ = "drone_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    battery_level = Column(Float, nullable=False)
    position_lat = Column(Float, nullable=False)
    position_lng = Column(Float, nullable=False)
    position_alt = Column(Float, nullable=False)
    heading = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    signal_strength = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    sensor_data = Column(JSON, nullable=True)

    # Relationships
    drone = relationship("Drone", back_populates="telemetry_data")

    def __repr__(self):
        return f"<DroneTelemetry(drone_id={self.drone_id}, timestamp={self.timestamp}, battery={self.battery_level})>"