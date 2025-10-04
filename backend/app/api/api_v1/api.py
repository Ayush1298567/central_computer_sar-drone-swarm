from fastapi import APIRouter
from app.api.api_v1.endpoints import websocket

api_router = APIRouter()

# Include WebSocket router
api_router.include_router(websocket.router, tags=["websocket"])