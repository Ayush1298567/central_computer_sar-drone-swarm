"""
Core configuration and database management for the SAR Mission Commander system.

This module provides:
- Application settings and configuration management
- Database connection and session management
- Environment configuration utilities
"""

from .config import settings, DroneCapabilities, MissionDefaults, get_environment_info
from .database import engine, SessionLocal, get_db, create_tables, DatabaseManager

__all__ = [
    "settings",
    "DroneCapabilities", 
    "MissionDefaults",
    "get_environment_info",
    "engine",
    "SessionLocal", 
    "get_db",
    "create_tables",
    "DatabaseManager"
]