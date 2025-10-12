"""
Conversational mission planner using local LLM (Ollama) with fallback.

Flow:
- interpret operator prompt via llm_wrapper.generate_response
- transform to mission parameters
- produce mission plan via services.mission_planner (existing logic)
- dispatch using RealMissionExecutionEngine if requested
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.ai.llm_wrapper import generate_response
from app.services.mission_planner import mission_planner
from app.services.real_mission_execution import RealMissionExecutionEngine

logger = logging.getLogger(__name__)


class ConversationalMissionPlanner:
    def __init__(self):
        self.execution = RealMissionExecutionEngine()

    async def plan_from_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # 1) LLM interpret
        llm_text = await generate_response(prompt, context)

        # 2) Reuse mission_planner to extract/plan
        result = await mission_planner.plan_mission(
            user_input=llm_text,
            context=context,
            conversation_id=context.get("conversation_id", "default"),
        )
        return result

    async def dispatch_plan(self, mission_plan: Dict[str, Any], drone_ids: list[str]) -> Dict[str, Any]:
        mission_id = mission_plan.get("id") or mission_plan.get("mission_id") or "auto"
        payload = {"mission": mission_plan}
        return await self.execution.assign_mission_to_drones(mission_id, drone_ids, payload)


conv_mission_planner = ConversationalMissionPlanner()


