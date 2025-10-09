"""
Conversation Orchestrator Agent
Manages AI conversation flow for mission planning
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service
from ...services.database import db_service

logger = logging.getLogger(__name__)

class ConversationOrchestratorAgent(BaseAgent):
    """Orchestrates conversation flow for mission planning"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("conversation_orchestrator", redis_service, websocket_manager)
        self.conversation_sessions: Dict[str, Dict[str, Any]] = {}
        self.current_mission_id: Optional[int] = None
    
    async def start_agent(self) -> None:
        """Start the conversation orchestrator"""
        await self.subscribe_to_channel("mission.intent")
        await self.subscribe_to_channel("mission.user_response")
        await self.subscribe_to_channel("mission.question_answered")
        await self.subscribe_to_channel("mission.plan_complete")
        logger.info("Conversation Orchestrator Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the conversation orchestrator"""
        logger.info("Conversation Orchestrator Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "mission.intent":
                await self._handle_mission_intent(message)
            elif channel == "mission.user_response":
                await self._handle_user_response(message)
            elif channel == "mission.question_answered":
                await self._handle_question_answered(message)
            elif channel == "mission.plan_complete":
                await self._handle_plan_complete(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_mission_intent(self, message: Dict[str, Any]) -> None:
        """Handle new mission intent from user"""
        session_id = message.get("session_id")
        mission_description = message.get("description", "")
        
        logger.info(f"New mission intent: {mission_description}")
        
        # Create conversation session
        self.conversation_sessions[session_id] = {
            "description": mission_description,
            "conversation_history": [],
            "gathered_info": {},
            "current_step": "initial_questions",
            "questions_asked": 0,
            "max_questions": 8
        }
        
        # Start conversation flow
        await self._start_conversation_flow(session_id)
    
    async def _start_conversation_flow(self, session_id: str) -> None:
        """Start the conversation flow"""
        session = self.conversation_sessions.get(session_id)
        if not session:
            return
        
        # Generate initial questions
        await self._generate_and_ask_questions(session_id)
    
    async def _generate_and_ask_questions(self, session_id: str) -> None:
        """Generate and ask follow-up questions"""
        session = self.conversation_sessions.get(session_id)
        if not session:
            return
        
        if session["questions_asked"] >= session["max_questions"]:
            # Enough questions asked, generate mission plan
            await self._generate_mission_plan(session_id)
            return
        
        try:
            # Generate question using Ollama
            question = await ollama_service.generate_mission_questions(
                session["description"],
                session["conversation_history"]
            )
            
            if question and question.strip():
                # Store question in conversation history
                session["conversation_history"].append({
                    "role": "assistant",
                    "content": question,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                session["questions_asked"] += 1
                
                # Send question to user via WebSocket
                await self.send_websocket_message("ai_question", {
                    "session_id": session_id,
                    "question": question,
                    "question_number": session["questions_asked"],
                    "max_questions": session["max_questions"]
                })
                
                # Publish to question channel
                await self.publish_message("mission.question_generated", {
                    "session_id": session_id,
                    "question": question,
                    "question_number": session["questions_asked"]
                })
                
                logger.info(f"Asked question {session['questions_asked']}: {question}")
            else:
                # No more questions, generate plan
                await self._generate_mission_plan(session_id)
        
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            # Fallback to generating plan
            await self._generate_mission_plan(session_id)
    
    async def _handle_user_response(self, message: Dict[str, Any]) -> None:
        """Handle user response to question"""
        session_id = message.get("session_id")
        response = message.get("response", "")
        
        session = self.conversation_sessions.get(session_id)
        if not session:
            return
        
        # Store user response
        session["conversation_history"].append({
            "role": "user",
            "content": response,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Extract information from response
        await self._extract_information(session_id, response)
        
        # Publish that question was answered
        await self.publish_message("mission.question_answered", {
            "session_id": session_id,
            "response": response,
            "question_number": session["questions_asked"]
        })
        
        # Continue conversation flow
        await asyncio.sleep(1)  # Brief pause
        await self._generate_and_ask_questions(session_id)
    
    async def _extract_information(self, session_id: str, response: str) -> None:
        """Extract structured information from user response"""
        session = self.conversation_sessions.get(session_id)
        if not session:
            return
        
        # Simple keyword extraction (in production, use more sophisticated NLP)
        response_lower = response.lower()
        
        # Extract location information
        if any(word in response_lower for word in ["location", "address", "coordinates", "lat", "lng"]):
            session["gathered_info"]["location"] = response
        
        # Extract area size
        if any(word in response_lower for word in ["size", "area", "square", "meters", "feet", "acres"]):
            session["gathered_info"]["area_size"] = response
        
        # Extract hazards
        if any(word in response_lower for word in ["hazard", "danger", "gas", "fire", "unstable", "collapsed"]):
            session["gathered_info"]["hazards"] = response
        
        # Extract priority
        if any(word in response_lower for word in ["urgent", "emergency", "critical", "immediate"]):
            session["gathered_info"]["priority"] = "high"
        elif any(word in response_lower for word in ["routine", "standard", "normal"]):
            session["gathered_info"]["priority"] = "low"
        else:
            session["gathered_info"]["priority"] = "medium"
        
        # Extract drone count preference
        if any(word in response_lower for word in ["drone", "drones"]):
            session["gathered_info"]["drone_count"] = response
        
        logger.info(f"Extracted info for session {session_id}: {session['gathered_info']}")
    
    async def _generate_mission_plan(self, session_id: str) -> None:
        """Generate complete mission plan"""
        session = self.conversation_sessions.get(session_id)
        if not session:
            return
        
        logger.info(f"Generating mission plan for session {session_id}")
        
        try:
            # Create mission in database
            mission = await db_service.create_mission(
                name=f"SAR Mission - {session['description'][:50]}",
                description=session["description"]
            )
            
            self.current_mission_id = mission.id
            
            # Generate plan using Ollama
            mission_plan = await ollama_service.generate_mission_plan(session["gathered_info"])
            
            # Store conversation context and plan in database
            await self._save_mission_data(mission.id, session, mission_plan)
            
            # Send plan to user
            await self.send_websocket_message("mission_plan_ready", {
                "session_id": session_id,
                "mission_id": mission.id,
                "plan": mission_plan
            })
            
            # Publish plan complete
            await self.publish_message("mission.plan_complete", {
                "session_id": session_id,
                "mission_id": mission.id,
                "plan": mission_plan
            })
            
            logger.info(f"Mission plan generated for mission {mission.id}")
        
        except Exception as e:
            logger.error(f"Error generating mission plan: {e}")
            await self.send_websocket_message("mission_plan_error", {
                "session_id": session_id,
                "error": str(e)
            })
    
    async def _save_mission_data(self, mission_id: int, session: Dict[str, Any], plan: Dict[str, Any]) -> None:
        """Save mission data to database"""
        try:
            # Update mission with conversation context and plan
            from ...services.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db_session:
                from ...services.database import Mission
                mission = await db_session.get(Mission, mission_id)
                if mission:
                    mission.conversation_context = json.dumps(session["conversation_history"])
                    mission.mission_plan = json.dumps(plan)
                    mission.search_area_json = json.dumps(plan.get("search_area", {}))
                    await db_session.commit()
        except Exception as e:
            logger.error(f"Error saving mission data: {e}")
    
    async def _handle_question_answered(self, message: Dict[str, Any]) -> None:
        """Handle question answered event"""
        # This is handled in _handle_user_response
        pass
    
    async def _handle_plan_complete(self, message: Dict[str, Any]) -> None:
        """Handle plan completion event"""
        session_id = message.get("session_id")
        mission_id = message.get("mission_id")
        
        logger.info(f"Mission plan completed for session {session_id}, mission {mission_id}")
        
        # Clean up session
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
    
    def get_conversation_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation status for session"""
        session = self.conversation_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "description": session["description"],
            "questions_asked": session["questions_asked"],
            "max_questions": session["max_questions"],
            "current_step": session["current_step"],
            "gathered_info": session["gathered_info"]
        }