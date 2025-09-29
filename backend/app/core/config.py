"""
Configuration settings for SAR Mission Commander
"""
import os
from typing import List
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """Application settings with validation"""

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sar_missions.db")

    # AI settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")

    # Mission settings
    MAX_MISSIONS: int = int(os.getenv("MAX_MISSIONS", "100"))
    MAX_DRONES: int = int(os.getenv("MAX_DRONES", "50"))
    DEFAULT_MISSION_TIMEOUT_MINUTES: int = int(os.getenv("DEFAULT_MISSION_TIMEOUT_MINUTES", "120"))

    # File upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

    # Notification settings
    ENABLE_WEBSOCKET_NOTIFICATIONS: bool = os.getenv("ENABLE_WEBSOCKET_NOTIFICATIONS", "true").lower() == "true"

    class Config:
        case_sensitive = True

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Validate secret key length"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @validator("PORT")
    def validate_port(cls, v):
        """Validate port range"""
        if not (1 <= v <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

# Global settings instance
settings = Settings()