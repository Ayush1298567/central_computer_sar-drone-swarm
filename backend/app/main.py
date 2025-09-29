"""
Main FastAPI Application

SAR Drone Swarm Backend API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api import missions, drones, discoveries, chat, websocket
from .core.config import settings
from .core.database import engine
from .models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title="SAR Drone Swarm API",
    description="Backend API for Search and Rescue drone swarm management",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
app.include_router(drones.router, prefix="/api/drones", tags=["drones"])
app.include_router(discoveries.router, prefix="/api/discoveries", tags=["discoveries"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SAR Drone Swarm API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )