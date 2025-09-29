"""
Main FastAPI application for SAR Mission Commander
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager

from .core.database import create_tables
from .core.config import settings
from .api.missions import router as missions_router
from .api.websocket import router as websocket_router
from .services.conversational_mission_planner import ConversationalMissionPlanner
from .services.notification_service import NotificationService
from .ai.ollama_client import OllamaClient
from .utils.logging import setup_logging

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Mission Commander SAR System")

    # Initialize database
    print("📊 Initializing database...")
    create_tables()
    print("✅ Database initialized")

    # Initialize services
    print("🔧 Initializing services...")

    # Initialize AI client
    app.state.ai_client = OllamaClient()

    # Initialize mission planner
    app.state.mission_planner = ConversationalMissionPlanner()

    # Initialize notification service
    app.state.notification_service = NotificationService()

    # Test AI connection
    try:
        health_check = await app.state.ai_client.health_check()
        if health_check:
            print("✅ AI service connected")
        else:
            print("⚠️ AI service not available - using fallback responses")
    except Exception as e:
        print(f"⚠️ AI service connection failed: {e}")
        print("ℹ️ System will use fallback responses")

    print("✅ Services initialized")
    print(f"🌐 Server starting on {settings.HOST}:{settings.PORT}")

    yield

    # Shutdown
    print("🛑 Shutting down Mission Commander SAR System")

# Create FastAPI application
app = FastAPI(
    title="SAR Mission Commander",
    description="Search and Rescue Mission Command and Control System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Include routers
app.include_router(missions_router)
app.include_router(websocket_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SAR Mission Commander",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Would be dynamic
        "services": {
            "database": "connected",
            "ai_service": "available" if hasattr(request.app.state, 'ai_client') else "unavailable"
        }
    }

@app.get("/api/v1/status")
async def api_status(request: Request):
    """API status endpoint"""
    ai_available = True
    try:
        await request.app.state.ai_client.health_check()
    except:
        ai_available = False

    return {
        "version": "1.0.0",
        "ai_service_available": ai_available,
        "websocket_connections": request.app.state.notification_service.connection_manager.get_connection_count() if hasattr(request.app.state, 'notification_service') else 0
    }

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )