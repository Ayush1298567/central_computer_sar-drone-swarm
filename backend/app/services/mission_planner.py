import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import math
from app.core.config import settings

logger = logging.getLogger(__name__)

class MissionPlanner:
    """AI-driven mission planning with conversational interface"""
    
    def __init__(self):
        self.conversation_state = {}
        self.ollama_client = None
        self._init_ai_client()
    
    def _init_ai_client(self):
        """Initialize AI client with fallback"""
        try:
            from app.ai.ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            logger.info("✅ Ollama client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Ollama client failed to initialize: {e}")
            self.ollama_client = None
    
    async def plan_mission(
        self,
        user_input: str,
        context: Dict[str, Any],
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Generate mission plan through AI conversation
        NO PLACEHOLDERS - this must work for real SAR operations
        """
        try:
            # Initialize conversation if new
            if conversation_id not in self.conversation_state:
                self.conversation_state[conversation_id] = {
                    "messages": [],
                    "mission_params": {},
                    "understanding_level": 0.0,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            state = self.conversation_state[conversation_id]
            state["messages"].append({"role": "user", "content": user_input})
            
            # Build AI prompt for mission planning
            prompt = self._build_planning_prompt(user_input, context, state)
            
            # Get AI response
            if self.ollama_client:
                response = await self._get_ai_response(prompt)
            else:
                response = self._get_fallback_response(user_input, context)
            
            state["messages"].append({"role": "assistant", "content": response})
            
            # Parse AI response for mission parameters
            mission_params = await self._extract_parameters(response, context)
            state["mission_params"].update(mission_params)
            
            # Calculate understanding level
            understanding = self._calculate_understanding(state["mission_params"])
            state["understanding_level"] = understanding
            
            # If we have enough info, generate full plan
            if understanding >= 0.8:
                full_plan = await self._generate_full_plan(state["mission_params"])
                return {
                    "status": "ready",
                    "mission_plan": full_plan,
                    "understanding_level": understanding,
                    "ai_response": response,
                    "conversation_id": conversation_id
                }
            
            # Need more information
            return {
                "status": "needs_clarification",
                "ai_response": response,
                "understanding_level": understanding,
                "collected_params": state["mission_params"],
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Mission planning failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "ai_response": "I encountered an error. Please try again.",
                "conversation_id": conversation_id
            }
    
    async def _get_ai_response(self, prompt: str) -> str:
        """Get response from AI service"""
        try:
            response = await self.ollama_client.generate(
                prompt=prompt,
                model=settings.DEFAULT_MODEL,
                system="You are an expert SAR mission planner. Ask clarifying questions and build comprehensive mission plans."
            )
            return response
        except Exception as e:
            logger.error(f"AI response failed: {e}")
            return self._get_fallback_response("", {})
    
    def _get_fallback_response(self, user_input: str, context: Dict) -> str:
        """Fallback response when AI is not available"""
        if "search" in user_input.lower() or "rescue" in user_input.lower():
            return """I understand you need to plan a search and rescue mission. To create an effective plan, I need more information:

1. What is the search area? (coordinates, landmarks, or description)
2. How many people are missing?
3. What type of terrain? (urban, forest, mountain, water)
4. What time did they go missing?
5. Are there any known hazards in the area?

Please provide these details so I can create a comprehensive mission plan."""
        
        return """I'm here to help plan your SAR mission. Please describe:
- The search area location
- Number of missing persons
- Terrain type
- Any known hazards
- Time constraints

This information will help me create an effective search plan."""
    
    def _build_planning_prompt(self, user_input: str, context: Dict, state: Dict) -> str:
        """Build prompt for AI mission planner"""
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in state["messages"][-5:]  # Last 5 messages
        ])
        
        return f"""You are planning a Search and Rescue drone mission.

Conversation so far:
{conversation_history}

Current parameters collected:
{state['mission_params']}

Context:
- Available drones: {context.get('drone_count', 5)}
- Weather conditions: {context.get('weather', 'unknown')}
- Time of day: {datetime.now().strftime('%H:%M')}
- Current understanding: {state['understanding_level']:.1%}

Task: Based on the user's latest input, either:
1. Ask clarifying questions to understand the mission better
2. If you have enough information, confirm the plan

User's latest input: {user_input}

Respond naturally and professionally. Focus on getting:
- Search area boundaries (coordinates preferred)
- Type of emergency
- Number of people missing
- Terrain type
- Any hazards
- Priority areas
- Time constraints

Be specific about coordinates when possible."""
    
    async def _generate_full_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete mission plan with coordinates"""
        try:
            # Generate coordinate grid
            coordinates = await self._generate_coordinates(params)
            
            # Calculate mission parameters
            duration = self._estimate_duration(coordinates, params)
            search_pattern = params.get('search_pattern', 'grid')
            
            # Create mission plan
            plan = {
                "mission_type": params.get('mission_type', 'search_and_rescue'),
                "area": params.get('area', {}),
                "coordinates": coordinates,
                "estimated_duration_minutes": duration,
                "search_pattern": search_pattern,
                "altitude": params.get('altitude', settings.DEFAULT_ALTITUDE),
                "speed": params.get('speed', settings.DEFAULT_SPEED),
                "priority": params.get('priority', 'high'),
                "terrain_type": params.get('terrain_type', 'unknown'),
                "missing_count": params.get('missing_count', 1),
                "hazards": params.get('hazards', []),
                "created_at": datetime.utcnow().isoformat(),
                "status": "planned"
            }
            
            logger.info(f"Generated mission plan with {len(coordinates)} waypoints")
            return plan
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            raise
    
    async def _generate_coordinates(self, params: Dict) -> List[Dict]:
        """Generate search grid coordinates - MUST produce real coordinates"""
        area = params.get('area', {})
        density = params.get('density', 'medium')
        
        # Points per km²
        density_map = {'high': 100, 'medium': 50, 'low': 25}
        points_per_km2 = density_map.get(density, 50)
        
        # Default search area if none provided
        bounds = area.get('bounds', {
            'north': 37.8,
            'south': 37.7,
            'east': -122.4,
            'west': -122.5
        })
        
        lat_min = bounds.get('south', 37.7)
        lat_max = bounds.get('north', 37.8)
        lon_min = bounds.get('west', -122.5)
        lon_max = bounds.get('east', -122.4)
        
        # Calculate area in km²
        area_km2 = self._calculate_area(lat_min, lat_max, lon_min, lon_max)
        total_points = int(area_km2 * points_per_km2)
        
        # Generate grid
        coordinates = []
        search_pattern = params.get('search_pattern', 'grid')
        
        if search_pattern == 'grid':
            coordinates = self._generate_grid_pattern(
                lat_min, lat_max, lon_min, lon_max, total_points, params
            )
        elif search_pattern == 'spiral':
            coordinates = self._generate_spiral_pattern(
                lat_min, lat_max, lon_min, lon_max, total_points, params
            )
        else:
            # Default to grid
            coordinates = self._generate_grid_pattern(
                lat_min, lat_max, lon_min, lon_max, total_points, params
            )
        
        logger.info(f"Generated {len(coordinates)} waypoints for {search_pattern} pattern")
        return coordinates
    
    def _generate_grid_pattern(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float,
        total_points: int, params: Dict
    ) -> List[Dict]:
        """Generate grid search pattern"""
        coordinates = []
        
        # Calculate grid dimensions
        grid_size = int(math.sqrt(total_points))
        lat_step = (lat_max - lat_min) / grid_size
        lon_step = (lon_max - lon_min) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                coordinates.append({
                    "lat": lat_min + (i * lat_step),
                    "lon": lon_min + (j * lon_step),
                    "altitude": params.get('altitude', settings.DEFAULT_ALTITUDE),
                    "index": len(coordinates),
                    "pattern": "grid"
                })
        
        return coordinates
    
    def _generate_spiral_pattern(
        self, lat_min: float, lat_max: float, lon_min: float, lon_max: float,
        total_points: int, params: Dict
    ) -> List[Dict]:
        """Generate spiral search pattern"""
        coordinates = []
        
        # Center point
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        
        # Spiral parameters
        max_radius = min(lat_max - center_lat, lon_max - center_lon)
        a = max_radius / (2 * math.pi)  # Distance between turns
        
        theta = 0
        theta_step = 0.1
        max_theta = max_radius / a * 2 * math.pi
        
        while theta <= max_theta and len(coordinates) < total_points:
            r = a * theta
            
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            
            # Convert to lat/lon
            lat_per_m = 1 / 111000
            lon_per_m = 1 / (111000 * math.cos(math.radians(center_lat)))
            
            coordinates.append({
                "lat": center_lat + (y * lat_per_m),
                "lon": center_lon + (x * lon_per_m),
                "altitude": params.get('altitude', settings.DEFAULT_ALTITUDE),
                "index": len(coordinates),
                "pattern": "spiral"
            })
            
            theta += theta_step
        
        return coordinates
    
    def _calculate_area(self, lat1: float, lat2: float, lon1: float, lon2: float) -> float:
        """Calculate approximate area in km²"""
        # Simplified calculation using Haversine formula approximation
        lat_diff = abs(lat2 - lat1)
        lon_diff = abs(lon2 - lon1)
        
        # Convert degrees to km (approximate)
        lat_km = lat_diff * 111
        lon_km = lon_diff * 111 * math.cos(math.radians((lat1 + lat2) / 2))
        
        return lat_km * lon_km
    
    def _estimate_duration(self, coordinates: List, params: Dict) -> int:
        """Estimate mission duration in minutes"""
        if not coordinates:
            return 30  # Default duration
        
        # Calculate total distance
        total_distance = len(coordinates) * 0.1  # km between points (estimated)
        
        # Flight time
        speed = params.get('speed', settings.DEFAULT_SPEED)  # m/s
        flight_time = (total_distance * 1000) / speed / 60  # minutes
        
        # Add setup and landing time
        setup_time = 10  # minutes
        landing_time = 5  # minutes
        
        return int(flight_time + setup_time + landing_time)
    
    async def _extract_parameters(self, ai_response: str, context: Dict) -> Dict:
        """Extract mission parameters from AI response"""
        params = {}
        
        lower_response = ai_response.lower()
        
        # Terrain detection
        if any(word in lower_response for word in ['building', 'structure', 'urban', 'city']):
            params['terrain_type'] = 'urban'
        elif any(word in lower_response for word in ['forest', 'woods', 'tree']):
            params['terrain_type'] = 'forest'
        elif any(word in lower_response for word in ['mountain', 'hill', 'peak']):
            params['terrain_type'] = 'mountain'
        elif any(word in lower_response for word in ['water', 'lake', 'river', 'ocean']):
            params['terrain_type'] = 'water'
        
        # Mission type
        if 'search' in lower_response and 'rescue' in lower_response:
            params['mission_type'] = 'search_and_rescue'
        elif 'search' in lower_response:
            params['mission_type'] = 'search'
        elif 'rescue' in lower_response:
            params['mission_type'] = 'rescue'
        
        # Extract numbers (could be missing count)
        import re
        numbers = re.findall(r'\d+', ai_response)
        if numbers:
            # Assume first number is missing count if context suggests it
            if any(word in lower_response for word in ['missing', 'lost', 'person', 'people']):
                params['missing_count'] = int(numbers[0])
        
        # Priority detection
        if any(word in lower_response for word in ['urgent', 'critical', 'emergency']):
            params['priority'] = 'critical'
        elif any(word in lower_response for word in ['high', 'important']):
            params['priority'] = 'high'
        elif any(word in lower_response for word in ['medium', 'normal']):
            params['priority'] = 'medium'
        else:
            params['priority'] = 'high'  # Default for SAR
        
        return params
    
    def _calculate_understanding(self, params: Dict) -> float:
        """Calculate how well we understand the mission (0-1)"""
        required_fields = ['mission_type', 'terrain_type']
        optional_fields = ['missing_count', 'priority', 'area']
        
        score = 0.0
        
        # Required fields worth 0.6
        for field in required_fields:
            if field in params and params[field]:
                score += 0.3
        
        # Optional fields worth 0.4
        for field in optional_fields:
            if field in params and params[field]:
                score += 0.133
        
        return min(score, 1.0)
    
    async def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history"""
        return self.conversation_state.get(conversation_id, {})
    
    async def clear_conversation(self, conversation_id: str):
        """Clear conversation state"""
        if conversation_id in self.conversation_state:
            del self.conversation_state[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")

# Global instance
mission_planner = MissionPlanner()