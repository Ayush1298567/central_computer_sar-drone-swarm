"""
Database management for SAR Drone Command & Control System.
Handles SQLAlchemy setup, connection management, and database operations.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings

# Create declarative base for models
Base = declarative_base()

# Global database manager instance
_db_manager: Optional["DatabaseManager"] = None


class DatabaseManager:
    """
    Manages database connections and sessions for the SAR system.
    Supports both synchronous and asynchronous operations.
    """
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.echo = settings.DATABASE_ECHO
        
        # Initialize engines
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database engines and session factories."""
        if self._initialized:
            return
        
        # Create synchronous engine
        if self.database_url.startswith("sqlite"):
            # SQLite specific configuration
            self._engine = create_engine(
                self.database_url,
                echo=self.echo,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                }
            )
            
            # Convert to async SQLite URL
            async_url = self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            self._async_engine = create_async_engine(
                async_url,
                echo=self.echo,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                }
            )
        else:
            # PostgreSQL or other databases
            self._engine = create_engine(
                self.database_url,
                echo=self.echo
            )
            self._async_engine = create_async_engine(
                self.database_url,
                echo=self.echo
            )
        
        # Create session factories
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )
        
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Enable WAL mode for SQLite
        if self.database_url.startswith("sqlite"):
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=1000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        # Create all tables
        await self.create_tables()
        
        self._initialized = True
    
    async def create_tables(self):
        """Create all database tables."""
        if self._async_engine is None:
            raise RuntimeError("Database not initialized")
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all database tables (use with caution)."""
        if self._async_engine is None:
            raise RuntimeError("Database not initialized")
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self._initialized or self._async_session_factory is None:
            raise RuntimeError("Database not initialized")
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """Get a synchronous database session."""
        if not self._initialized or self._session_factory is None:
            raise RuntimeError("Database not initialized")
        
        return self._session_factory()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            if not self._initialized:
                return False
            
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    async def close(self):
        """Close database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        
        if self._engine:
            self._engine.dispose()
        
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions in FastAPI."""
    db_manager = await get_database_manager()
    async with db_manager.get_session() as session:
        yield session


# Utility functions for testing and maintenance
async def reset_database():
    """Reset the database by dropping and recreating all tables."""
    db_manager = await get_database_manager()
    await db_manager.drop_tables()
    await db_manager.create_tables()


async def check_database_health() -> dict:
    """Comprehensive database health check."""
    try:
        db_manager = await get_database_manager()
        
        # Basic connectivity check
        is_healthy = await db_manager.health_check()
        
        if not is_healthy:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to database"
            }
        
        # Additional checks can be added here
        # - Table existence verification
        # - Performance metrics
        # - Connection pool status
        
        return {
            "status": "healthy",
            "database_url": db_manager.database_url.split("://")[0] + "://***",
            "initialized": db_manager.is_initialized
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }