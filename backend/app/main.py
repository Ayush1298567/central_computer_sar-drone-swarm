"""
Main FastAPI application for the SAR drone system
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import create_tables
from .api import missions, drones, chat, websocket

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SAR Drone Command and Control System API",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(missions.router, prefix=settings.API_V1_STR)
app.include_router(drones.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SAR Drone Command System API",
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.VERSION
    }

@app.get(f"{settings.API_V1_STR}/info")
async def api_info():
    """API information endpoint"""
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": "v1",
        "endpoints": {
            "missions": f"{settings.API_V1_STR}/missions",
            "drones": f"{settings.API_V1_STR}/drones",
            "chat": f"{settings.API_V1_STR}/chat",
            "websocket": f"{settings.API_V1_STR}/ws"
        }
    }