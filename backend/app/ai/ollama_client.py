"""
Ollama Client for local LLM integration in SAR drone operations.

This module provides async HTTP communication with local Ollama server,
supporting health checks, text generation, and model management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama server fails."""
    pass


class OllamaModelError(OllamaError):
    """Raised when model operations fail.""" 
    pass


@dataclass
class OllamaResponse:
    """Response from Ollama API."""
    content: str
    model: str
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OllamaResponse':
        """Create response from API response data."""
        return cls(
            content=data.get('response', ''),
            model=data.get('model', ''),
            total_duration=data.get('total_duration'),
            load_duration=data.get('load_duration'),
            prompt_eval_count=data.get('prompt_eval_count'),
            eval_count=data.get('eval_count')
        )


@dataclass
class ModelInfo:
    """Information about an Ollama model."""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Dict[str, Any]


class GenerationRequest(BaseModel):
    """Request for text generation."""
    prompt: str
    model: str = "llama2"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None
    stream: bool = False
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class StructuredRequest(GenerationRequest):
    """Request for structured output generation."""
    format: str = "json"
    schema: Optional[Dict[str, Any]] = None


class OllamaClient:
    """
    Async HTTP client for Ollama server communication.
    
    Provides methods for health checks, text generation, model management,
    and structured output generation for SAR drone AI operations.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def connect(self):
        """Establish connection to Ollama server."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
    async def close(self):
        """Close connection to Ollama server."""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], httpx.Response]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            stream: Whether to return streaming response
            
        Returns:
            Response data or streaming response
            
        Raises:
            OllamaConnectionError: If connection fails
            OllamaError: If request fails
        """
        if not self._client:
            await self.connect()
            
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    response = await self._client.request(
                        method, url, json=data, headers={"Accept": "application/x-ndjson"}
                    )
                    response.raise_for_status()
                    return response
                else:
                    response = await self._client.request(method, url, json=data)
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.ConnectError as e:
                if attempt == self.max_retries:
                    raise OllamaConnectionError(f"Failed to connect to Ollama server at {self.base_url}: {e}")
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {self.retry_delay}s...")
                await asyncio.sleep(self.retry_delay)
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                raise OllamaError(f"Request failed: {error_msg}")
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise OllamaError(f"Unexpected error: {e}")
                logger.warning(f"Request attempt {attempt + 1} failed: {e}, retrying...")
                await asyncio.sleep(self.retry_delay)
                
    async def health_check(self) -> bool:
        """
        Check if Ollama server is healthy and responsive.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            await self._make_request("GET", "/api/tags")
            logger.info("Ollama server health check passed")
            return True
        except Exception as e:
            logger.error(f"Ollama server health check failed: {e}")
            return False
            
    async def list_models(self) -> List[ModelInfo]:
        """
        List available models on Ollama server.
        
        Returns:
            List of available models
            
        Raises:
            OllamaError: If request fails
        """
        try:
            response = await self._make_request("GET", "/api/tags")
            models = []
            
            for model_data in response.get("models", []):
                models.append(ModelInfo(
                    name=model_data["name"],
                    size=model_data["size"],
                    digest=model_data["digest"],
                    modified_at=model_data["modified_at"],
                    details=model_data.get("details", {})
                ))
                
            logger.info(f"Found {len(models)} available models")
            return models
            
        except Exception as e:
            raise OllamaError(f"Failed to list models: {e}")
            
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {"name": model_name}
            response = await self._make_request("POST", "/api/pull", data, stream=True)
            
            # Process streaming response
            async for line in response.aiter_lines():
                if line:
                    status_data = json.loads(line)
                    if "error" in status_data:
                        raise OllamaModelError(f"Pull failed: {status_data['error']}")
                    if status_data.get("status") == "success":
                        logger.info(f"Successfully pulled model: {model_name}")
                        return True
                        
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
            
    async def generate_text(self, request: GenerationRequest) -> OllamaResponse:
        """
        Generate text using specified model.
        
        Args:
            request: Generation request parameters
            
        Returns:
            Generated response
            
        Raises:
            OllamaError: If generation fails
        """
        try:
            data = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": request.stream,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                }
            }
            
            if request.max_tokens:
                data["options"]["num_predict"] = request.max_tokens
            if request.stop:
                data["options"]["stop"] = request.stop
                
            response_data = await self._make_request("POST", "/api/generate", data)
            
            logger.info(f"Generated text using model {request.model}")
            return OllamaResponse.from_dict(response_data)
            
        except Exception as e:
            raise OllamaError(f"Text generation failed: {e}")
            
    async def generate_structured(self, request: StructuredRequest) -> Dict[str, Any]:
        """
        Generate structured output (JSON) using specified model.
        
        Args:
            request: Structured generation request
            
        Returns:
            Parsed JSON response
            
        Raises:
            OllamaError: If generation or parsing fails
        """
        try:
            # Add JSON format instruction to prompt
            structured_prompt = f"{request.prompt}\n\nPlease respond with valid JSON only."
            
            gen_request = GenerationRequest(
                prompt=structured_prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop
            )
            
            response = await self.generate_text(gen_request)
            
            # Parse JSON response
            try:
                structured_data = json.loads(response.content.strip())
                logger.info(f"Generated structured output using model {request.model}")
                return structured_data
            except json.JSONDecodeError as e:
                raise OllamaError(f"Failed to parse JSON response: {e}\nResponse: {response.content}")
                
        except Exception as e:
            raise OllamaError(f"Structured generation failed: {e}")
            
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> OllamaResponse:
        """
        Perform chat completion with conversation history.
        
        Args:
            messages: List of chat messages with role and content
            model: Model to use for completion
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Chat completion response
            
        Raises:
            OllamaError: If chat completion fails
        """
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
                
            response_data = await self._make_request("POST", "/api/chat", data)
            
            # Extract message content
            message = response_data.get("message", {})
            content = message.get("content", "")
            
            logger.info(f"Completed chat using model {model}")
            return OllamaResponse(
                content=content,
                model=model,
                total_duration=response_data.get("total_duration"),
                load_duration=response_data.get("load_duration"),
                prompt_eval_count=response_data.get("prompt_eval_count"),
                eval_count=response_data.get("eval_count")
            )
            
        except Exception as e:
            raise OllamaError(f"Chat completion failed: {e}")


# Utility functions for model management
async def get_default_model(client: OllamaClient) -> Optional[str]:
    """
    Get the default model to use for SAR operations.
    
    Args:
        client: Ollama client instance
        
    Returns:
        Name of default model or None if no models available
    """
    try:
        models = await client.list_models()
        if not models:
            return None
            
        # Prefer specific models for SAR operations
        preferred_models = ["llama2", "codellama", "mistral", "phi"]
        
        for preferred in preferred_models:
            for model in models:
                if preferred in model.name.lower():
                    return model.name
                    
        # Return first available model
        return models[0].name
        
    except Exception as e:
        logger.error(f"Failed to get default model: {e}")
        return None


async def ensure_model_available(client: OllamaClient, model_name: str) -> bool:
    """
    Ensure specified model is available, pull if necessary.
    
    Args:
        client: Ollama client instance
        model_name: Name of required model
        
    Returns:
        True if model is available, False otherwise
    """
    try:
        models = await client.list_models()
        model_names = [model.name for model in models]
        
        if model_name in model_names:
            return True
            
        logger.info(f"Model {model_name} not found, attempting to pull...")
        return await client.pull_model(model_name)
        
    except Exception as e:
        logger.error(f"Failed to ensure model availability: {e}")
        return False


# Context manager for easy client usage
@asynccontextmanager
async def ollama_client(base_url: str = "http://localhost:11434", **kwargs):
    """
    Async context manager for Ollama client.
    
    Args:
        base_url: Ollama server URL
        **kwargs: Additional client parameters
        
    Yields:
        Connected Ollama client
    """
    client = OllamaClient(base_url=base_url, **kwargs)
    try:
        await client.connect()
        yield client
    finally:
        await client.close()