"""
Chat models for SAR Mission Commander
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base

class MessageType(enum.Enum):
    TEXT = "text"
    SYSTEM = "system"
    AI_RESPONSE = "ai_response"
    USER_INPUT = "user_input"

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))

    # Message content
    content = Column(Text)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, nullable=True)  # For multi-user support

    # AI context (if applicable)
    ai_confidence = Column(Float, nullable=True)
    ai_model_used = Column(String, nullable=True)

    # Relationship
    session = relationship("ChatSession", back_populates="messages")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)

    # Session details
    title = Column(String, default="Mission Planning Session")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Mission context
    mission_id = Column(String, ForeignKey("missions.id"), nullable=True)
    current_stage = Column(String, default="planning")  # planning, active, review, etc.

    # AI context storage (JSON)
    context_data = Column(Text)  # Mission planning context
    conversation_history = Column(Text)  # Recent conversation for AI context

    # Relationships
    mission = relationship("Mission", back_populates="chat_session")
    messages = relationship("ChatMessageDB", back_populates="session")