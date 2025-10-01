"""
Conversational Mission Planner for natural language mission planning
"""
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from .ollama_client import OllamaClient
from .ollama_intelligence import OllamaIntelligenceEngine, MissionContext, create_ollama_intelligence_engine
from ..core.config import settings
from ..models.chat import ChatSession, ChatMessage
from ..models.mission import Mission, MissionType, MissionStatus

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Current state of the conversation"""
    session_id: str
    current_step: str
    extracted_data: Dict[str, Any]
    missing_parameters: List[str]
    next_questions: List[str]
    is_complete: bool


@dataclass
class MissionPlan:
    """Complete mission plan generated from conversation"""
    mission_name: str
    mission_type: MissionType
    search_area: Dict[str, Any]
    priority: int
    max_flight_time: int
    search_altitude: float
    weather_thresholds: Dict[str, Any]
    estimated_duration: int
    required_drones: int
    risk_assessment: Dict[str, Any]
    search_strategy: Dict[str, Any]


class ConversationalMissionPlanner:
    """Natural language mission planning using AI conversation"""
    
    def __init__(self, client: OllamaClient = None, intelligence_engine: OllamaIntelligenceEngine = None):
        self.client = client or OllamaClient()
        self.intelligence_engine = intelligence_engine or OllamaIntelligenceEngine()
        self.model = settings.OLLAMA_MODEL
        
        # Conversation templates and parameters
        self.required_parameters = {
            "mission_type": ["missing_person", "emergency_response", "surveillance", "delivery", "mapping"],
            "search_area": ["size", "location", "terrain_type"],
            "priority": ["1-10 scale"],
            "time_constraints": ["urgency", "deadline"],
            "weather_conditions": ["wind_speed", "visibility", "precipitation"],
            "resource_requirements": ["drone_count", "specialized_equipment"]
        }
        
        self.conversation_prompts = self._load_conversation_prompts()
    
    def _load_conversation_prompts(self) -> Dict[str, str]:
        """Load conversation prompts for different planning steps"""
        return {
            "system": """You are an expert SAR mission planning assistant. Your role is to help users plan search and rescue missions through natural conversation.

            You should:
            1. Ask clarifying questions to gather mission requirements
            2. Extract key parameters from user responses
            3. Identify missing information and ask follow-up questions
            4. Provide expert guidance on mission planning
            5. Confirm understanding before finalizing plans
            
            Be conversational, professional, and thorough. Focus on safety and mission effectiveness.
            """,
            
            "greeting": """Hello! I'm your SAR mission planning assistant. I'll help you plan a search and rescue operation step by step.

            To get started, please tell me:
            - What type of mission you're planning (missing person, emergency response, surveillance, etc.)
            - Any specific details you already know about the situation
            
            I'll ask questions to gather all the necessary information for a successful mission plan.""",
            
            "parameter_extraction": """Extract the following mission parameters from the user's message:

            1. Mission type (missing_person, emergency_response, surveillance, delivery, mapping)
            2. Search area details (size, location, terrain)
            3. Priority level (1-10 scale)
            4. Time constraints and urgency
            5. Weather conditions
            6. Resource requirements
            7. Any special considerations
            
            Return as JSON with extracted parameters and any missing information that needs clarification.""",
            
            "follow_up": """Based on the conversation so far, ask 1-2 specific follow-up questions to gather missing mission parameters.

            Focus on:
            - Critical missing information for mission planning
            - Safety-related parameters
            - Resource allocation needs
            - Time-sensitive constraints
            
            Be specific and helpful in your questions.""",
            
            "plan_confirmation": """Present the complete mission plan for user confirmation:

            Include:
            1. Mission summary and objectives
            2. Search area and approach
            3. Resource allocation
            4. Risk assessment
            5. Estimated timeline
            6. Success probability
            
            Ask for confirmation or any modifications before finalizing."""
        }
    
    async def start_conversation(self, initial_message: str, user_id: str = "default") -> Dict[str, Any]:
        """Start a new mission planning conversation"""
        try:
            # Create new session
            session_id = str(uuid.uuid4())
            
            # Analyze initial message
            async with self.client as client:
                analysis_response = await client.generate_text(
                    model=self.model,
                    prompt=f"""
                    Initial user message: "{initial_message}"
                    
                    Analyze this message and provide:
                    1. Detected mission type or intent
                    2. Any specific parameters mentioned
                    3. Questions needed for clarification
                    4. Suggested next steps
                    
                    Format as JSON with clear categories.
                    """,
                    system=self.conversation_prompts["system"]
                )
            
            analysis_text = analysis_response.get("response", "")
            
            # Extract initial parameters
            extracted_data = self._extract_parameters_from_text(initial_message)
            missing_parameters = self._identify_missing_parameters(extracted_data)
            
            # Generate initial response
            if not extracted_data.get("mission_type"):
                response = self.conversation_prompts["greeting"]
                next_questions = ["What type of mission are you planning?", "What specific situation requires SAR assistance?"]
            else:
                response = await self._generate_contextual_response(
                    initial_message, extracted_data, missing_parameters
                )
                next_questions = self._generate_follow_up_questions(missing_parameters)
            
            # Create conversation state
            conversation_state = ConversationState(
                session_id=session_id,
                current_step="initial_planning",
                extracted_data=extracted_data,
                missing_parameters=missing_parameters,
                next_questions=next_questions,
                is_complete=False
            )
            
            return {
                "session_id": session_id,
                "response": response,
                "conversation_state": conversation_state.__dict__,
                "next_questions": next_questions,
                "extracted_parameters": extracted_data,
                "missing_parameters": missing_parameters
            }
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            return {
                "session_id": str(uuid.uuid4()),
                "response": "I apologize, but I'm having trouble starting the mission planning conversation. Please try again.",
                "error": str(e)
            }
    
    async def continue_conversation(
        self, 
        session_id: str, 
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Continue an existing conversation"""
        try:
            # Build conversation context
            messages = conversation_history or []
            messages.append({"role": "user", "content": user_message})
            
            # Extract parameters from new message
            new_parameters = self._extract_parameters_from_text(user_message)
            
            # Update conversation state (in real implementation, this would come from database)
            current_state = await self._get_conversation_state(session_id)
            if not current_state:
                return {"error": "Session not found"}
            
            # Merge new parameters
            current_state["extracted_data"].update(new_parameters)
            
            # Check if conversation is complete
            missing_params = self._identify_missing_parameters(current_state["extracted_data"])
            
            if not missing_params:
                # Generate final mission plan
                mission_plan = await self._generate_mission_plan(current_state["extracted_data"])
                
                # Generate confirmation response
                async with self.client as client:
                    confirmation_response = await client.generate_text(
                        model=self.model,
                        prompt=f"""
                        Generate a confirmation message for this mission plan:
                        
                        Mission Plan:
                        {json.dumps(mission_plan.__dict__, indent=2, default=str)}
                        
                        Present the plan professionally and ask for confirmation.
                        """,
                        system=self.conversation_prompts["plan_confirmation"]
                    )
                
                return {
                    "session_id": session_id,
                    "response": confirmation_response.get("response", "Mission plan ready for confirmation."),
                    "conversation_state": {
                        **current_state,
                        "is_complete": True
                    },
                    "mission_plan": mission_plan.__dict__,
                    "next_action": "confirmation"
                }
            else:
                # Generate follow-up questions
                response = await self._generate_follow_up_response(
                    user_message, current_state["extracted_data"], missing_params
                )
                
                return {
                    "session_id": session_id,
                    "response": response,
                    "conversation_state": current_state,
                    "next_questions": self._generate_follow_up_questions(missing_params),
                    "missing_parameters": missing_params
                }
                
        except Exception as e:
            logger.error(f"Failed to continue conversation: {e}")
            return {
                "session_id": session_id,
                "response": "I apologize, but I'm having trouble processing your message. Please try rephrasing your request.",
                "error": str(e)
            }
    
    async def finalize_mission_plan(self, session_id: str, user_confirmation: str) -> Dict[str, Any]:
        """Finalize mission plan based on user confirmation"""
        try:
            # Get final conversation state
            conversation_state = await self._get_conversation_state(session_id)
            if not conversation_state:
                return {"error": "Session not found"}
            
            # Generate final mission plan
            mission_plan = await self._generate_mission_plan(conversation_state["extracted_data"])
            
            # Create mission in database (placeholder)
            mission_data = {
                "name": mission_plan.mission_name,
                "mission_type": mission_plan.mission_type,
                "status": MissionStatus.PLANNING,
                "search_area": mission_plan.search_area,
                "priority": mission_plan.priority,
                "max_flight_time": mission_plan.max_flight_time,
                "search_altitude": mission_plan.search_altitude,
                "weather_thresholds": mission_plan.weather_thresholds,
                "estimated_duration": mission_plan.estimated_duration,
                "search_strategy": mission_plan.search_strategy,
                "risk_assessment": mission_plan.risk_assessment
            }
            
            return {
                "session_id": session_id,
                "mission_plan": mission_plan.__dict__,
                "mission_data": mission_data,
                "status": "completed",
                "message": "Mission plan has been finalized and is ready for execution."
            }
            
        except Exception as e:
            logger.error(f"Failed to finalize mission plan: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "status": "failed"
            }
    
    def _extract_parameters_from_text(self, text: str) -> Dict[str, Any]:
        """Extract mission parameters from natural language text"""
        parameters = {}
        text_lower = text.lower()
        
        # Mission type detection
        if any(word in text_lower for word in ["missing person", "lost person", "search for"]):
            parameters["mission_type"] = "missing_person"
        elif any(word in text_lower for word in ["emergency", "rescue", "urgent"]):
            parameters["mission_type"] = "emergency_response"
        elif any(word in text_lower for word in ["surveillance", "monitor", "watch"]):
            parameters["mission_type"] = "surveillance"
        elif any(word in text_lower for word in ["delivery", "transport", "supply"]):
            parameters["mission_type"] = "delivery"
        elif any(word in text_lower for word in ["mapping", "survey", "scan"]):
            parameters["mission_type"] = "mapping"
        
        # Priority detection
        if any(word in text_lower for word in ["urgent", "critical", "emergency"]):
            parameters["priority"] = 9
        elif any(word in text_lower for word in ["high priority", "important"]):
            parameters["priority"] = 7
        elif any(word in text_lower for word in ["medium", "normal"]):
            parameters["priority"] = 5
        elif any(word in text_lower for word in ["low priority", "routine"]):
            parameters["priority"] = 3
        
        # Size detection
        import re
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kilometer|square km)', text_lower)
        if size_match:
            parameters["search_area"] = {"size_km2": float(size_match.group(1))}
        
        # Time detection
        time_match = re.search(r'(\d+)\s*(?:hour|minute)', text_lower)
        if time_match:
            parameters["time_constraints"] = {"urgency": "time_sensitive"}
        
        return parameters
    
    def _identify_missing_parameters(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Identify missing required parameters"""
        missing = []
        
        if not extracted_data.get("mission_type"):
            missing.append("mission_type")
        
        if not extracted_data.get("search_area"):
            missing.append("search_area")
        
        if not extracted_data.get("priority"):
            missing.append("priority")
        
        if not extracted_data.get("time_constraints"):
            missing.append("time_constraints")
        
        return missing
    
    def _generate_follow_up_questions(self, missing_parameters: List[str]) -> List[str]:
        """Generate follow-up questions for missing parameters"""
        questions = []
        
        for param in missing_parameters:
            if param == "mission_type":
                questions.append("What type of mission are you planning? (missing person, emergency response, surveillance, etc.)")
            elif param == "search_area":
                questions.append("What is the size and location of the search area?")
            elif param == "priority":
                questions.append("What is the priority level for this mission? (1-10 scale)")
            elif param == "time_constraints":
                questions.append("Are there any time constraints or deadlines for this mission?")
        
        return questions[:2]  # Limit to 2 questions at a time
    
    async def _generate_contextual_response(
        self, 
        user_message: str, 
        extracted_data: Dict[str, Any], 
        missing_parameters: List[str]
    ) -> str:
        """Generate contextual response based on current state"""
        try:
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=f"""
                    User message: "{user_message}"
                    
                    Extracted parameters: {json.dumps(extracted_data, indent=2)}
                    Missing parameters: {missing_parameters}
                    
                    Generate a helpful response that:
                    1. Acknowledges what the user has shared
                    2. Asks for the most important missing information
                    3. Provides guidance if appropriate
                    
                    Be conversational and professional.
                    """,
                    system=self.conversation_prompts["system"]
                )
            
            return response.get("response", "Thank you for that information. Let me ask a few more questions to complete the mission plan.")
            
        except Exception as e:
            logger.error(f"Failed to generate contextual response: {e}")
            return "Thank you for that information. Let me ask a few more questions to complete the mission plan."
    
    async def _generate_follow_up_response(
        self, 
        user_message: str, 
        extracted_data: Dict[str, Any], 
        missing_parameters: List[str]
    ) -> str:
        """Generate follow-up response for continuing conversation"""
        try:
            async with self.client as client:
                response = await client.generate_text(
                    model=self.model,
                    prompt=f"""
                    User message: "{user_message}"
                    
                    Current extracted data: {json.dumps(extracted_data, indent=2)}
                    Still missing: {missing_parameters}
                    
                    Generate a follow-up response that asks for the next most important missing information.
                    """,
                    system=self.conversation_prompts["follow_up"]
                )
            
            return response.get("response", "I need a bit more information to complete your mission plan.")
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up response: {e}")
            return "I need a bit more information to complete your mission plan."
    
    async def _generate_mission_plan(self, extracted_data: Dict[str, Any]) -> MissionPlan:
        """Generate complete mission plan from extracted data"""
        # Use intelligence engine to analyze and plan
        context = MissionContext(
            mission_id="planning-session",
            mission_type=extracted_data.get("mission_type", "missing_person"),
            search_area=extracted_data.get("search_area", {"size_km2": 1.0}),
            weather_conditions=extracted_data.get("weather_conditions", {}),
            available_drones=[{"id": "drone-1"}],
            time_constraints=extracted_data.get("time_constraints", {}),
            priority_level=extracted_data.get("priority", 5),
            discovered_objects=[],
            current_progress=0.0
        )
        
        # Get AI analysis
        analysis = await self.intelligence_engine.analyze_mission_context(context)
        strategy = await self.intelligence_engine.plan_search_strategy(context)
        risk_assessment = await self.intelligence_engine.assess_risks(context)
        
        return MissionPlan(
            mission_name=f"SAR Mission - {extracted_data.get('mission_type', 'Unknown')}",
            mission_type=extracted_data.get("mission_type", "missing_person"),
            search_area=extracted_data.get("search_area", {"size_km2": 1.0}),
            priority=extracted_data.get("priority", 5),
            max_flight_time=30,
            search_altitude=100.0,
            weather_thresholds=extracted_data.get("weather_thresholds", {}),
            estimated_duration=strategy.estimated_time,
            required_drones=1,
            risk_assessment=risk_assessment.__dict__,
            search_strategy=strategy.__dict__
        )
    
    async def _get_conversation_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state (placeholder - would use database in real implementation)"""
        # In real implementation, this would query the database
        return {
            "session_id": session_id,
            "extracted_data": {},
            "missing_parameters": ["mission_type", "search_area"],
            "is_complete": False
        }


async def create_mission_planner() -> ConversationalMissionPlanner:
    """Create and initialize conversational mission planner"""
    client = OllamaClient()
    intelligence_engine = await create_ollama_intelligence_engine()
    return ConversationalMissionPlanner(client=client, intelligence_engine=intelligence_engine)