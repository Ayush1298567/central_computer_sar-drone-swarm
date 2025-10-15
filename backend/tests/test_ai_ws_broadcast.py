import pytest
from datetime import datetime

from app.api.api_v1.websocket import manager


class _DummyWS:
    def __init__(self):
        self.sent = []
    async def send_text(self, text):
        self.sent.append(text)


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_ai_decision_ws_broadcast(monkeypatch):
    ws = _DummyWS()
    cid = "c1"
    manager.active_connections[cid] = ws
    await manager.broadcast_to_topic({"type": "ai_decisions", "payload": {
        "decision_id": "x", "type": "low_battery", "reasoning": "", "confidence_score": 0.9, "severity": "high"
    }}, "ai_decisions")
    assert ws.sent, "No message sent to websocket"
