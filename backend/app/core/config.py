"""
Application configuration settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS Configuration
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./sar_missions.db"
    # For PostgreSQL in production:
    # DATABASE_URL: str = "postgresql://user:password@localhost/sar_missions"

    # File Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Weather API Configuration
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = "llama2"

    # Drone Configuration
    DEFAULT_DRONE_ALTITUDE: float = 20.0  # meters
    DEFAULT_SEARCH_ALTITUDE: float = 30.0  # meters
    MIN_DRONE_SEPARATION: float = 50.0  # meters
    BATTERY_RESERVE_THRESHOLD: float = 25.0  # percentage

    # Mission Configuration
    MAX_MISSION_DURATION: int = 120  # minutes
    DEFAULT_SEARCH_PATTERN: str = "lawnmower"
    DISCOVERY_INVESTIGATION_RADIUS: float = 100.0  # meters

    # Analytics Configuration
    ANALYTICS_RETENTION_DAYS: int = 30
    PERFORMANCE_METRICS_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()