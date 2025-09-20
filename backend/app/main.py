"""
Main FastAPI application for SAR Drone Command & Control System.
Implements the central command interface for managing drone swarms in search and rescue operations.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import Settings
from .core.database import DatabaseManager
from .utils.logging import setup_logging, MissionLogger

# Initialize settings
settings = Settings()

# Initialize mission logger
mission_logger = MissionLogger("main_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    mission_logger.info("Starting SAR Drone Command & Control System")
    
    try:
        # Setup logging
        setup_logging()
        mission_logger.info("Logging system initialized")
        
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.initialize()
        mission_logger.info("Database initialized successfully")
        
        # Create upload directories
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        (upload_dir / "mission_data").mkdir(exist_ok=True)
        (upload_dir / "drone_logs").mkdir(exist_ok=True)
        mission_logger.info("Upload directories created")
        
        mission_logger.info("Application startup completed successfully")
        
    except Exception as e:
        mission_logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    mission_logger.info("Shutting down SAR Drone Command & Control System")
    
    try:
        # Close database connections
        if 'db_manager' in locals():
            await db_manager.close()
        mission_logger.info("Database connections closed")
        
        mission_logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        mission_logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="SAR Drone Command & Control System",
    description="Central command interface for managing drone swarms in search and rescue operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add TrustedHost middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper logging."""
    mission_logger.warning(
        f"HTTP {exc.status_code} error on {request.url.path}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed logging."""
    mission_logger.warning(
        f"Validation error on {request.url.path}: {exc.errors()}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "validation_errors": exc.errors(),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "status_code": 422,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with comprehensive logging."""
    mission_logger.error(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "client_ip": request.client.host if request.client else "unknown"
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support if this persists.",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify system status.
    Returns comprehensive system health information.
    """
    try:
        # Check database connectivity
        db_manager = DatabaseManager()
        db_status = await db_manager.health_check()
        
        # Check disk space
        upload_dir = Path("uploads")
        disk_usage = {
            "total": 0,
            "used": 0,
            "free": 0
        }
        
        if upload_dir.exists():
            stat = os.statvfs(str(upload_dir))
            disk_usage = {
                "total": stat.f_frsize * stat.f_blocks,
                "used": stat.f_frsize * (stat.f_blocks - stat.f_bavail),
                "free": stat.f_frsize * stat.f_bavail
            }
        
        health_data = {
            "status": "healthy",
            "timestamp": mission_logger.get_timestamp(),
            "version": "1.0.0",
            "components": {
                "database": {
                    "status": "healthy" if db_status else "unhealthy",
                    "connected": db_status
                },
                "storage": {
                    "status": "healthy",
                    "disk_usage": disk_usage
                },
                "logging": {
                    "status": "healthy",
                    "log_level": logging.getLogger().getEffectiveLevel()
                }
            }
        }
        
        mission_logger.info("Health check completed successfully")
        return health_data
        
    except Exception as e:
        mission_logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": mission_logger.get_timestamp(),
                "error": str(e)
            }
        )


# Mount static files
static_path = Path("frontend/dist")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    mission_logger.info("Static files mounted from frontend/dist")
else:
    # Fallback to public directory during development
    public_path = Path("frontend/public")
    if public_path.exists():
        app.mount("/static", StaticFiles(directory=str(public_path)), name="static")
        mission_logger.info("Static files mounted from frontend/public")


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint providing system information."""
    return {
        "message": "SAR Drone Command & Control System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


# Include API routers (will be implemented in subsequent phases)
# from .api.missions import router as missions_router
# from .api.drones import router as drones_router
# from .api.discoveries import router as discoveries_router

# app.include_router(missions_router, prefix="/api/v1/missions", tags=["Missions"])
# app.include_router(drones_router, prefix="/api/v1/drones", tags=["Drones"])
# app.include_router(discoveries_router, prefix="/api/v1/discoveries", tags=["Discoveries"])


if __name__ == "__main__":
    import uvicorn
    
    mission_logger.info("Starting FastAPI application directly")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None  # Use our custom logging setup
    )