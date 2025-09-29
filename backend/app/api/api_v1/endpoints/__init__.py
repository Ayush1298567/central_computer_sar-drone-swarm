"""
API endpoints package.
"""

from .drones import router as drones_router
from .missions import router as missions_router
from .discoveries import router as discoveries_router
from .chat import router as chat_router
from .analytics import router as analytics_router
from .coordination import router as coordination_router
from .tasks import router as tasks_router
from .weather import router as weather_router

__all__ = [
    "drones_router",
    "missions_router",
    "discoveries_router",
    "chat_router",
    "analytics_router",
    "coordination_router",
    "tasks_router",
    "weather_router"
]