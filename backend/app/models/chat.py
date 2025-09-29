"""
Chat model definitions for conversational AI.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChatSession(Base):
    """Chat session model for conversational mission planning."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(100), nullable=True)  # For user identification
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)

    # Session metadata
    title = Column(String(200), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    ai_model = Column(String(50), default="llama2", nullable=False)

    # Session data
    context = Column(JSON, nullable=True)  # Mission context, user preferences, etc.
    current_mission_plan = Column(JSON, nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    mission = relationship("Mission", back_populates="chat_messages")
    messages = relationship("ChatMessage", back_populates="session")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class ChatMessage(Base):
    """Individual chat messages within a session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_id = Column(String(50), unique=True, index=True, nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)

    # Message metadata
    message_type = Column(String(50), default="text", nullable=False)  # text, mission_plan, confirmation, etc.
    metadata = Column(JSON, nullable=True)  # Additional message data

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', type='{self.message_type}')>"