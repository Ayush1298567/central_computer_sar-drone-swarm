"""
API Package

This package contains all API routers for the SAR drone system.
"""

from .missions import router as missions_router
from .drones import router as drones_router
from .discoveries import router as discoveries_router
from .chat import router as chat_router
from .websocket import router as websocket_router

__all__ = [
    'missions_router',
    'drones_router',
    'discoveries_router',
    'chat_router',
    'websocket_router'
]