"""
Core configuration settings for the SAR Mission Commander backend.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./sar_missions.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB

    # AI/Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # Mission settings
    max_drones_per_mission: int = 10
    default_search_altitude: float = 50.0  # meters
    max_mission_duration: int = 120  # minutes

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/sar_mission_commander.log"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()