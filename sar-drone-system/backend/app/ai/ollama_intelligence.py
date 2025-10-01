"""
Ollama Intelligence Engine for SAR Mission Planning and Decision Making
"""
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from .ollama_client import OllamaClient
from ..core.config import settings

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    RESOURCE_ALLOCATION = "resource_allocation"
    SEARCH_PATTERN = "search_pattern"
    RISK_ASSESSMENT = "risk_assessment"
    EMERGENCY_RESPONSE = "emergency_response"
    ROUTE_PLANNING = "route_planning"


@dataclass
class MissionContext:
    """Context data for mission analysis"""
    mission_id: str
    mission_type: str
    search_area: Dict[str, Any]
    weather_conditions: Dict[str, Any]
    available_drones: List[Dict[str, Any]]
    time_constraints: Dict[str, Any]
    priority_level: int
    discovered_objects: List[Dict[str, Any]]
    current_progress: float


@dataclass
class SearchStrategy:
    """AI-generated search strategy"""
    pattern_type: str
    estimated_time: int  # minutes
    success_probability: float  # 0-1
    resource_requirements: Dict[str, Any]
    risk_factors: List[str]
    alternative_approaches: List[str]


@dataclass
class RiskAssessment:
    """AI risk analysis results"""
    overall_risk: str  # "low", "medium", "high", "critical"
    go_no_go: bool
    risk_factors: List[Dict[str, Any]]
    mitigation_strategies: List[str]
    confidence_score: float


@dataclass
class TacticalDecision:
    """AI tactical decision result"""
    decision_type: DecisionType
    recommendation: str
    reasoning: str
    confidence: float
    alternative_options: List[str]
    expected_outcome: str


class OllamaIntelligenceEngine:
    """Main AI intelligence engine using Ollama"""
    
    def __init__(self, client: OllamaClient = None, model: str = None):
        self.client = client or OllamaClient()
        self.model = model or settings.OLLAMA_MODEL
        self.system_prompts = self._load_system_prompts()
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different AI tasks"""
        return {
            "mission_analyst": """You are an expert SAR (Search and Rescue) mission analyst. 
            Your role is to analyze mission contexts and provide strategic insights for drone operations.
            Focus on:
            - Risk assessment and safety considerations
            - Resource optimization and allocation
            - Time-critical decision making
            - Terrain and weather impact analysis
            - Success probability estimation
            
            Always provide clear, actionable recommendations with confidence levels.""",
            
            "search_strategist": """You are a specialized search strategy planner for drone SAR operations.
            Your expertise includes:
            - Optimal search pattern selection (grid, spiral, sector, etc.)
            - Coverage optimization algorithms
            - Multi-drone coordination strategies
            - Time and resource efficiency calculations
            - Success probability modeling
            
            Provide detailed search strategies with quantitative estimates.""",
            
            "risk_assessor": """You are a SAR operations risk assessment specialist.
            Your responsibilities include:
            - Identifying operational hazards and threats
            - Evaluating weather and environmental risks
            - Assessing equipment and personnel safety
            - Determining mission feasibility (go/no-go decisions)
            - Developing risk mitigation strategies
            
            Always prioritize safety while maximizing mission effectiveness.""",
            
            "tactical_advisor": """You are a tactical decision support system for SAR drone operations.
            Your role involves:
            - Real-time decision making support
            - Resource allocation optimization
            - Emergency response coordination
            - Mission adaptation strategies
            - Performance monitoring and adjustment
            
            Provide clear, actionable tactical recommendations with reasoning."""
        }
    
    async def analyze_mission_context(self, context: MissionContext) -> Dict[str, Any]:
        """Analyze mission context and provide strategic insights"""
        try:
            prompt = f"""
            Analyze this SAR mission context and provide strategic insights:
            
            Mission ID: {context.mission_id}
            Mission Type: {context.mission_type}
            Search Area: {json.dumps(context.search_area, indent=2)}
            Weather Conditions: {json.dumps(context.weather_conditions, indent=2)}
            Available Drones: {len(context.available_drones)} drones
            Time Constraints: {json.dumps(context.time_constraints, indent=2)}
            Priority Level: {context.priority_level}/10
            Current Progress: {context.current_progress:.1%}
            Discovered Objects: {len(context.discovered_objects)} items
            
            Provide analysis covering:
            1. Mission feasibility assessment
            2. Key challenges and opportunities
            3. Resource optimization recommendations
            4. Critical success factors
            5. Risk indicators to monitor
            
            Format as JSON with clear categories and actionable insights.
            """
            
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=prompt,
                    system=self.system_prompts["mission_analyst"]
                )
            
            # Parse and structure the response
            analysis_text = response.get("response", "")
            
            # Extract JSON if present, otherwise structure the text response
            try:
                # Try to extract JSON from response
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis_data = json.loads(analysis_text[json_start:json_end])
                else:
                    # Structure text response
                    analysis_data = {
                        "analysis": analysis_text,
                        "feasibility": "moderate",
                        "confidence": 0.7
                    }
            except json.JSONDecodeError:
                analysis_data = {
                    "analysis": analysis_text,
                    "feasibility": "moderate", 
                    "confidence": 0.6
                }
            
            return {
                "mission_id": context.mission_id,
                "analysis": analysis_data,
                "timestamp": "2024-01-01T00:00:00Z",
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"Mission context analysis failed: {e}")
            return {
                "mission_id": context.mission_id,
                "analysis": {
                    "error": str(e),
                    "feasibility": "unknown",
                    "confidence": 0.0
                },
                "timestamp": "2024-01-01T00:00:00Z",
                "model_used": self.model
            }
    
    async def plan_search_strategy(
        self, 
        context: MissionContext, 
        terrain_type: str = "mixed",
        urgency_level: str = "medium"
    ) -> SearchStrategy:
        """Generate optimal search strategy"""
        try:
            prompt = f"""
            Plan an optimal search strategy for this SAR mission:
            
            Mission Context:
            - Type: {context.mission_type}
            - Area: {context.search_area.get('size_km2', 'unknown')} km²
            - Available Drones: {len(context.available_drones)}
            - Time Limit: {context.time_constraints.get('remaining_minutes', 'unlimited')} minutes
            - Priority: {context.priority_level}/10
            
            Environmental Factors:
            - Terrain: {terrain_type}
            - Weather: {json.dumps(context.weather_conditions, indent=2)}
            - Urgency: {urgency_level}
            
            Provide a detailed search strategy including:
            1. Recommended search pattern (grid, spiral, sector, etc.)
            2. Estimated completion time
            3. Success probability (0-100%)
            4. Resource requirements
            5. Risk factors
            6. Alternative approaches
            
            Format as structured analysis with quantitative estimates.
            """
            
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=prompt,
                    system=self.system_prompts["search_strategist"]
                )
            
            strategy_text = response.get("response", "")
            
            # Parse strategy from response
            pattern_type = self._extract_pattern_type(strategy_text)
            estimated_time = self._extract_estimated_time(strategy_text)
            success_probability = self._extract_success_probability(strategy_text)
            
            return SearchStrategy(
                pattern_type=pattern_type,
                estimated_time=estimated_time,
                success_probability=success_probability,
                resource_requirements={"drones": len(context.available_drones)},
                risk_factors=self._extract_risk_factors(strategy_text),
                alternative_approaches=self._extract_alternatives(strategy_text)
            )
            
        except Exception as e:
            logger.error(f"Search strategy planning failed: {e}")
            return SearchStrategy(
                pattern_type="grid",
                estimated_time=60,
                success_probability=0.5,
                resource_requirements={"drones": 1},
                risk_factors=["unknown"],
                alternative_approaches=["manual search"]
            )
    
    async def assess_risks(self, context: MissionContext) -> RiskAssessment:
        """Assess mission risks and provide go/no-go recommendation"""
        try:
            prompt = f"""
            Assess the risks for this SAR mission:
            
            Mission Details:
            - Type: {context.mission_type}
            - Weather: {json.dumps(context.weather_conditions, indent=2)}
            - Available Resources: {len(context.available_drones)} drones
            - Time Constraints: {json.dumps(context.time_constraints, indent=2)}
            - Priority: {context.priority_level}/10
            
            Evaluate:
            1. Overall risk level (low/medium/high/critical)
            2. Go/No-Go recommendation
            3. Specific risk factors
            4. Mitigation strategies
            5. Confidence in assessment
            
            Consider weather, terrain, equipment, personnel safety, and mission urgency.
            """
            
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=prompt,
                    system=self.system_prompts["risk_assessor"]
                )
            
            assessment_text = response.get("response", "")
            
            # Parse risk assessment
            overall_risk = self._extract_risk_level(assessment_text)
            go_no_go = self._extract_go_no_go(assessment_text)
            risk_factors = self._extract_risk_factors(assessment_text)
            mitigation_strategies = self._extract_mitigation_strategies(assessment_text)
            
            return RiskAssessment(
                overall_risk=overall_risk,
                go_no_go=go_no_go,
                risk_factors=risk_factors,
                mitigation_strategies=mitigation_strategies,
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return RiskAssessment(
                overall_risk="high",
                go_no_go=False,
                risk_factors=[{"factor": "system_error", "severity": "high"}],
                mitigation_strategies=["manual assessment required"],
                confidence_score=0.0
            )
    
    async def make_tactical_decision(
        self, 
        decision_type: DecisionType,
        context: MissionContext,
        additional_info: Dict[str, Any] = None
    ) -> TacticalDecision:
        """Make tactical decisions based on current situation"""
        try:
            prompt = f"""
            Make a tactical decision for this SAR operation:
            
            Decision Type: {decision_type.value}
            Mission Context: {context.mission_id}
            Current Progress: {context.current_progress:.1%}
            
            Additional Information:
            {json.dumps(additional_info or {}, indent=2)}
            
            Provide:
            1. Clear recommendation
            2. Detailed reasoning
            3. Confidence level (0-100%)
            4. Alternative options
            5. Expected outcome
            
            Focus on immediate tactical needs and operational effectiveness.
            """
            
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=prompt,
                    system=self.system_prompts["tactical_advisor"]
                )
            
            decision_text = response.get("response", "")
            
            # Parse tactical decision
            recommendation = self._extract_recommendation(decision_text)
            reasoning = self._extract_reasoning(decision_text)
            confidence = self._extract_confidence(decision_text)
            
            return TacticalDecision(
                decision_type=decision_type,
                recommendation=recommendation,
                reasoning=reasoning,
                confidence=confidence,
                alternative_options=["manual override"],
                expected_outcome="improved mission effectiveness"
            )
            
        except Exception as e:
            logger.error(f"Tactical decision making failed: {e}")
            return TacticalDecision(
                decision_type=decision_type,
                recommendation="manual assessment required",
                reasoning=f"System error: {e}",
                confidence=0.0,
                alternative_options=["manual override"],
                expected_outcome="unknown"
            )
    
    # Helper methods for parsing AI responses
    def _extract_pattern_type(self, text: str) -> str:
        """Extract search pattern type from AI response"""
        text_lower = text.lower()
        if "spiral" in text_lower:
            return "spiral"
        elif "sector" in text_lower:
            return "sector"
        elif "grid" in text_lower:
            return "grid"
        elif "expanding" in text_lower:
            return "expanding_square"
        else:
            return "grid"
    
    def _extract_estimated_time(self, text: str) -> int:
        """Extract estimated time from AI response"""
        import re
        time_match = re.search(r'(\d+)\s*(?:minutes?|mins?|hours?)', text.lower())
        if time_match:
            time_val = int(time_match.group(1))
            if "hour" in text.lower():
                return time_val * 60
            return time_val
        return 60  # default
    
    def _extract_success_probability(self, text: str) -> float:
        """Extract success probability from AI response"""
        import re
        prob_match = re.search(r'(\d+(?:\.\d+)?)%', text)
        if prob_match:
            return float(prob_match.group(1)) / 100.0
        return 0.7  # default
    
    def _extract_risk_factors(self, text: str) -> List[str]:
        """Extract risk factors from AI response"""
        factors = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['risk', 'danger', 'hazard', 'threat']):
                factors.append(line.strip())
        return factors[:5] if factors else ["unknown risks"]
    
    def _extract_alternatives(self, text: str) -> List[str]:
        """Extract alternative approaches from AI response"""
        alternatives = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['alternative', 'option', 'backup']):
                alternatives.append(line.strip())
        return alternatives[:3] if alternatives else ["manual approach"]
    
    def _extract_risk_level(self, text: str) -> str:
        """Extract overall risk level from AI response"""
        text_lower = text.lower()
        if "critical" in text_lower:
            return "critical"
        elif "high" in text_lower:
            return "high"
        elif "medium" in text_lower:
            return "medium"
        else:
            return "low"
    
    def _extract_go_no_go(self, text: str) -> bool:
        """Extract go/no-go recommendation from AI response"""
        text_lower = text.lower()
        return "go" in text_lower and "no-go" not in text_lower
    
    def _extract_mitigation_strategies(self, text: str) -> List[str]:
        """Extract mitigation strategies from AI response"""
        strategies = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['mitigate', 'reduce', 'prevent', 'minimize']):
                strategies.append(line.strip())
        return strategies[:3] if strategies else ["manual assessment"]
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from AI response"""
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'advise']):
                return line.strip()
        return "Manual assessment required"
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning from AI response"""
        lines = text.split('\n')
        reasoning_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['because', 'due to', 'reason', 'rationale']):
                reasoning_lines.append(line.strip())
        return ' '.join(reasoning_lines) if reasoning_lines else "Analysis in progress"
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from AI response"""
        import re
        conf_match = re.search(r'confidence[:\s]*(\d+(?:\.\d+)?)%?', text.lower())
        if conf_match:
            return float(conf_match.group(1)) / 100.0
        return 0.7  # default


async def create_ollama_intelligence_engine() -> OllamaIntelligenceEngine:
    """Create and initialize Ollama intelligence engine"""
    client = OllamaClient()
    return OllamaIntelligenceEngine(client=client)