"""
Chat data models for conversational mission planning
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatStatus(str, Enum):
    ACTIVE = "active"
    PLANNING = "planning"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class PlanningStage(str, Enum):
    INITIAL = "initial"
    AREA_DEFINITION = "area_definition"
    REQUIREMENTS = "requirements"
    DRONE_SELECTION = "drone_selection"
    VALIDATION = "validation"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

class ChatMessage(BaseModel):
    """Chat message model"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MissionPlanningContext(BaseModel):
    """Context for mission planning conversation"""
    stage: PlanningStage = Field(default=PlanningStage.INITIAL)
    mission_type: Optional[str] = None
    priority: Optional[str] = None
    search_area: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None
    selected_drones: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None
    progress: Dict[str, bool] = Field(default_factory=dict)

# SQLAlchemy Models
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default=ChatStatus.ACTIVE.value)
    
    # Planning context
    planning_context = Column(JSON)
    current_stage = Column(String, default=PlanningStage.INITIAL.value)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Results
    generated_mission_id = Column(String)
    final_plan = Column(JSON)

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    
    # Message content
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API
class ChatSessionCreate(BaseModel):
    user_id: str = Field(..., description="User identifier")
    initial_message: Optional[str] = Field(None, description="Initial message to start conversation")

class ChatSessionResponse(BaseModel):
    session_id: str
    user_id: str
    status: ChatStatus
    current_stage: PlanningStage
    planning_context: Optional[MissionPlanningContext]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    generated_mission_id: Optional[str]
    message_count: int

    class Config:
        from_attributes = True

class SendMessageRequest(BaseModel):
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[MessageResponse]
    suggestions: Optional[List[str]] = Field(default_factory=list)
    next_steps: Optional[List[str]] = Field(default_factory=list)

class PlanningProgressResponse(BaseModel):
    session_id: str
    current_stage: PlanningStage
    progress_percentage: float
    completed_stages: List[PlanningStage]
    next_stage: Optional[PlanningStage]
    context: MissionPlanningContext
    can_generate_mission: bool