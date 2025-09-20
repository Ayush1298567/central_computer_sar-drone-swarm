"""
Structured logging system for SAR Drone operations
"""
import json
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from ..core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "mission_id"):
            log_entry["mission_id"] = record.mission_id
        if hasattr(record, "drone_id"):
            log_entry["drone_id"] = record.drone_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        
        return json.dumps(log_entry)


def setup_logging() -> None:
    """Setup application logging with file and console handlers"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON format and rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class MissionLogger:
    """Context-aware logger for mission operations"""
    
    def __init__(
        self,
        logger_name: str = "mission",
        mission_id: Optional[str] = None,
        drone_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        self.logger = logging.getLogger(logger_name)
        self.mission_id = mission_id
        self.drone_id = drone_id
        self.user_id = user_id
    
    def _log(
        self,
        level: int,
        message: str,
        operation: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Internal logging method with context"""
        extra = {
            "mission_id": self.mission_id,
            "drone_id": self.drone_id,
            "user_id": self.user_id,
            "operation": operation,
        }
        
        # Add any extra data
        if extra_data:
            extra.update(extra_data)
        
        # Remove None values
        extra = {k: v for k, v in extra.items() if v is not None}
        
        self.logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, operation: Optional[str] = None, **kwargs) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, operation, **kwargs)
    
    def info(self, message: str, operation: Optional[str] = None, **kwargs) -> None:
        """Log info message"""
        self._log(logging.INFO, message, operation, **kwargs)
    
    def warning(self, message: str, operation: Optional[str] = None, **kwargs) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, operation, **kwargs)
    
    def error(self, message: str, operation: Optional[str] = None, **kwargs) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, operation, **kwargs)
    
    def critical(self, message: str, operation: Optional[str] = None, **kwargs) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, operation, **kwargs)
    
    def mission_start(self, mission_data: Dict[str, Any]) -> None:
        """Log mission start event"""
        self.info(
            f"Mission {self.mission_id} started",
            operation="mission_start",
            extra_data={"mission_data": mission_data}
        )
    
    def mission_end(self, result: str, summary: Dict[str, Any]) -> None:
        """Log mission end event"""
        self.info(
            f"Mission {self.mission_id} ended: {result}",
            operation="mission_end",
            extra_data={"result": result, "summary": summary}
        )
    
    def drone_status(self, status: str, location: Optional[Dict[str, float]] = None) -> None:
        """Log drone status update"""
        extra_data = {"status": status}
        if location:
            extra_data["location"] = location
        
        self.info(
            f"Drone {self.drone_id} status: {status}",
            operation="drone_status",
            extra_data=extra_data
        )
    
    def discovery_event(self, discovery_type: str, confidence: float, location: Dict[str, float]) -> None:
        """Log discovery event"""
        self.info(
            f"Discovery detected: {discovery_type} (confidence: {confidence:.2f})",
            operation="discovery",
            extra_data={
                "discovery_type": discovery_type,
                "confidence": confidence,
                "location": location
            }
        )
    
    def error_event(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error event with context"""
        extra_data = {"error_type": error_type, "error_message": error_message}
        if context:
            extra_data["context"] = context
        
        self.error(
            f"Error occurred: {error_type} - {error_message}",
            operation="error",
            extra_data=extra_data
        )