"""
Application configuration settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./sar_missions.db")
    DATABASE_TEST_URL: str = Field(default="sqlite:///./test_sar_missions.db")

    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # API settings
    API_V1_PREFIX: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="SAR Drone Swarm API")

    # Drone settings
    MIN_DRONE_SEPARATION: float = Field(default=50.0)  # meters
    MAX_MISSION_DURATION: int = Field(default=360)  # minutes
    BATTERY_RESERVE_THRESHOLD: float = Field(default=20.0)  # percentage
    DEFAULT_SEARCH_ALTITUDE: float = Field(default=30.0)  # meters
    DISCOVERY_INVESTIGATION_RADIUS: float = Field(default=100.0)  # meters

    # Weather settings
    WEATHER_API_KEY: Optional[str] = Field(default=None)
    WEATHER_API_URL: str = Field(default="https://api.openweathermap.org/data/2.5")

    # AI settings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    AI_MODEL: str = Field(default="llama2")

    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    UPLOAD_DIR: str = Field(default="./uploads")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="./logs/sar_mission_commander.log")

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",  # React dev server
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()