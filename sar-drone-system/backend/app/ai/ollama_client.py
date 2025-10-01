"""
Ollama HTTP client for local LLM communication
"""
import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from ..core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async HTTP client for Ollama API"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Ollama API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        response = await self._make_request("GET", "/api/tags")
        return response.get("models", [])
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download a model"""
        data = {"name": model_name}
        return await self._make_request("POST", "/api/pull", json=data)
    
    async def generate_text(
        self, 
        model: str, 
        prompt: str, 
        system: str = None,
        context: List[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate text using specified model"""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        if system:
            data["system"] = system
        
        if context:
            data["context"] = context
        
        return await self._make_request("POST", "/api/generate", json=data)
    
    async def generate_stream(
        self, 
        model: str, 
        prompt: str, 
        system: str = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text response"""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        if system:
            data["system"] = system
        
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}/api/generate"
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama streaming error {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"Ollama streaming error: {e}")
            raise Exception(f"Failed to stream from Ollama: {e}")
    
    async def chat(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        stream: bool = False
    ) -> Dict[str, Any]:
        """Chat with model using message history"""
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        return await self._make_request("POST", "/api/chat", json=data)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama service health"""
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "models_count": len(models),
                "available_models": [m["name"] for m in models]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        data = {"name": model_name}
        return await self._make_request("POST", "/api/show", json=data)


# Global client instance for convenience
async def get_ollama_client() -> OllamaClient:
    """Get a configured Ollama client instance"""
    return OllamaClient()