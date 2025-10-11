"""
SQLite Fallback Database for Testing
Fallback when PostgreSQL is not available
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
from dataclasses import dataclass, asdict

# SQLite imports
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

class TestMission(Base):
    """Test mission table"""
    __tablename__ = "test_missions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    mission_type = Column(String, nullable=False)
    status = Column(String, default="planning")
    created_at = Column(DateTime, default=datetime.utcnow)

class TestTelemetry(Base):
    """Test telemetry table"""
    __tablename__ = "test_telemetry"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    battery_level = Column(Float)

class TestDiscovery(Base):
    """Test discovery table"""
    __tablename__ = "test_discoveries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mission_id = Column(String, nullable=False)
    discovery_type = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

class SQLiteFallback:
    """SQLite fallback database for testing"""
    
    def __init__(self):
        self.database_url = "sqlite:///./test_sar_drone.db"
        self.engine = None
        self.SessionLocal = None
        self.is_connected = False
        
        logger.info("Initializing SQLite Fallback Database")
    
    async def initialize(self):
        """Initialize SQLite database"""
        try:
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=False
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            self.is_connected = True
            logger.info("SQLite Fallback Database initialized successfully")
            
        except Exception as e:
            logger.error(f"SQLite Fallback Database initialization failed: {e}")
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
                mission = TestMission(
                    name=mission_data['name'],
                    mission_type=mission_data['mission_type'],
                    status="planning"
                )
                
                session.add(mission)
                session.commit()
                session.refresh(mission)
                
                logger.info(f"Created test mission {mission.id}")
                return str(mission.id)
                
        except Exception as e:
            logger.error(f"Failed to create test mission: {e}")
            raise
    
    async def add_telemetry_data(self, telemetry_data: Dict[str, Any]) -> bool:
        """Add telemetry data"""
        try:
            with self.get_session() as session:
                telemetry = TestTelemetry(
                    mission_id=telemetry_data['mission_id'],
                    latitude=telemetry_data['latitude'],
                    longitude=telemetry_data['longitude'],
                    altitude=telemetry_data['altitude'],
                    battery_level=telemetry_data['battery_level']
                )
                
                session.add(telemetry)
                session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to add telemetry data: {e}")
            raise
    
    async def add_discovery(self, discovery_data: Dict[str, Any]) -> str:
        """Add discovery"""
        try:
            with self.get_session() as session:
                discovery = TestDiscovery(
                    mission_id=discovery_data['mission_id'],
                    discovery_type=discovery_data['discovery_type'],
                    confidence_score=discovery_data['confidence_score'],
                    latitude=discovery_data['latitude'],
                    longitude=discovery_data['longitude']
                )
                
                session.add(discovery)
                session.commit()
                session.refresh(discovery)
                
                logger.info(f"Added test discovery {discovery.id}")
                return str(discovery.id)
                
        except Exception as e:
            logger.error(f"Failed to add discovery: {e}")
            raise
    
    async def get_mission_telemetry(self, mission_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get telemetry data"""
        try:
            with self.get_session() as session:
                telemetry_data = session.query(TestTelemetry).filter(
                    TestTelemetry.mission_id == mission_id
                ).limit(limit).all()
                
                return [
                    {
                        'id': t.id,
                        'timestamp': t.timestamp.isoformat(),
                        'latitude': t.latitude,
                        'longitude': t.longitude,
                        'altitude': t.altitude,
                        'battery_level': t.battery_level
                    }
                    for t in telemetry_data
                ]
                
        except Exception as e:
            logger.error(f"Failed to get telemetry: {e}")
            return []
    
    async def get_mission_discoveries(self, mission_id: str) -> List[Dict[str, Any]]:
        """Get discoveries"""
        try:
            with self.get_session() as session:
                discoveries = session.query(TestDiscovery).filter(
                    TestDiscovery.mission_id == mission_id
                ).all()
                
                return [
                    {
                        'id': d.id,
                        'discovery_type': d.discovery_type,
                        'confidence_score': d.confidence_score,
                        'latitude': d.latitude,
                        'longitude': d.longitude
                    }
                    for d in discoveries
                ]
                
        except Exception as e:
            logger.error(f"Failed to get discoveries: {e}")
            return []
    
    async def update_mission_status(self, mission_id: str, status: str, **kwargs) -> bool:
        """Update mission status"""
        try:
            with self.get_session() as session:
                mission = session.query(TestMission).filter(TestMission.id == mission_id).first()
                if mission:
                    mission.status = status
                    session.commit()
                    return True
                return False
                    
        except Exception as e:
            logger.error(f"Failed to update mission status: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            with self.get_session() as session:
                mission_count = session.query(TestMission).count()
                telemetry_count = session.query(TestTelemetry).count()
                discovery_count = session.query(TestDiscovery).count()
                
                return {
                    'status': 'healthy',
                    'connected': self.is_connected,
                    'database_url': self.database_url,
                    'table_counts': {
                        'missions': mission_count,
                        'telemetry_data': telemetry_count,
                        'discoveries': discovery_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
    
    async def get_mission_performance(self, mission_id: str) -> Dict[str, Any]:
        """Get mission performance (simplified version)"""
        try:
            with self.get_session() as session:
                mission = session.query(TestMission).filter(TestMission.id == mission_id).first()
                if not mission:
                    return {}
                
                telemetry_data = session.query(TestTelemetry).filter(
                    TestTelemetry.mission_id == mission_id
                ).all()
                
                discoveries = session.query(TestDiscovery).filter(
                    TestDiscovery.mission_id == mission_id
                ).all()
                
                return {
                    'mission_id': mission_id,
                    'total_flight_time': len(telemetry_data) * 10,  # Simplified
                    'total_distance': len(telemetry_data) * 100,  # Simplified
                    'coverage_percentage': min(100, len(telemetry_data) * 5),
                    'discoveries_count': len(discoveries),
                    'success_rate': len(discoveries) / 10.0 if discoveries else 0,
                    'status': mission.status,
                    'created_at': mission.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get mission performance: {e}")
            return {}

# Global fallback database instance
sqlite_fallback = SQLiteFallback()
