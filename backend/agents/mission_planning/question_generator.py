"""
Question Generator Agent
Generates intelligent follow-up questions for mission planning
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

class QuestionGeneratorAgent(BaseAgent):
    """Generates intelligent follow-up questions for mission planning"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("question_generator", redis_service, websocket_manager)
        self.question_templates = {
            "location": [
                "Where exactly is this {location_type} located? Please provide coordinates or address.",
                "Can you give me the precise location coordinates for the search area?",
                "What's the nearest landmark or address to help locate the search area?"
            ],
            "area_size": [
                "How large is the search area approximately? (e.g., square meters, acres, city blocks)",
                "What are the approximate dimensions of the area we need to cover?",
                "Can you estimate the size of the search zone?"
            ],
            "hazards": [
                "Are there any known hazards in the area? (gas leaks, unstable structures, fire, etc.)",
                "What safety concerns should our drones be aware of?",
                "Are there any environmental dangers or obstacles we need to consider?"
            ],
            "survivors": [
                "How many people are we searching for approximately?",
                "Do you have any information about the victims' last known locations?",
                "Are there any specific characteristics that might help identify survivors?"
            ],
            "urgency": [
                "What's the priority level for this search? (immediate, high, medium, low)",
                "Are there any time constraints we should be aware of?",
                "How urgent is this rescue operation?"
            ],
            "environment": [
                "What are the current weather conditions in the area?",
                "Are there any visibility issues or environmental factors affecting the search?",
                "What time of day will the search be conducted?"
            ],
            "resources": [
                "How many drones would you like to deploy for this mission?",
                "Do you have any preference for search pattern or coverage strategy?",
                "Are there any specific drone capabilities or sensors needed?"
            ]
        }
        
        self.question_priority = [
            "location", "urgency", "area_size", "hazards", 
            "survivors", "environment", "resources"
        ]
    
    async def start_agent(self) -> None:
        """Start the question generator"""
        await self.subscribe_to_channel("mission.question_needed")
        await self.subscribe_to_channel("mission.info_gathered")
        logger.info("Question Generator Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the question generator"""
        logger.info("Question Generator Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "mission.question_needed":
                await self._handle_question_needed(message)
            elif channel == "mission.info_gathered":
                await self._handle_info_gathered(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_question_needed(self, message: Dict[str, Any]) -> None:
        """Handle request for new question"""
        session_id = message.get("session_id")
        conversation_history = message.get("conversation_history", [])
        gathered_info = message.get("gathered_info", {})
        question_number = message.get("question_number", 1)
        
        logger.info(f"Generating question {question_number} for session {session_id}")
        
        # Determine what information is still needed
        needed_info = await self._determine_needed_info(gathered_info, question_number)
        
        if not needed_info:
            # No more questions needed
            await self.publish_message("mission.questions_complete", {
                "session_id": session_id,
                "gathered_info": gathered_info
            })
            return
        
        # Generate question for the needed information
        question = await self._generate_question(needed_info, conversation_history, question_number)
        
        if question:
            # Publish the generated question
            await self.publish_message("mission.question_generated", {
                "session_id": session_id,
                "question": question,
                "question_type": needed_info,
                "question_number": question_number
            })
            
            # Send to WebSocket
            await self.send_websocket_message("ai_question", {
                "session_id": session_id,
                "question": question,
                "question_type": needed_info,
                "question_number": question_number
            })
            
            logger.info(f"Generated question: {question}")
        else:
            # Could not generate question, mark as complete
            await self.publish_message("mission.questions_complete", {
                "session_id": session_id,
                "gathered_info": gathered_info
            })
    
    async def _handle_info_gathered(self, message: Dict[str, Any]) -> None:
        """Handle information that was just gathered"""
        session_id = message.get("session_id")
        info_type = message.get("info_type")
        info_value = message.get("info_value")
        
        logger.info(f"Info gathered for session {session_id}: {info_type} = {info_value}")
        
        # This could be used to adjust question strategy
        # For now, we just log it
        pass
    
    async def _determine_needed_info(self, gathered_info: Dict[str, Any], question_number: int) -> Optional[str]:
        """Determine what information is still needed"""
        # Check what we already have
        has_location = "location" in gathered_info and gathered_info["location"]
        has_urgency = "priority" in gathered_info and gathered_info["priority"]
        has_area_size = "area_size" in gathered_info and gathered_info["area_size"]
        has_hazards = "hazards" in gathered_info and gathered_info["hazards"]
        has_survivors = "survivors" in gathered_info and gathered_info["survivors"]
        has_environment = "environment" in gathered_info and gathered_info["environment"]
        has_resources = "drone_count" in gathered_info and gathered_info["drone_count"]
        
        # Check priority order
        for info_type in self.question_priority:
            if info_type == "location" and not has_location:
                return "location"
            elif info_type == "urgency" and not has_urgency:
                return "urgency"
            elif info_type == "area_size" and not has_area_size:
                return "area_size"
            elif info_type == "hazards" and not has_hazards:
                return "hazards"
            elif info_type == "survivors" and not has_survivors:
                return "survivors"
            elif info_type == "environment" and not has_environment:
                return "environment"
            elif info_type == "resources" and not has_resources:
                return "resources"
        
        # If we have all priority info, check for additional details
        if question_number <= 8:  # Max 8 questions
            # Ask for clarification on existing info
            if has_location and question_number <= 6:
                return "location_clarification"
            elif has_hazards and question_number <= 7:
                return "hazards_clarification"
            elif has_survivors and question_number <= 8:
                return "survivors_clarification"
        
        return None  # No more questions needed
    
    async def _generate_question(self, info_type: str, conversation_history: List[Dict[str, str]], 
                                question_number: int) -> Optional[str]:
        """Generate a specific question for the needed information type"""
        try:
            # Use LLM to generate contextual question
            context = self._build_context(conversation_history)
            
            prompt = f"""Generate a specific, actionable question to gather this information: {info_type}

Context from conversation so far:
{context}

Question number: {question_number}

Requirements:
- Ask exactly ONE question
- Be direct and specific
- Make it easy for the user to answer
- Don't repeat information already gathered
- Focus on practical operational details

Return only the question text, no additional formatting."""

            question = await ollama_service.generate_response(
                prompt,
                system_prompt="You are an expert search and rescue mission planner asking critical questions."
            )
            
            if question and question.strip():
                return question.strip()
            
        except Exception as e:
            logger.error(f"Error generating question with LLM: {e}")
        
        # Fallback to template-based question
        return self._get_template_question(info_type)
    
    def _build_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build context string from conversation history"""
        context_parts = []
        for msg in conversation_history[-3:]:  # Last 3 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts) if context_parts else "No previous conversation"
    
    def _get_template_question(self, info_type: str) -> Optional[str]:
        """Get template-based question as fallback"""
        templates = self.question_templates.get(info_type, [])
        if templates:
            import random
            return random.choice(templates)
        
        # Generic fallback questions
        fallback_questions = {
            "location": "Can you provide more specific location details for the search area?",
            "urgency": "What's the priority level for this search operation?",
            "area_size": "How large is the area we need to search?",
            "hazards": "Are there any safety hazards we should be aware of?",
            "survivors": "How many people are we searching for?",
            "environment": "What are the current conditions in the search area?",
            "resources": "How many drones should we deploy for this mission?",
            "location_clarification": "Can you provide coordinates or a more precise location?",
            "hazards_clarification": "Are there any additional safety concerns?",
            "survivors_clarification": "Do you have any more details about the missing persons?"
        }
        
        return fallback_questions.get(info_type, "Can you provide more details about this mission?")
    
    async def generate_validation_question(self, info_type: str, value: str) -> str:
        """Generate a validation question to confirm information"""
        validation_templates = {
            "location": f"Just to confirm, the search area is at: {value}?",
            "area_size": f"To clarify, the search area is approximately {value}?",
            "hazards": f"Let me confirm the hazards you mentioned: {value}?",
            "survivors": f"To verify, we're searching for {value}?",
            "priority": f"Just to confirm, this is a {value} priority mission?"
        }
        
        return validation_templates.get(info_type, f"Can you confirm: {value}?")
    
    async def generate_clarification_question(self, info_type: str, value: str) -> str:
        """Generate a clarification question for unclear information"""
        clarification_templates = {
            "location": f"You mentioned the location as '{value}'. Can you be more specific with coordinates or address?",
            "area_size": f"You said the area is '{value}'. Can you provide dimensions in meters or square footage?",
            "hazards": f"You mentioned '{value}' as hazards. Can you elaborate on the specific risks?",
            "survivors": f"You mentioned '{value}' people. Is this the exact number or an estimate?",
            "priority": f"You indicated '{value}' priority. Is this immediate, urgent, or can it wait?"
        }
        
        return clarification_templates.get(info_type, f"Can you clarify what you mean by '{value}'?")