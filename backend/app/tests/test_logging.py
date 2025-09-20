"""
Tests for logging system
"""
import json
import logging
import tempfile
import os
from pathlib import Path
from ..utils.logging import JSONFormatter, setup_logging, MissionLogger


class TestJSONFormatter:
    """Test cases for JSONFormatter"""
    
    def test_json_formatter_basic(self):
        """Test basic JSON formatting"""
        formatter = JSONFormatter()
        
        # Create a test log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        # Format the record
        formatted = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(formatted)
        
        # Verify required fields
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
    
    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatting with extra fields"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.mission_id = "mission_123"
        record.drone_id = "drone_456"
        record.operation = "test_operation"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify extra fields
        assert log_data["mission_id"] == "mission_123"
        assert log_data["drone_id"] == "drone_456"
        assert log_data["operation"] == "test_operation"


class TestMissionLogger:
    """Test cases for MissionLogger"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Create temporary log file
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
        
        # Setup basic logging to file
        logger = logging.getLogger("test_mission")
        logger.handlers.clear()
        
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        # Clean up temp files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_mission_logger_creation(self):
        """Test MissionLogger creation"""
        logger = MissionLogger(
            logger_name="test_mission",
            mission_id="mission_123",
            drone_id="drone_456",
            user_id="user_789"
        )
        
        assert logger.mission_id == "mission_123"
        assert logger.drone_id == "drone_456"
        assert logger.user_id == "user_789"
    
    def test_mission_logger_basic_logging(self):
        """Test basic logging methods"""
        logger = MissionLogger(
            logger_name="test_mission",
            mission_id="mission_123"
        )
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Check that log file was created and contains entries
        assert os.path.exists(self.log_file)
        
        with open(self.log_file, 'r') as f:
            log_contents = f.read()
            assert "Debug message" in log_contents
            assert "Info message" in log_contents
            assert "Warning message" in log_contents
            assert "Error message" in log_contents
            assert "Critical message" in log_contents
    
    def test_mission_logger_specialized_methods(self):
        """Test specialized logging methods"""
        logger = MissionLogger(
            logger_name="test_mission",
            mission_id="mission_123",
            drone_id="drone_456"
        )
        
        # Test mission start/end
        mission_data = {"area": "test_area", "priority": "high"}
        logger.mission_start(mission_data)
        
        summary = {"discoveries": 2, "area_covered": 50.5}
        logger.mission_end("completed", summary)
        
        # Test drone status
        location = {"latitude": 40.7128, "longitude": -74.0060}
        logger.drone_status("flying", location)
        
        # Test discovery event
        logger.discovery_event("person", 0.85, location)
        
        # Test error event
        context = {"battery_level": 15}
        logger.error_event("low_battery", "Battery critically low", context)
        
        # Verify log file contains all events
        with open(self.log_file, 'r') as f:
            log_contents = f.read()
            assert "mission_start" in log_contents
            assert "mission_end" in log_contents
            assert "drone_status" in log_contents
            assert "discovery" in log_contents
            assert "error" in log_contents


class TestLoggingSetup:
    """Test logging setup function"""
    
    def test_setup_logging_creates_directories(self):
        """Test that setup_logging creates necessary directories"""
        # Change to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Run setup
            setup_logging()
            
            # Check that logs directory was created
            assert os.path.exists("logs")
            assert os.path.isdir("logs")
    
    def test_setup_logging_configures_handlers(self):
        """Test that setup_logging configures handlers properly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Clear existing handlers
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            
            setup_logging()
            
            # Check that handlers were added
            assert len(root_logger.handlers) >= 2  # Console + File
            
            # Check handler types
            handler_types = [type(h).__name__ for h in root_logger.handlers]
            assert "StreamHandler" in handler_types  # Console
            assert "RotatingFileHandler" in handler_types  # File


def run_logging_tests():
    """Run all logging tests"""
    print("Testing JSON Formatter...")
    formatter_test = TestJSONFormatter()
    formatter_test.test_json_formatter_basic()
    formatter_test.test_json_formatter_with_extra_fields()
    print("✓ JSON Formatter tests passed")
    
    print("Testing Mission Logger...")
    logger_test = TestMissionLogger()
    logger_test.setup_method()
    try:
        logger_test.test_mission_logger_creation()
        logger_test.test_mission_logger_basic_logging()
        logger_test.test_mission_logger_specialized_methods()
        print("✓ Mission Logger tests passed")
    finally:
        logger_test.teardown_method()
    
    print("Testing Logging Setup...")
    setup_test = TestLoggingSetup()
    setup_test.test_setup_logging_creates_directories()
    setup_test.test_setup_logging_configures_handlers()
    print("✓ Logging Setup tests passed")
    
    print("All logging tests passed!")


if __name__ == "__main__":
    run_logging_tests()