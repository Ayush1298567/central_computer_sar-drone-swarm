from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    websocket,
    missions,
    drones,
    discoveries,
    tasks,
    computer_vision,
    coordination,
    adaptive_planning,
    learning_system,
    analytics,
    chat,
    video,
    weather,
    ai_governance,
    test_data,
    ai as ai_endpoints,
)
from app.auth import routes as auth_routes

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_routes.router, tags=["auth"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(computer_vision.router, prefix="/vision", tags=["computer-vision"])
api_router.include_router(coordination.router, prefix="/coordination", tags=["coordination"])
api_router.include_router(adaptive_planning.router, prefix="/planning", tags=["adaptive-planning"])
api_router.include_router(learning_system.router, prefix="/learning", tags=["learning"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(video.router, prefix="/video", tags=["video"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(ai_governance.router, prefix="/ai-governance", tags=["ai-governance"])
api_router.include_router(test_data.router, prefix="/test-data", tags=["test-data"])

# Conditionally include AI endpoints
try:
    from app.core.config import settings
    if settings.AI_ENABLED:
        api_router.include_router(ai_endpoints.router, prefix="/ai", tags=["ai"])
except Exception:
    pass