"""
Chat and conversational AI API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models import ChatMessage, Mission
from ..services import conversational_mission_planner
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/messages")
async def get_chat_messages(
    mission_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get chat messages with optional filtering."""
    query = db.query(ChatMessage)

    if mission_id:
        query = query.filter(ChatMessage.mission_id == mission_id)

    messages = query.order_by(ChatMessage.timestamp.desc()).offset(skip).limit(limit).all()
    return messages


@router.get("/messages/{message_id}")
async def get_chat_message(message_id: int, db: Session = Depends(get_db)):
    """Get a specific chat message by ID."""
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/messages")
async def create_chat_message(message_data: dict, db: Session = Depends(get_db)):
    """Create a new chat message."""
    try:
        message = ChatMessage(**message_data)
        db.add(message)
        db.commit()
        db.refresh(message)

        logger.info(f"Created chat message from {message.sender} (ID: {message.id})")
        return message
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating chat message: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/converse")
async def converse_with_ai(
    mission_id: int,
    user_message: str,
    db: Session = Depends(get_db)
):
    """Have a conversation with the AI mission planner."""
    try:
        # Get mission context
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        # Get conversation history for context
        history = db.query(ChatMessage).filter(
            ChatMessage.mission_id == mission_id
        ).order_by(ChatMessage.timestamp).all()

        # Process with AI planner
        ai_response = await conversational_mission_planner.process_message(
            user_message=user_message,
            mission=mission,
            history=history
        )

        # Save user message
        user_msg = ChatMessage(
            mission_id=mission_id,
            sender="user",
            message=user_message,
            message_type="text"
        )
        db.add(user_msg)

        # Save AI response
        ai_msg = ChatMessage(
            mission_id=mission_id,
            sender="ai",
            message=ai_response["message"],
            message_type="text",
            ai_context=ai_response.get("context", {}),
            suggested_actions=ai_response.get("suggested_actions", []),
            mission_updates=ai_response.get("mission_updates", {})
        )
        db.add(ai_msg)

        db.commit()

        logger.info(f"AI conversation for mission {mission_id}: user message processed")

        return {
            "user_message": user_msg,
            "ai_response": ai_msg,
            "suggested_actions": ai_response.get("suggested_actions", []),
            "mission_updates": ai_response.get("mission_updates", {})
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error in AI conversation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan-mission")
async def start_mission_planning(db: Session = Depends(get_db)):
    """Start an interactive mission planning session."""
    try:
        # Create a new mission in planning status
        mission = Mission(
            name="New Mission",
            description="Interactive mission planning session",
            status="planning",
            center_lat=0.0,  # Will be updated during conversation
            center_lng=0.0,
            area_size_km2=1.0,
            user_approved=False
        )
        db.add(mission)
        db.commit()
        db.refresh(mission)

        # Create initial AI greeting message
        greeting_msg = ChatMessage(
            mission_id=mission.id,
            sender="ai",
            message="Hello! I'm your AI mission planner. I'll help you create a comprehensive search and rescue mission. What type of area would you like to search and where is it located?",
            message_type="text",
            ai_context={"stage": "greeting", "next_question": "location"}
        )
        db.add(greeting_msg)
        db.commit()

        logger.info(f"Started mission planning session (ID: {mission.id})")

        return {
            "mission": mission,
            "initial_message": greeting_msg,
            "session_id": mission.id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error starting mission planning: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mission/{mission_id}/planning-progress")
async def get_planning_progress(mission_id: int, db: Session = Depends(get_db)):
    """Get the current planning progress for a mission."""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        messages = db.query(ChatMessage).filter(
            ChatMessage.mission_id == mission_id
        ).order_by(ChatMessage.timestamp).all()

        # Analyze planning progress based on conversation
        progress = conversational_mission_planner.analyze_planning_progress(messages)

        return {
            "mission": mission,
            "progress": progress,
            "total_messages": len(messages)
        }

    except Exception as e:
        logger.error(f"Error getting planning progress: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mission/{mission_id}/approve")
async def approve_mission_plan(mission_id: int, db: Session = Depends(get_db)):
    """Approve the current mission plan."""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status != "planning":
            raise HTTPException(status_code=400, detail="Mission must be in planning status")

        mission.user_approved = True
        mission.status = "ready"  # Ready to start

        # Add approval message to chat
        approval_msg = ChatMessage(
            mission_id=mission_id,
            sender="system",
            message="Mission plan approved by user. Ready to execute.",
            message_type="text"
        )
        db.add(approval_msg)

        db.commit()

        logger.info(f"Mission plan approved (ID: {mission.id})")

        return {
            "message": "Mission plan approved successfully",
            "mission": mission
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error approving mission plan: {e}")
        raise HTTPException(status_code=400, detail=str(e))