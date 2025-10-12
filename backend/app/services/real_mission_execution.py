"""
RealMissionExecution: lightweight coordinator that assigns missions to drones using DroneConnectionHub.
Avoids heavy imports; network operations are performed by the hub.
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio

from app.communication.drone_registry import get_registry
from app.communication.drone_connection_hub import get_hub

logger = logging.getLogger(__name__)


class RealMissionExecutionEngine:
    def __init__(self):
        self.registry = get_registry()
        self.hub = get_hub()
        self._running_missions: Dict[str, Dict[str, Any]] = {}

    async def assign_mission_to_drones(
        self, mission_id: str, drone_ids: List[str], mission_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        async def _send(drone_id: str):
            try:
                result = await self.hub.send_mission_to_drone(drone_id, mission_payload)
                return drone_id, {"ok": True, "result": result}
            except Exception as e:
                logger.exception("Failed to send mission to %s: %s", drone_id, e)
                return drone_id, {"ok": False, "error": str(e)}

        tasks = [asyncio.create_task(_send(d)) for d in drone_ids]
        results: Dict[str, Any] = {}
        for t in tasks:
            drone_id, res = await t
            results[drone_id] = res

        self._running_missions[mission_id] = {
            "drones": drone_ids,
            "payload": mission_payload,
            "results": results,
        }
        return results

    def get_mission_summary(self, mission_id: str) -> Optional[Dict[str, Any]]:
        return self._running_missions.get(mission_id)
