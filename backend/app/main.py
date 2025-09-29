"""
SAR Drone Swarm Central Computer - Main Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.api_v1.api import api_router
from app.services.coordination_engine import coordination_engine
from app.services.analytics_engine import analytics_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sar_mission_commander.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting SAR Mission Commander...")
    await create_tables()
    logger.info("Database tables created successfully")

    # Initialize services
    await analytics_engine.initialize()

    yield

    # Shutdown
    logger.info("Shutting down SAR Mission Commander...")

# Create FastAPI application
app = FastAPI(
    title="SAR Drone Swarm Central Computer",
    description="Advanced Search and Rescue drone coordination system",
    version="1.0.0",
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

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time mission updates."""
    await websocket.accept()
    logger.info(f"WebSocket client {client_id} connected")

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            if data.get("type") == "subscribe_mission":
                mission_id = data.get("mission_id")
                # Subscribe client to mission updates
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "mission_id": mission_id
                })

            elif data.get("type") == "heartbeat":
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": asyncio.get_event_loop().time()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SAR Drone Swarm Central Computer",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "database": "connected",
            "coordination_engine": "running",
            "analytics_engine": "running"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )