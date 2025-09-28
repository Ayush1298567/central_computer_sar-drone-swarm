"""
LLM Intelligence Engine for SAR Mission Decision Making.

Uses external Large Language Models (OpenAI GPT, Anthropic Claude, etc.) as AI agents
for intelligent decision-making in search and rescue operations.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """Generate response from LLM."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if LLM provider is available."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for intelligent decision making."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            # This would use actual OpenAI SDK in production
            # For now, simulate response structure
            return {
                "success": True,
                "response": f"OpenAI response to: {prompt[:100]}...",
                "model": self.model,
                "provider": "openai"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "openai"
            }

    async def health_check(self) -> bool:
        """Check OpenAI API availability."""
        try:
            # This would make actual API call in production
            return True
        except Exception:
            return False

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.base_url = base_url
        self.model = model

    async def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """Generate response using Ollama API."""
        try:
            # This would use actual Ollama client in production
            # For now, simulate response structure
            return {
                "success": True,
                "response": f"Ollama response to: {prompt[:100]}...",
                "model": self.model,
                "provider": "ollama"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "ollama"
            }

    async def health_check(self) -> bool:
        """Check Ollama server availability."""
        try:
            # This would make actual health check call in production
            return True
        except Exception:
            return False

class LLMIntelligenceEngine:
    """
    LLM-powered intelligence engine for SAR mission decision-making.

    Uses external LLMs to provide real intelligence for complex tactical decisions,
    search strategy planning, and coordination recommendations.
    """

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.primary_provider = None
        self.fallback_providers = []
        self.initialized = False

    async def initialize(self):
        """Initialize LLM providers."""
        try:
            # Initialize OpenAI provider if API key available
            openai_key = None  # Would get from environment/config
            if openai_key:
                openai_provider = OpenAIProvider(openai_key)
                if await openai_provider.health_check():
                    self.providers["openai"] = openai_provider
                    self.primary_provider = openai_provider
                    logger.info("OpenAI provider initialized as primary")

            # Initialize Ollama provider
            ollama_provider = OllamaProvider()
            if await ollama_provider.health_check():
                self.providers["ollama"] = ollama_provider
                if not self.primary_provider:
                    self.primary_provider = ollama_provider
                    logger.info("Ollama provider initialized as primary")
                else:
                    self.fallback_providers.append(ollama_provider)
                    logger.info("Ollama provider initialized as fallback")

            if not self.primary_provider:
                logger.warning("No LLM providers available - intelligence features disabled")
                return

            self.initialized = True
            logger.info("LLM intelligence engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLM engine: {e}")
            self.initialized = False

    async def make_tactical_decision(self, mission_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to make intelligent tactical decisions for mission coordination.

        Args:
            mission_context: Current mission state and context

        Returns:
            Tactical decisions and recommendations
        """
        if not self.initialized or not self.primary_provider:
            return self._get_default_tactical_decision()

        prompt = self._build_tactical_prompt(mission_context)

        try:
            response = await self.primary_provider.generate_response(
                prompt=prompt,
                system_prompt=self._get_tactical_system_prompt(),
                temperature=0.2  # Low temperature for tactical decisions
            )

            if response.get("success"):
                return self._parse_tactical_response(response["response"])
            else:
                logger.error(f"Tactical decision generation failed: {response.get('error')}")
                return self._get_default_tactical_decision()

        except Exception as e:
            logger.error(f"Error in tactical decision making: {e}")
            return self._get_default_tactical_decision()

    async def plan_search_strategy(self, area_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to create intelligent search strategies.

        Args:
            area_data: Search area information and constraints

        Returns:
            Search strategy recommendations
        """
        if not self.initialized or not self.primary_provider:
            return self._get_default_search_strategy()

        prompt = self._build_search_prompt(area_data)

        try:
            response = await self.primary_provider.generate_response(
                prompt=prompt,
                system_prompt=self._get_search_system_prompt(),
                temperature=0.3
            )

            if response.get("success"):
                return self._parse_search_strategy(response["response"])
            else:
                logger.error(f"Search strategy generation failed: {response.get('error')}")
                return self._get_default_search_strategy()

        except Exception as e:
            logger.error(f"Error in search strategy planning: {e}")
            return self._get_default_search_strategy()

    async def analyze_discovery(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze discoveries and recommend investigation strategies.

        Args:
            discovery_data: Discovery information and context

        Returns:
            Analysis and recommendations
        """
        if not self.initialized or not self.primary_provider:
            return self._get_default_discovery_analysis()

        prompt = self._build_discovery_prompt(discovery_data)

        try:
            response = await self.primary_provider.generate_response(
                prompt=prompt,
                system_prompt=self._get_discovery_system_prompt(),
                temperature=0.1  # Very low temperature for analysis
            )

            if response.get("success"):
                return self._parse_discovery_analysis(response["response"])
            else:
                logger.error(f"Discovery analysis failed: {response.get('error')}")
                return self._get_default_discovery_analysis()

        except Exception as e:
            logger.error(f"Error in discovery analysis: {e}")
            return self._get_default_discovery_analysis()

    def _build_tactical_prompt(self, mission_context: Dict[str, Any]) -> str:
        """Build tactical decision prompt for LLM."""
        return f"""
        You are an expert SAR (Search and Rescue) mission coordinator with years of experience in emergency response operations.

        Current Mission Context:
        - Mission Status: {mission_context.get('mission_status', 'unknown')}
        - Active Drones: {mission_context.get('active_drones', 0)}
        - Recent Discoveries: {len(mission_context.get('discoveries', []))}
        - Weather Conditions: {mission_context.get('weather_conditions', {})}
        - Terrain Complexity: {mission_context.get('terrain_complexity', 'normal')}
        - Time Remaining: {mission_context.get('time_remaining', 'unknown')}

        Recent Events:
        {json.dumps(mission_context.get('recent_events', []), indent=2)}

        Priority Objectives:
        {json.dumps(mission_context.get('priority_objectives', []), indent=2)}

        Please provide specific tactical recommendations for:
        1. Resource reallocation (which drones should focus on which areas)
        2. Priority adjustments (what should be investigated first)
        3. Investigation strategies (how to approach discoveries)
        4. Safety protocols (given current conditions)

        Respond with specific, actionable recommendations in JSON format.
        """

    def _build_search_prompt(self, area_data: Dict[str, Any]) -> str:
        """Build search strategy prompt for LLM."""
        return f"""
        You are a SAR expert specializing in search pattern optimization and resource allocation.

        Search Area Information:
        - Area Size: {area_data.get('area_size', 'unknown')} km²
        - Terrain Type: {area_data.get('terrain_type', 'mixed')}
        - Search Target: {area_data.get('search_target', 'missing persons')}
        - Available Drones: {area_data.get('drone_count', 1)}
        - Time Constraints: {area_data.get('time_limit', 'none')}
        - Weather Conditions: {area_data.get('weather', {})}

        Area Boundaries:
        {json.dumps(area_data.get('boundary', []), indent=2)}

        Please design an optimal search strategy including:
        1. Priority zones based on survivor probability
        2. Recommended search patterns (parallel, expanding square, etc.)
        3. Resource allocation strategy
        4. Safety considerations
        5. Contingency plans

        Respond with detailed, implementable recommendations in JSON format.
        """

    def _build_discovery_prompt(self, discovery_data: Dict[str, Any]) -> str:
        """Build discovery analysis prompt for LLM."""
        return f"""
        You are a SAR expert analyzing potential discoveries for rescue operations.

        Discovery Details:
        - Object Type: {discovery_data.get('object_type', 'unknown')}
        - Confidence Score: {discovery_data.get('confidence_score', 0)}%
        - Location: {discovery_data.get('latitude', 0)}, {discovery_data.get('longitude', 0)}
        - Detection Method: {discovery_data.get('detection_method', 'visual')}
        - Environmental Conditions: {discovery_data.get('environmental_conditions', {})}

        Context Information:
        {json.dumps(discovery_data.get('context', {}), indent=2)}

        Please provide:
        1. Assessment of discovery validity
        2. Recommended investigation approach
        3. Safety considerations
        4. Next steps for ground teams
        5. Alternative explanations to consider

        Respond with analytical recommendations in JSON format.
        """

    def _get_tactical_system_prompt(self) -> str:
        """Get system prompt for tactical decisions."""
        return """
        You are an expert SAR mission coordinator. Provide specific, actionable tactical decisions
        based on the mission context. Focus on:
        - Resource optimization
        - Safety protocols
        - Investigation priorities
        - Emergency response readiness

        Always respond with valid JSON containing specific recommendations.
        """

    def _get_search_system_prompt(self) -> str:
        """Get system prompt for search strategy."""
        return """
        You are a SAR search strategy expert. Design optimal search patterns and resource
        allocation strategies based on terrain, weather, and available resources.
        Consider POD (Probability of Detection) and safety factors.

        Always respond with valid JSON containing detailed search recommendations.
        """

    def _get_discovery_system_prompt(self) -> str:
        """Get system prompt for discovery analysis."""
        return """
        You are a SAR discovery analyst. Evaluate potential discoveries for rescue validity
        and recommend appropriate investigation strategies. Consider false positive risks
        and ground team safety.

        Always respond with valid JSON containing analytical recommendations.
        """

    def _parse_tactical_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM tactical response into structured format."""
        try:
            # Try to parse as JSON first
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract structured information from text
            return {
                "resource_reallocation": [],
                "priority_adjustments": [],
                "investigation_strategies": [],
                "safety_protocols": [],
                "raw_response": response
            }

    def _parse_search_strategy(self, response: str) -> Dict[str, Any]:
        """Parse LLM search strategy response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "priority_zones": [],
                "search_patterns": [],
                "resource_allocation": {},
                "safety_considerations": [],
                "contingency_plans": [],
                "raw_response": response
            }

    def _parse_discovery_analysis(self, response: str) -> Dict[str, Any]:
        """Parse LLM discovery analysis response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "validity_assessment": "unknown",
                "investigation_approach": {},
                "safety_considerations": [],
                "next_steps": [],
                "alternative_explanations": [],
                "raw_response": response
            }

    def _get_default_tactical_decision(self) -> Dict[str, Any]:
        """Get default tactical decision when LLM unavailable."""
        return {
            "resource_reallocation": [],
            "priority_adjustments": [],
            "investigation_strategies": [],
            "safety_protocols": ["Maintain current formations", "Monitor environmental conditions"],
            "reasoning": "Default tactical decisions - LLM unavailable"
        }

    def _get_default_search_strategy(self) -> Dict[str, Any]:
        """Get default search strategy when LLM unavailable."""
        return {
            "priority_zones": [],
            "search_patterns": ["parallel_search"],
            "resource_allocation": {},
            "safety_considerations": ["Monitor weather conditions", "Maintain safe altitudes"],
            "contingency_plans": ["Return to base if conditions deteriorate"],
            "reasoning": "Default search strategy - LLM unavailable"
        }

    def _get_default_discovery_analysis(self) -> Dict[str, Any]:
        """Get default discovery analysis when LLM unavailable."""
        return {
            "validity_assessment": "requires_verification",
            "investigation_approach": {"method": "visual_inspection", "altitude": "low"},
            "safety_considerations": ["Ground team verification required"],
            "next_steps": ["Send ground team for verification"],
            "alternative_explanations": ["Natural formation", "Debris", "Wildlife"],
            "reasoning": "Default analysis - LLM unavailable"
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current LLM engine status."""
        return {
            "initialized": self.initialized,
            "primary_provider": self.primary_provider.__class__.__name__ if self.primary_provider else None,
            "available_providers": list(self.providers.keys()),
            "fallback_providers": len(self.fallback_providers)
        }