#!/usr/bin/env python3
"""
SAR Drone Central Computer System
Main application entry point
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from api.routes import router as api_router
from services.database import init_database
from services.redis_service import RedisService
from services.websocket_manager import WebSocketManager
from simulation.drone_simulator import DroneSimulator
from agents.agent_manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
redis_service = None
websocket_manager = None
drone_simulator = None
agent_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_service, websocket_manager, drone_simulator, agent_manager
    
    logger.info("Starting SAR Drone Central Computer System...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize Redis
        redis_service = RedisService()
        await redis_service.connect()
        logger.info("Redis connected")
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(redis_service)
        await websocket_manager.start()
        logger.info("WebSocket manager started")
        
        # Initialize drone simulator
        drone_simulator = DroneSimulator(redis_service, websocket_manager)
        await drone_simulator.start()
        logger.info("Drone simulator started")
        
        # Initialize AI agents
        agent_manager = AgentManager(redis_service, websocket_manager, drone_simulator)
        await agent_manager.start_all_agents()
        logger.info("AI agents started")
        
        logger.info("System fully operational")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down system...")
        if agent_manager:
            await agent_manager.stop_all_agents()
        if drone_simulator:
            await drone_simulator.stop()
        if websocket_manager:
            await websocket_manager.stop()
        if redis_service:
            await redis_service.disconnect()
        logger.info("System shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SAR Drone Central Computer",
    description="Central command system for search and rescue drone operations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files (React frontend)
frontend_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(frontend_path / "index.html"))
    
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        if path.startswith("api/"):
            return {"error": "API route not found"}
        return FileResponse(str(frontend_path / "index.html"))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "redis": redis_service.is_connected() if redis_service else False,
            "websocket": websocket_manager.is_running() if websocket_manager else False,
            "drone_simulator": drone_simulator.is_running() if drone_simulator else False,
            "agents": agent_manager.is_running() if agent_manager else False
        }
    }

if __name__ == "__main__":
    # Check if Ollama is running
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            logger.warning("Ollama not running. Please start Ollama and pull mistral:7b model")
    except:
        logger.warning("Ollama not running. Please start Ollama and pull mistral:7b model")
    
    # Start the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )