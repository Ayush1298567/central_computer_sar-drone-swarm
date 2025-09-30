#!/usr/bin/env python3
"""
Simple test script to verify logging system works without external dependencies.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Simple configuration class (no external dependencies)
class SimpleSettings:
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/sar_system.log"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    DEBUG = True

settings = SimpleSettings()

# Simple JSON formatter
class SimpleJSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        return json.dumps(log_entry)

def setup_simple_logging():
    """Simple logging setup without external dependencies."""
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler for development
    if settings.DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Use JSON formatter for file logs
    json_formatter = SimpleJSONFormatter()
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    return True

# Test the logging system
def test_logging():
    print("🧪 Testing logging system...")

    try:
        # Setup logging
        if setup_simple_logging():
            print("✅ Logging system setup successful")
        else:
            print("❌ Logging system setup failed")
            return False

        # Test basic logging
        logger = logging.getLogger("test_logger")
        logger.info("✅ Basic logging test successful")
        logger.warning("⚠️ Warning test message")
        logger.error("❌ Error test message")

        # Test logging with extra context
        mission_logger = logging.getLogger("mission")
        extra_data = {"mission_id": "test_mission_001", "drone_id": "drone_001"}
        mission_logger.info("🚁 Mission logging test", extra=extra_data)

        # Check if log file exists
        log_file_path = Path(settings.LOG_FILE)
        if log_file_path.exists():
            print(f"✅ Log file created successfully: {log_file_path}")

            # Show last few lines of log file
            try:
                with open(log_file_path, 'r') as f:
                    lines = f.readlines()
                    print(f"📄 Last {min(3, len(lines))} log entries:")
                    for line in lines[-3:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"⚠️ Could not read log file: {e}")
        else:
            print("❌ Log file was not created")
            return False

        print("✅ All logging tests passed!")
        return True

    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging()
    sys.exit(0 if success else 1)