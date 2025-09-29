"""
Database models for chat and conversational AI.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class ChatMessage(Base):
    """Chat message model for conversational mission planning."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)

    # Message details
    sender = Column(String(50), nullable=False)  # user, ai, system
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, image, file, etc.

    # AI context
    ai_context = Column(JSON)  # Store AI reasoning and context
    suggested_actions = Column(JSON)  # AI-suggested next steps

    # Mission planning data
    mission_updates = Column(JSON)  # Any mission parameter updates from this message

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True))

    # Relationships
    mission = relationship("Mission", back_populates="chat_messages")