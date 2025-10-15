import pytest
from datetime import datetime

from app.core.database import init_db
from app.api.api_v1.endpoints.ai import apply_decision, ApplyDecisionBody
from app.services.real_mission_execution import real_mission_execution_engine


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_apply_decision_emergency_rtl(monkeypatch):
    await init_db()

    # Stub the command sender to avoid external dependency
    async def _send_mission_command(drone_id, cmd):
        return True

    monkeypatch.setattr(real_mission_execution_engine, "_send_mission_command", _send_mission_command, raising=True)

    body = ApplyDecisionBody(decision_id="d1", decision_type="emergency_rtl", payload={}, mission_id=None, drone_id="dr1")
    resp = await apply_decision("d1", body)
    assert resp.get("success") is True
