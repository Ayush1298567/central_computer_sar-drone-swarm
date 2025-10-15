"""
ContextAggregator: Aggregates mission, telemetry, and environment context for AI decisions.
"""
from typing import Any, Dict, Optional
from datetime import datetime

from app.models.mission import Mission
from app.models.drone import Drone
from app.core.database import SessionLocal


class ContextAggregator:
    def __init__(self) -> None:
        pass

    def snapshot(self, mission_id: Optional[str] = None, drone_id: Optional[str] = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            mission_data = None
            if mission_id:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if mission:
                    mission_data = mission.to_dict()

            drone_data = None
            if drone_id:
                drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
                if drone:
                    drone_data = drone.to_dict()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "mission": mission_data,
                "drone": drone_data,
            }
        finally:
            db.close()

context_aggregator = ContextAggregator()
