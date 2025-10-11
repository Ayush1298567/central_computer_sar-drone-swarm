from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models import Mission
from app.models.chat import ChatMessageDB, ChatSession

router = APIRouter()


@router.post("/message")
async def send_message(message_data: dict, db: Session = Depends(get_db)):
    """Send a chat message (user or AI)."""
    try:
        message = ChatMessageDB(
            mission_id=message_data.get("mission_id"),
            sender=message_data.get("sender", "user"),
            content=message_data.get("content"),
            message_type=message_data.get("message_type", "text"),
            ai_confidence=message_data.get("ai_confidence"),
            attachments=message_data.get("attachments")
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        response = {
            "success": True,
            "message": {
                "id": message.id,
                "sender": message.sender,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat()
            }
        }
        
        # If user message, generate AI response
        if message.sender == "user":
            ai_response = await generate_ai_response(message.content, message.mission_id, db)
            response["ai_response"] = ai_response
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


async def generate_ai_response(user_message: str, mission_id: int, db: Session):
    """Generate AI response to user message."""
    # Simple response for now - can be enhanced with actual AI integration
    response_content = f"I understand you want to: {user_message}. How can I help you plan this mission?"
    
    ai_message = ChatMessageDB(
        mission_id=mission_id,
        sender="ai",
        content=response_content,
        message_type="response",
        ai_confidence=0.8
    )
    
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return {
        "id": ai_message.id,
        "sender": ai_message.sender,
        "content": ai_message.content,
        "message_type": ai_message.message_type,
        "created_at": ai_message.created_at.isoformat()
    }


@router.get("/{mission_id}/history")
async def get_chat_history(mission_id: int, db: Session = Depends(get_db)):
    """Get chat history for a mission."""
    messages = db.query(ChatMessageDB).filter(
        ChatMessageDB.mission_id == mission_id
    ).order_by(ChatMessageDB.created_at.asc()).all()
    
    return {
        "success": True,
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "message_type": msg.message_type,
                "ai_confidence": msg.ai_confidence,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "count": len(messages)
    }


@router.delete("/{message_id}")
async def delete_message(message_id: int, db: Session = Depends(get_db)):
    """Delete a chat message."""
    message = db.query(ChatMessageDB).filter(ChatMessageDB.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    try:
        db.delete(message)
        db.commit()
        
        return {
            "success": True,
            "message": "Message deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")

