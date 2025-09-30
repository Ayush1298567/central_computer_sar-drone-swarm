import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.core.config import settings
except ImportError:
    # Fallback to simple config for testing
    from app.core.simple_config import settings

class ConversationalMissionPlanner:
    """AI-powered conversational mission planner."""

    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
        self.conversations: dict = {}

    async def process_message(self, message_data: dict) -> dict:
        """Process user message and generate intelligent AI response."""
        message = message_data.get('message', '').lower()
        conversation_id = message_data.get('conversation_id', 'default')

        # Simple AI logic for mission planning
        response = await self._generate_ai_response(message, conversation_id)

        return {
            "response": response,
            "confidence": 0.9,
            "conversation_id": conversation_id,
            "message_type": "response",
            "next_action": self._determine_next_action(message)
        }

    async def _generate_ai_response(self, message: str, conversation_id: str) -> str:
        """Generate AI response based on message content."""

        # Mission planning keywords
        mission_keywords = {
            'search': 'I understand you want to conduct a search mission. I can help you plan the optimal search strategy.',
            'find': 'I\'ll help you locate what you\'re looking for. Let me gather the mission parameters.',
            'locate': 'Location-based missions require careful planning. I\'ll help you set up the search area.',
            'rescue': 'This appears to be a rescue operation. I\'ll prioritize safety and efficiency in the mission plan.',
            'monitor': 'I\'ll help you set up monitoring for the specified area with appropriate drone coverage.',
            'survey': 'Survey missions require systematic coverage. I\'ll help you plan the optimal flight paths.',
            'patrol': 'Patrol missions need regular coverage patterns. I\'ll help you establish the patrol routes.'
        }

        # Emergency keywords
        emergency_keywords = {
            'missing': 'This is a missing person case - I\'ll prioritize thorough coverage and quick response times.',
            'lost': 'I\'ll help you search for the lost individual with systematic coverage patterns.',
            'injured': 'Medical emergency detected - I\'ll prioritize the search area and enable emergency protocols.',
            'trapped': 'Trapped individual scenario - I\'ll focus on the specified location with emergency response coordination.',
            'collapsed': 'Structural collapse detected - I\'ll plan for hazardous area navigation and emergency services coordination.'
        }

        # Generate contextual response
        response_parts = []

        # Check for mission type
        for keyword, ai_response in mission_keywords.items():
            if keyword in message:
                response_parts.append(ai_response)
                break

        # Check for emergency situations
        for keyword, emergency_response in emergency_keywords.items():
            if keyword in message:
                response_parts.append(emergency_response)
                break

        # Default response if no specific patterns detected
        if not response_parts:
            response_parts.append("I understand your mission requirements. Let me help you plan an effective search and rescue operation.")

        # Add next steps
        response_parts.append("To create an optimal mission plan, I'll need to know more about the search area, available drones, and any specific requirements.")

        return " ".join(response_parts)

    def _determine_next_action(self, message: str) -> str:
        """Determine what the user should do next in the conversation."""

        if any(word in message for word in ['area', 'location', 'where', 'map']):
            return "area_selection"
        elif any(word in message for word in ['drone', 'drones', 'equipment']):
            return "drone_selection"
        elif any(word in message for word in ['time', 'duration', 'when']):
            return "time_preferences"
        elif any(word in message for word in ['altitude', 'height', 'flight']):
            return "flight_parameters"
        else:
            return "mission_details"

# Global instance
conversational_planner = None

def get_conversational_planner():
    """Get or create the global conversational planner instance."""
    global conversational_planner
    if conversational_planner is None:
        # This will be initialized properly when the app starts
        conversational_planner = ConversationalMissionPlanner(None)
    return conversational_planner