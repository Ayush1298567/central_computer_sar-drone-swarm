import logging
from typing import Any, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.core.config import settings
from app.ai.conversational_mission_planner import conv_mission_planner
from app.services.real_mission_execution import real_mission_execution_engine
from app.models.logs import MissionLog
from app.models.advanced_models import AIDecisionLog
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


class MissionPrompt(BaseModel):
    prompt: str
    context: Dict[str, Any] = {}


@router.post("/mission-plan")
async def mission_plan(body: MissionPrompt):
    # Phase 10: enable regardless of settings.AI_ENABLED
    try:
        result = await conv_mission_planner.plan_from_prompt(
            prompt=body.prompt,
            context=body.context,
        )
        return result
    except Exception as e:
        logger.error(f"AI mission plan failed: {e}")
        raise HTTPException(status_code=500, detail="AI mission planning error")

class ApplyDecisionBody(BaseModel):
    decision_id: str
    decision_type: str
    payload: Dict[str, Any] = {}
    mission_id: str | None = None
    drone_id: str | None = None

@router.post("/decisions/{decision_id}/apply")
async def apply_decision(decision_id: str, body: ApplyDecisionBody):
    """Apply an AI decision by routing to mission engine as needed."""
    try:
        # Minimal mapping for Phase 10
        if body.decision_type in {"emergency_rtl", "rtl"} and body.drone_id:
            ok = await real_mission_execution_engine.emergency_rtl(body.drone_id)
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        if body.decision_type in {"emergency_land", "land"} and body.drone_id:
            ok = await real_mission_execution_engine.emergency_land(body.drone_id)
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        if body.decision_type in {"pause_mission", "pause"} and body.mission_id:
            ok = await real_mission_execution_engine.pause_mission(body.mission_id)
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        if body.decision_type in {"resume_mission", "resume"} and body.mission_id:
            ok = await real_mission_execution_engine.resume_mission(body.mission_id)
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        if body.decision_type in {"abort_mission", "abort"} and body.mission_id:
            ok = await real_mission_execution_engine.abort_mission(body.mission_id)
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        if body.decision_type in {"replan_mission", "replan"} and body.mission_id:
            ok = await real_mission_execution_engine.replan_mission(body.mission_id, body.payload or {})
            _log_apply(decision_id, body, ok)
            return {"success": bool(ok), "decision_id": decision_id}
        return {"success": False, "decision_id": decision_id, "message": "Unsupported decision"}
    except Exception as e:
        logger.error(f"Apply decision failed: {e}")
        raise HTTPException(status_code=500, detail="Apply decision error")

def _log_apply(decision_id: str, body: ApplyDecisionBody, ok: bool) -> None:
    """Write MissionLog and AIDecisionLog entries for decision application."""
    try:
        db = SessionLocal()
        db.add(MissionLog(
            mission_id=body.mission_id or "unknown",
            event_type="ai_decision",
            payload={
                "decision_id": decision_id,
                "action": body.decision_type,
                "drone_id": body.drone_id,
                "result": bool(ok),
            },
        ))
        db.add(AIDecisionLog(
            decision_type=body.decision_type,
            decision_id=decision_id,
            mission_id=body.mission_id,
            drone_id=body.drone_id,
            decision_description=f"apply_decision: {body.decision_type}",
            selected_option={"action": body.decision_type},
            confidence_score=1.0,
            outcome="success" if ok else "failure",
            outcome_timestamp=datetime.utcnow(),
            timestamp=datetime.utcnow(),
        ))
        db.commit()
    except Exception:
        logger.exception("Failed to log apply_decision")
    finally:
        try:
            db.close()
        except Exception:
            pass
