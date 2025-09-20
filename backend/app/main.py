"""
Main FastAPI application for SAR Drone Swarm Central Computer
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import settings
from .utils.logging import setup_logging, MissionLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger = logging.getLogger("startup")
    logger.info("Starting SAR Drone Swarm Central Computer")
    
    # Setup logging
    setup_logging()
    
    # Create required directories
    directories = [
        Path("logs"),
        Path(settings.STATIC_FILES_PATH),
        Path(settings.UPLOADS_PATH),
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Initialize mission logger
    mission_logger = MissionLogger("system")
    mission_logger.info("System startup completed", operation="startup")
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SAR Drone Swarm Central Computer")
    mission_logger.info("System shutdown initiated", operation="shutdown")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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

# Add TrustedHost middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger = logging.getLogger("exceptions")
    logger.error(
        f"HTTP {exc.status_code} error on {request.url}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "url": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger = logging.getLogger("validation")
    logger.error(
        f"Validation error on {request.url}: {exc.errors()}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger = logging.getLogger("exceptions")
    logger.error(
        f"Unexpected error on {request.url}: {str(exc)}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    Returns system status and basic information
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        "environment": "development" if settings.DEBUG else "production"
    }


# System info endpoint
@app.get("/info", tags=["System"])
async def system_info() -> Dict[str, Any]:
    """
    System information endpoint
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "api_version": settings.API_V1_STR,
        "documentation": {
            "swagger": f"{settings.API_V1_STR}/docs",
            "redoc": f"{settings.API_V1_STR}/redoc"
        }
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with basic API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "health_check": "/health",
        "api_docs": f"{settings.API_V1_STR}/docs"
    }


# Mount static files
if Path(settings.STATIC_FILES_PATH).exists():
    app.mount(
        "/static",
        StaticFiles(directory=settings.STATIC_FILES_PATH),
        name="static"
    )

# Mount uploads directory
if Path(settings.UPLOADS_PATH).exists():
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOADS_PATH),
        name="uploads"
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    logger = logging.getLogger("requests")
    
    # Log request
    logger.info(
        f"{request.method} {request.url}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info(
        f"Response {response.status_code} for {request.method} {request.url}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )