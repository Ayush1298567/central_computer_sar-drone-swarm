import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

class MissionPlanner:
    """Mission planning and execution service."""

    def __init__(self):
        self.mission_plans = {}

    async def plan_mission(self, mission_data: dict) -> dict:
        """Create a mission plan."""
        return {
            "mission_id": mission_data.get("id"),
            "plan": "Basic mission plan",
            "estimated_duration": 30,
            "drone_assignments": []
        }

mission_planner = MissionPlanner()