"""
Chat API endpoints for conversational mission planning
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..core.database import get_db
from ..models.chat import (
    ChatSession, ChatMessageDB, ChatSessionCreate, ChatSessionResponse,
    SendMessageRequest, MessageResponse, ConversationResponse,
    PlanningProgressResponse, ChatStatus, PlanningStage, MessageRole,
    MissionPlanningContext
)
from ..services.conversational_mission_planner import ConversationalMissionPlanner
from ..services.notification_service import NotificationService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# Service instances
conversational_planner = ConversationalMissionPlanner()
notification_service = NotificationService()

@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    session_data: ChatSessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new chat session for mission planning"""
    try:
        # Generate unique session ID
        session_id = f"chat_{uuid.uuid4().hex[:8]}"
        
        # Initialize planning context
        initial_context = MissionPlanningContext()
        
        # Create database record
        db_session = ChatSession(
            session_id=session_id,
            user_id=session_data.user_id,
            planning_context=initial_context.dict(),
            current_stage=PlanningStage.INITIAL.value
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Send welcome message if no initial message provided
        if not session_data.initial_message:
            welcome_message = await conversational_planner.generate_welcome_message(session_data.user_id)
            await _add_message(db, session_id, MessageRole.ASSISTANT, welcome_message)
        else:
            # Process initial message
            background_tasks.add_task(
                _process_user_message,
                session_id,
                session_data.initial_message,
                db
            )
        
        logger.info(f"Chat session created: {session_id} for user {session_data.user_id}")
        return _convert_session_to_response(db_session, db)
        
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    user_id: Optional[str] = None,
    status: Optional[ChatStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List chat sessions with filtering"""
    try:
        query = db.query(ChatSession)
        
        # Apply filters
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        if status:
            query = query.filter(ChatSession.status == status.value)
        
        # Apply pagination and ordering
        sessions = query.order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()
        
        return [_convert_session_to_response(session, db) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")

@router.get("/sessions/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    include_suggestions: bool = Query(True, description="Include AI suggestions"),
    db: Session = Depends(get_db)
):
    """Get complete conversation for a session"""
    try:
        # Get session
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get messages
        messages = db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session_id
        ).order_by(ChatMessageDB.created_at.asc()).all()
        
        # Convert to response models
        session_response = _convert_session_to_response(session, db)
        message_responses = [_convert_message_to_response(msg) for msg in messages]
        
        # Generate suggestions and next steps
        suggestions = []
        next_steps = []
        
        if include_suggestions and session.status == ChatStatus.ACTIVE.value:
            context = MissionPlanningContext(**session.planning_context) if session.planning_context else MissionPlanningContext()
            suggestions = await conversational_planner.generate_suggestions(context, message_responses)
            next_steps = await conversational_planner.get_next_steps(context)
        
        return ConversationResponse(
            session=session_response,
            messages=message_responses,
            suggestions=suggestions,
            next_steps=next_steps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    message_data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a message in a chat session"""
    try:
        # Verify session exists
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        if session.status != ChatStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail=f"Cannot send message to {session.status} session")
        
        # Add user message
        user_message = await _add_message(
            db, session_id, MessageRole.USER, message_data.content, message_data.metadata
        )
        
        # Process message and generate response in background
        background_tasks.add_task(
            _process_user_message,
            session_id,
            message_data.content,
            db
        )
        
        return user_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/sessions/{session_id}/progress", response_model=PlanningProgressResponse)
async def get_planning_progress(session_id: str, db: Session = Depends(get_db)):
    """Get mission planning progress for a session"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        context = MissionPlanningContext(**session.planning_context) if session.planning_context else MissionPlanningContext()
        
        # Calculate progress
        all_stages = list(PlanningStage)
        current_stage_index = all_stages.index(PlanningStage(session.current_stage))
        progress_percentage = (current_stage_index / (len(all_stages) - 1)) * 100
        
        completed_stages = all_stages[:current_stage_index]
        next_stage = all_stages[current_stage_index + 1] if current_stage_index < len(all_stages) - 1 else None
        
        # Check if mission can be generated
        can_generate = await conversational_planner.can_generate_mission(context)
        
        return PlanningProgressResponse(
            session_id=session_id,
            current_stage=PlanningStage(session.current_stage),
            progress_percentage=progress_percentage,
            completed_stages=completed_stages,
            next_stage=next_stage,
            context=context,
            can_generate_mission=can_generate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting planning progress for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get planning progress: {str(e)}")

@router.post("/sessions/{session_id}/generate-mission")
async def generate_mission_from_chat(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a mission from the chat conversation"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        context = MissionPlanningContext(**session.planning_context) if session.planning_context else MissionPlanningContext()
        
        # Validate that planning is complete enough
        if not await conversational_planner.can_generate_mission(context):
            raise HTTPException(status_code=400, detail="Mission planning is not complete enough to generate mission")
        
        # Generate mission in background
        background_tasks.add_task(_generate_mission_from_context, session_id, context, db)
        
        # Update session status
        session.status = ChatStatus.PLANNING.value
        session.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Mission generation started", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating mission from chat {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate mission: {str(e)}")

@router.patch("/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: ChatStatus,
    db: Session = Depends(get_db)
):
    """Update chat session status"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        session.status = status.value
        session.updated_at = datetime.utcnow()
        
        if status == ChatStatus.COMPLETED:
            session.completed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Chat session {session_id} status updated to {status.value}")
        return {"message": "Session status updated", "session_id": session_id, "status": status.value}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session status {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session status: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    delete_messages: bool = Query(True, description="Also delete all messages"),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        if session.status == ChatStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Cannot delete active session")
        
        # Delete messages if requested
        if delete_messages:
            db.query(ChatMessageDB).filter(ChatMessageDB.session_id == session_id).delete()
        
        # Delete session
        db.delete(session)
        db.commit()
        
        logger.info(f"Chat session deleted: {session_id}")
        return {"message": "Chat session deleted", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")

@router.get("/sessions/{session_id}/export")
async def export_conversation(
    session_id: str,
    format: str = Query("json", regex="^(json|txt|csv)$"),
    db: Session = Depends(get_db)
):
    """Export conversation in different formats"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        messages = db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session_id
        ).order_by(ChatMessageDB.created_at.asc()).all()
        
        if format == "json":
            export_data = {
                "session": _convert_session_to_response(session, db).dict(),
                "messages": [_convert_message_to_response(msg).dict() for msg in messages]
            }
            return export_data
        elif format == "txt":
            lines = [f"Chat Session: {session_id}"]
            lines.append(f"User: {session.user_id}")
            lines.append(f"Created: {session.created_at}")
            lines.append("-" * 50)
            
            for msg in messages:
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{timestamp}] {msg.role.upper()}: {msg.content}")
            
            return {"content": "\n".join(lines), "filename": f"chat_{session_id}.txt"}
        else:  # csv
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["timestamp", "role", "content", "metadata"])
            
            for msg in messages:
                writer.writerow([
                    msg.created_at.isoformat(),
                    msg.role,
                    msg.content,
                    str(msg.metadata) if msg.metadata else ""
                ])
            
            return {"content": output.getvalue(), "filename": f"chat_{session_id}.csv"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export conversation: {str(e)}")

# Helper functions
async def _add_message(
    db: Session, 
    session_id: str, 
    role: MessageRole, 
    content: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> MessageResponse:
    """Add a message to the database"""
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    db_message = ChatMessageDB(
        message_id=message_id,
        session_id=session_id,
        role=role.value,
        content=content,
        metadata=metadata or {}
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return _convert_message_to_response(db_message)

def _convert_session_to_response(session: ChatSession, db: Session) -> ChatSessionResponse:
    """Convert database session to response model"""
    # Count messages
    message_count = db.query(ChatMessageDB).filter(ChatMessageDB.session_id == session.session_id).count()
    
    # Convert planning context
    planning_context = None
    if session.planning_context:
        planning_context = MissionPlanningContext(**session.planning_context)
    
    return ChatSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        status=ChatStatus(session.status),
        current_stage=PlanningStage(session.current_stage),
        planning_context=planning_context,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
        generated_mission_id=session.generated_mission_id,
        message_count=message_count
    )

def _convert_message_to_response(message: ChatMessageDB) -> MessageResponse:
    """Convert database message to response model"""
    return MessageResponse(
        message_id=message.message_id,
        session_id=message.session_id,
        role=MessageRole(message.role),
        content=message.content,
        metadata=message.metadata,
        created_at=message.created_at
    )

async def _process_user_message(session_id: str, content: str, db: Session):
    """Process user message and generate AI response"""
    try:
        # Get session and context
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            return
        
        context = MissionPlanningContext(**session.planning_context) if session.planning_context else MissionPlanningContext()
        
        # Get conversation history
        messages = db.query(ChatMessageDB).filter(
            ChatMessageDB.session_id == session_id
        ).order_by(ChatMessageDB.created_at.asc()).all()
        
        message_history = [_convert_message_to_response(msg) for msg in messages]
        
        # Generate AI response
        response_content, updated_context, new_stage = await conversational_planner.process_message(
            content, context, message_history
        )
        
        # Add AI response
        await _add_message(db, session_id, MessageRole.ASSISTANT, response_content)
        
        # Update session context and stage
        session.planning_context = updated_context.dict()
        session.current_stage = new_stage.value
        session.updated_at = datetime.utcnow()
        db.commit()
        
        logger.debug(f"Processed message for session {session_id}, new stage: {new_stage.value}")
        
    except Exception as e:
        logger.error(f"Error processing user message for {session_id}: {str(e)}")
        # Add error message
        try:
            await _add_message(
                db, session_id, MessageRole.ASSISTANT,
                "I'm sorry, I encountered an error processing your message. Please try again or rephrase your request."
            )
        except:
            pass

async def _generate_mission_from_context(session_id: str, context: MissionPlanningContext, db: Session):
    """Generate mission from planning context"""
    try:
        # Generate mission using conversational planner
        mission_data = await conversational_planner.generate_mission_from_context(context)
        
        # Create mission via API (import here to avoid circular imports)
        from .missions import create_mission
        from ..models.mission import MissionCreate
        
        # Convert context to mission create model
        mission_create = MissionCreate(
            name=mission_data.get("name", "AI Planned Mission"),
            description=mission_data.get("description", "Mission created through conversational planning"),
            mission_type=mission_data["mission_type"],
            priority=mission_data["priority"],
            search_area=mission_data["search_area"],
            requirements=mission_data.get("requirements"),
            created_by=f"chat_session_{session_id}"
        )
        
        # Create the mission (this would need proper background task handling)
        # For now, just update the session with the plan
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.status = ChatStatus.COMPLETED.value
            session.completed_at = datetime.utcnow()
            session.final_plan = mission_data
            session.updated_at = datetime.utcnow()
            db.commit()
            
            # Add completion message
            await _add_message(
                db, session_id, MessageRole.ASSISTANT,
                f"Mission plan completed! I've generated a comprehensive mission plan based on our conversation. The mission '{mission_data.get('name')}' is ready for execution."
            )
        
        logger.info(f"Mission generated from chat session {session_id}")
        
    except Exception as e:
        logger.error(f"Error generating mission from context for {session_id}: {str(e)}")
        # Update session with error
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.status = ChatStatus.ACTIVE.value  # Return to active for retry
            db.commit()
            
            await _add_message(
                db, session_id, MessageRole.ASSISTANT,
                "I encountered an error while generating your mission plan. Let me try to help you refine the requirements further."
            )