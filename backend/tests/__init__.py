"""
Test suite for SAR Drone Swarm System Backend

This package contains all test modules for the backend system.
Tests are designed to run without hardware dependencies using mocks and simulators.
"""

import sys
import os

# Add backend to path for imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

