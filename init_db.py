#!/usr/bin/env python3
"""
Database initialization script for SAR Mission Commander.
"""

import asyncio
import logging
from app.core.database import create_tables, init_db
from app.models import Drone, Mission, Discovery, ChatSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize the database with tables and seed data."""
    try:
        logger.info("Initializing SAR Mission Commander database...")

        # Create all tables
        await create_tables()

        # Initialize with seed data
        await init_db()

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())