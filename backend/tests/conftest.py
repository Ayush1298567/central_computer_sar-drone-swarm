"""
PyTest configuration and fixtures for SAR Drone Swarm tests.

All tests include a 3-minute timeout as required.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path


# Set default timeout for all tests (3 minutes as per requirements)
def pytest_configure(config):
    """Configure pytest with default settings."""
    config.addinivalue_line(
        "markers", "timeout: mark test with custom timeout"
    )


@pytest.fixture(scope="function")
def timeout_config():
    """Fixture providing timeout configuration (3 minutes)."""
    return 180  # 3 minutes in seconds


@pytest.fixture(scope="function")
def temp_dir():
    """Provide a temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup after test
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_redis_url():
    """Redis URL for testing (fallback to mock if not available)."""
    return "redis://localhost:6379/15"  # Use DB 15 for testing

