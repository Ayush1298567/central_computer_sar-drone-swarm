"""
Chat and conversational AI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ....core.database import get_db
from ....ai import create_mission_planner, create_ollama_intelligence_engine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    mission_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    suggestions: Optional[List[str]] = None

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessage,
    db: Session = Depends(get_db)
):
    """Send message to conversational AI"""
    try:
        # Create mission planner
        planner = await create_mission_planner()
        
        if message_data.session_id:
            # Continue existing conversation
            session = await planner.continue_conversation(
                message_data.session_id,
                message_data.message
            )
        else:
            # Start new conversation
            session = await planner.start_conversation(message_data.message)
        
        return ChatResponse(
            response=session.get("response", "Sorry, I couldn't process your message."),
            session_id=session.get("session_id", "unknown"),
            suggestions=session.get("next_questions", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    """Get conversation history for a session"""
    try:
        planner = await create_mission_planner()
        session = await planner.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session.session_id,
            "messages": session.messages,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/plan")
async def generate_mission_plan(session_id: str, db: Session = Depends(get_db)):
    """Generate mission plan from conversation"""
    try:
        planner = await create_mission_planner()
        session = await planner.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate mission plan from conversation
        plan = await planner.generate_mission_plan(session)
        
        return {
            "session_id": session_id,
            "mission_plan": plan,
            "status": "generated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate mission plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete conversation session"""
    try:
        planner = await create_mission_planner()
        success = await planner.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))