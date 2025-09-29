"""
Configuration Settings

Application configuration and environment variables.
"""

import os
from typing import Optional

class Settings:
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "SAR Drone Swarm API"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sar_missions.db")

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
    ]

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # WebSocket
    WS_URL: str = os.getenv("WS_URL", "ws://localhost:8000/ws")

    # External APIs
    OLLAMA_BASE_URL: Optional[str] = os.getenv("OLLAMA_BASE_URL")

    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    @property
    def CORS_ORIGINS(self) -> list:
        """Get CORS origins from environment or use defaults"""
        origins = os.getenv("CORS_ORIGINS")
        if origins:
            return [origin.strip() for origin in origins.split(",")]
        return self.BACKEND_CORS_ORIGINS

# Global settings instance
settings = Settings()