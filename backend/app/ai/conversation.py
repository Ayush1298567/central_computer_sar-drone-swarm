"""
Conversational Mission Planner for SAR drone operations.

This module provides natural language mission planning through iterative
conversation, allowing operators to define missions through AI-guided dialogue.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, validator

from .llm_intelligence import LLMIntelligenceEngine, MissionContext, create_intelligence_engine


logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States of mission planning conversation."""
    INITIALIZING = "initializing"
    GATHERING_REQUIREMENTS = "gathering_requirements"
    CLARIFYING_DETAILS = "clarifying_details"
    VALIDATING_PLAN = "validating_plan"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageRole(Enum):
    """Roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QuestionType(Enum):
    """Types of clarifying questions."""
    SEARCH_AREA = "search_area"
    MISSION_TYPE = "mission_type"
    TIME_CONSTRAINTS = "time_constraints"
    WEATHER_CONSIDERATIONS = "weather_considerations"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITY_SETTINGS = "priority_settings"
    SAFETY_PARAMETERS = "safety_parameters"


@dataclass
class ConversationMessage:
    """A single message in the planning conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class MissionRequirement:
    """A specific mission requirement extracted from conversation."""
    category: str
    requirement: str
    value: Any
    confidence: float
    source_message_id: str
    validated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MissionPlan(BaseModel):
    """Complete mission plan generated through conversation."""
    mission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mission_type: str = Field(description="Type of SAR mission")
    search_area: Dict[str, Any] = Field(description="Search area definition")
    time_constraints: Dict[str, Any] = Field(description="Time limits and scheduling")
    resource_requirements: Dict[str, Any] = Field(description="Required resources")
    weather_parameters: Dict[str, Any] = Field(description="Weather considerations")
    safety_settings: Dict[str, Any] = Field(description="Safety parameters")
    priority_level: int = Field(description="Mission priority (1-10)", ge=1, le=10)
    estimated_duration: int = Field(description="Estimated duration in minutes")
    success_criteria: List[str] = Field(description="Mission success criteria")
    contingency_plans: List[str] = Field(description="Contingency procedures")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        
    def to_mission_context(self) -> MissionContext:
        """Convert to MissionContext for intelligence engine."""
        return MissionContext(
            mission_id=self.mission_id,
            mission_type=self.mission_type,
            search_area=self.search_area,
            weather_conditions=self.weather_parameters,
            available_drones=self.resource_requirements.get("drones", []),
            time_constraints=self.time_constraints,
            priority_level=self.priority_level,
            discovered_objects=[],
            current_progress=0.0
        )


@dataclass
class ConversationSession:
    """A complete conversation session for mission planning."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ConversationState = ConversationState.INITIALIZING
    messages: List[ConversationMessage] = field(default_factory=list)
    requirements: Dict[str, MissionRequirement] = field(default_factory=dict)
    current_plan: Optional[MissionPlan] = None
    pending_questions: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, message: ConversationMessage):
        """Add message to conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in LLM format."""
        history = []
        for msg in self.messages:
            if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        return history
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "requirements": {k: v.to_dict() for k, v in self.requirements.items()},
            "current_plan": self.current_plan.dict() if self.current_plan else None,
            "pending_questions": self.pending_questions,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConversationalMissionPlanner:
    """
    AI-powered conversational mission planner.
    
    Guides operators through mission planning using natural language
    conversation with intelligent question generation and requirement extraction.
    """
    
    def __init__(
        self,
        intelligence_engine: Optional[LLMIntelligenceEngine] = None,
        max_conversation_turns: int = 20,
        requirement_confidence_threshold: float = 0.7
    ):
        """
        Initialize conversational mission planner.
        
        Args:
            intelligence_engine: LLM intelligence engine for conversation
            max_conversation_turns: Maximum conversation turns before timeout
            requirement_confidence_threshold: Minimum confidence for requirements
        """
        self.intelligence_engine = intelligence_engine
        self.max_turns = max_conversation_turns
        self.confidence_threshold = requirement_confidence_threshold
        self.active_sessions: Dict[str, ConversationSession] = {}
        
        # Essential mission parameters that must be gathered
        self.essential_parameters = {
            "mission_type": "What type of search and rescue mission is this?",
            "search_area": "Where should the drones search?",
            "time_constraints": "Are there any time limitations or deadlines?",
            "priority_level": "What is the urgency level of this mission?",
            "weather_considerations": "What are the current weather conditions?",
            "resource_requirements": "How many drones are available for this mission?"
        }
        
        logger.info("Conversational Mission Planner initialized")
        
    async def start_conversation(
        self,
        initial_message: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """
        Start a new mission planning conversation.
        
        Args:
            initial_message: User's initial message
            user_context: Additional context about the user/situation
            
        Returns:
            New conversation session
        """
        session = ConversationSession()
        session.context.update(user_context or {})
        
        # Add initial user message
        user_msg = ConversationMessage(
            role=MessageRole.USER,
            content=initial_message
        )
        session.add_message(user_msg)
        
        # Generate initial response
        response = await self._generate_response(session)
        session.state = ConversationState.GATHERING_REQUIREMENTS
        
        self.active_sessions[session.session_id] = session
        logger.info(f"Started conversation session {session.session_id}")
        
        return session
        
    async def continue_conversation(
        self,
        session_id: str,
        user_message: str
    ) -> ConversationSession:
        """
        Continue an existing conversation.
        
        Args:
            session_id: ID of conversation session
            user_message: User's message
            
        Returns:
            Updated conversation session
            
        Raises:
            ValueError: If session not found
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        if session.state in [ConversationState.COMPLETED, ConversationState.CANCELLED]:
            raise ValueError(f"Session {session_id} is already {session.state.value}")
            
        # Add user message
        user_msg = ConversationMessage(
            role=MessageRole.USER,
            content=user_message
        )
        session.add_message(user_msg)
        
        # Process message and generate response
        await self._process_user_message(session, user_message)
        response = await self._generate_response(session)
        
        # Update session state
        await self._update_conversation_state(session)
        
        logger.info(f"Continued conversation {session_id}, state: {session.state.value}")
        return session
        
    async def _process_user_message(
        self,
        session: ConversationSession,
        message: str
    ):
        """Extract requirements and information from user message."""
        if not self.intelligence_engine:
            return
            
        system_prompt = """You are a SAR mission planning assistant. Extract specific mission requirements from user messages. Identify concrete parameters, constraints, and preferences."""
        
        extraction_prompt = f"""
Analyze this user message for SAR mission planning requirements:
"{message}"

Previous conversation context:
{json.dumps([msg.content for msg in session.messages[-5:]], indent=2)}

Extract any specific requirements in these categories:
- mission_type: Type of SAR operation
- search_area: Location, coordinates, size, boundaries
- time_constraints: Deadlines, duration limits, scheduling
- priority_level: Urgency (1-10 scale)
- weather_considerations: Weather conditions, constraints
- resource_requirements: Number of drones, equipment needs
- safety_parameters: Safety constraints, no-fly zones
- success_criteria: What defines mission success

For each requirement found, provide:
1. Category (from list above)
2. Specific requirement description
3. Extracted value/parameter
4. Confidence level (0.0-1.0)

Respond in JSON format:
{{
    "requirements": [
        {{
            "category": "string",
            "requirement": "string", 
            "value": "any",
            "confidence": "number"
        }}
    ]
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": extraction_prompt}
        ]
        
        try:
            response = await self.intelligence_engine._generate_response(messages)
            extraction_data = json.loads(response)
            
            # Process extracted requirements
            for req_data in extraction_data.get("requirements", []):
                if req_data["confidence"] >= self.confidence_threshold:
                    requirement = MissionRequirement(
                        category=req_data["category"],
                        requirement=req_data["requirement"],
                        value=req_data["value"],
                        confidence=req_data["confidence"],
                        source_message_id=session.messages[-1].id
                    )
                    
                    session.requirements[requirement.category] = requirement
                    
        except Exception as e:
            logger.error(f"Requirement extraction failed: {e}")
            
    async def _generate_response(self, session: ConversationSession) -> ConversationMessage:
        """Generate AI response for current conversation state."""
        if not self.intelligence_engine:
            # Fallback response without AI
            response_msg = ConversationMessage(
                role=MessageRole.ASSISTANT,
                content="I understand. Can you provide more details about your search and rescue mission requirements?"
            )
            session.add_message(response_msg)
            return response_msg
            
        # Determine what information is still needed
        missing_params = []
        for param, question in self.essential_parameters.items():
            if param not in session.requirements:
                missing_params.append(param)
                
        # Generate contextual response
        if session.state == ConversationState.GATHERING_REQUIREMENTS:
            response = await self._generate_gathering_response(session, missing_params)
        elif session.state == ConversationState.CLARIFYING_DETAILS:
            response = await self._generate_clarifying_response(session)
        elif session.state == ConversationState.VALIDATING_PLAN:
            response = await self._generate_validation_response(session)
        else:
            response = await self._generate_general_response(session)
            
        response_msg = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=response
        )
        session.add_message(response_msg)
        return response_msg
        
    async def _generate_gathering_response(
        self,
        session: ConversationSession,
        missing_params: List[str]
    ) -> str:
        """Generate response for requirement gathering phase."""
        system_prompt = """You are a SAR mission planning assistant. Guide the conversation to gather essential mission parameters through natural, intelligent questions. Be conversational but focused."""
        
        # Build context about what we know and need
        known_requirements = []
        for req in session.requirements.values():
            known_requirements.append(f"- {req.category}: {req.requirement}")
            
        missing_info = []
        for param in missing_params[:3]:  # Focus on top 3 missing items
            missing_info.append(f"- {param}: {self.essential_parameters[param]}")
            
        conversation_history = session.get_conversation_history()
        
        user_prompt = f"""
Current conversation with user planning a SAR mission:
{json.dumps(conversation_history, indent=2)}

Information gathered so far:
{chr(10).join(known_requirements) if known_requirements else "None yet"}

Still need to understand:
{chr(10).join(missing_info)}

Generate a natural, conversational response that:
1. Acknowledges what the user has told you
2. Asks about the most critical missing information
3. Provides helpful context or examples if needed
4. Keeps the conversation flowing naturally

Be concise but thorough. Ask only 1-2 questions at a time to avoid overwhelming the user.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.intelligence_engine._generate_response(messages)
            return response.strip()
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback to simple question
            if missing_params:
                param = missing_params[0]
                return self.essential_parameters[param]
            return "Can you tell me more about your mission requirements?"
            
    async def _generate_clarifying_response(self, session: ConversationSession) -> str:
        """Generate response for detail clarification phase."""
        system_prompt = """You are a SAR mission planning assistant in the clarification phase. Ask specific questions to refine and validate mission parameters."""
        
        # Find requirements that need clarification
        unclear_requirements = []
        for req in session.requirements.values():
            if req.confidence < 0.9 or not req.validated:
                unclear_requirements.append(req)
                
        user_prompt = f"""
Mission requirements that need clarification:
{json.dumps([req.to_dict() for req in unclear_requirements], indent=2)}

Current conversation:
{json.dumps(session.get_conversation_history()[-6:], indent=2)}

Ask specific clarifying questions to:
1. Validate uncertain requirements
2. Get precise parameters (coordinates, times, quantities)
3. Identify potential conflicts or issues
4. Ensure safety considerations are addressed

Focus on the most critical uncertainties first.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.intelligence_engine._generate_response(messages)
            return response.strip()
        except Exception as e:
            logger.error(f"Clarifying response generation failed: {e}")
            return "Let me clarify a few details to ensure we have an accurate mission plan."
            
    async def _generate_validation_response(self, session: ConversationSession) -> str:
        """Generate response for plan validation phase."""
        if not session.current_plan:
            return "I'm preparing your mission plan for review..."
            
        system_prompt = """You are a SAR mission planning assistant presenting a complete mission plan for user validation. Summarize the plan clearly and ask for confirmation."""
        
        user_prompt = f"""
Present this complete SAR mission plan to the user for validation:
{session.current_plan.json(indent=2)}

Conversation context:
{json.dumps(session.get_conversation_history()[-4:], indent=2)}

Create a clear, structured summary of the mission plan including:
1. Mission overview
2. Key parameters (area, time, resources)
3. Safety considerations
4. Success criteria

Ask the user to confirm the plan or request changes. Be specific about what you're asking them to validate.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.intelligence_engine._generate_response(messages)
            return response.strip()
        except Exception as e:
            logger.error(f"Validation response generation failed: {e}")
            return f"Here's your mission plan: {session.current_plan.mission_type} mission. Please review and confirm if this looks correct."
            
    async def _generate_general_response(self, session: ConversationSession) -> str:
        """Generate general contextual response."""
        system_prompt = """You are a SAR mission planning assistant. Provide helpful, contextual responses to guide mission planning."""
        
        user_prompt = f"""
Current conversation state: {session.state.value}
Recent messages:
{json.dumps(session.get_conversation_history()[-4:], indent=2)}

Provide an appropriate response to continue the mission planning conversation.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self.intelligence_engine._generate_response(messages)
            return response.strip()
        except Exception as e:
            logger.error(f"General response generation failed: {e}")
            return "I'm here to help you plan your SAR mission. What would you like to discuss?"
            
    async def _update_conversation_state(self, session: ConversationSession):
        """Update conversation state based on current progress."""
        # Check if we have enough information to create a plan
        essential_count = len([param for param in self.essential_parameters.keys() 
                             if param in session.requirements])
        
        if session.state == ConversationState.GATHERING_REQUIREMENTS:
            if essential_count >= len(self.essential_parameters) * 0.8:  # 80% of essential params
                session.state = ConversationState.CLARIFYING_DETAILS
                
        elif session.state == ConversationState.CLARIFYING_DETAILS:
            # Check if requirements are sufficiently confident
            high_confidence_count = len([req for req in session.requirements.values() 
                                       if req.confidence >= 0.8])
            
            if high_confidence_count >= len(session.requirements) * 0.9:
                session.state = ConversationState.VALIDATING_PLAN
                await self._create_mission_plan(session)
                
        elif session.state == ConversationState.VALIDATING_PLAN:
            # Check for user confirmation in recent messages
            last_message = session.messages[-2] if len(session.messages) >= 2 else None
            if last_message and last_message.role == MessageRole.USER:
                content_lower = last_message.content.lower()
                if any(word in content_lower for word in ["yes", "confirm", "approve", "looks good", "correct"]):
                    session.state = ConversationState.FINALIZING
                elif any(word in content_lower for word in ["no", "change", "modify", "different"]):
                    session.state = ConversationState.CLARIFYING_DETAILS
                    
        # Check for conversation timeout
        if len(session.messages) > self.max_turns:
            logger.warning(f"Session {session.session_id} exceeded max turns")
            session.state = ConversationState.CANCELLED
            
    async def _create_mission_plan(self, session: ConversationSession):
        """Create complete mission plan from gathered requirements."""
        try:
            # Extract values from requirements
            mission_data = {}
            
            for req in session.requirements.values():
                if req.category == "mission_type":
                    mission_data["mission_type"] = req.value
                elif req.category == "search_area":
                    mission_data["search_area"] = self._parse_search_area(req.value)
                elif req.category == "time_constraints":
                    mission_data["time_constraints"] = self._parse_time_constraints(req.value)
                elif req.category == "priority_level":
                    mission_data["priority_level"] = self._parse_priority(req.value)
                elif req.category == "weather_considerations":
                    mission_data["weather_parameters"] = self._parse_weather(req.value)
                elif req.category == "resource_requirements":
                    mission_data["resource_requirements"] = self._parse_resources(req.value)
                elif req.category == "safety_parameters":
                    mission_data["safety_settings"] = self._parse_safety(req.value)
                    
            # Set defaults for missing fields
            mission_data.setdefault("mission_type", "general_search")
            mission_data.setdefault("search_area", {"type": "polygon", "coordinates": []})
            mission_data.setdefault("time_constraints", {"max_duration_minutes": 120})
            mission_data.setdefault("resource_requirements", {"drones": []})
            mission_data.setdefault("weather_parameters", {"conditions": "unknown"})
            mission_data.setdefault("safety_settings", {"max_wind_speed": 15})
            mission_data.setdefault("priority_level", 5)
            mission_data.setdefault("estimated_duration", 60)
            mission_data.setdefault("success_criteria", ["Complete search coverage"])
            mission_data.setdefault("contingency_plans", ["Return to base if weather deteriorates"])
            
            session.current_plan = MissionPlan(**mission_data)
            logger.info(f"Created mission plan for session {session.session_id}")
            
        except Exception as e:
            logger.error(f"Mission plan creation failed: {e}")
            # Create basic plan with available information
            session.current_plan = MissionPlan(
                mission_type="general_search",
                search_area={"type": "polygon", "coordinates": []},
                time_constraints={"max_duration_minutes": 120},
                resource_requirements={"drones": []},
                weather_parameters={"conditions": "unknown"},
                safety_settings={"max_wind_speed": 15},
                priority_level=5,
                estimated_duration=60,
                success_criteria=["Complete search coverage"],
                contingency_plans=["Return to base if weather deteriorates"]
            )
            
    def _parse_search_area(self, value: Any) -> Dict[str, Any]:
        """Parse search area from requirement value."""
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"description": value, "type": "description"}
        else:
            return {"type": "polygon", "coordinates": []}
            
    def _parse_time_constraints(self, value: Any) -> Dict[str, Any]:
        """Parse time constraints from requirement value."""
        if isinstance(value, dict):
            return value
        elif isinstance(value, (int, float)):
            return {"max_duration_minutes": int(value)}
        else:
            return {"max_duration_minutes": 120}
            
    def _parse_priority(self, value: Any) -> int:
        """Parse priority level from requirement value."""
        if isinstance(value, int):
            return max(1, min(10, value))
        elif isinstance(value, str):
            priority_map = {
                "low": 3, "medium": 5, "high": 7, "critical": 9,
                "urgent": 8, "routine": 2, "emergency": 10
            }
            return priority_map.get(value.lower(), 5)
        else:
            return 5
            
    def _parse_weather(self, value: Any) -> Dict[str, Any]:
        """Parse weather parameters from requirement value."""
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"description": value}
        else:
            return {"conditions": "unknown"}
            
    def _parse_resources(self, value: Any) -> Dict[str, Any]:
        """Parse resource requirements from requirement value."""
        if isinstance(value, dict):
            return value
        elif isinstance(value, int):
            return {"drone_count": value, "drones": []}
        else:
            return {"drones": []}
            
    def _parse_safety(self, value: Any) -> Dict[str, Any]:
        """Parse safety settings from requirement value."""
        if isinstance(value, dict):
            return value
        else:
            return {"max_wind_speed": 15, "min_visibility": 1000}
            
    async def finalize_mission(self, session_id: str) -> Optional[MissionPlan]:
        """
        Finalize mission plan and complete conversation.
        
        Args:
            session_id: ID of conversation session
            
        Returns:
            Finalized mission plan or None if not ready
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None
            
        if session.state != ConversationState.VALIDATING_PLAN or not session.current_plan:
            return None
            
        session.state = ConversationState.COMPLETED
        
        # Add completion message
        completion_msg = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Mission plan finalized successfully. Your SAR mission is ready to begin."
        )
        session.add_message(completion_msg)
        
        logger.info(f"Finalized mission plan for session {session_id}")
        return session.current_plan
        
    async def cancel_conversation(self, session_id: str) -> bool:
        """
        Cancel conversation session.
        
        Args:
            session_id: ID of session to cancel
            
        Returns:
            True if cancelled successfully
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
            
        session.state = ConversationState.CANCELLED
        
        # Add cancellation message
        cancel_msg = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Mission planning conversation has been cancelled."
        )
        session.add_message(cancel_msg)
        
        logger.info(f"Cancelled conversation session {session_id}")
        return True
        
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID."""
        return self.active_sessions.get(session_id)
        
    def list_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_sessions.keys())
        
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old conversation sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.updated_at < cutoff_time:
                sessions_to_remove.append(session_id)
                
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up old session {session_id}")
            
        return len(sessions_to_remove)


# Utility functions
async def create_mission_planner(
    config: Optional[Dict[str, Any]] = None
) -> ConversationalMissionPlanner:
    """
    Create and configure conversational mission planner.
    
    Args:
        config: Configuration parameters
        
    Returns:
        Configured mission planner
    """
    config = config or {}
    
    # Create intelligence engine if not provided
    intelligence_engine = None
    if config.get("enable_ai", True):
        try:
            intelligence_engine = await create_intelligence_engine(config.get("ai_config", {}))
        except Exception as e:
            logger.warning(f"Failed to create intelligence engine: {e}")
            
    planner = ConversationalMissionPlanner(
        intelligence_engine=intelligence_engine,
        max_conversation_turns=config.get("max_turns", 20),
        requirement_confidence_threshold=config.get("confidence_threshold", 0.7)
    )
    
    return planner


# Example conversation flow for testing
async def test_conversation_flow():
    """Test the conversation flow with sample interactions."""
    planner = await create_mission_planner()
    
    # Start conversation
    session = await planner.start_conversation(
        "I need to set up a search mission for a missing hiker in the mountains."
    )
    
    print(f"Started session {session.session_id}")
    print(f"AI: {session.messages[-1].content}")
    
    # Continue conversation
    responses = [
        "The hiker was last seen near Mount Wilson, about 5 square kilometers to search.",
        "We have 3 drones available and need to find them before dark - about 4 hours from now.",
        "Weather is clear but windy, around 20 mph gusts. This is high priority.",
        "Yes, that plan looks good. Let's proceed."
    ]
    
    for response in responses:
        session = await planner.continue_conversation(session.session_id, response)
        print(f"User: {response}")
        print(f"AI: {session.messages[-1].content}")
        print(f"State: {session.state.value}")
        print("---")
        
        if session.state == ConversationState.COMPLETED:
            break
            
    # Finalize mission
    if session.current_plan:
        final_plan = await planner.finalize_mission(session.session_id)
        print(f"Final plan: {final_plan.mission_type}")
        return final_plan
        
    return None


if __name__ == "__main__":
    # Run test conversation
    asyncio.run(test_conversation_flow())