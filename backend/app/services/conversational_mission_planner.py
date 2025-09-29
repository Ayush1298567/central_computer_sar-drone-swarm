"""
Conversational AI mission planner service.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..models import Mission, ChatMessage

logger = logging.getLogger(__name__)


class ConversationalMissionPlanner:
    """AI-powered conversational mission planner."""

    def __init__(self):
        self.conversation_state = {}
        self.mission_parameters = {}

    async def process_message(
        self,
        user_message: str,
        mission: Mission,
        history: List[ChatMessage]
    ) -> Dict[str, Any]:
        """Process a user message and generate AI response."""

        # Analyze current conversation state
        conversation_context = self._analyze_conversation_context(history)

        # Extract mission parameters from user message
        extracted_params = self._extract_mission_parameters(user_message, conversation_context)

        # Update mission if parameters were extracted
        if extracted_params:
            self._update_mission_parameters(mission, extracted_params)

        # Generate AI response based on current state and user input
        ai_response = self._generate_ai_response(
            user_message,
            mission,
            conversation_context,
            extracted_params
        )

        # Determine next steps and suggested actions
        suggested_actions = self._generate_suggested_actions(
            conversation_context,
            extracted_params
        )

        # Check if mission planning is complete
        mission_updates = self._check_planning_completion(mission, conversation_context)

        return {
            "message": ai_response,
            "context": conversation_context,
            "suggested_actions": suggested_actions,
            "mission_updates": mission_updates
        }

    def _analyze_conversation_context(self, history: List[ChatMessage]) -> Dict[str, Any]:
        """Analyze the conversation history to understand current planning stage."""

        context = {
            "stage": "unknown",
            "parameters_gathered": {},
            "questions_asked": [],
            "user_responses": []
        }

        # Extract information from conversation history
        for message in history:
            if message.sender == "user":
                context["user_responses"].append(message.message)
            elif message.sender == "ai":
                context["questions_asked"].append(message.message)
                # Look for stage indicators in AI messages
                if "location" in message.message.lower():
                    context["stage"] = "location"
                elif "area" in message.message.lower() or "size" in message.message.lower():
                    context["stage"] = "area"
                elif "altitude" in message.message.lower():
                    context["stage"] = "altitude"
                elif "priority" in message.message.lower():
                    context["stage"] = "priority"
                elif "weather" in message.message.lower():
                    context["stage"] = "weather"

        # Determine current stage based on what's been discussed
        if not any("location" in response.lower() for response in context["user_responses"]):
            context["stage"] = "location"
        elif not any("area" in response.lower() or "size" in response.lower() for response in context["user_responses"]):
            context["stage"] = "area"
        elif not any("altitude" in response.lower() for response in context["user_responses"]):
            context["stage"] = "altitude"
        else:
            context["stage"] = "confirmation"

        return context

    def _extract_mission_parameters(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract mission parameters from user message using simple pattern matching."""

        parameters = {}
        message_lower = message.lower()

        # Location extraction (simple coordinate or address patterns)
        if context["stage"] == "location":
            # Look for coordinate patterns like "37.7749, -122.4194"
            import re
            coord_pattern = r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)'
            coords = re.findall(coord_pattern, message)

            if coords:
                parameters["center_lat"] = float(coords[0][0])
                parameters["center_lng"] = float(coords[0][1])
                parameters["location_detected"] = True

            # Look for common location keywords
            elif any(word in message_lower for word in ["downtown", "airport", "hospital", "school", "building"]):
                parameters["location_type"] = "urban"
            elif any(word in message_lower for word in ["forest", "mountain", "desert", "field"]):
                parameters["location_type"] = "wilderness"

        # Area size extraction
        elif context["stage"] == "area":
            # Look for area measurements
            area_patterns = [
                r'(\d+\.?\d*)\s*(square\s*kilometers?|km2?|sq\s*km)',
                r'(\d+\.?\d*)\s*(hectares?|ha)',
                r'(\d+\.?\d*)\s*(acres?|ac)',
                r'(\d+\.?\d*)\s*(miles?|mi)',
            ]

            for pattern in area_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)

                    # Convert to square kilometers
                    if "hectare" in unit or "ha" in unit:
                        value = value * 0.01
                    elif "acre" in unit or "ac" in unit:
                        value = value * 0.004047
                    elif "mile" in unit or "mi" in unit:
                        value = value * 2.59

                    parameters["area_size_km2"] = value
                    break

        # Altitude extraction
        elif context["stage"] == "altitude":
            alt_patterns = [
                r'(\d+\.?\d*)\s*(meters?|m)\s*(altitude|height)',
                r'(\d+\.?\d*)\s*(feet|ft)\s*(altitude|height)',
            ]

            for pattern in alt_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)

                    # Convert to meters if needed
                    if "feet" in unit or "ft" in unit:
                        value = value * 0.3048

                    parameters["search_altitude"] = value
                    break

        # Priority extraction
        if any(word in message_lower for word in ["critical", "emergency", "urgent", "high priority"]):
            parameters["priority"] = "critical"
        elif any(word in message_lower for word in ["important", "moderate"]):
            parameters["priority"] = "high"
        elif any(word in message_lower for word in ["low", "routine"]):
            parameters["priority"] = "low"

        return parameters

    def _update_mission_parameters(self, mission: Mission, parameters: Dict[str, Any]):
        """Update mission object with extracted parameters."""
        for key, value in parameters.items():
            if hasattr(mission, key):
                setattr(mission, key, value)

    def _generate_ai_response(
        self,
        user_message: str,
        mission: Mission,
        context: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> str:
        """Generate an AI response based on current context and user input."""

        stage = context["stage"]

        if stage == "location":
            if parameters.get("location_detected"):
                return f"Great! I've set the mission center to coordinates {parameters['center_lat']:.4f}, {parameters['center_lng']:.4f}. Now, what size area would you like to search? (e.g., '5 square kilometers' or '2 hectares')"
            else:
                return "I need to know the location for the search area. Please provide coordinates (latitude, longitude) or describe the general area you want to search."

        elif stage == "area":
            if parameters.get("area_size_km2"):
                area_km2 = parameters["area_size_km2"]
                return f"Perfect! I've set the search area to {area_km2:.2f} square kilometers. Now, at what altitude should the drones fly? (e.g., '50 meters' or '100 feet')"
            else:
                return "Please specify the size of the area you want to search. You can say something like '2 square kilometers' or '500 acres'."

        elif stage == "altitude":
            if parameters.get("search_altitude"):
                altitude = parameters["search_altitude"]
                return f"Excellent! I've set the search altitude to {altitude:.1f} meters. Based on the information you've provided, I can now create a mission plan. Let me summarize what we have so far..."

        elif stage == "confirmation":
            return self._generate_mission_summary(mission, parameters)

        else:
            return "I'm not sure what you're asking about. Could you please clarify what aspect of the mission you'd like to discuss?"

    def _generate_suggested_actions(self, context: Dict[str, Any], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggested next actions for the user."""

        actions = []

        if context["stage"] == "location":
            actions.append({
                "type": "provide_coordinates",
                "label": "Provide Coordinates",
                "description": "Enter latitude and longitude for the search area",
                "example": "37.7749, -122.4194"
            })
            actions.append({
                "type": "describe_location",
                "label": "Describe Location",
                "description": "Describe the general area or landmarks",
                "example": "Downtown area near the central hospital"
            })

        elif context["stage"] == "area":
            actions.append({
                "type": "specify_area",
                "label": "Specify Area Size",
                "description": "Enter the size of the search area",
                "example": "5 square kilometers"
            })

        elif context["stage"] == "altitude":
            actions.append({
                "type": "set_altitude",
                "label": "Set Flight Altitude",
                "description": "Specify the altitude for drone operations",
                "example": "50 meters"
            })

        if context["stage"] != "location":
            actions.append({
                "type": "change_location",
                "label": "Change Location",
                "description": "Go back and modify the search location"
            })

        if context["stage"] != "area":
            actions.append({
                "type": "change_area",
                "label": "Change Area Size",
                "description": "Go back and modify the search area size"
            })

        return actions

    def _generate_mission_summary(self, mission: Mission, parameters: Dict[str, Any]) -> str:
        """Generate a summary of the current mission plan."""

        summary = "Here's a summary of your mission plan:\n\n"

        if hasattr(mission, 'center_lat') and mission.center_lat:
            summary += f"📍 Location: {mission.center_lat:.4f}, {mission.center_lng:.4f}\n"

        if hasattr(mission, 'area_size_km2') and mission.area_size_km2:
            summary += f"🏔️ Search Area: {mission.area_size_km2:.2f} km²\n"

        if hasattr(mission, 'search_altitude') and mission.search_altitude:
            summary += f"✈️ Flight Altitude: {mission.search_altitude:.1f} meters\n"

        if hasattr(mission, 'priority'):
            priority_emoji = {"low": "🟢", "normal": "🟡", "high": "🟠", "critical": "🔴"}
            summary += f"🚨 Priority: {priority_emoji.get(mission.priority, '⚪')} {mission.priority.title()}\n"

        summary += "\nWould you like to make any changes to this plan, or should I proceed with creating the mission?"

        return summary

    def _check_planning_completion(self, mission: Mission, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if mission planning is complete and ready for execution."""

        required_params = ['center_lat', 'center_lng', 'area_size_km2', 'search_altitude']
        updates = {}

        # Check if all required parameters are set
        all_params_set = all(
            hasattr(mission, param) and getattr(mission, param) is not None
            for param in required_params
        )

        if all_params_set and context["stage"] == "confirmation":
            updates["status"] = "ready_for_approval"
            updates["estimated_drones"] = self._calculate_required_drones(mission)
            updates["estimated_duration"] = self._calculate_mission_duration(mission)

        return updates

    def _calculate_required_drones(self, mission: Mission) -> int:
        """Calculate how many drones are needed for the mission."""
        # Simple calculation based on area size
        area_km2 = getattr(mission, 'area_size_km2', 1)
        base_drones = 1

        # Add drones based on area size
        if area_km2 > 1:
            base_drones += int(area_km2 / 2)  # 1 drone per 2 km²
        if area_km2 > 10:
            base_drones += int(area_km2 / 10)  # Additional drones for large areas

        return min(base_drones, 10)  # Cap at 10 drones

    def _calculate_mission_duration(self, mission: Mission) -> int:
        """Estimate mission duration in minutes."""
        area_km2 = getattr(mission, 'area_size_km2', 1)
        altitude = getattr(mission, 'search_altitude', 50)

        # Base time calculation
        base_time = 30  # 30 minutes base

        # Add time based on area size (larger areas take longer)
        area_time = int(area_km2 * 10)  # 10 minutes per km²

        # Adjust for altitude (higher altitude = faster coverage but less detail)
        altitude_factor = max(0.5, altitude / 100)  # Higher altitude = less time needed

        total_time = int((base_time + area_time) * altitude_factor)
        return min(total_time, 180)  # Cap at 3 hours

    def analyze_planning_progress(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """Analyze the overall progress of mission planning."""

        progress = {
            "stage": "unknown",
            "completion_percentage": 0,
            "parameters_gathered": {},
            "next_steps": []
        }

        # Count different types of information gathered
        location_found = False
        area_found = False
        altitude_found = False
        priority_found = False

        for message in messages:
            message_text = message.message.lower()

            if any(word in message_text for word in ["lat", "lng", "coordinate", "location"]):
                location_found = True
            if any(word in message_text for word in ["area", "size", "km2", "hectare", "acre"]):
                area_found = True
            if any(word in message_text for word in ["altitude", "height", "meter", "feet"]):
                altitude_found = True
            if any(word in message_text for word in ["priority", "urgent", "critical", "important"]):
                priority_found = True

        # Calculate completion percentage
        total_params = 4  # location, area, altitude, priority
        completed_params = sum([location_found, area_found, altitude_found, priority_found])
        progress["completion_percentage"] = int((completed_params / total_params) * 100)

        # Determine current stage
        if not location_found:
            progress["stage"] = "location"
            progress["next_steps"] = ["Gather location coordinates or description"]
        elif not area_found:
            progress["stage"] = "area"
            progress["next_steps"] = ["Determine search area size"]
        elif not altitude_found:
            progress["stage"] = "altitude"
            progress["next_steps"] = ["Set appropriate flight altitude"]
        else:
            progress["stage"] = "confirmation"
            progress["next_steps"] = ["Review and approve mission plan"]

        progress["parameters_gathered"] = {
            "location": location_found,
            "area": area_found,
            "altitude": altitude_found,
            "priority": priority_found
        }

        return progress


# Global instance
conversational_mission_planner = ConversationalMissionPlanner()