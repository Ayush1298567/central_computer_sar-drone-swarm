"""
Mission Model

Defines the structure for SAR mission data.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Mission(Base):
    """Mission model for SAR operations."""

    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)

    # Location fields using backend naming convention
    center_lat = Column(Float, nullable=False)  # Center latitude
    center_lng = Column(Float, nullable=False)  # Center longitude
    area_size_km2 = Column(Float, nullable=False)  # Area size in square kilometers
    search_altitude = Column(Float, nullable=False)  # Search altitude in meters

    # Mission status
    status = Column(String, default="planning")  # planning, active, completed, cancelled
    priority = Column(String, default="medium")  # low, medium, high, critical

    # Mission parameters
    weather_conditions = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)
    estimated_duration = Column(Integer)  # Duration in minutes
    max_drones = Column(Integer, default=1)

    # Mission results
    discoveries_count = Column(Integer, default=0)
    area_covered = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert mission to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'center_lat': self.center_lat,
            'center_lng': self.center_lng,
            'area_size_km2': self.area_size_km2,
            'search_altitude': self.search_altitude,
            'status': self.status,
            'priority': self.priority,
            'weather_conditions': self.weather_conditions,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'estimated_duration': self.estimated_duration,
            'max_drones': self.max_drones,
            'discoveries_count': self.discoveries_count,
            'area_covered': self.area_covered,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }