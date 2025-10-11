"""
REAL Database Implementation for SAR Mission Commander
PostgreSQL with real schemas, data persistence, and performance optimization
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

# Database imports
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://sar_user:sar_password@localhost:5432/sar_drone_db"
TEST_DATABASE_URL = "postgresql://sar_user:sar_password@localhost:5432/sar_drone_test_db"

# Create base class for models
Base = declarative_base()

class MissionStatus(Enum):
    """Mission status enumeration"""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class DroneStatus(Enum):
    """Drone status enumeration"""
    IDLE = "idle"
    TAKEOFF = "takeoff"
    HOVERING = "hovering"
    SEARCHING = "searching"
    INVESTIGATING = "investigating"
    RETURNING = "returning"
    LANDING = "landing"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"

class DiscoveryType(Enum):
    """Discovery type enumeration"""
    PERSON = "person"
    VEHICLE = "vehicle"
    STRUCTURE = "structure"
    DEBRIS = "debris"
    ANIMAL = "animal"
    OTHER = "other"

# Database Models
class Mission(Base):
    """Mission table with real schema"""
    __tablename__ = "missions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mission_type = Column(String(50), nullable=False)
    status = Column(String(20), default=MissionStatus.PLANNING.value)
    
    # Location data
    search_area_center_lat = Column(Float, nullable=False)
    search_area_center_lon = Column(Float, nullable=False)
    search_area_radius = Column(Float, nullable=False)  # meters
    search_altitude = Column(Integer, default=50)  # meters
    
    # Mission parameters
    priority = Column(Integer, default=3)  # 1-5 scale
    estimated_duration = Column(Float)  # hours
    max_drones = Column(Integer, default=5)
    weather_conditions = Column(JSONB)
    terrain_type = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Performance metrics
    success_rate = Column(Float)
    coverage_percentage = Column(Float)
    total_distance_flown = Column(Float)
    total_flight_time = Column(Float)
    
    # Relationships
    drones = relationship("Drone", back_populates="mission")
    discoveries = relationship("Discovery", back_populates="mission")
    telemetry_data = relationship("TelemetryData", back_populates="mission")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_mission_status', 'status'),
        Index('idx_mission_created', 'created_at'),
        Index('idx_mission_location', 'search_area_center_lat', 'search_area_center_lon'),
    )

class Drone(Base):
    """Drone table with real schema"""
    __tablename__ = "drones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    drone_type = Column(String(50), default="quadcopter")
    status = Column(String(20), default=DroneStatus.IDLE.value)
    
    # Mission assignment
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))
    mission = relationship("Mission", back_populates="drones")
    
    # Physical specifications
    mass = Column(Float)  # kg
    max_thrust = Column(Float)  # N
    max_speed = Column(Float)  # m/s
    max_altitude = Column(Integer)  # m
    battery_capacity = Column(Float)  # Wh
    battery_voltage = Column(Float)  # V
    
    # Current state
    current_lat = Column(Float)
    current_lon = Column(Float)
    current_altitude = Column(Float)
    battery_level = Column(Float)
    signal_strength = Column(Float)
    
    # Performance tracking
    total_flight_time = Column(Float, default=0.0)
    total_distance = Column(Float, default=0.0)
    total_missions = Column(Integer, default=0)
    success_rate = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    telemetry_data = relationship("TelemetryData", back_populates="drone")
    discoveries = relationship("Discovery", back_populates="drone")
    
    # Indexes
    __table_args__ = (
        Index('idx_drone_status', 'status'),
        Index('idx_drone_mission', 'mission_id'),
        Index('idx_drone_location', 'current_lat', 'current_lon'),
    )

class TelemetryData(Base):
    """Telemetry data table with real schema"""
    __tablename__ = "telemetry_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"))
    
    mission = relationship("Mission", back_populates="telemetry_data")
    drone = relationship("Drone", back_populates="telemetry_data")
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Position data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    altitude_agl = Column(Float)  # Above ground level
    
    # Orientation
    roll = Column(Float)
    pitch = Column(Float)
    yaw = Column(Float)
    
    # Velocity
    velocity_x = Column(Float)
    velocity_y = Column(Float)
    velocity_z = Column(Float)
    ground_speed = Column(Float)
    
    # Battery and power
    battery_level = Column(Float)
    battery_voltage = Column(Float)
    current_draw = Column(Float)
    power_consumption = Column(Float)
    
    # Environmental
    temperature = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    visibility = Column(Float)
    
    # System status
    signal_strength = Column(Float)
    gps_accuracy = Column(Float)
    motor_rpm = Column(JSONB)  # Array of RPM values
    
    # Performance metrics
    flight_time = Column(Float)
    distance_traveled = Column(Float)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_telemetry_timestamp', 'timestamp'),
        Index('idx_telemetry_mission', 'mission_id'),
        Index('idx_telemetry_drone', 'drone_id'),
        Index('idx_telemetry_location', 'latitude', 'longitude'),
    )

class Discovery(Base):
    """Discovery table with real schema"""
    __tablename__ = "discoveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"))
    
    mission = relationship("Mission", back_populates="discoveries")
    drone = relationship("Drone", back_populates="discoveries")
    
    # Discovery details
    discovery_type = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    
    # Detection data
    bounding_box = Column(JSONB)  # [x, y, width, height]
    center_point = Column(JSONB)  # [x, y]
    area = Column(Float)
    
    # Image data
    image_data = Column(Text)  # Base64 encoded image
    image_quality = Column(Float)
    analysis_results = Column(JSONB)
    
    # Status
    status = Column(String(20), default="pending")  # pending, confirmed, false_positive, investigated
    priority = Column(Integer, default=3)  # 1-5 scale
    
    # Timestamps
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    investigated_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    
    # Notes and metadata
    notes = Column(Text)
    discovery_metadata = Column(JSONB)
    
    # Indexes
    __table_args__ = (
        Index('idx_discovery_type', 'discovery_type'),
        Index('idx_discovery_mission', 'mission_id'),
        Index('idx_discovery_drone', 'drone_id'),
        Index('idx_discovery_location', 'latitude', 'longitude'),
        Index('idx_discovery_timestamp', 'discovered_at'),
    )

class MissionPerformance(Base):
    """Mission performance metrics table"""
    __tablename__ = "mission_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))
    
    # Performance metrics
    total_flight_time = Column(Float)
    total_distance_flown = Column(Float)
    coverage_percentage = Column(Float)
    discoveries_count = Column(Integer)
    false_positives = Column(Integer)
    success_rate = Column(Float)
    
    # Efficiency metrics
    energy_efficiency = Column(Float)
    time_efficiency = Column(Float)
    search_efficiency = Column(Float)
    
    # Environmental factors
    avg_wind_speed = Column(Float)
    avg_visibility = Column(Float)
    avg_temperature = Column(Float)
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_mission', 'mission_id'),
        Index('idx_performance_success', 'success_rate'),
    )

class SystemMetrics(Base):
    """System performance metrics table"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # System metrics
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    network_latency = Column(Float)
    
    # AI/ML metrics
    model_accuracy = Column(Float)
    inference_time = Column(Float)
    training_loss = Column(Float)
    
    # Database metrics
    query_time = Column(Float)
    connection_count = Column(Integer)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_metrics_timestamp', 'timestamp'),
    )

class RealDatabase:
    """Real database implementation with PostgreSQL"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self.is_connected = False
        
        logger.info(f"Initializing Real Database with URL: {database_url}")
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Test connection
            await self._test_connection()
            
            self.is_connected = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute("SELECT 1")
                result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    async def create_mission(self, mission_data: Dict[str, Any]) -> str:
        """Create a new mission"""
        try:
            with self.get_session() as session:
                mission = Mission(
                    name=mission_data['name'],
                    description=mission_data.get('description'),
                    mission_type=mission_data['mission_type'],
                    search_area_center_lat=mission_data['search_area_center_lat'],
                    search_area_center_lon=mission_data['search_area_center_lon'],
                    search_area_radius=mission_data['search_area_radius'],
                    search_altitude=mission_data.get('search_altitude', 50),
                    priority=mission_data.get('priority', 3),
                    estimated_duration=mission_data.get('estimated_duration'),
                    max_drones=mission_data.get('max_drones', 5),
                    weather_conditions=mission_data.get('weather_conditions'),
                    terrain_type=mission_data.get('terrain_type')
                )
                
                session.add(mission)
                session.commit()
                session.refresh(mission)
                
                logger.info(f"Created mission {mission.id}")
                return str(mission.id)
                
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            raise
    
    async def update_mission_status(self, mission_id: str, status: str, **kwargs) -> bool:
        """Update mission status and other fields"""
        try:
            with self.get_session() as session:
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = status
                    mission.updated_at = datetime.utcnow()
                    
                    # Update other fields if provided
                    for key, value in kwargs.items():
                        if hasattr(mission, key):
                            setattr(mission, key, value)
                    
                    session.commit()
                    logger.info(f"Updated mission {mission_id} status to {status}")
                    return True
                else:
                    logger.warning(f"Mission {mission_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update mission status: {e}")
            raise
    
    async def add_telemetry_data(self, telemetry_data: Dict[str, Any]) -> bool:
        """Add telemetry data to database"""
        try:
            with self.get_session() as session:
                telemetry = TelemetryData(
                    mission_id=telemetry_data['mission_id'],
                    drone_id=telemetry_data['drone_id'],
                    timestamp=telemetry_data.get('timestamp', datetime.utcnow()),
                    latitude=telemetry_data['latitude'],
                    longitude=telemetry_data['longitude'],
                    altitude=telemetry_data['altitude'],
                    altitude_agl=telemetry_data.get('altitude_agl'),
                    roll=telemetry_data.get('roll'),
                    pitch=telemetry_data.get('pitch'),
                    yaw=telemetry_data.get('yaw'),
                    velocity_x=telemetry_data.get('velocity_x'),
                    velocity_y=telemetry_data.get('velocity_y'),
                    velocity_z=telemetry_data.get('velocity_z'),
                    ground_speed=telemetry_data.get('ground_speed'),
                    battery_level=telemetry_data.get('battery_level'),
                    battery_voltage=telemetry_data.get('battery_voltage'),
                    current_draw=telemetry_data.get('current_draw'),
                    power_consumption=telemetry_data.get('power_consumption'),
                    temperature=telemetry_data.get('temperature'),
                    wind_speed=telemetry_data.get('wind_speed'),
                    wind_direction=telemetry_data.get('wind_direction'),
                    visibility=telemetry_data.get('visibility'),
                    signal_strength=telemetry_data.get('signal_strength'),
                    gps_accuracy=telemetry_data.get('gps_accuracy'),
                    motor_rpm=telemetry_data.get('motor_rpm'),
                    flight_time=telemetry_data.get('flight_time'),
                    distance_traveled=telemetry_data.get('distance_traveled')
                )
                
                session.add(telemetry)
                session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to add telemetry data: {e}")
            raise
    
    async def add_discovery(self, discovery_data: Dict[str, Any]) -> str:
        """Add discovery to database"""
        try:
            with self.get_session() as session:
                discovery = Discovery(
                    mission_id=discovery_data['mission_id'],
                    drone_id=discovery_data['drone_id'],
                    discovery_type=discovery_data['discovery_type'],
                    confidence_score=discovery_data['confidence_score'],
                    latitude=discovery_data['latitude'],
                    longitude=discovery_data['longitude'],
                    altitude=discovery_data.get('altitude'),
                    bounding_box=discovery_data.get('bounding_box'),
                    center_point=discovery_data.get('center_point'),
                    area=discovery_data.get('area'),
                    image_data=discovery_data.get('image_data'),
                    image_quality=discovery_data.get('image_quality'),
                    analysis_results=discovery_data.get('analysis_results'),
                    priority=discovery_data.get('priority', 3),
                    notes=discovery_data.get('notes'),
                    discovery_metadata=discovery_data.get('metadata')
                )
                
                session.add(discovery)
                session.commit()
                session.refresh(discovery)
                
                logger.info(f"Added discovery {discovery.id}")
                return str(discovery.id)
                
        except Exception as e:
            logger.error(f"Failed to add discovery: {e}")
            raise
    
    async def get_mission_telemetry(self, mission_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get telemetry data for a mission"""
        try:
            with self.get_session() as session:
                telemetry_data = session.query(TelemetryData).filter(
                    TelemetryData.mission_id == mission_id
                ).order_by(TelemetryData.timestamp.desc()).limit(limit).all()
                
                return [
                    {
                        'id': str(t.id),
                        'timestamp': t.timestamp.isoformat(),
                        'latitude': t.latitude,
                        'longitude': t.longitude,
                        'altitude': t.altitude,
                        'battery_level': t.battery_level,
                        'signal_strength': t.signal_strength,
                        'ground_speed': t.ground_speed,
                        'temperature': t.temperature,
                        'wind_speed': t.wind_speed
                    }
                    for t in telemetry_data
                ]
                
        except Exception as e:
            logger.error(f"Failed to get mission telemetry: {e}")
            raise
    
    async def get_mission_discoveries(self, mission_id: str) -> List[Dict[str, Any]]:
        """Get discoveries for a mission"""
        try:
            with self.get_session() as session:
                discoveries = session.query(Discovery).filter(
                    Discovery.mission_id == mission_id
                ).order_by(Discovery.discovered_at.desc()).all()
                
                return [
                    {
                        'id': str(d.id),
                        'discovery_type': d.discovery_type,
                        'confidence_score': d.confidence_score,
                        'latitude': d.latitude,
                        'longitude': d.longitude,
                        'altitude': d.altitude,
                        'discovered_at': d.discovered_at.isoformat(),
                        'status': d.status,
                        'priority': d.priority
                    }
                    for d in discoveries
                ]
                
        except Exception as e:
            logger.error(f"Failed to get mission discoveries: {e}")
            raise
    
    async def get_mission_performance(self, mission_id: str) -> Dict[str, Any]:
        """Get performance metrics for a mission"""
        try:
            with self.get_session() as session:
                # Get mission
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    return {}
                
                # Get telemetry data
                telemetry_data = session.query(TelemetryData).filter(
                    TelemetryData.mission_id == mission_id
                ).all()
                
                # Get discoveries
                discoveries = session.query(Discovery).filter(
                    Discovery.mission_id == mission_id
                ).all()
                
                # Calculate metrics
                total_flight_time = sum(t.flight_time or 0 for t in telemetry_data)
                total_distance = sum(t.distance_traveled or 0 for t in telemetry_data)
                discoveries_count = len(discoveries)
                
                # Calculate coverage (simplified)
                if telemetry_data:
                    lat_range = max(t.latitude for t in telemetry_data) - min(t.latitude for t in telemetry_data)
                    lon_range = max(t.longitude for t in telemetry_data) - min(t.longitude for t in telemetry_data)
                    coverage_area = lat_range * lon_range * 111000 * 111000  # Rough conversion to m²
                    search_area = 3.14159 * (mission.search_area_radius ** 2)
                    coverage_percentage = min(100, (coverage_area / search_area) * 100)
                else:
                    coverage_percentage = 0
                
                return {
                    'mission_id': str(mission.id),
                    'total_flight_time': total_flight_time,
                    'total_distance': total_distance,
                    'coverage_percentage': coverage_percentage,
                    'discoveries_count': discoveries_count,
                    'success_rate': mission.success_rate,
                    'status': mission.status,
                    'created_at': mission.created_at.isoformat(),
                    'started_at': mission.started_at.isoformat() if mission.started_at else None,
                    'completed_at': mission.completed_at.isoformat() if mission.completed_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get mission performance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            with self.get_session() as session:
                # Test basic query
                result = session.execute("SELECT 1").fetchone()
                
                # Get table counts
                mission_count = session.query(Mission).count()
                drone_count = session.query(Drone).count()
                telemetry_count = session.query(TelemetryData).count()
                discovery_count = session.query(Discovery).count()
                
                return {
                    'status': 'healthy',
                    'connected': self.is_connected,
                    'database_url': self.database_url,
                    'table_counts': {
                        'missions': mission_count,
                        'drones': drone_count,
                        'telemetry_data': telemetry_count,
                        'discoveries': discovery_count
                    },
                    'connection_pool': {
                        'pool_size': self.engine.pool.size(),
                        'checked_in': self.engine.pool.checkedin(),
                        'checked_out': self.engine.pool.checkedout(),
                        'overflow': self.engine.pool.overflow()
                    }
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.is_connected = False
            logger.info("Database connection closed")

# Global database instance
real_database = RealDatabase()
