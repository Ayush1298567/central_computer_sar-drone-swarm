"""
Main API router that includes all v1 API endpoints.
"""

from fastapi import APIRouter
from .endpoints import chat, drones, missions, discoveries, websocket

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])