from fastapi import APIRouter
from .endpoints import drones, analytics, computer_vision, coordination, learning_system, tasks, weather, missions, discoveries, chat, video, drone_connections, real_mission_execution
from .websocket import router as websocket_router

api_router = APIRouter()

# Include all routers from endpoints directory and websocket
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(drones.router, prefix="/drones", tags=["drones"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
api_router.include_router(video.router, prefix="/video", tags=["video"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(computer_vision.router, prefix="/computer-vision", tags=["computer-vision"])
api_router.include_router(coordination.router, prefix="/coordination", tags=["coordination"])
api_router.include_router(learning_system.router, prefix="/learning", tags=["learning"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(drone_connections.router, prefix="/drone-connections", tags=["drone-connections"])
api_router.include_router(real_mission_execution.router, prefix="/real-mission-execution", tags=["real-mission-execution"])

