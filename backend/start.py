#!/usr/bin/env python3
"""
Startup script for SAR Mission Commander backend.
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Mission Commander SAR System - Backend")
    print("=" * 60)
    print(f"Version: {settings.APP_VERSION}")
    print(f"Host: {settings.API_HOST}:{settings.API_PORT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL}")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
