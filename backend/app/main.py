from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import os

from .core.config import settings, get_environment_info
from .core.database import create_tables, DatabaseManager
from .api import missions, drones, chat, websocket
from .utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup procedures
    logger.info("Starting Mission Commander SAR System")
    logger.info(f"Environment: {get_environment_info()}")

    try:
        # Initialize database
        create_tables()
        db_manager = DatabaseManager()

        if db_manager.health_check():
            logger.info("Database connection established successfully")
        else:
            logger.error("Database connection failed")
            raise Exception("Database initialization failed")

        # Initialize AI system
        from .ai.ollama_client import OllamaClient
        ai_client = OllamaClient()

        if await ai_client.health_check():
            logger.info(f"AI system initialized with model: {settings.DEFAULT_MODEL}")
        else:
            logger.warning("AI system not available - some features will be limited")

        # Store clients in app state for access by routes
        app.state.db_manager = db_manager
        app.state.ai_client = ai_client

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown procedures
    logger.info("Shutting down Mission Commander SAR System")

    try:
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Search and Rescue Drone Control System",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Mount static files for uploads and media
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routers
app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
app.include_router(drones.router, prefix="/api/drones", tags=["drones"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error responses."""
    logger.error(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error on {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": get_environment_info()
        }

        # Check database
        if hasattr(app.state, 'db_manager'):
            db_healthy = app.state.db_manager.health_check()
            health_status["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection_info": app.state.db_manager.get_connection_info()
            }

        # Check AI system
        if hasattr(app.state, 'ai_client'):
            ai_healthy = await app.state.ai_client.health_check()
            health_status["ai_system"] = {
                "status": "healthy" if ai_healthy else "unhealthy",
                "model": settings.DEFAULT_MODEL,
                "host": settings.OLLAMA_HOST
            }

        return health_status

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
    """Root endpoint with basic system information."""
    return {
        "message": "Mission Commander SAR System",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs_url": "/docs" if settings.DEBUG else None
    }

def get_environment_info() -> dict:
    """Get current environment configuration information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "database_type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
        "ai_model": settings.DEFAULT_MODEL,
        "log_level": settings.LOG_LEVEL,
        "max_drones": settings.MAX_DRONES_PER_MISSION,
        "upload_dir": settings.UPLOAD_DIR,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )