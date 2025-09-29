"""
Drone Model

Defines the structure for drone data and status.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Drone(Base):
    """Drone model for SAR operations."""

    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    model = Column(String)
    status = Column(String, default="offline")  # offline, online, active, maintenance, error

    # Location fields using backend naming convention
    current_lat = Column(Float, nullable=False)  # Current latitude
    current_lng = Column(Float, nullable=False)  # Current longitude
    altitude = Column(Float, nullable=False)  # Current altitude in meters

    # Performance fields
    battery_level = Column(Float, default=100.0)  # Battery percentage (0-100)
    max_speed = Column(Float, default=15.0)  # Maximum speed in m/s
    current_speed = Column(Float, default=0.0)  # Current speed in m/s

    # Operational status
    is_connected = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    signal_strength = Column(Float, default=0.0)  # Signal strength percentage

    # Mission assignment
    assigned_mission_id = Column(Integer, nullable=True)
    mission_status = Column(String, default="idle")  # idle, assigned, enroute, searching, returning

    # Hardware status
    camera_status = Column(String, default="operational")  # operational, malfunction, offline
    sensor_status = Column(String, default="operational")  # operational, malfunction, offline

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert drone to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'status': self.status,
            'current_lat': self.current_lat,
            'current_lng': self.current_lng,
            'altitude': self.altitude,
            'battery_level': self.battery_level,
            'max_speed': self.max_speed,
            'current_speed': self.current_speed,
            'is_connected': self.is_connected,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'signal_strength': self.signal_strength,
            'assigned_mission_id': self.assigned_mission_id,
            'mission_status': self.mission_status,
            'camera_status': self.camera_status,
            'sensor_status': self.sensor_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }