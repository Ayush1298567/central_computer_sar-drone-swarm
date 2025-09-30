#!/usr/bin/env python3
"""
Mission Commander SAR System - Backend Startup Script

This script initializes the SAR drone control system with proper logging,
database setup, and application startup.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import configuration first
try:
    from app.core.config import settings
except ImportError as e:
    print(f"Failed to import configuration: {e}")
    sys.exit(1)

# Setup logging system
try:
    from app.utils.logging import setup_logging
    setup_logging()
except ImportError as e:
    print(f"Failed to setup logging: {e}")
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

def main():
    """Main application startup function."""

    logger.info("Starting Mission Commander SAR System")
    logger.info(f"Environment: Development Mode = {settings.DEBUG}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"AI Model: {settings.DEFAULT_MODEL}")

    try:
        # Test database connection
        from app.core.database import DatabaseManager
        db_manager = DatabaseManager()

        if db_manager.health_check():
            logger.info("✅ Database connection established successfully")
        else:
            logger.error("❌ Database connection failed")
            raise Exception("Database initialization failed")

        # Test logging system
        logger.info("✅ Logging system initialized successfully")
        logger.info("✅ Application startup completed successfully")

        # Start the FastAPI application
        logger.info("🚀 Starting FastAPI server...")

        uvicorn.run(
            "app.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )

    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        logger.error("Stack trace:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()