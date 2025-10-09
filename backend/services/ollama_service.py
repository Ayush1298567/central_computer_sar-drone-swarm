"""
Ollama service for local LLM integration
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with local Ollama LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "mistral:7b"
        self.session: Optional[aiohttp.ClientSession] = None
        self._available_models: List[str] = []
    
    async def start(self):
        """Start the Ollama service"""
        self.session = aiohttp.ClientSession()
        await self._check_ollama_availability()
        await self._load_available_models()
    
    async def stop(self):
        """Stop the Ollama service"""
        if self.session:
            await self.session.close()
    
    async def _check_ollama_availability(self):
        """Check if Ollama is running and available"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    logger.info("Ollama is available")
                    return True
                else:
                    logger.error(f"Ollama returned status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False
    
    async def _load_available_models(self):
        """Load available models from Ollama"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self._available_models = [model["name"] for model in data.get("models", [])]
                    logger.info(f"Available models: {self._available_models}")
                    
                    # Check if mistral:7b is available
                    if "mistral:7b" not in self._available_models:
                        logger.warning("mistral:7b not found. Available models: {self._available_models}")
                        if self._available_models:
                            self.model = self._available_models[0]
                            logger.info(f"Using model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    async def generate_response(self, prompt: str, context: str = "", 
                              system_prompt: str = "", max_tokens: int = 1000) -> str:
        """Generate response from LLM"""
        if not self.session:
            raise RuntimeError("Ollama service not started")
        
        # Construct full prompt
        full_prompt = self._construct_prompt(prompt, context, system_prompt)
        
        try:
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "").strip()
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error {response.status}: {error_text}")
                    return f"Error: Ollama API returned status {response.status}"
        
        except asyncio.TimeoutError:
            logger.error("Ollama request timeout")
            return "Error: Request timeout"
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return f"Error: {str(e)}"
    
    def _construct_prompt(self, prompt: str, context: str = "", system_prompt: str = "") -> str:
        """Construct full prompt with context and system instructions"""
        parts = []
        
        if system_prompt:
            parts.append(f"System: {system_prompt}")
        
        if context:
            parts.append(f"Context: {context}")
        
        parts.append(f"User: {prompt}")
        parts.append("Assistant:")
        
        return "\n\n".join(parts)
    
    async def generate_mission_questions(self, mission_description: str, 
                                       conversation_history: List[Dict[str, str]]) -> str:
        """Generate follow-up questions for mission planning"""
        system_prompt = """You are an expert search and rescue mission planner. Your job is to ask intelligent, specific questions to gather all necessary information for a SAR mission. Ask 1-2 critical questions at a time. Be direct and practical. Focus on safety, logistics, and operational details."""
        
        context_parts = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            context_parts.append(f"{msg['role']}: {msg['content']}")
        
        context = "\n".join(context_parts) if context_parts else ""
        
        prompt = f"""The user wants to plan this SAR mission: "{mission_description}"

Based on the conversation so far, what is the most critical information you still need to ask about? Provide exactly ONE specific, actionable question that will help plan this mission effectively.

Consider: location details, hazards, number of survivors, time constraints, weather, access routes, equipment needs, safety concerns."""
        
        return await self.generate_response(prompt, context, system_prompt)
    
    async def generate_mission_plan(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete mission plan from gathered information"""
        system_prompt = """You are an expert SAR mission planner. Create a detailed, actionable mission plan in JSON format. Include search areas, drone assignments, safety parameters, and waypoints."""
        
        prompt = f"""Based on this mission information, create a complete SAR mission plan:

Mission: {mission_data.get('description', 'Unknown')}
Location: {mission_data.get('location', 'Not specified')}
Area Size: {mission_data.get('area_size', 'Not specified')}
Hazards: {mission_data.get('hazards', 'None identified')}
Priority: {mission_data.get('priority', 'Standard')}
Drones Available: {mission_data.get('drone_count', 'Unknown')}

Return a JSON object with:
- mission_name: string
- search_area: GeoJSON polygon
- drone_assignments: array of drone zones
- estimated_duration: minutes
- safety_parameters: object
- waypoints: array of lat/lng coordinates
- coverage_strategy: string
- emergency_procedures: array of strings"""
        
        response = await self.generate_response(prompt, "", system_prompt)
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to structured response
                return self._parse_mission_plan_response(response, mission_data)
        except json.JSONDecodeError:
            return self._parse_mission_plan_response(response, mission_data)
    
    def _parse_mission_plan_response(self, response: str, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse mission plan from text response"""
        # Create a basic mission plan structure
        return {
            "mission_name": mission_data.get('description', 'SAR Mission'),
            "search_area": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.5, 37.7], [-122.4, 37.7], 
                    [-122.4, 37.8], [-122.5, 37.8], 
                    [-122.5, 37.7]
                ]]
            },
            "drone_assignments": [
                {
                    "drone_id": 1,
                    "zone": "northwest",
                    "waypoints": [
                        {"lat": 37.75, "lng": -122.45},
                        {"lat": 37.76, "lng": -122.44}
                    ]
                }
            ],
            "estimated_duration": 120,
            "safety_parameters": {
                "min_battery": 30,
                "max_altitude": 100,
                "weather_limits": "clear conditions only"
            },
            "waypoints": [
                {"lat": 37.75, "lng": -122.45},
                {"lat": 37.76, "lng": -122.44}
            ],
            "coverage_strategy": "Grid pattern with 50m spacing",
            "emergency_procedures": [
                "Return to base if battery < 30%",
                "Land immediately if weather deteriorates",
                "Report any structural hazards immediately"
            ]
        }
    
    async def parse_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse natural language command into structured action"""
        system_prompt = """You are a drone command parser. Convert natural language commands into structured JSON actions for drone control."""
        
        prompt = f"""Parse this command: "{command}"

Available drones: {context.get('available_drones', [])}
Current mission: {context.get('current_mission', 'None')}

Return JSON with:
- action: string (return_to_base, investigate, pause, resume, etc.)
- target_drones: array of drone IDs
- parameters: object with specific details
- priority: string (high, medium, low)"""
        
        response = await self.generate_response(prompt, "", system_prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing
        return self._parse_command_fallback(command)
    
    def _parse_command_fallback(self, command: str) -> Dict[str, Any]:
        """Fallback command parsing"""
        command_lower = command.lower()
        
        if "return" in command_lower and "base" in command_lower:
            return {
                "action": "return_to_base",
                "target_drones": "all",
                "parameters": {},
                "priority": "high"
            }
        elif "investigate" in command_lower:
            return {
                "action": "investigate",
                "target_drones": "all",
                "parameters": {"area": "specified location"},
                "priority": "medium"
            }
        elif "pause" in command_lower:
            return {
                "action": "pause",
                "target_drones": "all",
                "parameters": {},
                "priority": "medium"
            }
        else:
            return {
                "action": "unknown",
                "target_drones": "all",
                "parameters": {},
                "priority": "low"
            }
    
    async def analyze_discovery(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze discovery data and provide assessment"""
        system_prompt = """You are a SAR expert analyzing drone discovery data. Provide assessment of findings."""
        
        prompt = f"""Analyze this discovery:

Type: {discovery_data.get('type', 'Unknown')}
Location: {discovery_data.get('location', 'Unknown')}
Confidence: {discovery_data.get('confidence', 0)}%
Description: {discovery_data.get('description', 'No description')}

Provide assessment with:
- likelihood: string (high, medium, low)
- recommended_action: string
- urgency: string (immediate, high, medium, low)
- additional_notes: string"""
        
        response = await self.generate_response(prompt, "", system_prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback assessment
        return {
            "likelihood": "medium",
            "recommended_action": "Investigate further",
            "urgency": "medium",
            "additional_notes": "Requires human verification"
        }

# Global Ollama service instance
ollama_service = OllamaService()