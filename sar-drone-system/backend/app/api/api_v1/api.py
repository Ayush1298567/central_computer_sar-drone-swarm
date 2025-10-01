"""
API v1 router configuration
"""
from fastapi import APIRouter
from .endpoints import missions, drones, discoveries, chat, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])