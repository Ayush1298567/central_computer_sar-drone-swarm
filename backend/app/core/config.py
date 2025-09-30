from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application configuration management."""

    # Application basics
    APP_NAME: str = "Mission Commander SAR System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./sar_missions.db"
    POSTGRES_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"

    # AI Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama3.2:3b"
    MODEL_TIMEOUT: int = 30
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.1

    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_VIDEO_FORMATS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
    ALLOWED_IMAGE_FORMATS: List[str] = [".jpg", ".jpeg", ".png", ".bmp"]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/sar_system.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Mission Configuration
    MAX_CONCURRENT_MISSIONS: int = 10
    MAX_DRONES_PER_MISSION: int = 15
    DEFAULT_SEARCH_ALTITUDE: float = 20.0  # meters
    MIN_BATTERY_LEVEL: float = 20.0  # percentage
    MAX_WIND_SPEED: float = 15.0  # m/s

    # Communication Configuration
    WEBSOCKET_PING_INTERVAL: int = 30  # seconds
    WEBSOCKET_PING_TIMEOUT: int = 10  # seconds
    TELEMETRY_UPDATE_INTERVAL: float = 1.0  # seconds
    MAX_TELEMETRY_BUFFER: int = 1000  # records

    @validator("SECRET_KEY")
    def secret_key_must_be_set(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be set")
        return v

    @validator("UPLOAD_DIR")
    def create_upload_directory(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @validator("LOG_FILE")
    def create_log_directory(cls, v):
        Path(v).parent.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

class DroneCapabilities:
    """Default drone performance capabilities."""

    DEFAULT_MAX_FLIGHT_TIME = 25  # minutes
    DEFAULT_CRUISE_SPEED = 10.0  # m/s
    DEFAULT_MAX_RANGE = 5000.0  # meters
    DEFAULT_COVERAGE_RATE = 0.1  # km²/minute

    # Battery performance curves
    BATTERY_DISCHARGE_RATES = {
        "hovering": 0.8,  # %/minute
        "cruising": 1.2,  # %/minute
        "searching": 1.5,  # %/minute
        "high_speed": 2.0  # %/minute
    }

    # Environmental impact factors
    WIND_IMPACT_FACTOR = 0.1  # 10% battery increase per m/s wind
    TEMPERATURE_IMPACT = {
        "cold": 1.2,  # 20% increase in cold weather
        "normal": 1.0,
        "hot": 1.1  # 10% increase in hot weather
    }