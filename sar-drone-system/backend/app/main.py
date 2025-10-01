"""
Main FastAPI application for SAR Drone System
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import uvicorn

from .core.config import settings
from .core.database import create_tables
from .api.api_v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Search and Rescue Drone Swarm Management System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting SAR Drone System...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # Test AI engine health (non-blocking)
    try:
        from .ai import create_ollama_intelligence_engine
        # Don't await here to prevent blocking startup
        logger.info("AI Intelligence Engine will be initialized on first use")
    except Exception as e:
        logger.warning(f"AI Engine import failed: {e}")
    
    logger.info("SAR Drone System startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down SAR Drone System...")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SAR Drone System API",
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "unknown"
    ai_status = "unknown"
    
    try:
        # Test database connection
        from .core.database import get_db
        db = next(get_db())
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)[:100]}"
    
    try:
        # Test AI engine (non-blocking)
        from .ai import create_ollama_intelligence_engine
        # Just test if we can import, don't actually initialize
        ai_status = "available"
    except Exception as e:
        logger.error(f"AI engine health check failed: {e}")
        ai_status = f"error: {str(e)[:100]}"
    
    overall_status = "healthy" if db_status == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "database": db_status,
        "ai_engine": ai_status,
        "version": settings.VERSION,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info"
    )