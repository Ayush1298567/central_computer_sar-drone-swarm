from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db, check_db_health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting SAR Drone Swarm Control System (Simplified)")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Health check
        if await check_db_health():
            logger.info("✅ Database health check passed")
        else:
            logger.critical("❌ Database health check failed")
            raise RuntimeError("Database not accessible")
        
        logger.info("🎯 SAR Drone System ready for operations")
        
    except Exception as e:
        logger.critical(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SAR Drone System")
    try:
        # Close database connections
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}", exc_info=True)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Life-saving Search and Rescue drone swarm control system",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# SECURE CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

logger.info(f"🔒 CORS configured for origins: {settings.ALLOWED_ORIGINS}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": f"ERR_{id(exc)}"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        db_healthy = await check_db_health()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": "connected" if db_healthy else "disconnected",
            "services": {
                "database": db_healthy,
                "api": True,
                "websocket": False  # Will be implemented later
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "SAR Drone Swarm Control System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health"
    }

# Basic API endpoints
@app.get("/api/v1/drones")
async def get_drones():
    """Get all drones"""
    return {
        "drones": [
            {"id": 1, "name": "Drone 1", "status": "active", "battery": 85},
            {"id": 2, "name": "Drone 2", "status": "standby", "battery": 92}
        ]
    }

@app.get("/api/v1/missions")
async def get_missions():
    """Get all missions"""
    return {
        "missions": [
            {"id": 1, "name": "Search Mission 1", "status": "planning"},
            {"id": 2, "name": "Rescue Mission 2", "status": "active"}
        ]
    }

@app.post("/api/v1/missions")
async def create_mission(mission_data: dict):
    """Create a new mission"""
    return {
        "message": "Mission created",
        "mission_id": 3,
        "status": "created"
    }

# Emergency stop endpoint
@app.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop endpoint"""
    logger.critical("🚨 EMERGENCY STOP ACTIVATED")
    
    return {
        "status": "emergency_stop_activated",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "All drone operations halted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )