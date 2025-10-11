"""
Chat API endpoints for conversational AI.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import uuid
from datetime import datetime

import sys
import os

# Add the backend directory to Python path for proper imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import get_db
from app.models.chat import ChatSession, ChatMessageDB
from app.models.mission import Mission
from app.services.conversational_mission_planner import ConversationalMissionPlanner

logger = logging.getLogger(__name__)

# Initialize conversational mission planner
conversational_planner = ConversationalMissionPlanner()

router = APIRouter()


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_chat_sessions(
    skip: int = 0,
    limit: int = 100,
    mission_id: str = None,
    db: Session = Depends(get_db)
):
    """Get all chat sessions with optional filtering."""
    try:
        query = db.query(ChatSession)

        if mission_id:
            mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
            if mission:
                query = query.filter(ChatSession.mission_id == mission.id)

        sessions = query.order_by(ChatSession.created_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": session.id,
                "session_id": session.session_id,
                "user_id": session.user_id,
                "mission_id": session.mission_id,
                "title": session.title,
                "status": session.status,
                "ai_model": session.ai_model,
                "context": session.context,
                "current_mission_plan": session.current_mission_plan,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": len(session.messages)
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions")
async def create_chat_session(
    session_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Create new session
        session = ChatSession(
            session_id=session_id,
            user_id=session_data.get("user_id"),
            mission_id=session_data.get("mission_id"),
            title=session_data.get("title"),
            status="active",
            ai_model=session_data.get("ai_model", "llama2"),
            context=session_data.get("context", {}),
            current_mission_plan=session_data.get("current_mission_plan")
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Created new chat session {session_id}")
        return {
            "message": "Chat session created successfully",
            "session_id": session_id,
            "id": session.id
        }

    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific chat session with messages."""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Get messages
        messages = db.query(ChatMessageDB).filter(ChatMessageDB.session_id == session.id).order_by(ChatMessageDB.timestamp).all()

        return {
            "id": session.id,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "mission_id": session.mission_id,
            "title": session.title,
            "status": session.status,
            "ai_model": session.ai_model,
            "context": session.context,
            "current_mission_plan": session.current_mission_plan,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "message_id": msg.message_id,
                    "role": msg.role,
                    "content": msg.content,
                    "tokens_used": msg.tokens_used,
                    "message_type": msg.message_type,
                    "metadata": msg.metadata,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Send a message in a chat session."""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        if session.status != "active":
            raise HTTPException(status_code=400, detail="Chat session is not active")

        # Generate unique message ID
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        # Create user message
        user_message = ChatMessageDB(
            session_id=session.id,
            message_id=message_id,
            role="user",
            content=message_data["content"],
            message_type=message_data.get("message_type", "text"),
            message_metadata=message_data.get("metadata")
        )

        db.add(user_message)
        db.commit()

        # Update session activity
        session.last_activity = datetime.utcnow()
        db.commit()

        # Process message with conversational AI
        try:
            ai_response = await conversational_planner.process_message(
                session_id, message_data["content"], message_data.get("context", {})
            )

            # Create AI response message
            ai_message_id = f"msg_{uuid.uuid4().hex[:8]}"
            ai_message = ChatMessageDB(
                session_id=session.id,
                message_id=ai_message_id,
                role="assistant",
                content=ai_response["content"],
                tokens_used=ai_response.get("tokens_used"),
                message_type=ai_response.get("message_type", "text"),
                message_metadata=ai_response.get("metadata")
            )

            db.add(ai_message)
            db.commit()

            # Update session with current mission plan if provided
            if ai_response.get("current_mission_plan"):
                session.current_mission_plan = ai_response["current_mission_plan"]
                db.commit()

            logger.info(f"Processed message in session {session_id}")

            return {
                "message": "Message processed successfully",
                "user_message_id": message_id,
                "ai_message_id": ai_message_id,
                "ai_response": ai_response["content"],
                "tokens_used": ai_response.get("tokens_used")
            }

        except Exception as e:
            logger.error(f"Error processing message with AI: {e}")
            # Return error message
            error_message_id = f"msg_{uuid.uuid4().hex[:8]}"
            error_message = ChatMessageDB(
                session_id=session.id,
                message_id=error_message_id,
                role="assistant",
                content="I'm sorry, I encountered an error processing your message. Please try again.",
                message_type="error",
                metadata={"error": str(e)}
            )

            db.add(error_message)
            db.commit()

            return {
                "message": "Message saved but AI processing failed",
                "user_message_id": message_id,
                "error": str(e)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/generate-mission")
async def generate_mission_plan(
    session_id: str,
    mission_requirements: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate a mission plan from chat conversation."""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Generate mission plan using conversational AI
        mission_plan = await conversational_planner.generate_mission_plan(
            session_id, mission_requirements
        )

        # Update session with mission plan
        session.current_mission_plan = mission_plan
        session.last_activity = datetime.utcnow()
        db.commit()

        logger.info(f"Generated mission plan for session {session_id}")
        return {
            "message": "Mission plan generated successfully",
            "mission_plan": mission_plan
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mission plan for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages."""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Delete all messages first
        db.query(ChatMessageDB).filter(ChatMessageDB.session_id == session.id).delete()

        # Delete session
        db.delete(session)
        db.commit()

        logger.info(f"Deleted chat session {session_id}")
        return {"message": "Chat session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
