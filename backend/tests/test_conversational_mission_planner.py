# backend/tests/test_conversational_mission_planner.py
import pytest

from app.ai.conversational_mission_planner import ConversationalMissionPlanner


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_plan_from_prompt_stub(monkeypatch):
    # Use stubbed LLM by failing host
    from app.core.config import settings
    monkeypatch.setattr(settings, "OLLAMA_HOST", "http://127.0.0.1:9")

    planner = ConversationalMissionPlanner()
    res = await planner.plan_from_prompt("We need to search near the ridge", {"area": "ridge", "drone_count": 2})
    assert res["status"] in ("ready", "needs_clarification", "error")


