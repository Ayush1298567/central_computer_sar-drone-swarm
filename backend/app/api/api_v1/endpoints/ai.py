import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.ai.conversational_mission_planner import conv_mission_planner

logger = logging.getLogger(__name__)

router = APIRouter()


class MissionPrompt(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}


@router.post("/mission-plan")
async def mission_plan(body: MissionPrompt):
    if not settings.AI_ENABLED:
        raise HTTPException(status_code=403, detail="AI is disabled")
    try:
        result = await conv_mission_planner.plan_from_prompt(
            prompt=body.prompt,
            context=body.context,
        )
        return result
    except Exception as e:
        logger.error(f"AI mission plan failed: {e}")
        raise HTTPException(status_code=500, detail="AI mission planning error")


