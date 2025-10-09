"""
NLP Agent for parsing user input and extracting intent
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

class NLPAgent(BaseAgent):
    """Natural Language Processing agent for user input analysis"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("nlp_agent", redis_service, websocket_manager)
        self.intent_patterns = {
            "mission_planning": [
                r"search.*for.*survivor",
                r"find.*missing.*person",
                r"rescue.*operation",
                r"search.*and.*rescue",
                r"locate.*victim",
                r"emergency.*search"
            ],
            "drone_control": [
                r"drone.*return.*base",
                r"pause.*mission",
                r"resume.*mission",
                r"investigate.*area",
                r"change.*course",
                r"land.*drone"
            ],
            "status_inquiry": [
                r"status.*mission",
                r"how.*many.*drones",
                r"battery.*level",
                r"mission.*progress",
                r"coverage.*percentage"
            ],
            "emergency": [
                r"emergency.*stop",
                r"abort.*mission",
                r"immediate.*return",
                r"urgent.*action"
            ]
        }
    
    async def start_agent(self) -> None:
        """Start the NLP agent"""
        await self.subscribe_to_channel("user.input")
        await self.subscribe_to_channel("mission.user_response")
        logger.info("NLP Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the NLP agent"""
        logger.info("NLP Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "user.input":
                await self._process_user_input(message)
            elif channel == "mission.user_response":
                await self._process_mission_response(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _process_user_input(self, message: Dict[str, Any]) -> None:
        """Process general user input"""
        user_input = message.get("input", "")
        session_id = message.get("session_id", "default")
        
        if not user_input.strip():
            return
        
        logger.info(f"Processing user input: {user_input}")
        
        # Analyze intent
        intent_analysis = await self._analyze_intent(user_input)
        
        # Extract entities
        entities = await self._extract_entities(user_input)
        
        # Determine action
        action = await self._determine_action(intent_analysis, entities)
        
        # Publish analysis result
        await self.publish_message("nlp.analysis_complete", {
            "session_id": session_id,
            "original_input": user_input,
            "intent": intent_analysis,
            "entities": entities,
            "action": action,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Route to appropriate handler
        await self._route_to_handler(action, user_input, session_id, intent_analysis, entities)
    
    async def _process_mission_response(self, message: Dict[str, Any]) -> None:
        """Process mission planning response"""
        response = message.get("response", "")
        session_id = message.get("session_id", "default")
        
        if not response.strip():
            return
        
        # Extract information from response
        entities = await self._extract_entities(response)
        
        # Determine if response contains specific information
        info_type = await self._classify_response_type(response)
        
        # Publish response analysis
        await self.publish_message("mission.response_analyzed", {
            "session_id": session_id,
            "response": response,
            "entities": entities,
            "info_type": info_type,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze user intent using pattern matching and LLM"""
        user_input_lower = user_input.lower()
        
        # Pattern-based intent detection
        detected_intents = []
        confidence_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    detected_intents.append(intent)
                    confidence_scores[intent] = 0.8  # High confidence for pattern match
                    break
        
        # Use LLM for more sophisticated analysis
        try:
            llm_analysis = await ollama_service.generate_response(
                f"Analyze this user input and determine the primary intent: '{user_input}'\n\n"
                "Return JSON with: intent (string), confidence (0-1), reasoning (string)",
                system_prompt="You are an expert at analyzing user intent for drone control systems."
            )
            
            # Try to parse LLM response
            try:
                llm_result = json.loads(llm_analysis)
                if llm_result.get("intent"):
                    detected_intents.append(llm_result["intent"])
                    confidence_scores[llm_result["intent"]] = float(llm_result.get("confidence", 0.5))
            except json.JSONDecodeError:
                pass
        
        except Exception as e:
            logger.error(f"LLM intent analysis failed: {e}")
        
        # Determine primary intent
        primary_intent = "unknown"
        if detected_intents:
            primary_intent = max(confidence_scores.items(), key=lambda x: x[1])[0]
        
        return {
            "primary_intent": primary_intent,
            "all_intents": detected_intents,
            "confidence_scores": confidence_scores,
            "raw_input": user_input
        }
    
    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {
            "locations": [],
            "coordinates": [],
            "numbers": [],
            "drone_ids": [],
            "time_references": [],
            "urgency_indicators": []
        }
        
        # Extract coordinates (lat, lng patterns)
        coord_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        coords = re.findall(coord_pattern, text)
        entities["coordinates"] = [{"lat": float(lat), "lng": float(lng)} for lat, lng in coords]
        
        # Extract numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        entities["numbers"] = re.findall(number_pattern, text)
        
        # Extract drone references
        drone_pattern = r'drone\s*(\d+)'
        entities["drone_ids"] = re.findall(drone_pattern, text, re.IGNORECASE)
        
        # Extract time references
        time_pattern = r'\b(immediately|now|urgent|asap|soon|later|minutes?|hours?)\b'
        entities["time_references"] = re.findall(time_pattern, text, re.IGNORECASE)
        
        # Extract urgency indicators
        urgency_pattern = r'\b(emergency|urgent|critical|immediate|asap|stop|abort)\b'
        entities["urgency_indicators"] = re.findall(urgency_pattern, text, re.IGNORECASE)
        
        # Use LLM for more sophisticated entity extraction
        try:
            llm_entities = await ollama_service.generate_response(
                f"Extract entities from this text: '{text}'\n\n"
                "Return JSON with: locations (array), actions (array), objects (array)",
                system_prompt="You are an expert at extracting entities from natural language."
            )
            
            try:
                llm_result = json.loads(llm_entities)
                if llm_result.get("locations"):
                    entities["locations"].extend(llm_result["locations"])
                if llm_result.get("actions"):
                    entities["actions"] = llm_result["actions"]
                if llm_result.get("objects"):
                    entities["objects"] = llm_result["objects"]
            except json.JSONDecodeError:
                pass
        
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
        
        return entities
    
    async def _determine_action(self, intent_analysis: Dict[str, Any], entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Determine action based on intent and entities"""
        primary_intent = intent_analysis.get("primary_intent", "unknown")
        confidence = intent_analysis.get("confidence_scores", {}).get(primary_intent, 0.0)
        
        action = {
            "type": "unknown",
            "target": "none",
            "parameters": {},
            "confidence": confidence,
            "priority": "low"
        }
        
        if primary_intent == "mission_planning":
            action.update({
                "type": "start_mission_planning",
                "target": "conversation_orchestrator",
                "parameters": {
                    "description": intent_analysis.get("raw_input", ""),
                    "entities": entities
                },
                "priority": "high"
            })
        
        elif primary_intent == "drone_control":
            drone_ids = entities.get("drone_ids", [])
            if not drone_ids:
                drone_ids = ["all"]
            
            action.update({
                "type": "drone_command",
                "target": "command_dispatcher",
                "parameters": {
                    "drone_ids": drone_ids,
                    "command": intent_analysis.get("raw_input", ""),
                    "entities": entities
                },
                "priority": "high"
            })
        
        elif primary_intent == "status_inquiry":
            action.update({
                "type": "status_request",
                "target": "status_reporter",
                "parameters": {
                    "query": intent_analysis.get("raw_input", ""),
                    "entities": entities
                },
                "priority": "medium"
            })
        
        elif primary_intent == "emergency":
            action.update({
                "type": "emergency_action",
                "target": "emergency_handler",
                "parameters": {
                    "command": intent_analysis.get("raw_input", ""),
                    "entities": entities
                },
                "priority": "critical"
            })
        
        return action
    
    async def _classify_response_type(self, response: str) -> str:
        """Classify the type of information in a response"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["location", "address", "coordinates", "lat", "lng"]):
            return "location"
        elif any(word in response_lower for word in ["size", "area", "square", "meters", "feet"]):
            return "area_size"
        elif any(word in response_lower for word in ["hazard", "danger", "gas", "fire", "unstable"]):
            return "hazards"
        elif any(word in response_lower for word in ["urgent", "emergency", "critical", "immediate"]):
            return "priority"
        elif any(word in response_lower for word in ["drone", "drones", "fleet"]):
            return "drone_count"
        else:
            return "general"
    
    async def _route_to_handler(self, action: Dict[str, Any], user_input: str, 
                               session_id: str, intent_analysis: Dict[str, Any], 
                               entities: Dict[str, List[str]]) -> None:
        """Route action to appropriate handler"""
        action_type = action.get("type")
        target = action.get("target")
        
        if action_type == "start_mission_planning":
            await self.publish_message("mission.intent", {
                "session_id": session_id,
                "description": user_input,
                "intent_analysis": intent_analysis,
                "entities": entities
            })
        
        elif action_type == "drone_command":
            await self.publish_message("command.drone_control", {
                "session_id": session_id,
                "action": action,
                "user_input": user_input
            })
        
        elif action_type == "status_request":
            await self.publish_message("status.request", {
                "session_id": session_id,
                "action": action,
                "user_input": user_input
            })
        
        elif action_type == "emergency_action":
            await self.publish_message("emergency.action", {
                "session_id": session_id,
                "action": action,
                "user_input": user_input
            })
        
        else:
            # Unknown action, send to general handler
            await self.publish_message("general.unknown_action", {
                "session_id": session_id,
                "action": action,
                "user_input": user_input
            })