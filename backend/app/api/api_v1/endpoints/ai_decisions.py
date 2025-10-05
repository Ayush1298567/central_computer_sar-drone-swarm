"""
API endpoints for AI decision management and approval workflow
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

from app.ai.ai_decision_integration import (
    ai_decision_integration,
    DecisionType,
    DecisionStatus,
    IntegratedAIDecision,
    DecisionApprovalRequest
)
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/decisions/make")
async def make_ai_decision(
    decision_type: str,
    context_data: Dict[str, Any],
    mission_id: str,
    current_user: User = Depends(get_current_user)
):
    """Make an intelligent AI decision"""
    try:
        # Validate decision type
        try:
            decision_type_enum = DecisionType(decision_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid decision type: {decision_type}")
        
        # Make decision
        decision = await ai_decision_integration.make_intelligent_decision(
            decision_type=decision_type_enum,
            context_data=context_data,
            mission_id=mission_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "decision": {
                "decision_id": decision.decision_id,
                "decision_type": decision.decision_type.value,
                "status": decision.status.value,
                "confidence_score": decision.confidence_score,
                "authority_level": decision.authority_level.value,
                "human_approval_required": decision.human_approval_required,
                "recommendation": decision.recommendation,
                "reasoning_chain": decision.reasoning_chain,
                "risk_assessment": decision.risk_assessment,
                "expected_impact": decision.expected_impact,
                "created_at": decision.created_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to make AI decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions/pending")
async def get_pending_decisions(
    current_user: User = Depends(get_current_user)
):
    """Get all pending AI decisions"""
    try:
        decisions = await ai_decision_integration.get_pending_decisions()
        
        return {
            "success": True,
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type.value,
                    "status": d.status.value,
                    "confidence_score": d.confidence_score,
                    "authority_level": d.authority_level.value,
                    "human_approval_required": d.human_approval_required,
                    "recommendation": d.recommendation,
                    "reasoning_chain": d.reasoning_chain,
                    "risk_assessment": d.risk_assessment,
                    "expected_impact": d.expected_impact,
                    "created_at": d.created_at.isoformat()
                }
                for d in decisions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions/approval-requests")
async def get_approval_requests(
    current_user: User = Depends(get_current_user)
):
    """Get all pending approval requests"""
    try:
        requests = await ai_decision_integration.get_approval_requests()
        
        return {
            "success": True,
            "approval_requests": [
                {
                    "decision_id": r.decision_id,
                    "decision_type": r.decision_type,
                    "confidence_score": r.confidence_score,
                    "recommendation": r.recommendation,
                    "reasoning": r.reasoning,
                    "risk_assessment": r.risk_assessment,
                    "expected_impact": r.expected_impact,
                    "alternatives": r.alternatives,
                    "urgency_level": r.urgency_level,
                    "created_at": r.created_at.isoformat(),
                    "expires_at": r.expires_at.isoformat()
                }
                for r in requests
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get approval requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decisions/{decision_id}/approve")
async def approve_decision(
    decision_id: str,
    approval: bool,
    override_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Approve or reject an AI decision"""
    try:
        success = await ai_decision_integration.approve_decision(
            decision_id=decision_id,
            user_id=current_user.id,
            approval=approval,
            override_reason=override_reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        return {
            "success": True,
            "message": f"Decision {'approved' if approval else 'rejected'} successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to approve decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions/history")
async def get_decision_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get AI decision history"""
    try:
        history = await ai_decision_integration.get_decision_history(limit=limit)
        
        return {
            "success": True,
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type.value,
                    "status": d.status.value,
                    "confidence_score": d.confidence_score,
                    "authority_level": d.authority_level.value,
                    "recommendation": d.recommendation,
                    "created_at": d.created_at.isoformat(),
                    "approved_at": d.approved_at.isoformat() if d.approved_at else None,
                    "approved_by": d.approved_by,
                    "execution_result": d.execution_result
                }
                for d in history
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get decision history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions/performance")
async def get_ai_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get AI performance metrics"""
    try:
        metrics = await ai_decision_integration.get_ai_performance_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/decisions/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI decision updates"""
    await websocket.accept()
    
    # Add connection to integration layer
    ai_decision_integration.add_websocket_connection(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "subscribe":
                # Client wants to subscribe to updates
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "message": "Subscribed to AI decision updates"
                }))
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove connection from integration layer
        ai_decision_integration.remove_websocket_connection(websocket)

@router.post("/decisions/analyze-context")
async def analyze_mission_context(
    context_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Analyze mission context for AI decision making"""
    try:
        # This would use the LLM intelligence to analyze context
        from app.ai.llm_intelligence import llm_intelligence
        
        analysis = await llm_intelligence.generate_mission_plan(
            context_data, 
            "Analyze this mission context and provide insights for decision making"
        )
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decisions/simulate")
async def simulate_decision_outcome(
    decision_type: str,
    context_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Simulate the outcome of a decision before making it"""
    try:
        # This would use the ML models to predict outcomes
        from app.ai.real_ml_models import RealMLModels
        from app.ai.real_ml_models import MissionFeatures, MissionType, TerrainType, WeatherCondition
        
        ml_models = RealMLModels()
        await ml_models.initialize()
        
        # Create mission features for prediction
        mission_features = MissionFeatures(
            mission_type=context_data.get('mission_type', 'search'),
            terrain_type=context_data.get('terrain_type', 'rural'),
            weather_condition=WeatherCondition.CLEAR,
            area_size=context_data.get('area_size', 1.0),
            duration_hours=context_data.get('duration_hours', 2.0),
            num_drones=context_data.get('num_drones', 1),
            target_urgency=context_data.get('urgency_level', 'medium'),
            time_of_day=12,
            season=1,
            wind_speed=context_data.get('wind_speed', 0),
            visibility=context_data.get('visibility', 10000),
            temperature=context_data.get('temperature', 25),
            humidity=context_data.get('humidity', 50),
            battery_reserve=80,
            communication_range=10,
            search_density="medium",
            search_pattern="grid",
            altitude=50,
            speed=5
        )
        
        prediction = await ml_models.predict_mission_outcome(mission_features)
        
        return {
            "success": True,
            "simulation": {
                "success_rate": prediction.success_rate,
                "estimated_duration": prediction.estimated_duration,
                "confidence": prediction.confidence,
                "risk_factors": prediction.risk_factors,
                "recommendations": prediction.recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))