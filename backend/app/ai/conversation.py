"""
Conversation Engine for SAR Mission Commander
Handles natural language processing, chat interactions, and AI conversations using Ollama.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from app.ai.ollama_client import ollama_client
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    """Main conversation processing engine using real AI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the conversation engine"""
        try:
            # Test Ollama connection
            await ollama_client.health_check()
            
            self.is_initialized = True
            self.logger.info("✅ Conversation Engine initialized with Ollama")
            
        except Exception as e:
            self.logger.error(f"⚠️ Conversation Engine initialization failed: {e}")
            self.is_initialized = False
    
    async def start_conversation(self, session_id: str, initial_message: str = "") -> Dict[str, Any]:
        """
        Start a new conversation session using AI
        
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
            
            # Generate AI greeting using Ollama
            greeting_prompt = """
            You are an AI assistant for Search and Rescue (SAR) mission planning. 
            A user is starting a conversation about planning a SAR mission.
            
            Generate a friendly, professional greeting that:
            1. Welcomes them to the SAR Mission Commander
            2. Explains you're here to help plan their search and rescue operation
            3. Asks what type of mission they're planning (search, rescue, survey, training)
            4. Keeps it conversational and encouraging
            
            Respond in a natural, helpful tone. Don't use bullet points or formal lists.
            """
            
            ai_response = await ollama_client.generate(
                greeting_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.7
            )
            
            # Add AI response to history
            ai_message = ConversationMessage(
                content=ai_response.strip(),
                message_type=MessageType.AI_RESPONSE,
                timestamp=datetime.utcnow()
            )
            context.conversation_history.append(ai_message)
            
            # Move to mission planning stage
            context.current_stage = ConversationStage.MISSION_PLANNING
            
            return {
                "session_id": session_id,
                "message": ai_response.strip(),
                "stage": context.current_stage.value,
                "next_questions": await self._get_next_questions(context),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start conversation: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process a user message using AI analysis
        
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
            
            # Process the message using AI
            response = await self._process_with_ai(context, user_message)
            
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
            self.logger.error(f"Failed to process message: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_with_ai(self, context: ConversationContext, message: str) -> Dict[str, Any]:
        """Process message using AI analysis"""
        try:
            # Create conversation context for AI
            conversation_text = self._format_conversation_for_ai(context)
            
            # Create AI prompt
            ai_prompt = f"""
            You are an AI assistant for Search and Rescue (SAR) mission planning.
            
            Current conversation context:
            {conversation_text}
            
            User's latest message: "{message}"
            
            Your task:
            1. Analyze the user's message to extract mission information
            2. Respond naturally and helpfully
            3. Ask clarifying questions if needed
            4. Progress the conversation toward completing mission planning
            
            Extract and identify:
            - Mission type (search, rescue, survey, training)
            - Priority level (low, medium, high, critical)
            - Location/area information
            - Number of drones needed
            - Altitude preferences
            - Time constraints
            - Any other relevant parameters
            
            Respond in a conversational, helpful tone. If you extract new information, 
            acknowledge it and ask for the next piece of information needed.
            
            Current stage: {context.current_stage.value}
            Current parameters: {json.dumps(context.mission_parameters, indent=2)}
            """
            
            # Get AI response
            ai_response = await ollama_client.generate(
                ai_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.7
            )
            
            # Extract structured information using AI
            extraction_prompt = f"""
            Extract structured mission information from this user message: "{message}"
            
            Return a JSON response with:
            {{
                "mission_type": "search|rescue|survey|training|null",
                "priority": "low|medium|high|critical|null",
                "location": "extracted location info or null",
                "drone_count": "number or null",
                "altitude": "number in meters or null",
                "time_limit": "number in minutes or null",
                "other_parameters": {{"key": "value"}},
                "stage_advancement": "true|false",
                "next_stage": "next stage name or current stage"
            }}
            
            Only include parameters that are clearly mentioned or can be reasonably inferred.
            """
            
            extraction_response = await ollama_client.generate(
                extraction_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            # Parse extraction results
            try:
                extracted_info = json.loads(extraction_response)
                await self._update_mission_parameters(context, extracted_info)
                
                # Update stage if needed
                if extracted_info.get("stage_advancement") and extracted_info.get("next_stage"):
                    try:
                        context.current_stage = ConversationStage(extracted_info["next_stage"])
                    except ValueError:
                        pass  # Invalid stage name, keep current
                
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse AI extraction response")
            
            return {
                "message": ai_response.strip(),
                "metadata": {
                    "ai_processed": True,
                    "extracted_parameters": extracted_info if 'extracted_info' in locals() else {}
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI processing: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your message right now. Could you please try again?",
                "metadata": {"error": str(e)}
            }
    
    async def _update_mission_parameters(self, context: ConversationContext, extracted_info: Dict[str, Any]) -> None:
        """Update mission parameters with extracted information"""
        try:
            # Update mission type
            if extracted_info.get("mission_type") and extracted_info["mission_type"] != "null":
                context.mission_parameters["mission_type"] = extracted_info["mission_type"]
            
            # Update priority
            if extracted_info.get("priority") and extracted_info["priority"] != "null":
                context.mission_parameters["priority"] = extracted_info["priority"]
            
            # Update location
            if extracted_info.get("location") and extracted_info["location"] != "null":
                context.mission_parameters["location"] = extracted_info["location"]
            
            # Update drone count
            if extracted_info.get("drone_count") and extracted_info["drone_count"] != "null":
                try:
                    context.mission_parameters["drone_count"] = int(extracted_info["drone_count"])
                except ValueError:
                    pass
            
            # Update altitude
            if extracted_info.get("altitude") and extracted_info["altitude"] != "null":
                try:
                    context.mission_parameters["altitude"] = int(extracted_info["altitude"])
                except ValueError:
                    pass
            
            # Update time limit
            if extracted_info.get("time_limit") and extracted_info["time_limit"] != "null":
                try:
                    context.mission_parameters["time_limit_minutes"] = int(extracted_info["time_limit"])
                except ValueError:
                    pass
            
            # Update other parameters
            if extracted_info.get("other_parameters"):
                context.mission_parameters.update(extracted_info["other_parameters"])
            
        except Exception as e:
            self.logger.error(f"Error updating mission parameters: {e}")
    
    def _format_conversation_for_ai(self, context: ConversationContext) -> str:
        """Format conversation history for AI context"""
        try:
            formatted_messages = []
            for msg in context.conversation_history[-10:]:  # Last 10 messages
                role = "User" if msg.message_type == MessageType.USER_INPUT else "Assistant"
                formatted_messages.append(f"{role}: {msg.content}")
            
            return "\n".join(formatted_messages)
            
        except Exception as e:
            self.logger.error(f"Error formatting conversation: {e}")
            return ""
    
    async def _get_next_questions(self, context: ConversationContext) -> List[str]:
        """Get next questions using AI analysis"""
        try:
            if not context.mission_parameters:
                return ["What type of mission are you planning?"]
            
            # Use AI to generate contextual questions
            question_prompt = f"""
            Based on this SAR mission planning conversation, generate 2-3 helpful follow-up questions.
            
            Current mission parameters: {json.dumps(context.mission_parameters, indent=2)}
            Current stage: {context.current_stage.value}
            
            Generate questions that:
            1. Fill in missing critical information
            2. Are specific to their mission type
            3. Help complete the mission planning
            4. Are conversational and natural
            
            Return as a JSON array of question strings.
            """
            
            ai_questions = await ollama_client.generate(
                question_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.6
            )
            
            try:
                questions = json.loads(ai_questions)
                return questions if isinstance(questions, list) else []
            except json.JSONDecodeError:
                # Fallback questions
                return [
                    "What's the priority level for this mission?",
                    "How many drones would you like to deploy?",
                    "What altitude should the drones fly at?"
                ]
            
        except Exception as e:
            self.logger.error(f"Error generating questions: {e}")
            return ["What else can I help you with for your mission?"]
    
    async def extract_mission_parameters(self, session_id: str) -> Dict[str, Any]:
        """Extract and return all mission parameters using AI"""
        try:
            if session_id not in self.active_conversations:
                return {"error": "Conversation not found"}
            
            context = self.active_conversations[session_id]
            
            # Use AI to analyze and structure all collected information
            analysis_prompt = f"""
            Analyze this SAR mission planning conversation and extract all mission parameters.
            
            Conversation history:
            {self._format_conversation_for_ai(context)}
            
            Current parameters: {json.dumps(context.mission_parameters, indent=2)}
            
            Return a comprehensive JSON response with:
            {{
                "mission_type": "search|rescue|survey|training",
                "priority": "low|medium|high|critical",
                "location": "detailed location information",
                "search_area": "coordinates or area description",
                "drone_count": "number of drones",
                "altitude": "flight altitude in meters",
                "duration": "mission duration in minutes",
                "weather_requirements": "any weather constraints",
                "safety_requirements": "safety considerations",
                "equipment_needs": "special equipment requirements",
                "timeline": "when the mission should be executed",
                "completeness_score": "0-100 score of how complete the plan is",
                "missing_information": ["list of missing critical information"],
                "recommendations": ["AI recommendations for the mission"]
            }}
            """
            
            ai_analysis = await ollama_client.generate(
                analysis_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            try:
                structured_parameters = json.loads(ai_analysis)
                return structured_parameters
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse AI analysis",
                    "raw_parameters": context.mission_parameters
                }
            
        except Exception as e:
            self.logger.error(f"Error extracting mission parameters: {e}")
            return {"error": str(e)}
    
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
            
            # Get final mission parameters using AI
            final_parameters = await self.extract_mission_parameters(session_id)
            
            # Save conversation data (in real implementation, save to database)
            summary = await self.get_conversation_summary(session_id)
            summary["final_parameters"] = final_parameters
            
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
        try:
            ollama_healthy = await ollama_client.health_check()
            return {
                "status": "healthy" if self.is_initialized and ollama_healthy else "unhealthy",
                "initialized": self.is_initialized,
                "ollama_connected": ollama_healthy,
                "active_conversations": len(self.active_conversations)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self.is_initialized,
                "active_conversations": len(self.active_conversations)
            }

# Global conversation engine instance
conversation_engine = ConversationEngine()

# Convenience functions
async def start_conversation(session_id: str, initial_message: str = "") -> Dict[str, Any]:
    """Start a new conversation"""
    return await conversation_engine.start_conversation(session_id, initial_message)

async def process_message(session_id: str, user_message: str) -> Dict[str, Any]:
    """Process a user message"""
    return await conversation_engine.process_message(session_id, user_message)

async def extract_mission_parameters(session_id: str) -> Dict[str, Any]:
    """Extract mission parameters from conversation"""
    return await conversation_engine.extract_mission_parameters(session_id)