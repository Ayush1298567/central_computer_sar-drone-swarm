"""
AI Governance API endpoints
Provides access to AI decision tracking, performance metrics, and governance controls
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from app.api.api_v1.dependencies import get_db
from app.ai.ai_governance import (
    ai_governance, ai_safety, ai_performance,
    create_ai_decision, record_human_action, record_execution_result,
    DecisionAuthority, ConfidenceLevel
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/decisions")
def get_ai_decisions(
    component: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI decision history"""
    try:
        decisions = ai_governance.get_decision_history(component, limit)
        
        return {
            "decisions": [
                {
                    "timestamp": decision.timestamp.isoformat(),
                    "component": decision.component,
                    "decision_type": decision.decision_type,
                    "confidence_score": decision.confidence_score,
                    "authority_level": decision.authority_level.value,
                    "recommendation": decision.recommendation,
                    "human_approval_required": decision.human_approval_required,
                    "human_action": decision.human_action,
                    "human_override_reason": decision.human_override_reason,
                    "execution_result": decision.execution_result
                }
                for decision in decisions
            ],
            "total_count": len(decisions),
            "component_filter": component
        }
    except Exception as e:
        logger.error(f"Error fetching AI decisions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/performance")
def get_ai_performance(
    component: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI performance metrics"""
    try:
        governance_metrics = ai_governance.get_performance_metrics(component)
        performance_summary = ai_performance.get_performance_summary()
        
        return {
            "governance_metrics": governance_metrics,
            "performance_summary": performance_summary,
            "component_filter": component,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching AI performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/decisions")
def create_decision(
    decision_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new AI decision record"""
    try:
        decision = create_ai_decision(
            component=decision_data["component"],
            decision_type=decision_data["decision_type"],
            confidence_score=decision_data["confidence_score"],
            input_data=decision_data["input_data"],
            recommendation=decision_data["recommendation"]
        )
        
        return {
            "decision_id": len(ai_governance.decision_log) - 1,
            "timestamp": decision.timestamp.isoformat(),
            "human_approval_required": decision.human_approval_required,
            "authority_level": decision.authority_level.value,
            "message": "AI decision recorded successfully"
        }
    except Exception as e:
        logger.error(f"Error creating AI decision: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/decisions/{decision_id}/human-action")
def record_human_decision(
    decision_id: int,
    action_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Record human action on AI decision"""
    try:
        if decision_id >= len(ai_governance.decision_log):
            raise HTTPException(status_code=404, detail="Decision not found")
        
        decision = ai_governance.decision_log[decision_id]
        
        record_human_action(
            decision=decision,
            action=action_data["action"],
            override_reason=action_data.get("override_reason")
        )
        
        return {
            "decision_id": decision_id,
            "human_action": action_data["action"],
            "override_reason": action_data.get("override_reason"),
            "message": "Human action recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording human action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/decisions/{decision_id}/execution-result")
def record_execution_result(
    decision_id: int,
    result_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Record execution result of AI decision"""
    try:
        if decision_id >= len(ai_governance.decision_log):
            raise HTTPException(status_code=404, detail="Decision not found")
        
        decision = ai_governance.decision_log[decision_id]
        
        record_execution_result(
            decision=decision,
            result=result_data["result"],
            metrics=result_data.get("metrics")
        )
        
        return {
            "decision_id": decision_id,
            "execution_result": result_data["result"],
            "message": "Execution result recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording execution result: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/safety-check")
def check_safety_conditions(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check current safety conditions"""
    try:
        # Get current system state (this would come from actual system monitoring)
        system_state = {
            "battery_level": 85,  # This would be real data
            "wind_speed": 15,
            "communication_lost": False,
            "collision_risk": False
        }
        
        emergencies = ai_safety.check_emergency_conditions(system_state)
        
        return {
            "system_state": system_state,
            "emergency_conditions": emergencies,
            "safety_status": "SAFE" if not emergencies else "EMERGENCY",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking safety conditions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/confidence-calibration")
def get_confidence_calibration(
    component: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI confidence calibration data"""
    try:
        decisions = ai_governance.get_decision_history(component)
        
        if not decisions:
            return {"message": "No decisions found for calibration"}
        
        # Group by confidence levels
        confidence_groups = {
            "very_high": [],
            "high": [],
            "medium": [],
            "low": [],
            "very_low": []
        }
        
        for decision in decisions:
            level = ai_governance.get_confidence_level(decision.confidence_score)
            confidence_groups[level.value].append(decision)
        
        # Calculate calibration metrics
        calibration_data = {}
        for level, group in confidence_groups.items():
            if group:
                avg_confidence = sum(d.confidence_score for d in group) / len(group)
                human_override_rate = len([d for d in group if d.human_override_reason]) / len(group)
                
                calibration_data[level] = {
                    "count": len(group),
                    "average_confidence": avg_confidence,
                    "human_override_rate": human_override_rate
                }
        
        return {
            "calibration_data": calibration_data,
            "total_decisions": len(decisions),
            "component_filter": component,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting confidence calibration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/authority-matrix")
def get_authority_matrix(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI decision authority matrix"""
    try:
        return {
            "authority_matrix": {
                decision_type: authority.value
                for decision_type, authority in ai_governance.authority_matrix.items()
            },
            "confidence_thresholds": ai_governance.confidence_thresholds,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting authority matrix: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/emergency-override")
def emergency_override(
    override_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Emergency override of AI decision"""
    try:
        decision_id = override_data.get("decision_id")
        reason = override_data.get("reason", "Emergency override")
        
        if decision_id is not None and decision_id < len(ai_governance.decision_log):
            decision = ai_governance.decision_log[decision_id]
            record_human_action(decision, "EMERGENCY_OVERRIDE", reason)
        
        # Log emergency override
        logger.critical(f"🚨 EMERGENCY AI OVERRIDE: {reason}")
        
        return {
            "status": "EMERGENCY_OVERRIDE_ACTIVATED",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Emergency override activated - AI decision overridden"
        }
    except Exception as e:
        logger.error(f"Error processing emergency override: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
