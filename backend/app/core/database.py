from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import String, Integer, DateTime, Float, Boolean, Text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging
from datetime import datetime
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Modern SQLAlchemy declarative base"""
    pass

# Create engine with proper configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Async session factory (for future async operations)
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://").replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database sessions with comprehensive error handling"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db():
    """Synchronous database session dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

async def init_db():
    """Initialize database with proper error handling"""
    try:
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
        # Create default admin user if none exists
        await create_default_admin()
        
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        raise

async def create_default_admin():
    """Create default admin user if none exists"""
    try:
        from app.models.user import User
        from app.core.security import get_password_hash
        
        async with AsyncSessionLocal() as session:
            # Check if admin exists
            admin = await session.get(User, 1)
            if not admin:
                admin_user = User(
                    id=1,
                    username="admin",
                    email="admin@sardrone.local",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True,
                    is_admin=True,
                    created_at=datetime.utcnow()
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Default admin user created: admin/admin123")
            else:
                logger.info("Admin user already exists")
                
    except Exception as e:
        logger.error(f"Failed to create default admin: {e}", exc_info=True)

async def close_db():
    """Close database connections"""
    try:
        await async_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)

# Database health check
async def check_db_health() -> bool:
    """Check database connectivity"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False