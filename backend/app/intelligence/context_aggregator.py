"""
Context Aggregator

Builds a unified context snapshot for AI reasoning and replanning.
Aggregates telemetry, registry status, missions, discoveries, recent AI decisions,
and optional weather/knowledge outputs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import SessionLocal
from app.models.mission import Mission
from app.models.discovery import Discovery

logger = logging.getLogger(__name__)


async def build_context(mission_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a comprehensive context snapshot.

    - Telemetry snapshot from TelemetryReceiver cache
    - Drone registry state (status, last_seen, mission status)
    - Mission (specific or active missions) and recent logs/AI decisions
    - Discoveries (for mission or recent globally)
    - Optional weather for mission center
    - Optional knowledge/RAG hooks (placeholder for now)
    """
    context: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "telemetry": {},
        "registry": {},
        "missions": [],
        "discoveries": [],
        "ai_decisions": [],
        "weather": None,
        "knowledge": [],
    }

    # Telemetry snapshot
    try:
        from app.communication.telemetry_receiver import get_telemetry_receiver
        recv = get_telemetry_receiver()
        # Ensure receiver is started lazily
        recv.start()
        context["telemetry"] = recv.cache.snapshot()
    except Exception:
        logger.exception("Telemetry snapshot unavailable")

    # Registry snapshot
    try:
        from app.communication.drone_registry import get_registry
        reg = get_registry()
        registry_state: Dict[str, Any] = {}
        for did in reg.list_drones():
            registry_state[did] = {
                "status": reg.get_status(did),
                "last_seen": reg.get_last_seen(did),
                "mission_status": reg.get_mission_status(did),
            }
        context["registry"] = registry_state
    except Exception:
        logger.exception("Registry snapshot unavailable")

    # Missions, discoveries, recent AI decisions
    db = SessionLocal()
    try:
        missions: List[Mission] = []
        if mission_id:
            m = db.query(Mission).filter(Mission.mission_id == mission_id).first()
            if m:
                missions = [m]
        else:
            missions = (
                db.query(Mission)
                .filter(Mission.status.in_(["active", "paused"]))
                .order_by(Mission.updated_at.desc())
                .limit(5)
                .all()
            )

        context["missions"] = [m.to_dict() for m in missions]

        # Discoveries
        discoveries_query = db.query(Discovery)
        if missions:
            mission_db_ids = [m.id for m in missions]
            discoveries_query = discoveries_query.filter(Discovery.mission_id.in_(mission_db_ids))
        else:
            # Fallback: recent global discoveries
            recent_cutoff = datetime.utcnow() - timedelta(hours=12)
            discoveries_query = discoveries_query.filter(Discovery.discovered_at >= recent_cutoff)

        discoveries = (
            discoveries_query.order_by(Discovery.discovered_at.desc()).limit(50).all()
        )
        context["discoveries"] = [d.to_dict() for d in discoveries]

        # Recent AI decisions (audit log) - optional if advanced models available
        try:
            from app.models.advanced_models import AIDecisionLog  # type: ignore

            decisions_q = db.query(AIDecisionLog).order_by(AIDecisionLog.timestamp.desc())
            if mission_id:
                decisions_q = decisions_q.filter(AIDecisionLog.mission_id == mission_id)
            ai_decisions = decisions_q.limit(20).all()
            context["ai_decisions"] = [
                {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type,
                    "mission_id": d.mission_id,
                    "drone_id": d.drone_id,
                    "confidence_score": d.confidence_score,
                    "timestamp": d.timestamp.isoformat() if getattr(d, "timestamp", None) else None,
                    "selected_option": d.selected_option,
                }
                for d in ai_decisions
            ]
        except Exception:
            # Advanced models may not be initialized in some environments
            pass

        # Weather (best-effort for mission center)
        try:
            if missions:
                m0 = missions[0]
                if m0.center_lat is not None and m0.center_lng is not None:
                    from app.services.weather_service import weather_service

                    weather = await weather_service.get_current_weather(
                        latitude=float(m0.center_lat), longitude=float(m0.center_lng)
                    )
                    context["weather"] = {
                        "condition": getattr(getattr(weather, "condition", ""), "value", str(getattr(weather, "condition", ""))),
                        "wind_speed_ms": getattr(weather, "wind_speed_ms", None),
                        "visibility_km": getattr(weather, "visibility_km", None),
                        "flight_safety": getattr(getattr(weather, "flight_safety", ""), "value", str(getattr(weather, "flight_safety", ""))),
                        "safety_reasons": getattr(weather, "safety_reasons", []),
                        "timestamp": getattr(weather, "timestamp", datetime.utcnow()).isoformat(),
                    }
        except Exception:
            logger.exception("Weather retrieval failed")

        # Optional: RAG/Knowledge Graph can be added here (stubbed)
        # from app.ai.rag_system import sar_rag
        # context["knowledge"] = await sar_rag.retrieve_relevant_context("SAR mission context")

    finally:
        try:
            db.close()
        except Exception:
            pass

    return context
