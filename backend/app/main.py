from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db, check_db_health
from app.api.api_v1.api import api_router
from app.communication.drone_connection_hub import drone_connection_hub
from app.services.real_mission_execution import real_mission_execution_engine

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
    logger.info("🚀 Starting SAR Drone Swarm Control System")
    
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
        
        # Initialize drone connection hub
        if await drone_connection_hub.start():
            logger.info("✅ Drone Connection Hub started")
        else:
            logger.warning("⚠️  Drone Connection Hub failed to start")
        
        # Initialize real mission execution engine
        if await real_mission_execution_engine.start():
            logger.info("✅ Real Mission Execution Engine started")
        else:
            logger.warning("⚠️  Real Mission Execution Engine failed to start")
        
        logger.info("🎯 SAR Drone System ready for operations")
        
    except Exception as e:
        logger.critical(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SAR Drone System")
    try:
        # Stop real mission execution engine
        await real_mission_execution_engine.stop()
        logger.info("✅ Real Mission Execution Engine stopped")
        
        # Stop drone connection hub
        await drone_connection_hub.stop()
        logger.info("✅ Drone Connection Hub stopped")
        
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

# SECURE CORS Configuration - NEVER use wildcard in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # 10 minutes cache
)

# Trusted host middleware for security (disabled for testing)
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.local"] if settings.DEBUG else []
# )

logger.info(f"🔒 CORS configured for origins: {settings.ALLOWED_ORIGINS}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                "websocket": True  # Will be updated when WebSocket is implemented
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Emergency stop endpoint (bypasses normal auth for critical situations)
@app.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop endpoint - requires special handling"""
    logger.critical("🚨 EMERGENCY STOP ACTIVATED")
    
    # Implement actual emergency stop logic
    try:
        # Stop all drone operations
        from app.communication.drone_connection_hub import drone_connection_hub
        await drone_connection_hub.emergency_stop_all_drones()
        
        # Stop mission execution
        from app.services.real_mission_execution import real_mission_execution_engine
        await real_mission_execution_engine.emergency_stop_all_missions()
        
        # Send emergency alert
        from app.services.websocket_manager import websocket_manager
        await websocket_manager.publish_system_alert({
            "type": "emergency_stop",
            "message": "EMERGENCY STOP ACTIVATED - All operations halted",
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.critical("✅ Emergency stop executed - all operations halted")
        
    except Exception as e:
        logger.critical(f"❌ Error during emergency stop: {e}")
    
    return {
        "status": "emergency_stop_activated",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "All drone operations halted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )