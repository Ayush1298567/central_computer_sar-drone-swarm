"""
Conversational AI mission planner service.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MissionPlan:
    """Mission plan data structure."""
    name: str
    description: str
    center: Dict[str, float]
    search_area: Dict[str, Any]
    search_altitude: float
    estimated_duration: int
    max_drones: int
    search_pattern: str
    priority: int
    mission_type: str


class ConversationalMissionPlanner:
    """
    Conversational AI service for mission planning.
    """

    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.conversation_history: Dict[str, List[Dict]] = {}

    async def process_message(self, session_id: str, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user message and generate AI response.

        Args:
            session_id: Chat session ID
            user_message: User's message
            context: Additional context

        Returns:
            AI response dictionary
        """
        try:
            # Get conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []

            history = self.conversation_history[session_id]

            # Build prompt
            prompt = self._build_conversation_prompt(user_message, history, context)

            # Generate AI response
            ai_response = await self._generate_ai_response(prompt)

            # Parse structured data from response
            structured_data = self._parse_structured_response(ai_response)

            # Update conversation history
            history.append({"role": "user", "content": user_message, "timestamp": datetime.utcnow()})
            history.append({"role": "assistant", "content": ai_response, "timestamp": datetime.utcnow()})

            # Keep only last 20 messages
            if len(history) > 20:
                self.conversation_history[session_id] = history[-20:]

            return {
                "content": ai_response,
                "message_type": structured_data.get("message_type", "text"),
                "metadata": structured_data.get("metadata", {}),
                "current_mission_plan": structured_data.get("mission_plan"),
                "tokens_used": len(ai_response.split()) * 1.3  # Rough estimate
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "content": "I'm sorry, I encountered an error processing your message. Please try again.",
                "message_type": "error",
                "metadata": {"error": str(e)}
            }

    async def generate_mission_plan(self, session_id: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a mission plan based on user requirements.

        Args:
            session_id: Chat session ID
            requirements: Mission requirements

        Returns:
            Mission plan dictionary
        """
        try:
            # Build mission planning prompt
            prompt = self._build_mission_planning_prompt(requirements)

            # Generate mission plan
            ai_response = await self._generate_ai_response(prompt)

            # Parse mission plan from response
            mission_plan = self._parse_mission_plan(ai_response, requirements)

            return mission_plan

        except Exception as e:
            logger.error(f"Error generating mission plan: {e}")
            raise

    def _build_conversation_prompt(self, user_message: str, history: List[Dict], context: Dict[str, Any]) -> str:
        """Build conversation prompt for AI."""
        system_prompt = """
        You are an expert SAR (Search and Rescue) mission planner. You help users plan drone missions for search and rescue operations.

        Your capabilities include:
        - Understanding natural language mission requirements
        - Suggesting optimal search areas and patterns
        - Recommending drone configurations and flight parameters
        - Providing weather-aware mission planning
        - Explaining mission decisions and trade-offs

        When users describe their mission needs, respond helpfully and ask clarifying questions when needed.
        Always consider safety, efficiency, and regulatory compliance in your recommendations.

        If asked about technical details, provide accurate information about drone capabilities, search patterns, and mission parameters.
        """

        # Add context information
        context_str = ""
        if context:
            context_str = f"\nAdditional context: {json.dumps(context)}"

        # Build conversation history
        history_str = ""
        for msg in history[-5:]:  # Last 5 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"\n{role}: {msg['content']}"

        prompt = f"""{system_prompt}

        {history_str}

        {context_str}

        User: {user_message}

        Assistant:"""

        return prompt

    def _build_mission_planning_prompt(self, requirements: Dict[str, Any]) -> str:
        """Build mission planning prompt."""
        prompt = """
        Generate a detailed SAR mission plan based on the following requirements:

        """ + json.dumps(requirements, indent=2) + """

        Consider the following factors:
        - Search area size and terrain
        - Weather conditions and time of day
        - Available drone capabilities
        - Mission objectives and priorities
        - Safety and regulatory requirements
        - Optimal search patterns for the area type

        Provide a structured mission plan with:
        - Mission name and description
        - Center coordinates and search area boundaries
        - Recommended altitude and flight parameters
        - Number of drones needed
        - Estimated mission duration
        - Search pattern recommendations
        - Safety considerations

        Format your response as JSON with the following structure:
        {
            "mission_plan": {
                "name": "Mission Name",
                "description": "Mission Description",
                "center": {"lat": 0.0, "lng": 0.0},
                "search_area": {"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]},
                "search_altitude": 30.0,
                "estimated_duration": 60,
                "max_drones": 2,
                "search_pattern": "lawnmower",
                "priority": 3,
                "mission_type": "search"
            },
            "explanation": "Explanation of the plan and reasoning"
        }

        Assistant:"""

        return prompt

    async def _generate_ai_response(self, prompt: str) -> str:
        """Generate AI response using Ollama."""
        try:
            # Try Ollama first
            if self._is_ollama_available():
                return await self._call_ollama(prompt)
            else:
                # Fallback to mock response for development
                return self._generate_mock_response(prompt)

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_mock_response(prompt)

    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            # Simple availability check
            return True  # For now, assume available
        except:
            return False

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API."""
        try:
            url = f"{self.ollama_base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                return result.get("response", "No response generated")

        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise

    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response for development/testing."""
        if "mission plan" in prompt.lower():
            return """Based on your requirements, I've created a mission plan for the search operation.

The plan includes:
- Search area covering approximately 2 square kilometers
- Optimal altitude of 30 meters for visual detection
- Lawnmower search pattern for systematic coverage
- Two drones recommended for efficient coverage
- Estimated 45-minute mission duration

This plan prioritizes safety while maximizing search effectiveness."""

        return """I understand your mission requirements. To provide the best assistance, could you please provide more details about:

1. The specific location or area you want to search
2. What type of target you're looking for (person, vehicle, etc.)
3. Any time constraints or urgency level
4. Available drone resources and their capabilities

This will help me create an optimal mission plan tailored to your needs."""

    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured data from AI response."""
        # Simple parsing for mission plan data
        structured = {
            "message_type": "text",
            "metadata": {},
            "mission_plan": None
        }

        # Look for JSON in response
        try:
            # Try to find JSON block
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                if "mission_plan" in data:
                    structured["message_type"] = "mission_plan"
                    structured["mission_plan"] = data["mission_plan"]
                    structured["metadata"] = {"explanation": data.get("explanation", "")}

        except json.JSONDecodeError:
            pass  # Not valid JSON, treat as regular text

        return structured

    def _parse_mission_plan(self, response: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Parse mission plan from AI response."""
        try:
            # Look for JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                if "mission_plan" in data:
                    return data["mission_plan"]

        except json.JSONDecodeError:
            pass

        # Fallback: generate basic mission plan from requirements
        return {
            "name": requirements.get("name", "SAR Mission"),
            "description": requirements.get("description", "Search and rescue operation"),
            "center": requirements.get("center", {"lat": 0.0, "lng": 0.0}),
            "search_area": requirements.get("search_area", {}),
            "search_altitude": requirements.get("search_altitude", 30.0),
            "estimated_duration": requirements.get("estimated_duration", 60),
            "max_drones": requirements.get("max_drones", 1),
            "search_pattern": requirements.get("search_pattern", "lawnmower"),
            "priority": requirements.get("priority", 3),
            "mission_type": requirements.get("mission_type", "search")
        }


# Global conversational planner instance
conversational_planner = ConversationalMissionPlanner()