"""
Ollama AI integration for SAR Mission Commander.
Provides AI-powered analysis and decision making capabilities.
"""
import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama AI service integration.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = "llama2"
        self.timeout = 30

    async def generate_response(self, prompt: str, model: str = None, context: str = None) -> str:
        """
        Generate AI response using Ollama.

        Args:
            prompt: Input prompt for the AI
            model: AI model to use
            context: Optional context information

        Returns:
            AI-generated response
        """
        try:
            model = model or self.default_model

            # Check if Ollama service is available
            if not await self._check_service_health():
                return self._get_fallback_response(prompt)

            # Prepare request payload
            payload = {
                "model": model,
                "prompt": self._format_prompt(prompt, context),
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 500
                }
            }

            # Make request to Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "").strip()
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return self._get_fallback_response(prompt)

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response(prompt)

    def _format_prompt(self, prompt: str, context: str = None) -> str:
        """Format prompt with context for better AI responses."""
        if context:
            formatted_prompt = f"""
Context: {context}

User Query: {prompt}

Please provide a helpful, accurate response based on the context provided.
If this is about SAR (Search and Rescue) mission planning, focus on:
- Mission parameters and constraints
- Safety considerations
- Resource optimization
- Weather impact assessment
- Emergency protocols

Response should be clear, concise, and actionable.
"""
        else:
            formatted_prompt = f"""
{prompt}

Please provide a helpful, accurate response. If this is about SAR mission planning,
focus on operational safety, efficiency, and effectiveness.
"""

        return formatted_prompt

    async def _check_service_health(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama service health check failed: {e}")
            return False

    def _get_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when AI service is unavailable."""
        # Simple rule-based responses for common queries
        prompt_lower = prompt.lower()

        if "weather" in prompt_lower and ("mission" in prompt_lower or "search" in prompt_lower):
            return (
                "Weather conditions significantly impact SAR mission safety and effectiveness. "
                "I recommend checking current wind speeds, visibility, and precipitation levels. "
                "High winds (>15 m/s) may require reduced altitude or pattern adjustments. "
                "Consider thermal imaging for low-visibility conditions."
            )

        elif "emergency" in prompt_lower or "abort" in prompt_lower:
            return (
                "For emergency situations: 1) Immediately command all drones to return to base, "
                "2) Alert emergency services if human life is at risk, "
                "3) Preserve all mission data and logs for analysis, "
                "4) Check drone status and ensure safe landing procedures."
            )

        elif "mission" in prompt_lower and ("plan" in prompt_lower or "create" in prompt_lower):
            return (
                "To plan an effective SAR mission: 1) Define the search area boundaries, "
                "2) Specify target type and characteristics, 3) Set time constraints and priorities, "
                "4) Consider weather conditions and drone capabilities, "
                "5) Plan for multiple search patterns and contingency scenarios."
            )

        else:
            return (
                "I understand you're asking about SAR mission operations. "
                "For optimal results, please provide specific details about: "
                "the search area, target description, time constraints, and any special requirements. "
                "I can help optimize drone deployment patterns and mission parameters accordingly."
            )

    async def analyze_mission_scenario(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a mission scenario and provide AI insights.

        Args:
            scenario_data: Mission scenario information

        Returns:
            AI analysis and recommendations
        """
        try:
            scenario_text = json.dumps(scenario_data, indent=2)

            prompt = f"""
Analyze this SAR mission scenario and provide strategic recommendations:

Scenario Details:
{scenario_text}

Please provide analysis covering:
1. Mission complexity assessment
2. Resource allocation recommendations
3. Risk factors and mitigation strategies
4. Optimal search patterns and timing
5. Success probability estimation
6. Contingency planning suggestions

Focus on operational safety, efficiency, and mission success probability.
"""

            analysis = await self.generate_response(prompt, context="SAR Mission Analysis")

            return {
                "analysis": analysis,
                "scenario_summary": scenario_data,
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": self.default_model
            }

        except Exception as e:
            logger.error(f"Error analyzing mission scenario: {e}")
            return {
                "error": str(e),
                "fallback_analysis": "Unable to generate AI analysis. Please review mission parameters manually."
            }

    async def optimize_search_pattern(self, area_data: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize search pattern based on area characteristics and constraints.

        Args:
            area_data: Search area information
            constraints: Mission constraints

        Returns:
            Optimized search pattern recommendations
        """
        try:
            prompt = f"""
Optimize search pattern for this SAR mission:

Area: {area_data.get('size_km2', 'unknown')} km² {area_data.get('terrain', 'mixed')} terrain
Target: {area_data.get('target_type', 'person')}
Constraints: {json.dumps(constraints, indent=2)}

Recommend:
1. Optimal search pattern (lawnmower, spiral, grid, etc.)
2. Flight altitude and speed settings
3. Estimated coverage time
4. Resource allocation (number of drones needed)
5. Pattern efficiency factors

Consider terrain type, target characteristics, and operational constraints.
"""

            optimization = await self.generate_response(prompt, context="Search Pattern Optimization")

            return {
                "optimization": optimization,
                "area_data": area_data,
                "constraints": constraints,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error optimizing search pattern: {e}")
            return {
                "error": str(e),
                "fallback_pattern": "lawnmower",
                "fallback_altitude": 30,
                "fallback_reasoning": "Default pattern when AI optimization fails"
            }


# Global Ollama client instance
ollama_client = OllamaClient()
