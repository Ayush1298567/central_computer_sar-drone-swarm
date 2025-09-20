"""
Configuration management for SAR Drone Command & Control System.
Handles environment variables, settings validation, and configuration defaults.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    All settings can be overridden via environment variables with SAR_ prefix.
    """
    
    # Application settings
    APP_NAME: str = "SAR Drone Command & Control System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./sar_missions.db"
    DATABASE_ECHO: bool = False
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/sar_system.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".txt", ".csv", ".json"]
    
    # Mission settings
    DEFAULT_SEARCH_ALTITUDE: float = 100.0  # meters
    MIN_SEARCH_ALTITUDE: float = 30.0
    MAX_SEARCH_ALTITUDE: float = 400.0
    DEFAULT_DRONE_SPEED: float = 10.0  # m/s
    MAX_MISSION_DURATION: int = 180  # minutes
    
    # Drone communication settings
    DRONE_HEARTBEAT_INTERVAL: int = 5  # seconds
    DRONE_TIMEOUT: int = 30  # seconds
    MAX_DRONES_PER_MISSION: int = 10
    
    # AI/ML settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    AI_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Weather API settings
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Notification settings
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_HOSTS from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Parse ALLOWED_EXTENSIONS from string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("DEFAULT_SEARCH_ALTITUDE")
    @classmethod
    def validate_search_altitude(cls, v, info):
        """Validate search altitude is within bounds."""
        # Access other field values from info.data
        if info.data:
            min_alt = info.data.get("MIN_SEARCH_ALTITUDE", 30.0)
            max_alt = info.data.get("MAX_SEARCH_ALTITUDE", 400.0)
            if not (min_alt <= v <= max_alt):
                raise ValueError(f"DEFAULT_SEARCH_ALTITUDE must be between {min_alt} and {max_alt}")
        return v
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            Path(self.LOG_FILE).parent,
            Path(self.UPLOAD_DIR),
            Path(self.UPLOAD_DIR) / "mission_data",
            Path(self.UPLOAD_DIR) / "drone_logs",
            Path(self.UPLOAD_DIR) / "discoveries",
            Path(self.UPLOAD_DIR) / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    model_config = {
        "env_prefix": "SAR_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.create_directories()