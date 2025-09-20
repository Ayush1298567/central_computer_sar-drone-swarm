"""
LLM Intelligence Engine for SAR drone tactical decision making.

This module provides integration with OpenAI/Claude APIs for advanced
tactical decision making, search strategy planning, and mission context analysis.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

import openai
import anthropic
from pydantic import BaseModel, Field

from .ollama_client import OllamaClient, GenerationRequest, ollama_client


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"


class DecisionType(Enum):
    """Types of tactical decisions."""
    SEARCH_PATTERN = "search_pattern"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_ASSESSMENT = "risk_assessment"
    MISSION_ADJUSTMENT = "mission_adjustment"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class MissionContext:
    """Context information for mission analysis."""
    mission_id: str
    mission_type: str
    search_area: Dict[str, Any]
    weather_conditions: Dict[str, Any]
    available_drones: List[Dict[str, Any]]
    time_constraints: Dict[str, Any]
    priority_level: int
    discovered_objects: List[Dict[str, Any]]
    current_progress: float
    
    def to_prompt_context(self) -> str:
        """Convert to natural language context for LLM prompts."""
        context = f"""
Mission Context:
- Mission ID: {self.mission_id}
- Type: {self.mission_type}
- Priority: {self.priority_level}/10
- Progress: {self.current_progress:.1%}
- Search Area: {self.search_area.get('size_km2', 'Unknown')} km²
- Weather: {self.weather_conditions.get('description', 'Unknown')}
- Available Drones: {len(self.available_drones)}
- Discoveries: {len(self.discovered_objects)}
"""
        
        if self.time_constraints:
            remaining = self.time_constraints.get('remaining_minutes', 0)
            context += f"- Time Remaining: {remaining} minutes\n"
            
        return context.strip()


@dataclass
class TacticalDecision:
    """Result of tactical decision making."""
    decision_type: DecisionType
    recommendation: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    estimated_impact: str
    risks: List[str]
    alternatives: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision_type": self.decision_type.value,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "parameters": self.parameters,
            "estimated_impact": self.estimated_impact,
            "risks": self.risks,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp.isoformat()
        }


class SearchStrategy(BaseModel):
    """Search strategy recommendation."""
    pattern_type: str = Field(description="Type of search pattern")
    coverage_priority: str = Field(description="Coverage vs speed priority")
    drone_assignments: List[Dict[str, Any]] = Field(description="Drone role assignments")
    waypoint_density: str = Field(description="Waypoint spacing recommendation")
    estimated_time: int = Field(description="Estimated completion time in minutes")
    success_probability: float = Field(description="Estimated success probability")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class RiskAssessment(BaseModel):
    """Risk assessment for mission operations."""
    overall_risk: str = Field(description="Overall risk level")
    weather_risk: str = Field(description="Weather-related risks")
    technical_risk: str = Field(description="Technical failure risks")
    time_risk: str = Field(description="Time constraint risks")
    recommendations: List[str] = Field(description="Risk mitigation recommendations")
    go_no_go: bool = Field(description="Mission continuation recommendation")


class LLMIntelligenceEngine:
    """
    Advanced LLM-based intelligence engine for SAR drone operations.
    
    Provides tactical decision making, search strategy planning, and mission
    context analysis using OpenAI, Claude, or local Ollama models.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        primary_provider: LLMProvider = LLMProvider.OPENAI,
        fallback_provider: LLMProvider = LLMProvider.OLLAMA,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        Initialize LLM Intelligence Engine.
        
        Args:
            openai_api_key: OpenAI API key (from env if None)
            claude_api_key: Claude API key (from env if None)
            ollama_url: Ollama server URL
            primary_provider: Primary LLM provider
            fallback_provider: Fallback provider if primary fails
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens per response
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        
        # Initialize API clients
        self.openai_client = None
        self.claude_client = None
        self.ollama_url = ollama_url
        
        # Setup OpenAI
        openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
            
        # Setup Claude
        claude_key = claude_api_key or os.getenv("ANTHROPIC_API_KEY")
        if claude_key:
            self.claude_client = anthropic.AsyncAnthropic(api_key=claude_key)
            
        logger.info(f"LLM Intelligence Engine initialized with primary: {primary_provider.value}")
        
    async def _call_openai(self, messages: List[Dict[str, str]], model: str = "gpt-4") -> str:
        """Call OpenAI API with retry logic."""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
            
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
            
    async def _call_claude(self, messages: List[Dict[str, str]], model: str = "claude-3-sonnet-20240229") -> str:
        """Call Claude API with retry logic."""
        if not self.claude_client:
            raise Exception("Claude client not initialized")
            
        try:
            # Convert messages format for Claude
            system_msg = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
                    
            response = await self.claude_client.messages.create(
                model=model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_msg,
                messages=user_messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
            
    async def _call_ollama(self, messages: List[Dict[str, str]], model: str = "llama2") -> str:
        """Call Ollama API with retry logic."""
        try:
            async with ollama_client(self.ollama_url) as client:
                response = await client.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.content
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
            
    async def _generate_response(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None
    ) -> str:
        """
        Generate response using specified or primary provider with fallback.
        
        Args:
            messages: Conversation messages
            provider: Specific provider to use (None for primary)
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If all providers fail
        """
        target_provider = provider or self.primary_provider
        
        try:
            if target_provider == LLMProvider.OPENAI:
                return await self._call_openai(messages)
            elif target_provider == LLMProvider.CLAUDE:
                return await self._call_claude(messages)
            elif target_provider == LLMProvider.OLLAMA:
                return await self._call_ollama(messages)
            else:
                raise ValueError(f"Unknown provider: {target_provider}")
                
        except Exception as e:
            if provider is None and target_provider != self.fallback_provider:
                logger.warning(f"Primary provider {target_provider.value} failed, trying fallback...")
                return await self._generate_response(messages, self.fallback_provider)
            else:
                raise Exception(f"All LLM providers failed: {e}")
                
    async def analyze_mission_context(self, context: MissionContext) -> Dict[str, Any]:
        """
        Analyze mission context and provide strategic insights.
        
        Args:
            context: Current mission context
            
        Returns:
            Strategic analysis and recommendations
        """
        system_prompt = """You are an expert SAR (Search and Rescue) mission analyst with deep knowledge of drone operations, search patterns, and emergency response tactics. Analyze the provided mission context and provide strategic insights."""
        
        user_prompt = f"""
{context.to_prompt_context()}

Please analyze this SAR mission context and provide:
1. Current situation assessment
2. Key challenges and opportunities
3. Strategic recommendations
4. Resource optimization suggestions
5. Risk factors to monitor

Respond in JSON format with these sections: situation_assessment, challenges, opportunities, recommendations, resource_optimization, risk_factors.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._generate_response(messages)
            analysis = json.loads(response)
            
            logger.info(f"Completed mission context analysis for {context.mission_id}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {"error": "Failed to parse analysis", "raw_response": response}
        except Exception as e:
            logger.error(f"Mission context analysis failed: {e}")
            raise
            
    async def plan_search_strategy(
        self,
        context: MissionContext,
        terrain_type: str = "mixed",
        urgency_level: str = "high"
    ) -> SearchStrategy:
        """
        Generate optimal search strategy based on mission context.
        
        Args:
            context: Mission context
            terrain_type: Type of terrain (urban, forest, mountain, water, mixed)
            urgency_level: Mission urgency (low, medium, high, critical)
            
        Returns:
            Recommended search strategy
        """
        system_prompt = """You are a SAR drone operations specialist. Design optimal search patterns and strategies based on mission parameters, terrain, weather, and available resources."""
        
        user_prompt = f"""
{context.to_prompt_context()}

Additional Parameters:
- Terrain Type: {terrain_type}
- Urgency Level: {urgency_level}

Design an optimal search strategy considering:
1. Search pattern type (grid, spiral, sector, adaptive)
2. Coverage vs speed trade-offs
3. Drone role assignments and coordination
4. Waypoint density and spacing
5. Estimated completion time
6. Success probability factors

Respond with a JSON object matching this schema:
{{
    "pattern_type": "string (grid/spiral/sector/adaptive)",
    "coverage_priority": "string (thorough/balanced/rapid)",
    "drone_assignments": [
        {{
            "drone_id": "string",
            "role": "string (primary_search/secondary_coverage/standby/relay)",
            "sector": "string",
            "altitude": "number"
        }}
    ],
    "waypoint_density": "string (high/medium/low)",
    "estimated_time": "number (minutes)",
    "success_probability": "number (0.0-1.0)"
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._generate_response(messages)
            strategy_data = json.loads(response)
            
            strategy = SearchStrategy(**strategy_data)
            logger.info(f"Generated search strategy: {strategy.pattern_type} pattern")
            return strategy
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse search strategy: {e}")
            # Return default strategy
            return SearchStrategy(
                pattern_type="grid",
                coverage_priority="balanced",
                drone_assignments=[],
                waypoint_density="medium",
                estimated_time=60,
                success_probability=0.5
            )
        except Exception as e:
            logger.error(f"Search strategy planning failed: {e}")
            raise
            
    async def assess_risks(self, context: MissionContext) -> RiskAssessment:
        """
        Assess mission risks and provide mitigation recommendations.
        
        Args:
            context: Mission context
            
        Returns:
            Risk assessment with recommendations
        """
        system_prompt = """You are a SAR mission risk analyst. Evaluate all potential risks including weather, technical, operational, and time-related factors. Provide clear go/no-go recommendations."""
        
        user_prompt = f"""
{context.to_prompt_context()}

Assess mission risks in these categories:
1. Weather-related risks (visibility, wind, precipitation)
2. Technical risks (equipment failure, communication loss)
3. Operational risks (terrain hazards, airspace conflicts)
4. Time constraint risks (daylight, search window)

Provide assessment in JSON format:
{{
    "overall_risk": "string (low/medium/high/critical)",
    "weather_risk": "string with assessment",
    "technical_risk": "string with assessment", 
    "time_risk": "string with assessment",
    "recommendations": ["string array of mitigation actions"],
    "go_no_go": "boolean (true to proceed, false to abort/delay)"
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._generate_response(messages)
            risk_data = json.loads(response)
            
            assessment = RiskAssessment(**risk_data)
            logger.info(f"Risk assessment completed: {assessment.overall_risk} risk level")
            return assessment
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse risk assessment: {e}")
            # Return conservative default
            return RiskAssessment(
                overall_risk="medium",
                weather_risk="Unknown weather conditions require monitoring",
                technical_risk="Standard technical risks apply",
                time_risk="Time constraints may impact mission success",
                recommendations=["Monitor weather conditions", "Verify equipment status"],
                go_no_go=False
            )
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            raise
            
    async def make_tactical_decision(
        self,
        decision_type: DecisionType,
        context: MissionContext,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> TacticalDecision:
        """
        Make tactical decision based on current mission state.
        
        Args:
            decision_type: Type of decision needed
            context: Current mission context
            additional_info: Additional context-specific information
            
        Returns:
            Tactical decision with reasoning
        """
        system_prompt = f"""You are an expert SAR tactical decision maker. You must make critical decisions during active search and rescue operations. Consider all factors including safety, efficiency, resource constraints, and mission success probability."""
        
        decision_context = context.to_prompt_context()
        if additional_info:
            decision_context += f"\n\nAdditional Information:\n{json.dumps(additional_info, indent=2)}"
            
        user_prompt = f"""
{decision_context}

Decision Required: {decision_type.value.replace('_', ' ').title()}

Provide a tactical decision with:
1. Clear recommendation
2. Confidence level (0.0-1.0)
3. Detailed reasoning
4. Implementation parameters
5. Expected impact
6. Potential risks
7. Alternative options

Respond in JSON format:
{{
    "recommendation": "string (clear action to take)",
    "confidence": "number (0.0-1.0)",
    "reasoning": "string (detailed explanation)",
    "parameters": {{"key": "value pairs for implementation"}},
    "estimated_impact": "string (expected outcomes)",
    "risks": ["array of potential risks"],
    "alternatives": ["array of alternative approaches"]
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._generate_response(messages)
            decision_data = json.loads(response)
            
            decision = TacticalDecision(
                decision_type=decision_type,
                recommendation=decision_data["recommendation"],
                confidence=decision_data["confidence"],
                reasoning=decision_data["reasoning"],
                parameters=decision_data["parameters"],
                estimated_impact=decision_data["estimated_impact"],
                risks=decision_data["risks"],
                alternatives=decision_data["alternatives"],
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Tactical decision made: {decision_type.value} (confidence: {decision.confidence:.2f})")
            return decision
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse tactical decision: {e}")
            # Return safe default decision
            return TacticalDecision(
                decision_type=decision_type,
                recommendation="Maintain current operations pending further analysis",
                confidence=0.3,
                reasoning="Unable to process decision request, maintaining safe status quo",
                parameters={},
                estimated_impact="Minimal change to current operations",
                risks=["Decision processing error may indicate system issues"],
                alternatives=["Manual decision making", "Seek additional input"],
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Tactical decision making failed: {e}")
            raise
            
    async def adapt_mission_parameters(
        self,
        context: MissionContext,
        new_discoveries: List[Dict[str, Any]],
        performance_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Adapt mission parameters based on discoveries and performance.
        
        Args:
            context: Current mission context
            new_discoveries: Recent discoveries
            performance_metrics: Current performance data
            
        Returns:
            Recommended parameter adjustments
        """
        system_prompt = """You are an adaptive mission control AI. Continuously optimize search parameters based on real-time discoveries, performance metrics, and changing conditions."""
        
        user_prompt = f"""
{context.to_prompt_context()}

Recent Discoveries:
{json.dumps(new_discoveries, indent=2)}

Performance Metrics:
{json.dumps(performance_metrics, indent=2)}

Based on this information, recommend parameter adjustments for:
1. Search pattern modifications
2. Resource reallocation
3. Priority area updates
4. Speed vs coverage trade-offs
5. Drone coordination changes

Respond in JSON format with specific parameter changes and justifications.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._generate_response(messages)
            adaptations = json.loads(response)
            
            logger.info("Mission parameter adaptations generated")
            return adaptations
            
        except Exception as e:
            logger.error(f"Mission adaptation failed: {e}")
            return {"error": "Adaptation failed", "maintain_current": True}
            
    async def explain_decision(self, decision: TacticalDecision) -> str:
        """
        Generate human-readable explanation of a tactical decision.
        
        Args:
            decision: Tactical decision to explain
            
        Returns:
            Clear explanation for operators
        """
        system_prompt = """You are a SAR mission briefing officer. Explain tactical decisions in clear, concise language that operators can quickly understand and act upon."""
        
        user_prompt = f"""
Explain this tactical decision to mission operators:

Decision Type: {decision.decision_type.value}
Recommendation: {decision.recommendation}
Confidence: {decision.confidence:.1%}
Reasoning: {decision.reasoning}

Provide a brief, actionable explanation that includes:
1. What to do
2. Why it's recommended  
3. What to watch for
4. When to reassess

Keep it under 200 words and use clear, direct language.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            explanation = await self._generate_response(messages)
            return explanation.strip()
            
        except Exception as e:
            logger.error(f"Decision explanation failed: {e}")
            return f"Decision: {decision.recommendation} (Confidence: {decision.confidence:.1%}). Reasoning: {decision.reasoning}"


# Utility functions
async def create_intelligence_engine(
    config: Optional[Dict[str, Any]] = None
) -> LLMIntelligenceEngine:
    """
    Create and configure LLM Intelligence Engine.
    
    Args:
        config: Configuration parameters
        
    Returns:
        Configured intelligence engine
    """
    config = config or {}
    
    engine = LLMIntelligenceEngine(
        openai_api_key=config.get("openai_api_key"),
        claude_api_key=config.get("claude_api_key"),
        ollama_url=config.get("ollama_url", "http://localhost:11434"),
        primary_provider=LLMProvider(config.get("primary_provider", "openai")),
        fallback_provider=LLMProvider(config.get("fallback_provider", "ollama")),
        temperature=config.get("temperature", 0.3),
        max_tokens=config.get("max_tokens", 2000)
    )
    
    return engine