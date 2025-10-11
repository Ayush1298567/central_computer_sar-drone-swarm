import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama AI client with comprehensive error handling"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_HOST
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0
        
        logger.info(f"Initializing Ollama client: {self.base_url}")
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> str:
        """
        Generate response with comprehensive error handling
        """
        model = model or settings.DEFAULT_MODEL
        
        try:
            # Check if Ollama is running
            await self._health_check()
            
            # Prepare request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system:
                payload["system"] = system
            
            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/api/generate",
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            generated_text = result.get("response", "")
                            
                            if not generated_text:
                                raise ValueError("Ollama returned empty response")
                            
                            logger.info(f"Generated {len(generated_text)} characters from Ollama")
                            return generated_text
                        
                        else:
                            error_text = response.text
                            logger.error(f"Ollama error ({response.status_code}): {error_text}")
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.retry_delay * (attempt + 1))
                                continue
                            else:
                                raise RuntimeError(f"Ollama request failed: {error_text}")
                
                except httpx.TimeoutException:
                    logger.error(f"Ollama request timed out (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise TimeoutError("AI model took too long to respond")
                
                except httpx.ConnectError:
                    logger.error(f"Cannot connect to Ollama at {self.base_url}")
                    raise ConnectionError(f"Ollama service not available at {self.base_url}")
                
                except Exception as e:
                    logger.error(f"Ollama request failed (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}", exc_info=True)
            raise RuntimeError(f"AI generation error: {str(e)}")
    
    async def _health_check(self):
        """Check if Ollama service is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    raise ConnectionError("Ollama not responding")
                logger.debug("Ollama health check passed")
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    logger.info(f"Found {len(models)} available models")
                    return models
                else:
                    raise RuntimeError(f"Failed to list models: {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download a model"""
        try:
            logger.info(f"Pulling model: {model_name}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for downloads
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Model {model_name} pulled successfully")
                    return result
                else:
                    raise RuntimeError(f"Failed to pull model: {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Chat with the model using message history"""
        model = model or settings.DEFAULT_MODEL
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get("message", {})
                    content = message.get("content", "")
                    
                    if not content:
                        raise ValueError("Ollama returned empty chat response")
                    
                    logger.info(f"Chat response generated: {len(content)} characters")
                    return content
                else:
                    raise RuntimeError(f"Chat request failed: {response.text}")
        
        except Exception as e:
            logger.error(f"Chat generation failed: {e}", exc_info=True)
            raise
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise RuntimeError(f"Failed to get model info: {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            raise
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    logger.info(f"Model {model_name} deleted successfully")
                    return True
                else:
                    raise RuntimeError(f"Failed to delete model: {response.text}")
        
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status"""
        try:
            # Test basic connectivity
            await self._health_check()
            
            # Test model availability
            models = await self.list_models()
            default_model_available = any(
                model.get("name", "").startswith(settings.DEFAULT_MODEL.split(":")[0])
                for model in models
            )
            
            return {
                "connected": True,
                "base_url": self.base_url,
                "available_models": len(models),
                "default_model_available": default_model_available,
                "status": "healthy"
            }
        
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "connected": False,
                "base_url": self.base_url,
                "error": str(e),
                "status": "unhealthy"
            }

# Global instance
ollama_client = OllamaClient()