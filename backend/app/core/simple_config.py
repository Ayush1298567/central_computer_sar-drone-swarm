"""
Simple configuration module for testing without external dependencies.
"""

import os
from pathlib import Path

class SimpleSettings:
    """Simple configuration settings without external dependencies."""

    # Application basics
    APP_NAME: str = "Mission Commander SAR System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database Configuration (using SQLite for simplicity)
    DATABASE_URL: str = "sqlite:///./sar_missions.db"

    # AI Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama3.2:3b"
    MODEL_TIMEOUT: int = 30

    # File Storage
    UPLOAD_DIR: str = "uploads"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/sar_system.log"

    # Mission Configuration
    MAX_CONCURRENT_MISSIONS: int = 10
    MAX_DRONES_PER_MISSION: int = 15
    DEFAULT_SEARCH_ALTITUDE: float = 20.0

# Create settings instance
settings = SimpleSettings()

# Create directories
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.LOG_FILE).parent.mkdir(exist_ok=True)