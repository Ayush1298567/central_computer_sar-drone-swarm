"""
Core configuration for SAR Drone System
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with Ollama integration"""
    
    # Application Configuration
    APP_NAME: str = "SAR Drone System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./sar_missions.db"
    
    # AI Configuration - Ollama Local LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT: int = 120
    
    # Legacy API keys (kept for compatibility but not used)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Security
    SECRET_KEY: str = "sar-drone-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Mission Configuration
    DEFAULT_SEARCH_ALTITUDE: float = 100.0  # meters
    DEFAULT_FLIGHT_TIME: int = 30  # minutes
    MAX_DRONES_PER_MISSION: int = 10
    
    # Computer Vision
    YOLO_MODEL_PATH: str = "./yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)