"""
Advanced logging system for SAR Drone Command & Control System.
Provides structured JSON logging, context-aware mission logging, and proper log rotation.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Converts log records to JSON format with additional context.
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add process and thread information
        log_data["process_id"] = record.process
        log_data["thread_id"] = record.thread
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if enabled
        if self.include_extra and hasattr(record, '__dict__'):
            extra_fields = {
                key: value for key, value in record.__dict__.items()
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                    'thread', 'threadName', 'processName', 'process', 'message',
                    'getMessage', 'taskName'  # Added more reserved fields
                }
            }
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format timestamp in ISO format with timezone."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat()


class MissionLogger:
    """
    Context-aware logger for mission operations.
    Provides mission-specific logging with structured context.
    """
    
    def __init__(self, logger_name: str, mission_id: Optional[str] = None):
        self.logger = logging.getLogger(logger_name)
        self.mission_id = mission_id
        self.context = {}
    
    def set_mission_context(self, mission_id: str, **kwargs):
        """Set mission context for all subsequent logs."""
        self.mission_id = mission_id
        self.context.update(kwargs)
    
    def add_context(self, **kwargs):
        """Add additional context to logs."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context."""
        self.mission_id = None
        self.context = {}
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Internal method to log with context."""
        extra = dict(self.context)
        
        if self.mission_id:
            extra["mission_id"] = self.mission_id
        
        # Handle exc_info separately to avoid conflicts
        exc_info = kwargs.pop('exc_info', False)
        
        # Add any additional kwargs
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def mission_start(self, mission_id: str, **mission_data):
        """Log mission start with full context."""
        self.set_mission_context(mission_id, **mission_data)
        self.info(
            f"Mission {mission_id} started",
            event_type="mission_start",
            mission_data=mission_data
        )
    
    def mission_end(self, status: str, **result_data):
        """Log mission end with results."""
        self.info(
            f"Mission {self.mission_id} ended with status: {status}",
            event_type="mission_end",
            status=status,
            result_data=result_data
        )
        self.clear_context()
    
    def drone_event(self, drone_id: str, event_type: str, **event_data):
        """Log drone-specific events."""
        self.info(
            f"Drone {drone_id} event: {event_type}",
            event_type="drone_event",
            drone_id=drone_id,
            drone_event_type=event_type,
            event_data=event_data
        )
    
    def discovery_event(self, discovery_type: str, confidence: float, **discovery_data):
        """Log discovery events with confidence scores."""
        self.info(
            f"Discovery detected: {discovery_type} (confidence: {confidence:.2f})",
            event_type="discovery",
            discovery_type=discovery_type,
            confidence=confidence,
            discovery_data=discovery_data
        )
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    json_format: bool = True,
    console_output: bool = True
) -> None:
    """
    Setup comprehensive logging system with file rotation and JSON formatting.
    
    Args:
        log_level: Logging level (defaults to settings.LOG_LEVEL)
        log_file: Log file path (defaults to settings.LOG_FILE)
        max_bytes: Max log file size (defaults to settings.LOG_MAX_SIZE)
        backup_count: Number of backup files (defaults to settings.LOG_BACKUP_COUNT)
        json_format: Use JSON formatting
        console_output: Enable console output
    """
    
    # Use settings defaults if not provided
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    max_bytes = max_bytes or settings.LOG_MAX_SIZE
    backup_count = backup_count or settings.LOG_BACKUP_COUNT
    
    # Create log directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        json_formatter = JSONFormatter(include_extra=True)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        json_formatter = detailed_formatter
        console_formatter = detailed_formatter
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    loggers_config = {
        'uvicorn': {'level': 'INFO', 'propagate': True},
        'uvicorn.access': {'level': 'INFO', 'propagate': True},
        'sqlalchemy.engine': {'level': 'WARNING', 'propagate': True},
        'sqlalchemy.pool': {'level': 'WARNING', 'propagate': True},
        'aiosqlite': {'level': 'WARNING', 'propagate': True},
    }
    
    for logger_name, config in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, config['level']))
        logger.propagate = config['propagate']
    
    # Log setup completion
    setup_logger = MissionLogger("logging_setup")
    setup_logger.info(
        "Logging system initialized",
        log_level=log_level,
        log_file=log_file,
        json_format=json_format,
        console_output=console_output
    )


def get_mission_logger(name: str, mission_id: Optional[str] = None) -> MissionLogger:
    """
    Get a mission logger instance.
    
    Args:
        name: Logger name
        mission_id: Optional mission ID for context
        
    Returns:
        MissionLogger instance
    """
    return MissionLogger(name, mission_id)


def log_performance(func_name: str, duration: float, **kwargs):
    """
    Log performance metrics for functions.
    
    Args:
        func_name: Function name
        duration: Execution duration in seconds
        **kwargs: Additional context
    """
    perf_logger = MissionLogger("performance")
    perf_logger.info(
        f"Function {func_name} executed",
        event_type="performance",
        function_name=func_name,
        duration_seconds=duration,
        **kwargs
    )


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """
    Log API request metrics.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
        **kwargs: Additional context
    """
    api_logger = MissionLogger("api")
    api_logger.info(
        f"{method} {path} - {status_code}",
        event_type="api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_seconds=duration,
        **kwargs
    )