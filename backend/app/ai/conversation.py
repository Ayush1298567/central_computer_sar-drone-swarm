"""
Conversation Engine for SAR Mission Commander
Handles natural language processing, chat interactions, and AI conversations
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class ConversationStage(Enum):
    """Stages of conversation flow"""
    GREETING = "greeting"
    MISSION_PLANNING = "mission_planning"
    AREA_SELECTION = "area_selection"
    PARAMETER_COLLECTION = "parameter_collection"
    CONFIRMATION = "confirmation"
    EXECUTION = "execution"
    COMPLETION = "completion"

class MessageType(Enum):
    """Types of messages in conversation"""
    USER_INPUT = "user_input"
    AI_RESPONSE = "ai_response"
    SYSTEM_MESSAGE = "system_message"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"

@dataclass
class ConversationMessage:
    """Represents a message in a conversation"""
    content: str
    message_type: MessageType
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    session_id: str
    current_stage: ConversationStage
    mission_parameters: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)

class ConversationEngine:
    """Main conversation processing engine"""
    
    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.conversation_templates = {}
        self.question_bank = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the conversation engine"""
        try:
            # Load conversation templates
            await self._load_conversation_templates()
            
            # Load question bank
            await self._load_question_bank()
            
            self.is_initialized = True
            print("✅ Conversation Engine initialized")
            
        except Exception as e:
            print(f"⚠️ Conversation Engine initialization failed: {e}")
            self.is_initialized = False
    
    async def _load_conversation_templates(self):
        """Load conversation templates for different scenarios"""
        self.conversation_templates = {
            "mission_planning": {
                "greeting": [
                    "Hello! I'm here to help you plan your SAR mission. Let's start by understanding what you need to accomplish.",
                    "Welcome to the SAR Mission Commander! I'll guide you through planning your search and rescue operation.",
                    "Hi! I'm your AI mission planning assistant. Let's create an effective search and rescue plan together."
                ],
                "area_selection": [
                    "Where would you like to conduct the search? Please provide coordinates, landmarks, or describe the area.",
                    "Let's define the search area. You can give me GPS coordinates, city names, or describe the terrain.",
                    "What's the target search location? I can work with coordinates, addresses, or geographic descriptions."
                ],
                "parameter_collection": [
                    "Great! Now let's set up the mission parameters. What's the priority level for this mission?",
                    "Perfect! Let's configure the mission details. How many drones should we deploy?",
                    "Excellent! Now let's fine-tune the mission. What altitude would you prefer for the search?"
                ]
            },
            "discovery_analysis": {
                "new_discovery": [
                    "I've detected something in the drone footage. Let me analyze this for you.",
                    "New discovery alert! I'm processing the image to identify what we've found.",
                    "Interesting finding! I'm running analysis to determine what the drone has spotted."
                ],
                "analysis_complete": [
                    "Analysis complete! Here's what I found in the image.",
                    "I've finished analyzing the discovery. Here are the results.",
                    "The analysis is ready! Here's what the drone detected."
                ]
            }
        }
    
    async def _load_question_bank(self):
        """Load questions for different conversation stages"""
        self.question_bank = {
            ConversationStage.MISSION_PLANNING: [
                "What type of mission are you planning? (search, rescue, survey, training)",
                "What's the priority level for this mission? (low, medium, high, critical)",
                "How many drones do you want to deploy?",
                "What's the maximum altitude for the search?",
                "Do you have any specific weather requirements?",
                "What's the time limit for this mission?",
                "Are there any restricted areas to avoid?"
            ],
            ConversationStage.AREA_SELECTION: [
                "Please provide the search area coordinates or describe the location",
                "What's the radius of the search area?",
                "Are there any specific landmarks or reference points?",
                "What type of terrain are we dealing with?",
                "Are there any accessibility constraints?"
            ],
            ConversationStage.PARAMETER_COLLECTION: [
                "What's the target altitude for the search?",
                "Should we use thermal imaging?",
                "Do you need night vision capabilities?",
                "What's the maximum flight duration?",
                "Are there any battery requirements?"
            ]
        }
    
    async def start_conversation(self, session_id: str, initial_message: str = "") -> Dict[str, Any]:
        """
        Start a new conversation session
        
        Args:
            session_id: Unique session identifier
            initial_message: Optional initial user message
        
        Returns:
            Response dictionary with AI message and conversation state
        """
        try:
            # Create new conversation context
            context = ConversationContext(
                session_id=session_id,
                current_stage=ConversationStage.GREETING
            )
            
            self.active_conversations[session_id] = context
            
            # Generate greeting response
            greeting_template = self.conversation_templates["mission_planning"]["greeting"]
            greeting_message = greeting_template[0]  # Use first greeting
            
            # Add AI response to history
            ai_message = ConversationMessage(
                content=greeting_message,
                message_type=MessageType.AI_RESPONSE,
                timestamp=datetime.utcnow()
            )
            context.conversation_history.append(ai_message)
            
            # Move to mission planning stage
            context.current_stage = ConversationStage.MISSION_PLANNING
            
            return {
                "session_id": session_id,
                "message": greeting_message,
                "stage": context.current_stage.value,
                "next_questions": await self._get_next_questions(context),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Failed to start conversation: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process a user message in an ongoing conversation
        
        Args:
            session_id: Session identifier
            user_message: User's message content
        
        Returns:
            Response dictionary with AI response and updated state
        """
        try:
            if session_id not in self.active_conversations:
                return await self.start_conversation(session_id, user_message)
            
            context = self.active_conversations[session_id]
            
            # Add user message to history
            user_msg = ConversationMessage(
                content=user_message,
                message_type=MessageType.USER_INPUT,
                timestamp=datetime.utcnow()
            )
            context.conversation_history.append(user_msg)
            
            # Process the message based on current stage
            response = await self._process_stage_message(context, user_message)
            
            # Add AI response to history
            if "message" in response:
                ai_message = ConversationMessage(
                    content=response["message"],
                    message_type=MessageType.AI_RESPONSE,
                    timestamp=datetime.utcnow()
                )
                context.conversation_history.append(ai_message)
            
            return {
                "session_id": session_id,
                "message": response.get("message", ""),
                "stage": context.current_stage.value,
                "mission_parameters": context.mission_parameters,
                "next_questions": await self._get_next_questions(context),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": response.get("metadata", {})
            }
            
        except Exception as e:
            print(f"Failed to process message: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_stage_message(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message based on current conversation stage"""
        stage = context.current_stage
        
        if stage == ConversationStage.MISSION_PLANNING:
            return await self._process_mission_planning_message(context, message)
        elif stage == ConversationStage.AREA_SELECTION:
            return await self._process_area_selection_message(context, message)
        elif stage == ConversationStage.PARAMETER_COLLECTION:
            return await self._process_parameter_collection_message(context, message)
        elif stage == ConversationStage.CONFIRMATION:
            return await self._process_confirmation_message(context, message)
        else:
            return {
                "message": "I'm not sure how to help with that. Let's start over with mission planning.",
                "metadata": {"stage_reset": True}
            }
    
    async def _process_mission_planning_message(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message in mission planning stage"""
        message_lower = message.lower()
        
        # Check for mission type
        if any(word in message_lower for word in ["search", "rescue", "survey", "training"]):
            if "search" in message_lower:
                context.mission_parameters["mission_type"] = "search"
            elif "rescue" in message_lower:
                context.mission_parameters["mission_type"] = "rescue"
            elif "survey" in message_lower:
                context.mission_parameters["mission_type"] = "survey"
            elif "training" in message_lower:
                context.mission_parameters["mission_type"] = "training"
            
            context.current_stage = ConversationStage.AREA_SELECTION
            return {
                "message": "Great! Now let's define the search area. Where would you like to conduct the search?",
                "metadata": {"stage_advanced": True}
            }
        
        # Check for priority level
        elif any(word in message_lower for word in ["low", "medium", "high", "critical"]):
            if "critical" in message_lower:
                context.mission_parameters["priority"] = "critical"
            elif "high" in message_lower:
                context.mission_parameters["priority"] = "high"
            elif "medium" in message_lower:
                context.mission_parameters["priority"] = "medium"
            elif "low" in message_lower:
                context.mission_parameters["priority"] = "low"
            
            return {
                "message": "Priority level noted. What type of mission are you planning?",
                "metadata": {"parameter_collected": "priority"}
            }
        
        # Default response
        return {
            "message": "I'd like to help you plan your mission. What type of mission are you planning? (search, rescue, survey, or training)",
            "metadata": {"clarification_needed": True}
        }
    
    async def _process_area_selection_message(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message in area selection stage"""
        # This is a simplified version - in reality, you'd use NLP to extract coordinates
        # For now, we'll just move to the next stage
        
        context.mission_parameters["search_area_description"] = message
        context.current_stage = ConversationStage.PARAMETER_COLLECTION
        
        return {
            "message": "Search area noted. Now let's configure the mission parameters. How many drones would you like to deploy?",
            "metadata": {"stage_advanced": True}
        }
    
    async def _process_parameter_collection_message(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message in parameter collection stage"""
        message_lower = message.lower()
        
        # Check for drone count
        if any(char.isdigit() for char in message):
            # Extract numbers from message
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                context.mission_parameters["max_drones"] = int(numbers[0])
        
        # Check for altitude
        if "altitude" in message_lower or "height" in message_lower:
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                context.mission_parameters["altitude"] = int(numbers[0])
        
        # Check for time limit
        if any(word in message_lower for word in ["hour", "minute", "time"]):
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                context.mission_parameters["time_limit_minutes"] = int(numbers[0]) * 60  # Convert to minutes
        
        # Move to confirmation if we have enough parameters
        if len(context.mission_parameters) >= 3:
            context.current_stage = ConversationStage.CONFIRMATION
            return {
                "message": "Excellent! Let me confirm the mission parameters before we proceed.",
                "metadata": {"ready_for_confirmation": True}
            }
        
        return {
            "message": "Got it! What altitude would you like for the search?",
            "metadata": {"parameter_collected": True}
        }
    
    async def _process_confirmation_message(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message in confirmation stage"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["yes", "confirm", "proceed", "start"]):
            context.current_stage = ConversationStage.EXECUTION
            return {
                "message": "Perfect! Mission confirmed. I'm now ready to execute the mission plan.",
                "metadata": {"mission_confirmed": True, "ready_for_execution": True}
            }
        elif any(word in message_lower for word in ["no", "cancel", "back", "change"]):
            context.current_stage = ConversationStage.PARAMETER_COLLECTION
            return {
                "message": "No problem! Let's modify the mission parameters. What would you like to change?",
                "metadata": {"mission_modified": True}
            }
        
        return {
            "message": "Please confirm if you'd like to proceed with this mission plan or make changes.",
            "metadata": {"confirmation_needed": True}
        }
    
    async def _get_next_questions(self, context: ConversationContext) -> List[str]:
        """Get next questions based on current stage and collected parameters"""
        stage = context.current_stage
        
        if stage in self.question_bank:
            questions = self.question_bank[stage]
            
            # Filter out questions for parameters we already have
            filtered_questions = []
            for question in questions:
                if "mission_type" in question.lower() and "mission_type" in context.mission_parameters:
                    continue
                if "priority" in question.lower() and "priority" in context.mission_parameters:
                    continue
                if "drone" in question.lower() and "max_drones" in context.mission_parameters:
                    continue
                if "altitude" in question.lower() and "altitude" in context.mission_parameters:
                    continue
                
                filtered_questions.append(question)
            
            return filtered_questions[:3]  # Return up to 3 questions
        
        return []
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of conversation and collected parameters"""
        if session_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        context = self.active_conversations[session_id]
        
        return {
            "session_id": session_id,
            "current_stage": context.current_stage.value,
            "mission_parameters": context.mission_parameters,
            "message_count": len(context.conversation_history),
            "conversation_duration": (
                context.conversation_history[-1].timestamp - 
                context.conversation_history[0].timestamp
            ).total_seconds() if len(context.conversation_history) > 1 else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        if session_id in self.active_conversations:
            context = self.active_conversations[session_id]
            
            # Save conversation data (in real implementation, save to database)
            summary = await self.get_conversation_summary(session_id)
            
            # Remove from active conversations
            del self.active_conversations[session_id]
            
            return {
                "session_id": session_id,
                "status": "ended",
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {"error": "Conversation not found"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of conversation engine"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "initialized": self.is_initialized,
            "active_conversations": len(self.active_conversations),
            "templates_loaded": len(self.conversation_templates),
            "questions_loaded": len(self.question_bank)
        }

# Global conversation engine instance
conversation_engine = ConversationEngine()