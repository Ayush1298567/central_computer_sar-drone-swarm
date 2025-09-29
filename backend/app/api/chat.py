"""
Chat API Router

Handles conversational AI chat endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from ..services.conversational_mission_planner import ConversationalMissionPlanner

router = APIRouter()

@router.post("/")
async def chat(request: dict):
    """Handle chat messages"""
    try:
        planner = ConversationalMissionPlanner()
        response = await planner.process_message(request.get("message", ""))

        return {
            "message": response,
            "session_id": "default",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))