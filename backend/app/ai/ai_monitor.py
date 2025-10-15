"""
AIMonitor: Real-time monitoring of telemetry and mission context to propose decisions.
- Detects low_battery, stale_heartbeat, lost_drone, off_route.
- Broadcasts decisions over WebSocket topic 'ai_decisions'.
- Optionally executes autonomously when autonomous_execute=True.
"""
import asyncio
import contextlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List

from app.core.config import settings
from app.api.api_v1.websocket import manager
from app.communication.drone_registry import drone_registry, DroneStatus
from app.ai.decision_framework import decision_framework, DecisionType
from app.models.advanced_models import AIDecisionLog
from app.core.database import SessionLocal


@dataclass
class DecisionCandidate:
    decision_id: str
    type: str
    reasoning: str
    confidence_score: float
    severity: str
    recommended_action: Optional[str] = None
    mission_id: Optional[str] = None
    drone_id: Optional[str] = None


class AIMonitor:
    def __init__(self) -> None:
        self.autonomous_execute = False
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_seen: Dict[str, datetime] = {}
        self.offroute_threshold_m = 50.0

    async def start(self) -> None:
        self._running = True
        if not self._task:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._scan()
            except Exception:
                pass
            await asyncio.sleep(1.0)

    async def _scan(self) -> None:
        now = datetime.utcnow()
        for drone_id in list(drone_registry.list_drones()):
            entry = drone_registry._store.get(drone_id, {})
            status = entry.get("status") or "offline"
            last_seen_iso = entry.get("last_seen")
            last_seen = None
            if last_seen_iso:
                try:
                    last_seen = datetime.fromisoformat(last_seen_iso)
                except Exception:
                    last_seen = None

            # stale_heartbeat
            if last_seen and (now - last_seen).total_seconds() > settings.COMMUNICATION_TIMEOUT:
                await self._emit_decision(
                    drone_id=drone_id,
                    mission_id=(entry.get("missions") or {}).keys().__iter__().__next__() if entry.get("missions") else None,
                    type_="stale_heartbeat",
                    reasoning=f"No heartbeat for >{settings.COMMUNICATION_TIMEOUT}s",
                    confidence=0.8,
                    severity="high",
                    recommended_action="rtl",
                )

            # low_battery (if available)
            meta = entry.get("meta", {})
            battery = meta.get("battery_level")
            if isinstance(battery, (int, float)) and battery < settings.LOW_BATTERY_THRESHOLD:
                await self._emit_decision(
                    drone_id=drone_id,
                    mission_id=(entry.get("missions") or {}).keys().__iter__().__next__() if entry.get("missions") else None,
                    type_="low_battery",
                    reasoning=f"Battery {battery}% below threshold {settings.LOW_BATTERY_THRESHOLD}%",
                    confidence=0.9,
                    severity="critical" if battery < settings.CRITICAL_BATTERY_THRESHOLD else "high",
                    recommended_action="rtl",
                )

            # lost_drone
            if status == "offline":
                await self._emit_decision(
                    drone_id=drone_id,
                    mission_id=(entry.get("missions") or {}).keys().__iter__().__next__() if entry.get("missions") else None,
                    type_="lost_drone",
                    reasoning="Drone marked offline in registry",
                    confidence=0.7,
                    severity="high",
                    recommended_action="rtl",
                )

            # off_route (compare current vs assigned area center if available)
            pos = entry.get("position") or {}
            lat, lon = pos.get("lat"), pos.get("lon")
            missions = entry.get("missions") or {}
            if lat is not None and lon is not None and missions:
                # pick latest mission
                latest_mid = None
                latest_ts = None
                for mid, rec in missions.items():
                    ts = rec.get("updated_at")
                    if latest_ts is None or (ts and ts > latest_ts):
                        latest_mid = mid
                        latest_ts = ts
                # center from mission not available in registry; skip unless stored in meta
                center = meta.get("planned_center")  # {lat, lon}
                if center and isinstance(center, dict):
                    dist_m = self._haversine_m(lat, lon, center.get("lat"), center.get("lon"))
                    if dist_m and dist_m > self.offroute_threshold_m:
                        await self._emit_decision(
                            drone_id=drone_id,
                            mission_id=latest_mid,
                            type_="off_route",
                            reasoning=f"Deviation {int(dist_m)}m exceeds threshold",
                            confidence=0.75,
                            severity="medium",
                            recommended_action="rtl",
                        )

    async def _emit_decision(self, drone_id: Optional[str], mission_id: Optional[str], type_: str, reasoning: str, confidence: float, severity: str, recommended_action: Optional[str] = None) -> None:
        decision_id = str(uuid.uuid4())
        payload = {
            "decision_id": decision_id,
            "type": type_,
            "reasoning": reasoning,
            "confidence_score": confidence,
            "severity": severity,
            "recommended_action": recommended_action,
            "mission_id": mission_id,
            "drone_id": drone_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # broadcast
        await manager.broadcast_to_topic({"type": "ai_decisions", "payload": payload}, "ai_decisions")
        # log
        try:
            db = SessionLocal()
            db.add(AIDecisionLog(
                decision_type=type_,
                decision_id=decision_id,
                mission_id=mission_id,
                drone_id=drone_id,
                decision_description=reasoning,
                decision_options=None,
                selected_option={"recommended_action": recommended_action},
                confidence_score=confidence,
                reasoning_chain=[reasoning],
                timestamp=datetime.utcnow(),
            ))
            db.commit()
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
        await self._maybe_execute(payload)

    async def _maybe_execute(self, payload: Dict[str, Any]) -> None:
        if not self.autonomous_execute:
            return
        # simple autonomous policy
        action = payload.get("recommended_action")
        drone_id = payload.get("drone_id")
        if not action or not drone_id:
            return
        from app.communication.drone_connection_hub import drone_connection_hub
        result = False
        if action == "rtl":
            result = drone_connection_hub.send_emergency_command(drone_id, "rtl")
        elif action == "land":
            result = drone_connection_hub.send_emergency_command(drone_id, "land")
        # record outcome
        try:
            db = SessionLocal()
            db.add(AIDecisionLog(
                decision_type=f"auto_execute:{payload.get('type')}",
                decision_id=payload["decision_id"],
                mission_id=payload.get("mission_id"),
                drone_id=drone_id,
                decision_description=f"Autonomous execution of {action}",
                selected_option={"action": action},
                confidence_score=payload.get("confidence_score", 0.0),
                outcome="success" if result else "failure",
                outcome_timestamp=datetime.utcnow(),
                timestamp=datetime.utcnow(),
            ))
            db.commit()
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass

    @staticmethod
    def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        try:
            from math import radians, cos, sin, asin, sqrt
            R = 6371000.0
            dlat = radians((lat2 or 0) - (lat1 or 0))
            dlon = radians((lon2 or 0) - (lon1 or 0))
            a = sin(dlat/2)**2 + cos(radians(lat1 or 0)) * cos(radians(lat2 or 0)) * sin(dlon/2)**2
            c = 2 * asin(min(1, sqrt(a)))
            return R * c
        except Exception:
            return None

ai_monitor = AIMonitor()
