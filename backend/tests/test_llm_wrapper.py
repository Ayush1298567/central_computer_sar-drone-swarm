# backend/tests/test_llm_wrapper.py
import asyncio
import pytest

from app.ai.llm_wrapper import generate_response, stream_response


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_generate_response_stub(monkeypatch):
    # Force failure path to use stub by pointing to bad host
    from app.core.config import settings
    monkeypatch.setattr(settings, "OLLAMA_HOST", "http://127.0.0.1:9")

    resp = await generate_response("Plan a search mission", {"area": "X"})
    assert "PLAN:" in resp and "area=X" in resp.replace(" ", "")


@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_stream_response_stub(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "OLLAMA_HOST", "http://127.0.0.1:9")

    chunks = []
    async for c in stream_response("Plan", {"area": "Y"}):
        chunks.append(c)
    assert chunks and any("PLAN:" in c for c in chunks)


