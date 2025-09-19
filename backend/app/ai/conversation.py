"""
Conversational Mission Planner - AI-driven mission planning through natural dialogue.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .ollama_client import OllamaClient
from ..core.config import settings

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """States of the mission planning conversation."""
    INITIAL = "initial"
    GATHERING_BASIC_INFO = "gathering_basic_info"
    REFINING_OBJECTIVES = "refining_objectives"
    PLANNING_RESOURCES = "planning_resources"
    SAFETY_VALIDATION = "safety_validation"
    FINAL_REVIEW = "final_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class MissionParameters:
    """Core mission parameters gathered through conversation."""
    # Basic Information
    mission_type: Optional[str] = None
    search_area_description: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    area_size_km2: Optional[float] = None
    
    # Search Objectives
    target_description: Optional[str] = None
    last_known_location: Optional[Dict[str, float]] = None
    urgency_level: Optional[str] = None  # low, medium, high, critical
    expected_search_duration: Optional[int] = None  # hours
    
    # Environmental Conditions
    weather_conditions: Optional[Dict[str, Any]] = None
    terrain_type: Optional[str] = None
    time_of_day_preference: Optional[str] = None
    
    # Resource Requirements
    num_drones_requested: Optional[int] = None
    search_altitude: Optional[float] = None
    camera_requirements: Optional[List[str]] = None
    special_equipment: Optional[List[str]] = None
    
    # Safety Parameters
    max_wind_speed: Optional[float] = None
    minimum_visibility: Optional[float] = None
    no_fly_zones: Optional[List[Dict]] = None
    emergency_landing_sites: Optional[List[Dict]] = None
    
    # Operational Constraints
    time_limit: Optional[int] = None  # maximum mission duration in hours
    battery_reserve_percentage: Optional[float] = None
    operator_contact_info: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def get_completion_percentage(self) -> float:
        """Calculate what percentage of parameters are filled."""
        total_fields = len(self.__dataclass_fields__)
        filled_fields = len(self.to_dict())
        return (filled_fields / total_fields) * 100

class ConversationalMissionPlanner:
    """AI-driven conversational mission planner."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        
        # Active conversations: client_id -> conversation_data
        self.active_conversations: Dict[str, dict] = {}
        
        # Conversation templates and prompts
        self.system_prompts = self._load_system_prompts()
        
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different conversation states."""
        return {
            "initial": """You are an expert SAR (Search and Rescue) mission planner AI assistant. 
            Your role is to help operators plan comprehensive and safe drone search missions through 
            natural conversation. Ask clarifying questions to gather all necessary information for 
            a complete mission plan. Be professional, empathetic, and focused on safety and efficiency.
            
            Start by understanding the basic situation and then systematically gather:
            1. Search objectives and target information
            2. Area and environmental conditions  
            3. Resource and equipment requirements
            4. Safety parameters and constraints
            5. Operational timeline and limitations
            
            Keep questions clear, specific, and relevant to SAR operations.""",
            
            "gathering_basic_info": """Continue gathering basic mission information. Focus on:
            - What or who is being searched for
            - General area and terrain description
            - Urgency level and time sensitivity
            - Any initial location information available
            
            Ask one focused question at a time to avoid overwhelming the operator.""",
            
            "refining_objectives": """Now focus on refining the search objectives and parameters:
            - Specific target characteristics (size, color, etc.)
            - Last known location and movement patterns
            - Search area boundaries and size
            - Environmental factors affecting the search
            
            Be thorough but efficient in gathering this critical information.""",
            
            "planning_resources": """Plan the resources and equipment needed:
            - Number of drones required based on area size
            - Optimal search altitude and patterns
            - Camera and sensor requirements
            - Special equipment needs
            - Operator staffing requirements
            
            Consider the mission complexity and environmental conditions.""",
            
            "safety_validation": """Validate safety parameters and constraints:
            - Weather conditions and limits
            - No-fly zones and airspace restrictions
            - Emergency procedures and landing sites
            - Communication protocols
            - Risk mitigation strategies
            
            Safety is the top priority - be thorough in this validation.""",
            
            "final_review": """Present the complete mission plan for final review:
            - Summarize all gathered parameters
            - Highlight any remaining concerns or gaps
            - Confirm operational readiness
            - Get final approval before mission execution
            
            Ensure the operator understands and approves all aspects of the plan."""
        }
    
    async def start_conversation(self, client_id: str, initial_message: str = "") -> str:
        """Start a new mission planning conversation."""
        # Initialize conversation state
        self.active_conversations[client_id] = {
            "state": ConversationState.INITIAL,
            "parameters": MissionParameters(),
            "conversation_history": [],
            "started_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "question_count": 0,
            "ai_confidence": 0.0
        }
        
        # Process initial message if provided
        if initial_message:
            return await self.process_message(initial_message, client_id)
        else:
            return await self._generate_initial_greeting(client_id)
    
    async def process_message(self, message: str, client_id: str) -> str:
        """Process a message in the conversation and generate appropriate response."""
        if client_id not in self.active_conversations:
            return await self.start_conversation(client_id, message)
        
        conversation = self.active_conversations[client_id]
        
        # Update conversation history
        conversation["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "role": "user",
            "content": message
        })
        conversation["last_activity"] = datetime.utcnow()
        
        # Process the message based on current state
        response = await self._process_message_by_state(message, conversation)
        
        # Update conversation history with AI response
        conversation["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "role": "assistant", 
            "content": response
        })
        
        # Update conversation state if needed
        await self._update_conversation_state(conversation)
        
        return response
    
    async def _generate_initial_greeting(self, client_id: str) -> str:
        """Generate initial greeting message."""
        return """Hello! I'm your AI mission planning assistant for SAR drone operations. 
        I'll help you create a comprehensive and safe search mission plan through a series of questions.
        
        Let's start: Can you tell me what situation we're dealing with? 
        What or who are we searching for, and do you have any initial location information?"""
    
    async def _process_message_by_state(self, message: str, conversation: dict) -> str:
        """Process message based on current conversation state."""
        state = conversation["state"]
        parameters = conversation["parameters"]
        history = conversation["conversation_history"]
        
        # Extract information from the message
        extracted_info = await self._extract_information(message, state, parameters)
        
        # Update parameters with extracted information
        self._update_parameters(parameters, extracted_info)
        
        # Generate appropriate response based on state
        if state == ConversationState.INITIAL:
            return await self._handle_initial_state(message, conversation)
        elif state == ConversationState.GATHERING_BASIC_INFO:
            return await self._handle_basic_info_state(message, conversation)
        elif state == ConversationState.REFINING_OBJECTIVES:
            return await self._handle_objectives_state(message, conversation)
        elif state == ConversationState.PLANNING_RESOURCES:
            return await self._handle_resources_state(message, conversation)
        elif state == ConversationState.SAFETY_VALIDATION:
            return await self._handle_safety_state(message, conversation)
        elif state == ConversationState.FINAL_REVIEW:
            return await self._handle_final_review_state(message, conversation)
        else:
            return "I'm not sure how to handle that request. Could you please clarify?"
    
    async def _extract_information(
        self,
        message: str,
        state: ConversationState,
        current_parameters: MissionParameters
    ) -> Dict[str, Any]:
        """Extract structured information from user message."""
        system_prompt = f"""Extract relevant SAR mission information from the user's message.
        Current conversation state: {state.value}
        Current parameters: {json.dumps(current_parameters.to_dict(), indent=2)}
        
        Return extracted information as JSON with relevant fields. Only include information
        that is explicitly mentioned or can be clearly inferred."""
        
        prompt = f"""
        User message: "{message}"
        
        Extract any relevant mission planning information and return as JSON.
        Possible fields include:
        - mission_type, target_description, search_area_description
        - coordinates, area_size_km2, last_known_location
        - urgency_level, expected_search_duration
        - weather_conditions, terrain_type, time_of_day_preference
        - num_drones_requested, search_altitude, camera_requirements
        - max_wind_speed, minimum_visibility, time_limit
        
        Only include fields with clear information from the message.
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            return json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Information extraction failed: {e}")
            return {}
    
    def _update_parameters(self, parameters: MissionParameters, extracted_info: Dict[str, Any]):
        """Update mission parameters with extracted information."""
        for key, value in extracted_info.items():
            if hasattr(parameters, key) and value is not None:
                setattr(parameters, key, value)
    
    async def _handle_initial_state(self, message: str, conversation: dict) -> str:
        """Handle initial conversation state."""
        parameters = conversation["parameters"]
        
        # Acknowledge the information and ask follow-up questions
        acknowledgment = await self._generate_acknowledgment(message, parameters)
        
        # Generate next question based on what's missing
        next_question = await self._generate_next_question(conversation)
        
        return f"{acknowledgment}\n\n{next_question}"
    
    async def _handle_basic_info_state(self, message: str, conversation: dict) -> str:
        """Handle basic information gathering state."""
        parameters = conversation["parameters"]
        
        # Check if we have enough basic info to move forward
        basic_info_complete = all([
            parameters.mission_type,
            parameters.target_description,
            parameters.search_area_description,
            parameters.urgency_level
        ])
        
        if basic_info_complete:
            conversation["state"] = ConversationState.REFINING_OBJECTIVES
            return await self._transition_to_objectives(conversation)
        else:
            acknowledgment = await self._generate_acknowledgment(message, parameters)
            next_question = await self._generate_next_question(conversation)
            return f"{acknowledgment}\n\n{next_question}"
    
    async def _handle_objectives_state(self, message: str, conversation: dict) -> str:
        """Handle objectives refinement state."""
        parameters = conversation["parameters"]
        
        # Check if objectives are sufficiently defined
        objectives_complete = all([
            parameters.coordinates or parameters.last_known_location,
            parameters.area_size_km2,
            parameters.expected_search_duration
        ])
        
        if objectives_complete:
            conversation["state"] = ConversationState.PLANNING_RESOURCES
            return await self._transition_to_resources(conversation)
        else:
            acknowledgment = await self._generate_acknowledgment(message, parameters)
            next_question = await self._generate_next_question(conversation)
            return f"{acknowledgment}\n\n{next_question}"
    
    async def _handle_resources_state(self, message: str, conversation: dict) -> str:
        """Handle resource planning state."""
        parameters = conversation["parameters"]
        
        # Auto-calculate some parameters if not provided
        if not parameters.num_drones_requested and parameters.area_size_km2:
            parameters.num_drones_requested = max(1, int(parameters.area_size_km2 / 2))
        
        if not parameters.search_altitude:
            parameters.search_altitude = settings.default_search_altitude
        
        # Check if resource planning is complete
        resources_complete = all([
            parameters.num_drones_requested,
            parameters.search_altitude
        ])
        
        if resources_complete:
            conversation["state"] = ConversationState.SAFETY_VALIDATION
            return await self._transition_to_safety(conversation)
        else:
            acknowledgment = await self._generate_acknowledgment(message, parameters)
            next_question = await self._generate_next_question(conversation)
            return f"{acknowledgment}\n\n{next_question}"
    
    async def _handle_safety_state(self, message: str, conversation: dict) -> str:
        """Handle safety validation state."""
        parameters = conversation["parameters"]
        
        # Apply default safety parameters if not specified
        if not parameters.max_wind_speed:
            parameters.max_wind_speed = settings.max_wind_speed
        
        if not parameters.battery_reserve_percentage:
            parameters.battery_reserve_percentage = settings.min_battery_level
        
        # Check if safety validation is complete
        safety_complete = all([
            parameters.max_wind_speed,
            parameters.battery_reserve_percentage
        ])
        
        if safety_complete:
            conversation["state"] = ConversationState.FINAL_REVIEW
            return await self._transition_to_final_review(conversation)
        else:
            acknowledgment = await self._generate_acknowledgment(message, parameters)
            next_question = await self._generate_next_question(conversation)
            return f"{acknowledgment}\n\n{next_question}"
    
    async def _handle_final_review_state(self, message: str, conversation: dict) -> str:
        """Handle final review and approval state."""
        if "approve" in message.lower() or "confirm" in message.lower() or "yes" in message.lower():
            conversation["state"] = ConversationState.COMPLETED
            return await self._finalize_mission_plan(conversation)
        elif "no" in message.lower() or "change" in message.lower() or "modify" in message.lower():
            return await self._handle_modification_request(message, conversation)
        else:
            return """Please confirm if you approve this mission plan by saying "yes" or "approve", 
            or let me know what changes you'd like to make."""
    
    async def _generate_acknowledgment(self, message: str, parameters: MissionParameters) -> str:
        """Generate acknowledgment of received information."""
        system_prompt = """Generate a brief, professional acknowledgment of the information 
        received from the SAR operator. Be empathetic and confirm understanding."""
        
        prompt = f"""
        User message: "{message}"
        Current mission parameters: {json.dumps(parameters.to_dict(), indent=2)}
        
        Generate a brief acknowledgment (1-2 sentences) that confirms understanding 
        of the key information provided.
        """
        
        try:
            return await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"Error generating acknowledgment: {e}")
            return "Thank you for that information."
    
    async def _generate_next_question(self, conversation: dict) -> str:
        """Generate the next clarifying question based on conversation state."""
        state = conversation["state"]
        parameters = conversation["parameters"]
        history = conversation["conversation_history"]
        
        # Use AI to generate contextually appropriate question
        questions = await self.ollama_client.generate_clarifying_questions(
            conversation_history=history,
            current_mission_state={
                "state": state.value,
                "parameters": parameters.to_dict(),
                "completion_percentage": parameters.get_completion_percentage()
            }
        )
        
        conversation["question_count"] += 1
        
        return questions[0] if questions else "What other information can you provide about the mission?"
    
    async def _transition_to_objectives(self, conversation: dict) -> str:
        """Transition to objectives refinement phase."""
        return """Great! I have the basic information about the search mission. 
        Now let's refine the specific objectives and search parameters.
        
        Can you provide more details about the search area? Do you have specific coordinates 
        or boundaries, and approximately how large is the area we need to cover?"""
    
    async def _transition_to_resources(self, conversation: dict) -> str:
        """Transition to resource planning phase."""
        parameters = conversation["parameters"]
        
        return f"""Perfect! I understand the search objectives. Based on the search area of 
        approximately {parameters.area_size_km2} km², I'm now planning the required resources.
        
        How many drones would you like to deploy for this mission? I recommend 
        {max(1, int(parameters.area_size_km2 / 2))} drones for optimal coverage."""
    
    async def _transition_to_safety(self, conversation: dict) -> str:
        """Transition to safety validation phase."""
        return """Excellent! The resource allocation looks good. Now let's validate 
        the safety parameters for this mission.
        
        What are the current weather conditions? Are there any wind speed limits 
        or visibility requirements I should consider for safe drone operations?"""
    
    async def _transition_to_final_review(self, conversation: dict) -> str:
        """Transition to final review phase."""
        parameters = conversation["parameters"]
        
        mission_summary = f"""
        **MISSION PLAN SUMMARY**
        
        **Mission Type:** {parameters.mission_type}
        **Target:** {parameters.target_description}
        **Search Area:** {parameters.search_area_description} (~{parameters.area_size_km2} km²)
        **Urgency:** {parameters.urgency_level}
        **Duration:** {parameters.expected_search_duration} hours
        
        **Resources:**
        - Drones: {parameters.num_drones_requested}
        - Search Altitude: {parameters.search_altitude}m
        
        **Safety Parameters:**
        - Max Wind Speed: {parameters.max_wind_speed} m/s
        - Battery Reserve: {parameters.battery_reserve_percentage}%
        
        Does this mission plan look correct? Please confirm to proceed with mission execution.
        """
        
        return mission_summary
    
    async def _finalize_mission_plan(self, conversation: dict) -> str:
        """Finalize the mission plan and prepare for execution."""
        conversation["state"] = ConversationState.COMPLETED
        parameters = conversation["parameters"]
        
        # Generate mission ID and prepare for execution
        mission_id = f"SAR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Store the completed mission plan (this would integrate with mission service)
        mission_plan = {
            "mission_id": mission_id,
            "parameters": parameters.to_dict(),
            "conversation_history": conversation["conversation_history"],
            "created_at": datetime.utcnow().isoformat(),
            "status": "ready_for_execution"
        }
        
        return f"""✅ **MISSION PLAN APPROVED**
        
        Mission ID: {mission_id}
        Status: Ready for execution
        
        The mission plan has been finalized and is ready to deploy. The system will now:
        1. Initialize drone systems
        2. Perform pre-flight checks
        3. Begin coordinated search operations
        
        You can monitor the mission progress through the real-time dashboard.
        
        Good luck with the search operation!"""
    
    async def _handle_modification_request(self, message: str, conversation: dict) -> str:
        """Handle requests to modify the mission plan."""
        # Extract what needs to be modified
        system_prompt = """The user wants to modify the mission plan. Identify what 
        specific aspect they want to change and reset the conversation to the appropriate state."""
        
        prompt = f"""
        User message: "{message}"
        
        What aspect of the mission plan do they want to modify?
        Return one of: basic_info, objectives, resources, safety, or general.
        """
        
        try:
            modification_type = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            # Reset to appropriate state
            if "basic_info" in modification_type.lower():
                conversation["state"] = ConversationState.GATHERING_BASIC_INFO
            elif "objectives" in modification_type.lower():
                conversation["state"] = ConversationState.REFINING_OBJECTIVES
            elif "resources" in modification_type.lower():
                conversation["state"] = ConversationState.PLANNING_RESOURCES
            elif "safety" in modification_type.lower():
                conversation["state"] = ConversationState.SAFETY_VALIDATION
            else:
                conversation["state"] = ConversationState.GATHERING_BASIC_INFO
            
            return f"I understand you'd like to modify the plan. What specific changes would you like to make?"
            
        except Exception as e:
            logger.error(f"Error handling modification request: {e}")
            return "I understand you'd like to make changes. What would you like to modify in the mission plan?"
    
    async def _update_conversation_state(self, conversation: dict):
        """Update conversation state based on completion progress."""
        parameters = conversation["parameters"]
        completion = parameters.get_completion_percentage()
        conversation["ai_confidence"] = completion / 100.0
        
        # Auto-advance state if we have sufficient information
        if completion >= 80 and conversation["state"] != ConversationState.FINAL_REVIEW:
            conversation["state"] = ConversationState.FINAL_REVIEW
    
    async def make_autonomous_decision(self, mission_id: str, mission_data: dict) -> dict:
        """Make autonomous decisions during mission execution."""
        return await self.ollama_client.make_autonomous_decision(
            mission_id=mission_id,
            situation_data=mission_data,
            decision_context="mission_execution"
        )
    
    def get_conversation_status(self, client_id: str) -> Optional[dict]:
        """Get current conversation status."""
        if client_id not in self.active_conversations:
            return None
        
        conversation = self.active_conversations[client_id]
        parameters = conversation["parameters"]
        
        return {
            "client_id": client_id,
            "state": conversation["state"].value,
            "completion_percentage": parameters.get_completion_percentage(),
            "question_count": conversation["question_count"],
            "ai_confidence": conversation["ai_confidence"],
            "last_activity": conversation["last_activity"].isoformat(),
            "parameters_summary": parameters.to_dict()
        }
    
    def cleanup_inactive_conversations(self, max_age_hours: int = 2):
        """Clean up inactive conversations."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        inactive_clients = [
            client_id for client_id, conversation in self.active_conversations.items()
            if conversation["last_activity"] < cutoff_time
        ]
        
        for client_id in inactive_clients:
            del self.active_conversations[client_id]
            logger.info(f"Cleaned up inactive conversation for client {client_id}")
        
        return len(inactive_clients)