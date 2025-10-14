import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.ai.conversational_mission_planner import conv_mission_planner
from app.services.real_mission_execution import real_mission_execution_engine
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


class MissionPrompt(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}


class ApplyDecisionRequest(BaseModel):
    decision: Dict[str, Any]


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


@router.post("/decisions/{decision_id}/apply")
async def apply_ai_decision(decision_id: str, body: ApplyDecisionRequest):
    """Apply an AI decision after operator approval."""
    try:
        success = await real_mission_execution_engine.apply_decision(body.decision)
        return {"success": bool(success)}
    except Exception as e:
        logger.error(f"Failed to apply AI decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply decision")


@router.get("/decisions/recent")
async def recent_ai_decisions(limit: int = 20):
    """Return recent AI decisions if audit table exists (best-effort)."""
    try:
        items: List[Dict[str, Any]] = []
        try:
            from app.models.advanced_models import AIDecisionLog  # type: ignore

            db = SessionLocal()
            try:
                rows = (
                    db.query(AIDecisionLog)
                    .order_by(AIDecisionLog.timestamp.desc())
                    .limit(max(1, min(limit, 100)))
                    .all()
                )
                for r in rows:
                    items.append({
                        "decision_id": r.decision_id,
                        "decision_type": r.decision_type,
                        "mission_id": r.mission_id,
                        "drone_id": r.drone_id,
                        "selected_option": r.selected_option,
                        "confidence_score": r.confidence_score,
                        "timestamp": r.timestamp.isoformat() if getattr(r, "timestamp", None) else None,
                    })
            finally:
                db.close()
        except Exception:
            # If table not present or DB not ready, return empty list gracefully
            pass

        return {"items": items}
    except Exception as e:
        logger.error(f"Failed to fetch recent AI decisions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent AI decisions")

