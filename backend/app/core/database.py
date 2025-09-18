"""
Database configuration and connection management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from .config import settings

# Database engine configuration
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Database dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

class DatabaseManager:
    """Database management utilities for the SAR system."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def health_check(self) -> bool:
        """Check database connection health."""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information."""
        return {
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
            "engine": str(self.engine.url.drivername),
            "pool_size": getattr(self.engine.pool, 'size', lambda: 'N/A')(),
            "checked_out": getattr(self.engine.pool, 'checkedout', lambda: 'N/A')()
        }