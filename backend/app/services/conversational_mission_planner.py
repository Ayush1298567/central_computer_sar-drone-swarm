"""
Conversational Mission Planner for SAR Mission Commander
"""
import json
import re
from typing import Dict, Any, Tuple, List
from datetime import datetime

from ..ai.ollama_client import OllamaClient

class ConversationalMissionPlanner:
    """AI-powered conversational mission planner"""

    def __init__(self):
        self.ollama_client = OllamaClient()
        self.current_context = {}

    async def process_message(self, user_message: str, context: Dict[str, Any], message_history: List[Dict]) -> Tuple[str, Dict[str, Any], str]:
        """Process a user message and generate AI response with updated context"""

        # Build intelligent prompt with context
        prompt = self._build_prompt(user_message, context, message_history)

        try:
            # Generate AI response
            ai_response = await self.ollama_client.generate(
                prompt=prompt,
                model="phi3:mini",  # Can be configured via environment
                temperature=0.7,
                max_tokens=300
            )

            # Parse AI response and extract structured data
            updated_context, new_stage = self._parse_ai_response(ai_response, context)

            return ai_response, updated_context, new_stage

        except Exception as e:
            # Fallback response if AI fails
            return self._get_fallback_response(user_message, context), context, context.get("stage", "planning")

    def _build_prompt(self, user_message: str, context: Dict[str, Any], message_history: List[Dict]) -> str:
        """Build intelligent prompt for the AI model"""

        # Format conversation history
        history_text = ""
        if message_history:
            history_text = "Recent conversation:\n"
            for msg in message_history[-5:]:  # Last 5 messages for context
                role = "User" if msg["role"] == "user_input" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"

        prompt = f"""
You are an expert SAR (Search and Rescue) mission coordinator with extensive experience in emergency response operations, drone operations, and mission planning.

CURRENT MISSION CONTEXT:
- Mission Stage: {context.get('stage', 'planning')}
- Mission Type: {context.get('mission_type', 'Not specified')}
- Priority Level: {context.get('priority', 'Not specified')}
- Search Area: {context.get('search_area_description', 'Not specified')}
- Target Location: {context.get('target_location', 'Not specified')}
- Weather Conditions: {context.get('weather_conditions', 'Not specified')}
- Time Constraints: {context.get('time_limit_minutes', 'Not specified')} minutes
- Available Resources: {context.get('available_drones', 'Not specified')} drones

{history_text}

USER MESSAGE: {user_message}

As the SAR mission coordinator, provide a helpful, intelligent response that:
1. Acknowledges the user's input and shows understanding
2. Advances the mission planning process when possible
3. Asks clarifying questions when information is missing or unclear
4. Provides specific, actionable recommendations based on SAR best practices
5. Updates the mission context with any new information extracted from the conversation

If you need more information to proceed, ask specific clarifying questions.
If enough information exists, provide detailed mission planning recommendations.

Response should be conversational, professional, and demonstrate expertise in SAR operations.
Keep responses focused and actionable - avoid unnecessary verbosity.

Based on the conversation, suggest an updated mission stage (planning, ready_for_execution, executing, completed, etc.) and any context updates.
"""

        return prompt

    def _parse_ai_response(self, ai_response: str, current_context: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Parse AI response to extract structured context updates"""

        updated_context = current_context.copy()
        new_stage = updated_context.get("stage", "planning")

        # Try to extract structured information from AI response
        # This is a simple heuristic-based parser - could be enhanced with more sophisticated NLP

        response_lower = ai_response.lower()

        # Extract mission type if mentioned
        if any(word in response_lower for word in ["search", "rescue", "survey", "training"]):
            if "search" in response_lower:
                updated_context["mission_type"] = "search"
            elif "rescue" in response_lower:
                updated_context["mission_type"] = "rescue"
            elif "survey" in response_lower:
                updated_context["mission_type"] = "survey"
            elif "training" in response_lower:
                updated_context["mission_type"] = "training"

        # Extract priority if mentioned
        if any(word in response_lower for word in ["low priority", "medium priority", "high priority", "critical", "urgent"]):
            if "critical" in response_lower or "urgent" in response_lower:
                updated_context["priority"] = "critical"
            elif "high" in response_lower:
                updated_context["priority"] = "high"
            elif "medium" in response_lower:
                updated_context["priority"] = "medium"
            elif "low" in response_lower:
                updated_context["priority"] = "low"

        # Extract location information if mentioned
        location_patterns = [
            r"latitude[:\s]+([-\d.]+)",
            r"longitude[:\s]+([-\d.]+)",
            r"coordinates?[:\s]+([-\d.]+)\s*,\s*([-\d.]+)",
            r"location[:\s]+(.+?)(?:\n|$)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE)
            if match:
                if "coordinates" in pattern and len(match.groups()) >= 2:
                    updated_context["target_latitude"] = float(match.group(1))
                    updated_context["target_longitude"] = float(match.group(2))
                elif "latitude" in pattern:
                    updated_context["target_latitude"] = float(match.group(1))
                elif "longitude" in pattern:
                    updated_context["target_longitude"] = float(match.group(1))
                elif "location" in pattern:
                    updated_context["target_location"] = match.group(1).strip()

        # Extract time information
        time_patterns = [
            r"time limit[:\s]+(\d+)\s*(minutes?|mins?|hours?|hrs?)",
            r"duration[:\s]+(\d+)\s*(minutes?|mins?|hours?|hrs?)",
        ]

        for pattern in time_patterns:
            match = re.search(pattern, ai_response, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                unit = match.group(2).lower()
                if "hour" in unit:
                    updated_context["time_limit_minutes"] = value * 60
                else:
                    updated_context["time_limit_minutes"] = value

        # Determine new stage based on context and response
        if any(word in response_lower for word in ["ready to start", "ready for execution", "can begin", "proceed with"]):
            new_stage = "ready_for_execution"
        elif any(word in response_lower for word in ["executing", "in progress", "underway"]):
            new_stage = "executing"
        elif any(word in response_lower for word in ["complete", "finished", "done"]):
            new_stage = "completed"
        elif any(word in response_lower for word in ["need more information", "clarifying", "questions"]):
            new_stage = "planning"
        else:
            new_stage = "planning"

        updated_context["stage"] = new_stage
        updated_context["last_updated"] = datetime.utcnow().isoformat()

        return updated_context, new_stage

    def _get_fallback_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate fallback response when AI is unavailable"""

        fallback_responses = [
            "I understand you're working on mission planning. Could you provide more details about the search area and mission objectives?",
            "I'm here to help with your SAR mission planning. What specific information can you share about the target location and timing requirements?",
            "To better assist with mission planning, I need more details about the search parameters and operational constraints.",
        ]

        # Simple keyword-based response
        message_lower = user_message.lower()

        if "location" in message_lower or "area" in message_lower:
            return "I see you're discussing the search location. Can you provide the latitude and longitude coordinates, or describe the target area in more detail?"
        elif "time" in message_lower or "urgent" in message_lower:
            return "Time is critical in SAR operations. What's the estimated time window for this mission, and are there any weather constraints?"
        elif "drone" in message_lower or "equipment" in message_lower:
            return "Regarding drone resources, how many aircraft are available and what capabilities do they have (thermal imaging, night vision, etc.)?"
        else:
            return "Thank you for your input. To provide the best mission planning assistance, could you elaborate on the specific requirements or constraints for this operation?"

    def get_mission_summary(self, context: Dict[str, Any]) -> str:
        """Generate a mission summary based on current context"""

        summary_parts = []

        if context.get("mission_type"):
            summary_parts.append(f"Mission Type: {context['mission_type'].title()}")

        if context.get("priority"):
            summary_parts.append(f"Priority: {context['priority'].title()}")

        if context.get("target_location"):
            summary_parts.append(f"Target Area: {context['target_location']}")

        if context.get("time_limit_minutes"):
            hours = context["time_limit_minutes"] // 60
            minutes = context["time_limit_minutes"] % 60
            if hours > 0:
                summary_parts.append(f"Time Limit: {hours}h {minutes}m")
            else:
                summary_parts.append(f"Time Limit: {minutes} minutes")

        if context.get("available_drones"):
            summary_parts.append(f"Available Drones: {context['available_drones']}")

        return " | ".join(summary_parts) if summary_parts else "Mission planning in progress..."