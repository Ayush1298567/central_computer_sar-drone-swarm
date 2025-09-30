from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ..core.database import get_db
from ..models.mission import ChatMessage

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/message")
async def send_chat_message(
    message_data: dict,
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response."""
    try:
        # Extract message data
        message = message_data.get("message", "")
        conversation_id = message_data.get("conversation_id", "default")

        # Get the conversational mission planner
        from ..services.conversational_mission_planner import get_conversational_planner
        planner = get_conversational_planner()

        # Process the message with AI
        ai_response = await planner.process_message({
            "message": message,
            "conversation_id": conversation_id,
            "mission_id": message_data.get("mission_id")
        })

        # Store the chat message
        chat_message = ChatMessage(
            mission_id=message_data.get("mission_id"),
            sender="user",
            content=message,
            message_type="text"
        )
        db.add(chat_message)

        # Store AI response
        ai_message = ChatMessage(
            mission_id=message_data.get("mission_id"),
            sender="ai",
            content=ai_response["response"],
            message_type=ai_response.get("message_type", "response"),
            ai_confidence=ai_response.get("confidence", 0.8)
        )
        db.add(ai_message)
        db.commit()

        return {
            "success": True,
            "response": ai_response,
            "message": "Chat message processed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")

@router.get("/sessions/{conversation_id}")
async def get_chat_session(conversation_id: str, db: Session = Depends(get_db)):
    """Get chat history for a conversation."""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.mission_id == conversation_id
        ).order_by(ChatMessage.created_at).all()

        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": [
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "confidence": msg.ai_confidence
                }
                for msg in messages
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat session: {str(e)}")