"""
Configuration settings for the SAR Drone System
"""
import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SAR Drone Swarm Central Computer"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Central command system for SAR drone operations"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./sar_missions.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Static Files
    STATIC_FILES_PATH: str = "static"
    UPLOADS_PATH: str = "uploads"
    
    # Mission Settings
    MAX_MISSION_DURATION_HOURS: int = 24
    MAX_DRONES_PER_MISSION: int = 10
    DEFAULT_SEARCH_ALTITUDE: int = 100  # meters
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()