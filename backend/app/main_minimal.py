from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Life-saving Search and Rescue drone swarm control system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": "not_connected",
        "services": {
            "database": False,
            "api": True,
            "websocket": False
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "SAR Drone Swarm Control System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

# Basic API endpoints
@app.get("/api/v1/drones")
async def get_drones():
    """Get all drones"""
    return {
        "drones": [
            {"id": 1, "name": "Drone 1", "status": "active", "battery": 85, "latitude": 37.7749, "longitude": -122.4194},
            {"id": 2, "name": "Drone 2", "status": "standby", "battery": 92, "latitude": 37.7849, "longitude": -122.4094}
        ]
    }

@app.get("/api/v1/missions")
async def get_missions():
    """Get all missions"""
    return {
        "missions": [
            {"id": 1, "name": "Search Mission 1", "status": "planning", "area": "San Francisco Bay"},
            {"id": 2, "name": "Rescue Mission 2", "status": "active", "area": "Golden Gate Park"}
        ]
    }

@app.post("/api/v1/missions")
async def create_mission(mission_data: dict):
    """Create a new mission"""
    return {
        "message": "Mission created",
        "mission_id": 3,
        "status": "created",
        "data": mission_data
    }

@app.get("/api/v1/discoveries")
async def get_discoveries():
    """Get all discoveries"""
    return {
        "discoveries": [
            {"id": 1, "type": "person", "confidence": 0.95, "location": {"lat": 37.7749, "lng": -122.4194}},
            {"id": 2, "type": "vehicle", "confidence": 0.87, "location": {"lat": 37.7849, "lng": -122.4094}}
        ]
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
        "app.main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )