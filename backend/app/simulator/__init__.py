"""
Drone Simulator Package

This package provides realistic drone simulation for testing the SAR system
without requiring actual drone hardware.
"""

from .drone_simulator import DroneSimulator
from .mock_detection import MockDetectionSystem

__all__ = ['DroneSimulator', 'MockDetectionSystem']