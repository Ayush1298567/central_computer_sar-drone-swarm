"""
AI Governance System for SAR Drone Swarm
Implements decision authority, confidence tracking, and safety protocols
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

class DecisionAuthority(Enum):
    """AI decision authority levels"""
    FULL_AUTO = "full_auto"           # No human approval needed
    RECOMMEND = "recommend"           # Human approval required
    ADVISORY_ONLY = "advisory_only"   # Human decision only

class ConfidenceLevel(Enum):
    """AI confidence levels"""
    VERY_HIGH = "very_high"    # 0.9-1.0
    HIGH = "high"              # 0.7-0.9
    MEDIUM = "medium"          # 0.5-0.7
    LOW = "low"                # 0.3-0.5
    VERY_LOW = "very_low"      # 0.0-0.3

@dataclass
class AIDecision:
    """AI decision record"""
    timestamp: datetime
    component: str
    decision_type: str
    confidence_score: float
    authority_level: DecisionAuthority
    input_data: Dict[str, Any]
    recommendation: str
    human_approval_required: bool
    human_action: Optional[str] = None
    human_override_reason: Optional[str] = None
    execution_result: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class AIGovernance:
    """AI governance and decision tracking system"""
    
    def __init__(self):
        self.decision_log: List[AIDecision] = []
        self.confidence_thresholds = {
            "mission_planning": 0.7,
            "detection_analysis": 0.8,
            "resource_allocation": 0.6,
            "emergency_stop": 0.9,
            "search_expansion": 0.5
        }
        self.authority_matrix = {
            "battery_management": DecisionAuthority.FULL_AUTO,
            "collision_avoidance": DecisionAuthority.FULL_AUTO,
            "weather_emergency": DecisionAuthority.FULL_AUTO,
            "mission_planning": DecisionAuthority.RECOMMEND,
            "detection_analysis": DecisionAuthority.RECOMMEND,
            "resource_allocation": DecisionAuthority.RECOMMEND,
            "emergency_stop": DecisionAuthority.RECOMMEND,
            "mission_abort": DecisionAuthority.ADVISORY_ONLY,
            "search_expansion": DecisionAuthority.ADVISORY_ONLY
        }
    
    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert confidence score to level"""
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def requires_human_approval(self, decision_type: str, confidence: float) -> bool:
        """Determine if human approval is required"""
        authority = self.authority_matrix.get(decision_type, DecisionAuthority.ADVISORY_ONLY)
        
        if authority == DecisionAuthority.FULL_AUTO:
            return False
        elif authority == DecisionAuthority.ADVISORY_ONLY:
            return True
        else:  # RECOMMEND
            threshold = self.confidence_thresholds.get(decision_type, 0.5)
            return confidence < threshold
    
    def log_decision(self, decision: AIDecision) -> None:
        """Log AI decision for audit trail"""
        self.decision_log.append(decision)
        
        # Log to system logger
        logger.info(f"AI Decision: {decision.component}.{decision.decision_type} "
                   f"(confidence: {decision.confidence_score:.2f}, "
                   f"authority: {decision.authority_level.value})")
        
        # Log to file for audit trail
        self._write_decision_log(decision)
    
    def _write_decision_log(self, decision: AIDecision) -> None:
        """Write decision to audit log file"""
        try:
            log_entry = {
                "timestamp": decision.timestamp.isoformat(),
                "component": decision.component,
                "decision_type": decision.decision_type,
                "confidence_score": decision.confidence_score,
                "authority_level": decision.authority_level.value,
                "input_data": decision.input_data,
                "recommendation": decision.recommendation,
                "human_approval_required": decision.human_approval_required,
                "human_action": decision.human_action,
                "human_override_reason": decision.human_override_reason,
                "execution_result": decision.execution_result,
                "performance_metrics": decision.performance_metrics
            }
            
            with open("logs/ai_decisions.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write AI decision log: {e}")
    
    def get_decision_history(self, component: str = None, limit: int = 100) -> List[AIDecision]:
        """Get decision history with optional filtering"""
        history = self.decision_log
        
        if component:
            history = [d for d in history if d.component == component]
        
        return history[-limit:] if limit else history
    
    def get_performance_metrics(self, component: str = None) -> Dict[str, Any]:
        """Calculate AI performance metrics"""
        history = self.get_decision_history(component)
        
        if not history:
            return {"total_decisions": 0}
        
        total_decisions = len(history)
        human_overrides = len([d for d in history if d.human_override_reason])
        avg_confidence = sum(d.confidence_score for d in history) / total_decisions
        
        return {
            "total_decisions": total_decisions,
            "human_override_rate": human_overrides / total_decisions,
            "average_confidence": avg_confidence,
            "decisions_by_component": self._group_by_component(history),
            "decisions_by_confidence": self._group_by_confidence(history)
        }
    
    def _group_by_component(self, history: List[AIDecision]) -> Dict[str, int]:
        """Group decisions by component"""
        components = {}
        for decision in history:
            components[decision.component] = components.get(decision.component, 0) + 1
        return components
    
    def _group_by_confidence(self, history: List[AIDecision]) -> Dict[str, int]:
        """Group decisions by confidence level"""
        confidence_levels = {}
        for decision in history:
            level = self.get_confidence_level(decision.confidence_score)
            confidence_levels[level.value] = confidence_levels.get(level.value, 0) + 1
        return confidence_levels

# Global AI governance instance
ai_governance = AIGovernance()

def create_ai_decision(
    component: str,
    decision_type: str,
    confidence_score: float,
    input_data: Dict[str, Any],
    recommendation: str
) -> AIDecision:
    """Create and log an AI decision"""
    
    authority_level = ai_governance.authority_matrix.get(decision_type, DecisionAuthority.ADVISORY_ONLY)
    human_approval_required = ai_governance.requires_human_approval(decision_type, confidence_score)
    
    decision = AIDecision(
        timestamp=datetime.utcnow(),
        component=component,
        decision_type=decision_type,
        confidence_score=confidence_score,
        authority_level=authority_level,
        input_data=input_data,
        recommendation=recommendation,
        human_approval_required=human_approval_required
    )
    
    ai_governance.log_decision(decision)
    return decision

def record_human_action(decision: AIDecision, action: str, override_reason: str = None) -> None:
    """Record human action on AI decision"""
    decision.human_action = action
    decision.human_override_reason = override_reason
    
    logger.info(f"Human action on AI decision: {action} "
               f"(override reason: {override_reason or 'none'})")

def record_execution_result(decision: AIDecision, result: str, metrics: Dict[str, Any] = None) -> None:
    """Record execution result of AI decision"""
    decision.execution_result = result
    decision.performance_metrics = metrics
    
    logger.info(f"AI decision execution result: {result}")

# AI Safety Protocols
class AISafetyProtocols:
    """AI safety protocol enforcement"""
    
    @staticmethod
    def check_emergency_conditions(system_state: Dict[str, Any]) -> List[str]:
        """Check for emergency conditions requiring immediate action"""
        emergencies = []
        
        # Battery critical
        if system_state.get("battery_level", 100) < 10:
            emergencies.append("BATTERY_CRITICAL")
        
        # Weather emergency
        if system_state.get("wind_speed", 0) > 25:
            emergencies.append("WEATHER_EMERGENCY")
        
        # Communication loss
        if system_state.get("communication_lost", False):
            emergencies.append("COMMUNICATION_LOSS")
        
        # Collision risk
        if system_state.get("collision_risk", False):
            emergencies.append("COLLISION_RISK")
        
        return emergencies
    
    @staticmethod
    def enforce_safety_limits(decision: AIDecision) -> bool:
        """Enforce AI safety limits"""
        # Never allow AI to make final mission abort decisions
        if decision.decision_type == "mission_abort":
            return False
        
        # Never allow AI to override human emergency commands
        if decision.human_override_reason and "emergency" in decision.human_override_reason.lower():
            return False
        
        # Never allow AI to operate outside defined parameters
        if decision.confidence_score < 0.1:
            return False
        
        return True

# AI Performance Monitoring
class AIPerformanceMonitor:
    """Monitor AI performance and provide metrics"""
    
    def __init__(self):
        self.metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "human_overrides": 0,
            "average_confidence": 0.0,
            "response_times": [],
            "error_count": 0
        }
    
    def record_decision_outcome(self, decision: AIDecision, success: bool, response_time: float) -> None:
        """Record decision outcome for performance tracking"""
        self.metrics["total_decisions"] += 1
        
        if success:
            self.metrics["successful_decisions"] += 1
        else:
            self.metrics["error_count"] += 1
        
        if decision.human_override_reason:
            self.metrics["human_overrides"] += 1
        
        # Update average confidence
        total = self.metrics["total_decisions"]
        current_avg = self.metrics["average_confidence"]
        self.metrics["average_confidence"] = ((current_avg * (total - 1)) + decision.confidence_score) / total
        
        # Track response times
        self.metrics["response_times"].append(response_time)
        if len(self.metrics["response_times"]) > 1000:  # Keep last 1000
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        total = self.metrics["total_decisions"]
        if total == 0:
            return {"status": "no_data"}
        
        success_rate = self.metrics["successful_decisions"] / total
        override_rate = self.metrics["human_overrides"] / total
        avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"]) if self.metrics["response_times"] else 0
        
        return {
            "total_decisions": total,
            "success_rate": success_rate,
            "human_override_rate": override_rate,
            "average_confidence": self.metrics["average_confidence"],
            "average_response_time": avg_response_time,
            "error_rate": self.metrics["error_count"] / total,
            "status": "operational" if success_rate > 0.9 else "degraded"
        }

# Global instances
ai_safety = AISafetyProtocols()
ai_performance = AIPerformanceMonitor()
