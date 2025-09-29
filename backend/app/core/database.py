"""
Database configuration and models for SAR Mission Commander
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Import Base after defining it
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sar_missions.db")

if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=0,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    # Import all models to ensure they are registered with SQLAlchemy
    from ..models.mission import Mission, MissionStatus, MissionType, MissionPriority
    from ..models.drone import Drone, DroneStatus, DroneType, TelemetryData
    from ..models.discovery import Discovery
    from ..models.chat import ChatSession, ChatMessageDB

    Base.metadata.create_all(bind=engine)