"""
Chat models for conversational mission planning
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    
    # Session metadata
    user_id = Column(String(255), nullable=False)
    session_type = Column(String(100), default="mission_planning")  # mission_planning, support, etc.
    is_active = Column(Boolean, default=True)
    
    # Conversation state
    current_step = Column(String(100))  # Current planning step
    planning_data = Column(JSON, default=dict)  # Accumulated planning information
    mission_parameters = Column(JSON, default=dict)  # Extracted mission parameters
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    mission = relationship("Mission", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "mission_id": self.mission_id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "is_active": self.is_active,
            "current_step": self.current_step,
            "planning_data": self.planning_data,
            "mission_parameters": self.mission_parameters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    message_type = Column(String(50), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    
    # AI processing data
    ai_analysis = Column(JSON)  # AI analysis of the message
    extracted_intent = Column(String(255))  # Detected user intent
    extracted_parameters = Column(JSON)  # Extracted mission parameters
    
    # Response data (for assistant messages)
    response_metadata = Column(JSON)  # Additional response data
    confidence_score = Column(Float)  # AI confidence in response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "ai_analysis": self.ai_analysis,
            "extracted_intent": self.extracted_intent,
            "extracted_parameters": self.extracted_parameters,
            "response_metadata": self.response_metadata,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }