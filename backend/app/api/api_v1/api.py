from fastapi import APIRouter, Response
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
    real_mission_execution,
    ai as ai_endpoints,
)
from app.monitoring.metrics import export_prometheus_text
from app.communication.drone_registry import get_registry
from app.core.config import settings
from app.api.api_v1.endpoints import emergency as emergency_endpoints
from app.auth import routes as auth_routes

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_routes.router, tags=["auth"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
try:
    from app.api.api_v1.endpoints import drone_connections as drone_connections
    api_router.include_router(drone_connections.router, prefix="/connections", tags=["drone-connections"])
except Exception:
    pass
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
api_router.include_router(real_mission_execution.router, prefix="/real-mission-execution", tags=["mission-execution"])
api_router.include_router(emergency_endpoints.router, prefix="/emergency", tags=["emergency"])

# Metrics endpoint (Prometheus text format)
@api_router.get("/metrics", tags=["monitoring"])
async def metrics_endpoint() -> Response:
    body, content_type = export_prometheus_text()
    return Response(content=body, media_type=content_type)

# Health endpoint per Phase 5
@api_router.get("/health", tags=["monitoring"])
async def v1_health() -> dict:
    try:
        reg = get_registry()
        drones = reg.list_drones()
        online = 0
        for drone_id in drones:
            if (reg.get_status(drone_id) or "").lower() != "offline":
                online += 1
        return {"status": "ok", "drones_online": online, "ai_enabled": bool(settings.AI_ENABLED)}
    except Exception:
        return {"status": "degraded", "drones_online": 0, "ai_enabled": bool(settings.AI_ENABLED)}

# Conditionally include HTTP telemetry ingestion when Redis is disabled
try:
    from app.core.config import settings
    if not settings.REDIS_ENABLED:
        from app.api.api_v1.endpoints import telemetry as telemetry_endpoint
        api_router.include_router(telemetry_endpoint.router, tags=["telemetry"])
except Exception:
    pass

# Conditionally include AI endpoints
try:
    from app.core.config import settings
    if settings.AI_ENABLED:
        api_router.include_router(ai_endpoints.router, prefix="/ai", tags=["ai"])
except Exception:
    pass