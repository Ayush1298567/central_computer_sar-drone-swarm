"""
Ollama AI client for SAR Mission Commander
"""
import asyncio
import json
import aiohttp
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class GenerationRequest:
    prompt: str
    model: str = "phi3:mini"
    temperature: float = 0.7
    max_tokens: int = 300
    stream: bool = False

@dataclass
class GenerationResponse:
    content: str
    model: str
    usage: Dict[str, int]

class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Ollama"""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")

                    data = await response.json()

                    return GenerationResponse(
                        content=data.get("response", ""),
                        model=data.get("model", request.model),
                        usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                        }
                    )

        except asyncio.TimeoutError:
            raise Exception("Ollama request timed out")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    async def list_models(self) -> list:
        """List available models"""
        url = f"{self.base_url}/api/tags"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")

                    data = await response.json()
                    return data.get("models", [])

        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")

    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            models = await self.list_models()
            return len(models) > 0
        except:
            return False