import os
from typing import Optional, List
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings with Pydantic V2 configuration"""
    
    model_config = ConfigDict(case_sensitive=True, env_file=".env")
    
    # Database
    DATABASE_URL: str = "sqlite:///./sar_drone.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SAR Drone Swarm Control"
    APP_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    
    # Ollama AI
    OLLAMA_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama3.2:3b"
    
    # OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None
    
    # WebSocket
    WS_URL: str = "ws://localhost:8000/ws"
    
    # Drone Configuration
    MAX_DRONES: int = 10
    DEFAULT_ALTITUDE: int = 50
    DEFAULT_SPEED: float = 5.0
    MIN_DRONE_SEPARATION: float = 10.0
    
    # Mission Settings
    DEFAULT_SEARCH_PATTERN: str = "grid"
    DEFAULT_SEARCH_DENSITY: str = "medium"
    MAX_MISSION_DURATION: int = 3600  # 1 hour in seconds
    DEFAULT_SEARCH_ALTITUDE: int = 50
    DISCOVERY_INVESTIGATION_RADIUS: float = 25.0
    
    # Emergency Settings
    LOW_BATTERY_THRESHOLD: float = 20.0
    CRITICAL_BATTERY_THRESHOLD: float = 15.0
    COMMUNICATION_TIMEOUT: int = 30
    BATTERY_RESERVE_THRESHOLD: float = 25.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        if not v or not v.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
            raise ValueError('Invalid DATABASE_URL format. Must start with sqlite:///, postgresql://, or mysql://')
        return v
    
    @field_validator('OLLAMA_HOST')
    @classmethod
    def validate_ollama_host(cls, v: str) -> str:
        """Validate Ollama host URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('OLLAMA_HOST must start with http:// or https://')
        return v
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength"""
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters for security')
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins - never allow wildcard in production"""
        if "*" in v:
            logger.warning("WARNING: Wildcard CORS origins detected - this is insecure!")
        return v
    
    @field_validator('MAX_DRONES')
    @classmethod
    def validate_max_drones(cls, v: int) -> int:
        """Validate maximum drone count"""
        if v < 1 or v > 50:
            raise ValueError('MAX_DRONES must be between 1 and 50')
        return v
    
    @field_validator('DEFAULT_ALTITUDE')
    @classmethod
    def validate_altitude(cls, v: int) -> int:
        """Validate default altitude"""
        if v < 10 or v > 120:
            raise ValueError('DEFAULT_ALTITUDE must be between 10 and 120 meters')
        return v

# Global settings instance
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger.info(f"Settings loaded: {settings.PROJECT_NAME}")
logger.info(f"Database: {settings.DATABASE_URL}")
logger.info(f"Ollama: {settings.OLLAMA_HOST}")
logger.info(f"CORS Origins: {settings.ALLOWED_ORIGINS}")