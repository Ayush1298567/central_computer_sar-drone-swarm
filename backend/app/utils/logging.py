"""
Logging configuration for SAR Mission Commander
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from .config import settings

def setup_logging():
    """Configure comprehensive logging"""

    # Create logs directory
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "sar_mission_commander.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure specific loggers
    configure_specific_loggers()

    # Suppress noisy third-party loggers
    suppress_noisy_loggers()

def configure_specific_loggers():
    """Configure specific application loggers"""

    # Database logger
    db_logger = logging.getLogger("sqlalchemy")
    db_logger.setLevel(logging.WARNING)  # Reduce SQL query noise

    # FastAPI logger
    fastapi_logger = logging.getLogger("uvicorn")
    fastapi_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Access logger
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(logging.INFO)

def suppress_noisy_loggers():
    """Suppress loggers from noisy third-party packages"""

    noisy_loggers = [
        "httpx",  # HTTP client
        "urllib3",  # HTTP client
        "asyncio",  # AsyncIO
        "aiohttp",  # Async HTTP client
    ]

    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"sar_mission_commander.{name}")

# Create a default logger for the application
logger = get_logger(__name__)