"""
Database configuration and session management for SQLAlchemy.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from .config import settings

logger = logging.getLogger(__name__)

# Database engine configuration
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.debug
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()

# Metadata for database operations
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_database():
    """
    Initialize database by creating all tables.
    This function should be called on application startup.
    """
    try:
        logger.info("Initializing database...")
        
        # Import all models to ensure they're registered with Base
        from ..models import mission, drone, ai_learning, discovery
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialization completed successfully")
        
        # Create default data if needed
        await create_default_data()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def create_default_data():
    """Create default data for the application."""
    db = SessionLocal()
    try:
        # Import models
        from ..models.mission import MissionStatus
        from ..models.drone import DroneStatus
        
        # Check if we need to create default data
        # (This would typically check if tables are empty and create initial records)
        
        logger.info("Default data creation completed")
        
    except Exception as e:
        logger.error(f"Failed to create default data: {e}")
    finally:
        db.close()

def get_db_sync() -> Session:
    """
    Get a synchronous database session.
    Remember to close the session when done.
    """
    return SessionLocal()

def close_db_connections():
    """Close all database connections."""
    engine.dispose()
    logger.info("Database connections closed")