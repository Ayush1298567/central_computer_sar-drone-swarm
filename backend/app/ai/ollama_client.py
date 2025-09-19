"""
Ollama client for local AI model integration.
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama AI service."""
    
    def __init__(self):
        self.base_url = settings.ollama_host
        self.default_model = settings.ollama_model
        self.session: Optional[aiohttp.ClientSession] = None
        self.available_models: List[str] = []
        self.model_info: Dict[str, dict] = {}
        
    async def initialize(self):
        """Initialize the Ollama client and check connectivity."""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection
            await self.health_check()
            
            # Load available models
            await self.load_models()
            
            # Ensure default model is available
            await self.ensure_model_available(self.default_model)
            
            logger.info(f"Ollama client initialized successfully with {len(self.available_models)} models")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    return True
                else:
                    logger.warning(f"Ollama health check failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def load_models(self):
        """Load list of available models from Ollama."""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model["name"] for model in data.get("models", [])]
                    
                    # Store model details
                    for model in data.get("models", []):
                        self.model_info[model["name"]] = {
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest")
                        }
                    
                    logger.info(f"Loaded {len(self.available_models)} models: {self.available_models}")
                else:
                    logger.error(f"Failed to load models: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    async def ensure_model_available(self, model_name: str) -> bool:
        """Ensure a specific model is available, pull if necessary."""
        if model_name in self.available_models:
            return True
        
        logger.info(f"Model {model_name} not found, attempting to pull...")
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status == 200:
                    # Stream the pull response
                    async for line in response.content:
                        if line:
                            pull_status = json.loads(line.decode())
                            if pull_status.get("status") == "success":
                                logger.info(f"Successfully pulled model {model_name}")
                                await self.load_models()  # Refresh model list
                                return True
                            elif "error" in pull_status:
                                logger.error(f"Error pulling model {model_name}: {pull_status['error']}")
                                return False
                else:
                    logger.error(f"Failed to pull model {model_name}: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Exception while pulling model {model_name}: {e}")
            return False
        
        return False
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """Generate a response from the AI model."""
        model = model or self.default_model
        
        if model not in self.available_models:
            if not await self.ensure_model_available(model):
                raise ValueError(f"Model {model} is not available and could not be pulled")
        
        # Prepare the request
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=request_data
            ) as response:
                if response.status == 200:
                    if stream:
                        return await self._handle_streaming_response(response)
                    else:
                        result = await response.json()
                        return result.get("response", "")
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error {response.status}: {error_text}")
                    raise Exception(f"Ollama API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def _handle_streaming_response(self, response) -> str:
        """Handle streaming response from Ollama."""
        full_response = ""
        
        async for line in response.content:
            if line:
                try:
                    chunk = json.loads(line.decode())
                    if "response" in chunk:
                        full_response += chunk["response"]
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
        
        return full_response
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a chat completion response."""
        model = model or self.default_model
        
        if model not in self.available_models:
            if not await self.ensure_model_available(model):
                raise ValueError(f"Model {model} is not available and could not be pulled")
        
        request_data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama chat API error {response.status}: {error_text}")
                    raise Exception(f"Ollama chat API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def analyze_mission_context(
        self,
        mission_data: dict,
        context_type: str = "planning"
    ) -> dict:
        """Analyze mission context and provide AI insights."""
        system_prompt = """You are an expert SAR (Search and Rescue) mission planner AI. 
        Analyze the provided mission context and provide structured insights, recommendations, 
        and potential risks. Your response should be in JSON format."""
        
        prompt = f"""
        Mission Context Analysis Request:
        Type: {context_type}
        Mission Data: {json.dumps(mission_data, indent=2)}
        
        Please analyze this SAR mission context and provide:
        1. Risk assessment
        2. Resource recommendations
        3. Weather considerations
        4. Search pattern suggestions
        5. Safety recommendations
        6. Timeline estimates
        
        Respond in JSON format with these sections.
        """
        
        try:
            response = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Try to parse as JSON, fallback to text response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "analysis_type": context_type,
                    "raw_response": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing mission context: {e}")
            return {
                "error": str(e),
                "analysis_type": context_type,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_clarifying_questions(
        self,
        conversation_history: List[dict],
        current_mission_state: dict
    ) -> List[str]:
        """Generate clarifying questions for mission planning."""
        system_prompt = """You are an expert SAR mission planner. Based on the conversation 
        history and current mission state, generate specific, practical clarifying questions 
        to gather missing critical information for the mission plan. Focus on safety, 
        efficiency, and operational requirements."""
        
        prompt = f"""
        Conversation History: {json.dumps(conversation_history, indent=2)}
        Current Mission State: {json.dumps(current_mission_state, indent=2)}
        
        Generate 1-3 specific clarifying questions to gather missing critical information.
        Focus on the most important gaps in the mission plan.
        Return as a JSON array of question strings.
        """
        
        try:
            response = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            # Try to parse as JSON array
            try:
                questions = json.loads(response)
                if isinstance(questions, list):
                    return questions
                else:
                    return [response]  # Fallback to single question
            except json.JSONDecodeError:
                # Extract questions from text response
                lines = response.strip().split('\n')
                questions = [line.strip('- ').strip() for line in lines if line.strip()]
                return questions[:3]  # Limit to 3 questions
                
        except Exception as e:
            logger.error(f"Error generating clarifying questions: {e}")
            return ["Could you provide more details about the search area and objectives?"]
    
    async def make_autonomous_decision(
        self,
        mission_id: str,
        situation_data: dict,
        decision_context: str
    ) -> dict:
        """Make an autonomous decision based on mission situation."""
        system_prompt = """You are an autonomous SAR mission AI making critical real-time 
        decisions. Analyze the situation and provide a structured decision with clear 
        reasoning. Always prioritize safety and mission effectiveness."""
        
        prompt = f"""
        Mission ID: {mission_id}
        Decision Context: {decision_context}
        Situation Data: {json.dumps(situation_data, indent=2)}
        
        Make an autonomous decision and provide:
        1. Decision type and action
        2. Reasoning
        3. Risk assessment
        4. Alternative options considered
        5. Expected outcomes
        
        Respond in JSON format with these fields: decision_type, action, reasoning, 
        risk_level, alternatives, expected_outcomes, confidence_level.
        """
        
        try:
            response = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2  # Very low temperature for consistent decisions
            )
            
            try:
                decision = json.loads(response)
                decision["timestamp"] = datetime.utcnow().isoformat()
                decision["mission_id"] = mission_id
                return decision
            except json.JSONDecodeError:
                return {
                    "decision_type": "analysis_only",
                    "action": "manual_review_required",
                    "reasoning": response,
                    "risk_level": "unknown",
                    "confidence_level": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "mission_id": mission_id
                }
                
        except Exception as e:
            logger.error(f"Error making autonomous decision: {e}")
            return {
                "decision_type": "error",
                "action": "manual_intervention_required",
                "reasoning": f"AI decision system error: {str(e)}",
                "risk_level": "high",
                "confidence_level": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "mission_id": mission_id
            }
    
    async def get_status(self) -> dict:
        """Get the status of the Ollama client."""
        is_healthy = await self.health_check() if self.session else False
        
        return {
            "connected": is_healthy,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "available_models": len(self.available_models),
            "models": self.available_models
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Ollama client cleanup completed")