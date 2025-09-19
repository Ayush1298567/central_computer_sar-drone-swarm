"""
AI Mission Planner API endpoints for conversational mission planning.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json
from datetime import datetime

from ..core.database import get_db
from ..ai.conversation import ConversationalMissionPlanner
from ..ai.ollama_client import OllamaClient
from ..ai.learning import LearningSystem

router = APIRouter()

# Initialize AI services
ollama_client = OllamaClient()
mission_planner = ConversationalMissionPlanner(ollama_client)
learning_system = LearningSystem(ollama_client)

@router.post("/start-conversation", response_model=Dict[str, Any])
async def start_mission_conversation(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Start a new AI-driven mission planning conversation."""
    try:
        client_id = request_data.get("client_id")
        initial_message = request_data.get("initial_message", "")
        
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        
        # Start conversation with AI planner
        response = await mission_planner.start_conversation(client_id, initial_message)
        
        return {
            "success": True,
            "client_id": client_id,
            "ai_response": response,
            "conversation_status": mission_planner.get_conversation_status(client_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/process-message", response_model=Dict[str, Any])
async def process_conversation_message(
    message_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Process a message in an ongoing conversation."""
    try:
        client_id = message_data.get("client_id")
        message = message_data.get("message")
        
        if not client_id or not message:
            raise HTTPException(status_code=400, detail="client_id and message are required")
        
        # Process message through AI planner
        response = await mission_planner.process_message(message, client_id)
        
        return {
            "success": True,
            "client_id": client_id,
            "ai_response": response,
            "conversation_status": mission_planner.get_conversation_status(client_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/conversation-status/{client_id}", response_model=Dict[str, Any])
async def get_conversation_status(client_id: str):
    """Get the current status of a conversation."""
    try:
        status = mission_planner.get_conversation_status(client_id)
        if not status:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation status: {str(e)}")

@router.post("/analyze-mission", response_model=Dict[str, Any])
async def analyze_mission_context(
    analysis_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Analyze mission context and provide AI insights."""
    try:
        mission_data = analysis_request.get("mission_data", {})
        context_type = analysis_request.get("context_type", "planning")
        
        # Analyze through Ollama client
        analysis = await ollama_client.analyze_mission_context(mission_data, context_type)
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze mission: {str(e)}")

@router.post("/generate-questions", response_model=Dict[str, Any])
async def generate_clarifying_questions(
    question_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate clarifying questions for mission planning."""
    try:
        conversation_history = question_request.get("conversation_history", [])
        mission_state = question_request.get("mission_state", {})
        
        # Generate questions through Ollama client
        questions = await ollama_client.generate_clarifying_questions(
            conversation_history, mission_state
        )
        
        return {
            "success": True,
            "questions": questions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

@router.post("/autonomous-decision", response_model=Dict[str, Any])
async def make_autonomous_decision(
    decision_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Make an autonomous decision based on mission situation."""
    try:
        mission_id = decision_request.get("mission_id")
        situation_data = decision_request.get("situation_data", {})
        decision_context = decision_request.get("decision_context", "mission_execution")
        
        if not mission_id:
            raise HTTPException(status_code=400, detail="mission_id is required")
        
        # Make decision through mission planner
        decision = await mission_planner.make_autonomous_decision(mission_id, situation_data)
        
        return {
            "success": True,
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to make autonomous decision: {str(e)}")

@router.post("/learn-from-mission", response_model=Dict[str, Any])
async def learn_from_mission_outcome(
    learning_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Record mission outcome for AI learning."""
    try:
        mission_id = learning_data.get("mission_id")
        mission_parameters = learning_data.get("mission_parameters", {})
        outcome_data = learning_data.get("outcome_data", {})
        performance_metrics = learning_data.get("performance_metrics", {})
        
        if not mission_id:
            raise HTTPException(status_code=400, detail="mission_id is required")
        
        # Record learning through learning system
        success = await learning_system.record_mission_outcome(
            mission_id, mission_parameters, outcome_data, performance_metrics
        )
        
        return {
            "success": success,
            "message": "Mission outcome recorded for learning" if success else "Failed to record learning",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record learning: {str(e)}")

@router.post("/get-recommendations", response_model=Dict[str, Any])
async def get_mission_recommendations(
    recommendation_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI recommendations for mission parameters based on learning."""
    try:
        proposed_parameters = recommendation_request.get("proposed_parameters", {})
        
        # Get recommendations through learning system
        recommendations = await learning_system.get_mission_recommendations(proposed_parameters)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.post("/adapt-to-conditions", response_model=Dict[str, Any])
async def adapt_to_current_conditions(
    adaptation_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Adapt mission parameters based on current conditions and learning."""
    try:
        current_conditions = adaptation_request.get("current_conditions", {})
        mission_parameters = adaptation_request.get("mission_parameters", {})
        
        # Get adaptations through learning system
        adaptations = await learning_system.adapt_to_conditions(
            current_conditions, mission_parameters
        )
        
        return {
            "success": True,
            "adaptations": adaptations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to adapt to conditions: {str(e)}")

@router.get("/learning-statistics", response_model=Dict[str, Any])
async def get_learning_statistics(db: Session = Depends(get_db)):
    """Get AI learning system statistics."""
    try:
        statistics = learning_system.get_learning_statistics()
        
        return {
            "success": True,
            "statistics": statistics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning statistics: {str(e)}")

@router.get("/ai-status", response_model=Dict[str, Any])
async def get_ai_system_status():
    """Get the status of AI services."""
    try:
        ollama_status = await ollama_client.get_status()
        
        return {
            "success": True,
            "ai_services": {
                "ollama": ollama_status,
                "conversation_planner": {
                    "active_conversations": len(mission_planner.active_conversations),
                    "status": "operational"
                },
                "learning_system": {
                    "total_entries": len(learning_system.learning_entries),
                    "status": "operational"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI status: {str(e)}")

@router.post("/cleanup-conversations", response_model=Dict[str, Any])
async def cleanup_inactive_conversations(
    cleanup_request: Optional[Dict[str, Any]] = None
):
    """Clean up inactive conversations."""
    try:
        max_age_hours = cleanup_request.get("max_age_hours", 2) if cleanup_request else 2
        
        cleaned_count = mission_planner.cleanup_inactive_conversations(max_age_hours)
        
        return {
            "success": True,
            "cleaned_conversations": cleaned_count,
            "message": f"Cleaned up {cleaned_count} inactive conversations",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup conversations: {str(e)}")

@router.websocket("/conversation-ws/{client_id}")
async def conversation_websocket(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time conversation with AI planner."""
    await websocket.accept()
    
    try:
        # Send welcome message
        welcome_response = await mission_planner.start_conversation(client_id, "")
        await websocket.send_text(json.dumps({
            "type": "ai_response",
            "content": welcome_response,
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            
            # Process through AI planner
            ai_response = await mission_planner.process_message(user_message, client_id)
            conversation_status = mission_planner.get_conversation_status(client_id)
            
            # Send response back
            response = {
                "type": "ai_response",
                "content": ai_response,
                "conversation_status": conversation_status,
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected from conversation WebSocket")
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Conversation error: {str(e)}",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
        except:
            pass  # Connection likely closed