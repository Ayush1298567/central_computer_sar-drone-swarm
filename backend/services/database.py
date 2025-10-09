"""
Database service with SQLAlchemy models and initialization
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean, 
    ForeignKey, create_engine, Index
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./sar_drone_system.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

class Mission(Base):
    """Mission model"""
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    search_area_json = Column(Text)  # GeoJSON polygon
    status = Column(String(50), default="planning")  # planning, active, paused, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    conversation_context = Column(Text)  # JSON string for AI conversation
    mission_plan = Column(Text)  # JSON string for generated plan
    
    # Relationships
    telemetry_records = relationship("Telemetry", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    drone_assignments = relationship("DroneAssignment", back_populates="mission")

class Drone(Base):
    """Drone model"""
    __tablename__ = "drones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    capabilities_json = Column(Text)  # JSON string for capabilities
    battery_capacity = Column(Integer, default=5000)  # mAh
    status = Column(String(50), default="available")  # available, in_mission, charging, maintenance
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    current_alt = Column(Float, nullable=True)
    battery_percent = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    telemetry_records = relationship("Telemetry", back_populates="drone")
    discoveries = relationship("Discovery", back_populates="drone")
    assignments = relationship("DroneAssignment", back_populates="drone")

class Telemetry(Base):
    """Telemetry data model"""
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    alt = Column(Float, nullable=False)
    battery_percent = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    heading = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    coverage_progress = Column(Float, default=0.0)
    
    # Relationships
    drone = relationship("Drone", back_populates="telemetry_records")
    mission = relationship("Mission", back_populates="telemetry_records")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_telemetry_drone_time', 'drone_id', 'timestamp'),
        Index('idx_telemetry_mission_time', 'mission_id', 'timestamp'),
    )

class Discovery(Base):
    """Discovery model for found items/survivors"""
    __tablename__ = "discoveries"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    discovery_type = Column(String(50), nullable=False)  # survivor, hazard, obstacle
    confidence = Column(Integer, nullable=False)  # 0-100
    description = Column(Text)
    image_data = Column(Text)  # Base64 encoded image if available
    
    # Relationships
    mission = relationship("Mission", back_populates="discoveries")
    drone = relationship("Drone", back_populates="discoveries")

class DroneAssignment(Base):
    """Drone mission assignments"""
    __tablename__ = "drone_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    search_zone_json = Column(Text)  # GeoJSON polygon for assigned zone
    status = Column(String(50), default="assigned")  # assigned, active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    mission = relationship("Mission", back_populates="drone_assignments")
    drone = relationship("Drone", back_populates="assignments")

class ConversationState(Base):
    """AI conversation state storage"""
    __tablename__ = "conversation_states"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    context_json = Column(Text)  # Full conversation context
    current_step = Column(String(100), default="initial")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mission = relationship("Mission")

async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Database utility functions
class DatabaseService:
    """Database service with common operations"""
    
    def __init__(self):
        self.session_factory = AsyncSessionLocal
    
    async def create_mission(self, name: str, description: str = None) -> Mission:
        """Create a new mission"""
        async with self.session_factory() as session:
            mission = Mission(
                name=name,
                description=description,
                status="planning"
            )
            session.add(mission)
            await session.commit()
            await session.refresh(mission)
            return mission
    
    async def get_mission(self, mission_id: int) -> Optional[Mission]:
        """Get mission by ID"""
        async with self.session_factory() as session:
            result = await session.get(Mission, mission_id)
            return result
    
    async def create_drone(self, name: str, capabilities: dict, battery_capacity: int = 5000) -> Drone:
        """Create a new drone"""
        async with self.session_factory() as session:
            import json
            drone = Drone(
                name=name,
                capabilities_json=json.dumps(capabilities),
                battery_capacity=battery_capacity,
                status="available"
            )
            session.add(drone)
            await session.commit()
            await session.refresh(drone)
            return drone
    
    async def get_all_drones(self) -> list[Drone]:
        """Get all drones"""
        async with self.session_factory() as session:
            from sqlalchemy import select
            result = await session.execute(select(Drone))
            return result.scalars().all()
    
    async def update_drone_status(self, drone_id: int, status: str, lat: float = None, 
                                 lng: float = None, alt: float = None, battery_percent: int = None):
        """Update drone status and position"""
        async with self.session_factory() as session:
            drone = await session.get(Drone, drone_id)
            if drone:
                drone.status = status
                drone.last_seen = datetime.utcnow()
                if lat is not None:
                    drone.current_lat = lat
                if lng is not None:
                    drone.current_lng = lng
                if alt is not None:
                    drone.current_alt = alt
                if battery_percent is not None:
                    drone.battery_percent = battery_percent
                await session.commit()
    
    async def save_telemetry(self, drone_id: int, mission_id: int, lat: float, lng: float, 
                           alt: float, battery_percent: int, status: str, heading: float = None, 
                           speed: float = None, coverage_progress: float = 0.0):
        """Save telemetry data"""
        async with self.session_factory() as session:
            telemetry = Telemetry(
                drone_id=drone_id,
                mission_id=mission_id,
                lat=lat,
                lng=lng,
                alt=alt,
                battery_percent=battery_percent,
                status=status,
                heading=heading,
                speed=speed,
                coverage_progress=coverage_progress
            )
            session.add(telemetry)
            await session.commit()
    
    async def create_discovery(self, mission_id: int, drone_id: int, lat: float, lng: float,
                              discovery_type: str, confidence: int, description: str = None):
        """Create a discovery record"""
        async with self.session_factory() as session:
            discovery = Discovery(
                mission_id=mission_id,
                drone_id=drone_id,
                lat=lat,
                lng=lng,
                discovery_type=discovery_type,
                confidence=confidence,
                description=description
            )
            session.add(discovery)
            await session.commit()
            await session.refresh(discovery)
            return discovery

# Global database service instance
db_service = DatabaseService()