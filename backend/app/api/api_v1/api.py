"""
Main API router for version 1 endpoints.
"""

from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    drones, missions, discoveries, chat, analytics, coordination, tasks, weather
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(coordination.router, prefix="/coordination", tags=["coordination"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])