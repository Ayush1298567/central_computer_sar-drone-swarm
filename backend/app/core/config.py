"""
Application configuration management using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "SAR Drone Swarm Command Center"
    version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./sar_missions.db",
        description="Database connection URL"
    )
    
    # AI/Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama2", description="Default Ollama model")
    ai_conversation_timeout: int = Field(default=300, description="AI conversation timeout in seconds")
    
    # Mission Configuration
    max_mission_duration: int = Field(default=14400, description="Maximum mission duration in seconds (4 hours)")
    max_drones_per_mission: int = Field(default=10, description="Maximum drones per mission")
    default_search_altitude: float = Field(default=100.0, description="Default search altitude in meters")
    
    # Safety Configuration
    min_battery_level: float = Field(default=25.0, description="Minimum battery level for operations (%)")
    max_wind_speed: float = Field(default=15.0, description="Maximum wind speed for operations (m/s)")
    emergency_return_battery: float = Field(default=15.0, description="Battery level for emergency return (%)")
    
    # WebSocket Configuration
    websocket_ping_interval: int = Field(default=30, description="WebSocket ping interval in seconds")
    websocket_ping_timeout: int = Field(default=10, description="WebSocket ping timeout in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    # Real-time Processing
    video_stream_buffer_size: int = Field(default=10, description="Video stream buffer size")
    telemetry_update_interval: float = Field(default=1.0, description="Telemetry update interval in seconds")
    
    # File Storage
    upload_dir: str = Field(default="./uploads", description="Directory for file uploads")
    max_file_size: int = Field(default=100 * 1024 * 1024, description="Maximum file size in bytes (100MB)")
    
    # External Services
    weather_api_key: Optional[str] = Field(default=None, description="Weather API key")
    maps_api_key: Optional[str] = Field(default=None, description="Maps API key")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)