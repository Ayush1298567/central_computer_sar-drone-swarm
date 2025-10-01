"""
Legacy LLM Intelligence Engine - Now uses Ollama exclusively
"""
import logging
from typing import Dict, List, Optional, Any
from .ollama_intelligence import OllamaIntelligenceEngine, MissionContext, create_ollama_intelligence_engine

logger = logging.getLogger(__name__)


class LLMIntelligenceEngine:
    """
    Legacy wrapper for LLM Intelligence Engine
    Now uses Ollama exclusively for all AI operations
    """
    
    def __init__(self):
        self.ollama_engine: Optional[OllamaIntelligenceEngine] = None
        logger.info("LLM Intelligence Engine initialized (Ollama-only mode)")
    
    async def _get_engine(self) -> OllamaIntelligenceEngine:
        """Get or create Ollama intelligence engine"""
        if not self.ollama_engine:
            self.ollama_engine = await create_ollama_intelligence_engine()
        return self.ollama_engine
    
    async def analyze_mission_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mission context using Ollama"""
        try:
            engine = await self._get_engine()
            
            # Convert context data to MissionContext
            context = MissionContext(
                mission_id=context_data.get("mission_id", "unknown"),
                mission_type=context_data.get("mission_type", "missing_person"),
                search_area=context_data.get("search_area", {}),
                weather_conditions=context_data.get("weather_conditions", {}),
                available_drones=context_data.get("available_drones", []),
                time_constraints=context_data.get("time_constraints", {}),
                priority_level=context_data.get("priority_level", 5),
                discovered_objects=context_data.get("discovered_objects", []),
                current_progress=context_data.get("current_progress", 0.0)
            )
            
            return await engine.analyze_mission_context(context)
            
        except Exception as e:
            logger.error(f"Mission context analysis failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def plan_search_strategy(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan search strategy using Ollama"""
        try:
            engine = await self._get_engine()
            
            # Convert context data to MissionContext
            context = MissionContext(
                mission_id=context_data.get("mission_id", "unknown"),
                mission_type=context_data.get("mission_type", "missing_person"),
                search_area=context_data.get("search_area", {}),
                weather_conditions=context_data.get("weather_conditions", {}),
                available_drones=context_data.get("available_drones", []),
                time_constraints=context_data.get("time_constraints", {}),
                priority_level=context_data.get("priority_level", 5),
                discovered_objects=context_data.get("discovered_objects", []),
                current_progress=context_data.get("current_progress", 0.0)
            )
            
            terrain_type = context_data.get("terrain_type", "mixed")
            urgency_level = context_data.get("urgency_level", "medium")
            
            strategy = await engine.plan_search_strategy(context, terrain_type, urgency_level)
            
            return {
                "pattern_type": strategy.pattern_type,
                "estimated_time": strategy.estimated_time,
                "success_probability": strategy.success_probability,
                "resource_requirements": strategy.resource_requirements,
                "risk_factors": strategy.risk_factors,
                "alternative_approaches": strategy.alternative_approaches
            }
            
        except Exception as e:
            logger.error(f"Search strategy planning failed: {e}")
            return {
                "error": str(e),
                "pattern_type": "grid",
                "estimated_time": 60,
                "success_probability": 0.5
            }
    
    async def assess_risks(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess mission risks using Ollama"""
        try:
            engine = await self._get_engine()
            
            # Convert context data to MissionContext
            context = MissionContext(
                mission_id=context_data.get("mission_id", "unknown"),
                mission_type=context_data.get("mission_type", "missing_person"),
                search_area=context_data.get("search_area", {}),
                weather_conditions=context_data.get("weather_conditions", {}),
                available_drones=context_data.get("available_drones", []),
                time_constraints=context_data.get("time_constraints", {}),
                priority_level=context_data.get("priority_level", 5),
                discovered_objects=context_data.get("discovered_objects", []),
                current_progress=context_data.get("current_progress", 0.0)
            )
            
            risk_assessment = await engine.assess_risks(context)
            
            return {
                "overall_risk": risk_assessment.overall_risk,
                "go_no_go": risk_assessment.go_no_go,
                "risk_factors": risk_assessment.risk_factors,
                "mitigation_strategies": risk_assessment.mitigation_strategies,
                "confidence_score": risk_assessment.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {
                "error": str(e),
                "overall_risk": "high",
                "go_no_go": False,
                "confidence_score": 0.0
            }
    
    async def make_tactical_decision(
        self, 
        decision_type: str, 
        context_data: Dict[str, Any],
        additional_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make tactical decisions using Ollama"""
        try:
            engine = await self._get_engine()
            
            # Convert decision type
            from .ollama_intelligence import DecisionType
            decision_type_enum = DecisionType(decision_type)
            
            # Convert context data to MissionContext
            context = MissionContext(
                mission_id=context_data.get("mission_id", "unknown"),
                mission_type=context_data.get("mission_type", "missing_person"),
                search_area=context_data.get("search_area", {}),
                weather_conditions=context_data.get("weather_conditions", {}),
                available_drones=context_data.get("available_drones", []),
                time_constraints=context_data.get("time_constraints", {}),
                priority_level=context_data.get("priority_level", 5),
                discovered_objects=context_data.get("discovered_objects", []),
                current_progress=context_data.get("current_progress", 0.0)
            )
            
            decision = await engine.make_tactical_decision(
                decision_type_enum, 
                context, 
                additional_info
            )
            
            return {
                "decision_type": decision.decision_type.value,
                "recommendation": decision.recommendation,
                "reasoning": decision.reasoning,
                "confidence": decision.confidence,
                "alternative_options": decision.alternative_options,
                "expected_outcome": decision.expected_outcome
            }
            
        except Exception as e:
            logger.error(f"Tactical decision making failed: {e}")
            return {
                "error": str(e),
                "decision_type": decision_type,
                "recommendation": "manual assessment required",
                "confidence": 0.0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check AI engine health"""
        try:
            engine = await self._get_engine()
            
            # Test basic functionality
            test_context = MissionContext(
                mission_id="health_check",
                mission_type="missing_person",
                search_area={"size_km2": 1.0},
                weather_conditions={"wind_speed": 10},
                available_drones=[{"id": "test-drone"}],
                time_constraints={"remaining_minutes": 60},
                priority_level=5,
                discovered_objects=[],
                current_progress=0.0
            )
            
            # Quick analysis test
            analysis = await engine.analyze_mission_context(test_context)
            
            return {
                "status": "healthy",
                "engine": "ollama",
                "test_analysis": analysis.get("analysis", {}),
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"AI engine health check failed: {e}")
            return {
                "status": "unhealthy",
                "engine": "ollama",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }


# Global instance for backward compatibility
llm_intelligence = LLMIntelligenceEngine()