"""
AI Monitor

Periodic loop that evaluates system state and generates AI decisions.
Emits decisions over WebSocket and logs them for audit/learning.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Decision framework imports
from app.ai.decision_framework import (
    decision_framework,
    DecisionType,
    DecisionContext,
    DecisionOption,
    DecisionAuthority,
)


class AIMonitor:
    def __init__(self, interval_seconds: float = 2.0, autonomous_execute: bool = False):
        self.interval_seconds = max(1.0, min(interval_seconds, 5.0))
        self.autonomous_execute = autonomous_execute
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except Exception:
                pass

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            try:
                # Build operational context
                from app.intelligence.context_aggregator import build_context

                context_snapshot = await build_context(mission_id=None)
                triggers = self._evaluate_triggers(context_snapshot)

                # Generate decisions for each trigger
                for trig in triggers:
                    try:
                        decision_dict = await self._make_and_broadcast_decision(trig, context_snapshot)
                        # Optional: execute autonomous action if allowed
                        await self._maybe_execute(decision_dict)
                    except Exception:
                        logger.exception("Failed to process AI trigger")

            except Exception:
                logger.exception("AIMonitor loop error")
            finally:
                await asyncio.sleep(self.interval_seconds)

    def _evaluate_triggers(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggers: List[Dict[str, Any]] = []

        telemetry = ctx.get("telemetry", {})
        registry = ctx.get("registry", {})

        now = datetime.utcnow()

        # Low battery / critical battery
        for drone_id, telem in telemetry.items():
            battery = telem.get("battery_level") or telem.get("battery_percentage")
            if battery is None:
                continue
            try:
                battery = float(battery)
            except Exception:
                continue

            if battery <= settings.CRITICAL_BATTERY_THRESHOLD:
                triggers.append({
                    "type": "critical_battery",
                    "drone_id": drone_id,
                    "level": battery,
                    "severity": "critical",
                })
            elif battery <= settings.LOW_BATTERY_THRESHOLD:
                triggers.append({
                    "type": "low_battery",
                    "drone_id": drone_id,
                    "level": battery,
                    "severity": "high",
                })

        # Stale heartbeat / lost drone from registry
        for drone_id, info in registry.items():
            last_seen_iso = info.get("last_seen")
            status = info.get("status")
            try:
                if last_seen_iso:
                    last_seen = datetime.fromisoformat(last_seen_iso)
                    age = (now - last_seen).total_seconds()
                    if age > settings.COMMUNICATION_TIMEOUT:
                        triggers.append({
                            "type": "stale_heartbeat",
                            "drone_id": drone_id,
                            "age_seconds": age,
                            "severity": "high",
                        })
            except Exception:
                pass

            if status == "offline":
                triggers.append({
                    "type": "lost_drone",
                    "drone_id": drone_id,
                    "severity": "critical",
                })

        # TODO: Off-route detection requires planned route vs actual; placeholder
        # Could use mission waypoints vs telemetry position

        return triggers

    async def _make_and_broadcast_decision(self, trig: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        drone_id = trig.get("drone_id")
        mission_id = self._infer_mission_for_drone(drone_id, ctx)

        objectives = ["safety", "efficiency", "success_probability"]
        decision_type = (
            DecisionType.EMERGENCY_RESPONSE
            if trig["type"] in {"critical_battery", "lost_drone", "stale_heartbeat"}
            else DecisionType.SAFETY_EVALUATION
        )

        # Build decision options
        options: List[DecisionOption] = []
        if trig["type"] in {"low_battery", "critical_battery"}:
            options = [
                DecisionOption(
                    option_id="rtl",
                    description="Return-to-launch immediately",
                    parameters={"action": "rtl", "drone_id": drone_id, "mission_id": mission_id},
                    expected_outcomes={"success_rate": 0.9, "duration_minutes": 5},
                    risk_factors=["communication"],
                    resource_requirements={"cost": 10},
                    confidence_score=0.8,
                    reasoning="Battery low; RTL maximizes safety",
                ),
                DecisionOption(
                    option_id="land",
                    description="Land at current safe location",
                    parameters={"action": "land", "drone_id": drone_id, "mission_id": mission_id},
                    expected_outcomes={"success_rate": 0.85, "duration_minutes": 3},
                    risk_factors=["terrain"],
                    resource_requirements={"cost": 5},
                    confidence_score=0.7,
                    reasoning="Battery critical; immediate landing reduces risk of crash",
                ),
                DecisionOption(
                    option_id="continue_short",
                    description="Continue mission for 1 minute then RTL",
                    parameters={"action": "continue_then_rtl", "drone_id": drone_id, "mission_id": mission_id, "minutes": 1},
                    expected_outcomes={"success_rate": 0.6, "duration_minutes": 6},
                    risk_factors=["equipment"],
                    resource_requirements={"cost": 15},
                    confidence_score=0.4,
                    reasoning="May recover critical data but increases risk",
                ),
            ]
        elif trig["type"] in {"stale_heartbeat", "lost_drone"}:
            options = [
                DecisionOption(
                    option_id="pause_mission",
                    description="Pause mission for affected drone",
                    parameters={"action": "pause", "mission_id": mission_id},
                    expected_outcomes={"success_rate": 0.75, "duration_minutes": 1},
                    risk_factors=["communication"],
                    resource_requirements={"cost": 2},
                    confidence_score=0.6,
                    reasoning="Pause to prevent unsafe autonomous continuation",
                ),
                DecisionOption(
                    option_id="reassign",
                    description="Reassign area to alternate drone",
                    parameters={"action": "reassign", "from_drone_id": drone_id, "mission_id": mission_id},
                    expected_outcomes={"success_rate": 0.7, "duration_minutes": 5},
                    risk_factors=["resource_usage"],
                    resource_requirements={"cost": 20},
                    confidence_score=0.55,
                    reasoning="Maintain coverage by reallocating resources",
                ),
                DecisionOption(
                    option_id="rtl_if_recovers",
                    description="If link recovers, command RTL",
                    parameters={"action": "rtl_if_recovers", "drone_id": drone_id, "mission_id": mission_id},
                    expected_outcomes={"success_rate": 0.65, "duration_minutes": 8},
                    risk_factors=["communication"],
                    resource_requirements={"cost": 10},
                    confidence_score=0.5,
                    reasoning="Conservative plan if comms return",
                ),
            ]
        else:
            options = [
                DecisionOption(
                    option_id="monitor",
                    description="Monitor situation",
                    parameters={"action": "monitor"},
                    expected_outcomes={"success_rate": 0.5, "duration_minutes": 1},
                    risk_factors=[],
                    resource_requirements={"cost": 1},
                    confidence_score=0.5,
                    reasoning="No immediate risk detected",
                )
            ]

        # Build decision context
        decision_ctx = DecisionContext(
            mission_id=mission_id or "unknown",
            current_state={"trigger": trig, **{k: v for k, v in ctx.items() if k in ("telemetry", "registry", "weather")}},
            constraints={
                "low_battery_threshold": settings.LOW_BATTERY_THRESHOLD,
                "critical_battery_threshold": settings.CRITICAL_BATTERY_THRESHOLD,
                "communication_timeout": settings.COMMUNICATION_TIMEOUT,
            },
            objectives=["safety", "efficiency", "success_probability"],
            urgency_level="critical" if trig["type"] in {"critical_battery", "lost_drone"} else "medium",
            available_resources={"drones": list(ctx.get("registry", {}).keys())},
            historical_data={},
        )

        decision = await decision_framework.make_decision(
            decision_type=decision_type,
            context=decision_ctx,
            options=options,
            authority_override=None,
        )

        decision_payload: Dict[str, Any] = {
            "decision_id": decision.decision_id,
            "decision_type": decision.decision_type.value,
            "mission_id": mission_id,
            "drone_id": drone_id,
            "selected_option": asdict(decision.selected_option),
            "alternative_options": [asdict(o) for o in decision.alternative_options],
            "confidence_level": decision.confidence_level.value,
            "reasoning_chain": decision.reasoning_chain,
            "risk_assessment": decision.risk_assessment,
            "expected_impact": decision.expected_impact,
            "authority_level": decision.authority_level.value,
            "created_at": decision.created_at.isoformat(),
            "trigger": trig,
        }

        # Persist to AIDecisionLog (optional if model exists)
        try:
            from app.models.advanced_models import AIDecisionLog  # type: ignore

            db = SessionLocal()
            try:
                rec = AIDecisionLog(
                    decision_type=decision.decision_type.value,
                    decision_id=decision.decision_id,
                    mission_id=mission_id,
                    drone_id=drone_id,
                    decision_description=decision.selected_option.description,
                    decision_options=decision_payload.get("alternative_options"),
                    selected_option=decision_payload.get("selected_option"),
                    confidence_score=float(decision.confidence_level.value),
                    reasoning_chain=decision.reasoning_chain,
                    knowledge_sources=None,
                    model_predictions=None,
                    outcome="unknown",
                    outcome_metrics=None,
                    decision_time_ms=None,
                    resources_used=None,
                )
                db.add(rec)
                db.commit()
            finally:
                db.close()
        except Exception:
            # Advanced model not available or DB not ready; skip
            pass

        # Broadcast via WebSocket
        try:
            from app.api.api_v1.websocket import broadcast_ai_decision

            await broadcast_ai_decision(decision_payload)
        except Exception:
            logger.exception("Failed to broadcast ai_decision")

        return decision_payload

    async def _maybe_execute(self, decision_payload: Dict[str, Any]) -> None:
        if not self.autonomous_execute:
            return
        try:
            authority = decision_payload.get("authority_level")
            if authority not in {DecisionAuthority.AI_AUTONOMOUS.value, DecisionAuthority.EMERGENCY_AUTONOMOUS.value}:
                return

            selected = decision_payload.get("selected_option", {})
            action = selected.get("parameters", {}).get("action")
            mission_id = decision_payload.get("mission_id")
            drone_id = decision_payload.get("drone_id")

            from app.services.real_mission_execution import real_mission_execution_engine as engine

            if action == "pause" and mission_id:
                await engine.pause_mission(mission_id)
            elif action in {"rtl", "rtl_if_recovers"} and drone_id:
                # Use emergency hub wrapper for RTL if available
                from app.communication.drone_connection_hub import drone_connection_hub

                drone_connection_hub.send_emergency_command(drone_id, "rtl")
            elif action == "land" and drone_id:
                from app.communication.drone_connection_hub import drone_connection_hub

                drone_connection_hub.send_emergency_command(drone_id, "land")
            # reassign/continue_then_rtl would require higher-level orchestration
        except Exception:
            logger.exception("Autonomous execution failed")

    def _infer_mission_for_drone(self, drone_id: Optional[str], ctx: Dict[str, Any]) -> Optional[str]:
        if not drone_id:
            return None
        # Try registry mission_status
        reg = ctx.get("registry", {})
        info = reg.get(drone_id) or {}
        ms = info.get("mission_status") or {}
        if isinstance(ms, dict):
            return ms.get("mission_id")
        return None


_monitor_singleton: Optional[AIMonitor] = None


def get_ai_monitor(singleton: bool = True) -> AIMonitor:
    global _monitor_singleton
    if singleton:
        if _monitor_singleton is None:
            _monitor_singleton = AIMonitor()
        return _monitor_singleton
    return AIMonitor()
