"""
Local LLM wrapper for Ollama with deterministic stub fallback.

Exposes:
- generate_response(prompt, context)
- stream_response(prompt, context) -> async generator of chunks

Never requires model downloads during tests; if Ollama is unreachable, uses stub.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _ollama_generate(prompt: str, context: Dict[str, Any]) -> str:
    import aiohttp  # lightweight HTTP client
    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": settings.DEFAULT_MODEL,
        "prompt": _build_prompt(prompt, context),
        "stream": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=5) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ollama HTTP {resp.status}")
            data = await resp.json()
            return data.get("response", "")


async def _ollama_stream(prompt: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
    import aiohttp
    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": settings.DEFAULT_MODEL,
        "prompt": _build_prompt(prompt, context),
        "stream": True,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=5) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ollama HTTP {resp.status}")
            async for line in resp.content:
                try:
                    obj = json.loads(line.decode("utf-8"))
                    chunk = obj.get("response", "")
                    if chunk:
                        yield chunk
                except Exception:
                    continue


def _build_prompt(prompt: str, context: Dict[str, Any]) -> str:
    ctx = json.dumps(context, ensure_ascii=False)
    return f"Context: {ctx}\n\nUser: {prompt}\nAssistant:"


def _stub_generate(prompt: str, context: Dict[str, Any]) -> str:
    # Deterministic stub for tests: reflect key fields
    area = context.get("area", "unknown-area")
    return f"PLAN: search area={area}; pattern=grid; altitude=50; speed=5.0"


async def generate_response(prompt: str, context: Dict[str, Any]) -> str:
    try:
        return await _ollama_generate(prompt, context)
    except Exception:
        logger.info("Using LLM stub (Ollama unavailable)")
        return _stub_generate(prompt, context)


async def stream_response(prompt: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
    try:
        async for chunk in _ollama_stream(prompt, context):
            yield chunk
    except Exception:
        # Fallback: yield the stub in one chunk
        yield _stub_generate(prompt, context)


