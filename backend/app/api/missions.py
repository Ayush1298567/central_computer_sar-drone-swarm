"""
Mission API endpoints for SAR Mission Commander
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime

from ..core.database import get_db
from ..models.mission import Mission, MissionStatus
from ..models.chat import ChatSession, ChatMessageDB, MessageType
from ..services.conversational_mission_planner import ConversationalMissionPlanner

router = APIRouter(prefix="/api/missions", tags=["missions"])

@router.get("/")
async def get_missions(db: Session = Depends(get_db)):
    """Get all missions"""
    missions = db.query(Mission).all()
    return missions

@router.get("/{mission_id}")
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get a specific mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.post("/")
async def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    """Create a new mission"""
    mission_id = str(uuid.uuid4())

    # Create mission
    mission = Mission(
        id=mission_id,
        name=mission_data.get("name", "New Mission"),
        description=mission_data.get("description", ""),
        mission_type=mission_data.get("mission_type", "search"),
        priority=mission_data.get("priority", "medium"),
        center_latitude=mission_data.get("center_latitude"),
        center_longitude=mission_data.get("center_longitude"),
        altitude=mission_data.get("altitude", 100.0),
        radius=mission_data.get("radius", 1000.0),
        search_area=json.dumps(mission_data.get("search_area", [])),
        weather_conditions=json.dumps(mission_data.get("weather_conditions", {})),
        time_limit_minutes=mission_data.get("time_limit_minutes", 120),
        max_drones=mission_data.get("max_drones", 5)
    )

    db.add(mission)

    # Create chat session for mission
    chat_session = ChatSession(
        id=str(uuid.uuid4()),
        mission_id=mission_id,
        title=f"Mission: {mission.name}",
        context_data=json.dumps({
            "mission_name": mission.name,
            "mission_type": mission.mission_type,
            "priority": mission.priority,
            "search_area": mission.search_area
        })
    )

    mission.chat_session = chat_session
    db.add(chat_session)
    db.commit()
    db.refresh(mission)

    return mission

@router.put("/{mission_id}")
async def update_mission(mission_id: str, mission_data: dict, db: Session = Depends(get_db)):
    """Update a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Update mission fields
    for key, value in mission_data.items():
        if hasattr(mission, key):
            setattr(mission, key, value)

    mission.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mission)

    return mission

@router.delete("/{mission_id}")
async def delete_mission(mission_id: str, db: Session = Depends(get_db)):
    """Delete a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    db.delete(mission)
    db.commit()

    return {"message": "Mission deleted successfully"}

@router.get("/{mission_id}/chat")
async def get_mission_chat(mission_id: str, db: Session = Depends(get_db)):
    """Get chat messages for a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if not mission.chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Get recent messages (last 50)
    messages = db.query(ChatMessageDB)\
        .filter(ChatMessageDB.session_id == mission.chat_session.id)\
        .order_by(ChatMessageDB.timestamp.desc())\
        .limit(50)\
        .all()

    # Reverse to chronological order
    messages.reverse()

    return {
        "session_id": mission.chat_session.id,
        "messages": messages,
        "current_stage": mission.chat_session.current_stage
    }

@router.post("/{mission_id}/chat")
async def send_mission_chat(
    mission_id: str,
    message_data: dict,
    db: Session = Depends(get_db)
):
    """Send chat message for mission planning"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Get or create chat session
    if not mission.chat_session:
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            mission_id=mission_id,
            title=f"Mission: {mission.name}"
        )
        mission.chat_session = chat_session
        db.add(chat_session)
        db.commit()
        db.refresh(mission)

    # Create user message
    user_message = ChatMessageDB(
        session_id=mission.chat_session.id,
        content=message_data.get("content", ""),
        message_type=MessageType.USER_INPUT,
        user_id=message_data.get("user_id", "default_user")
    )

    db.add(user_message)

    # Get conversation history
    recent_messages = db.query(ChatMessageDB)\
        .filter(ChatMessageDB.session_id == mission.chat_session.id)\
        .order_by(ChatMessageDB.timestamp.desc())\
        .limit(10)\
        .all()

    conversation_history = [
        {"role": msg.message_type.value, "content": msg.content}
        for msg in reversed(recent_messages)
    ]

    # Process with AI planner
    planner = ConversationalMissionPlanner()
    ai_response_content, updated_context, new_stage = await planner.process_message(
        user_message=message_data.get("content", ""),
        context=json.loads(mission.chat_session.context_data or "{}"),
        message_history=conversation_history
    )

    # Create AI response message
    ai_message = ChatMessageDB(
        session_id=mission.chat_session.id,
        content=ai_response_content,
        message_type=MessageType.AI_RESPONSE,
        ai_confidence=0.9,
        ai_model_used="phi3:mini"
    )

    db.add(ai_message)

    # Update chat session context and stage
    mission.chat_session.context_data = json.dumps(updated_context)
    mission.chat_session.current_stage = new_stage
    mission.chat_session.updated_at = datetime.utcnow()

    db.commit()

    return {
        "user_message": user_message,
        "ai_response": ai_message,
        "updated_context": updated_context,
        "current_stage": new_stage
    }

@router.post("/{mission_id}/start")
async def start_mission(mission_id: str, db: Session = Depends(get_db)):
    """Start a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.status != MissionStatus.PLANNING:
        raise HTTPException(status_code=400, detail="Mission must be in planning status to start")

    mission.status = MissionStatus.ACTIVE
    mission.start_time = datetime.utcnow()
    mission.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(mission)

    return mission

@router.post("/{mission_id}/complete")
async def complete_mission(mission_id: str, db: Session = Depends(get_db)):
    """Complete a mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.status != MissionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Mission must be active to complete")

    mission.status = MissionStatus.COMPLETED
    mission.end_time = datetime.utcnow()
    mission.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(mission)

    return mission