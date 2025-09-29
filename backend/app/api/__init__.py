"""
API router package.
"""

from fastapi import APIRouter
from . import missions, drones, discoveries, chat, websocket

# Create main API router
router = APIRouter()

# Include sub-routers
router.include_router(missions.router, prefix="/missions", tags=["missions"])
router.include_router(drones.router, prefix="/drones", tags=["drones"])
router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(websocket.router, prefix="/ws", tags=["websocket"])