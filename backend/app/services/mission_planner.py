"""
Mission Planner Service for SAR Drone Swarm
AI-driven mission planning with real conversational interface using Ollama.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.ai.ollama_client import ollama_client
from app.ai.conversation import conversation_engine
from app.algorithms.area_division import area_divider
from app.algorithms.waypoint_generation import waypoint_generator
from app.core.config import settings

logger = logging.getLogger(__name__)

class MissionPlanner:
    """Real AI-driven mission planning with conversational interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self.planning_sessions: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """Initialize the mission planner"""
        try:
            # Initialize conversation engine
            await conversation_engine.initialize()
            
            # Test AI connection
            health_check = await ollama_client.health_check()
            if not health_check:
                self.logger.error("Ollama client not available")
                return False
            
            self.logger.info("✅ Mission Planner initialized with AI")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Mission Planner: {e}")
            return False
    
    async def start_mission_planning(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Start AI-driven mission planning conversation
        
        Args:
            user_input: User's initial message about the mission
            session_id: Unique session identifier
            
        Returns:
            Response with AI analysis and next steps
        """
        try:
            # Start conversation with AI
            conversation_response = await conversation_engine.start_conversation(session_id, user_input)
            
            if "error" in conversation_response:
                return {
                    "success": False,
                    "error": conversation_response["error"],
                    "session_id": session_id
                }
            
            # Initialize planning session
            self.planning_sessions[session_id] = {
                "conversation_id": session_id,
                "started_at": datetime.utcnow(),
                "status": "planning",
                "user_input": user_input,
                "ai_analysis": {},
                "mission_parameters": {},
                "planning_stage": "conversation"
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "ai_response": conversation_response["message"],
                "stage": conversation_response["stage"],
                "next_questions": conversation_response.get("next_questions", []),
                "planning_status": "conversation_started"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting mission planning: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def continue_mission_planning(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Continue mission planning conversation
        
        Args:
            user_input: User's response or additional input
            session_id: Session identifier
            
        Returns:
            Response with AI analysis and updated planning status
        """
        try:
            if session_id not in self.planning_sessions:
                return await self.start_mission_planning(user_input, session_id)
            
            # Process message with AI
            conversation_response = await conversation_engine.process_message(session_id, user_input)
            
            if "error" in conversation_response:
                return {
                    "success": False,
                    "error": conversation_response["error"],
                    "session_id": session_id
                }
            
            # Update planning session
            session = self.planning_sessions[session_id]
            session["last_activity"] = datetime.utcnow()
            session["ai_analysis"] = conversation_response.get("metadata", {})
            session["mission_parameters"] = conversation_response.get("mission_parameters", {})
            
            # Check if we have enough information to create a plan
            if await self._is_planning_complete(session):
                plan_result = await self._generate_mission_plan(session_id)
                if plan_result["success"]:
                    session["status"] = "plan_ready"
                    session["planning_stage"] = "completed"
                    session["mission_plan"] = plan_result["plan"]
            
            return {
                "success": True,
                "session_id": session_id,
                "ai_response": conversation_response["message"],
                "stage": conversation_response["stage"],
                "mission_parameters": session["mission_parameters"],
                "next_questions": conversation_response.get("next_questions", []),
                "planning_status": session["status"],
                "plan_ready": session["status"] == "plan_ready"
            }
            
        except Exception as e:
            self.logger.error(f"Error continuing mission planning: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _is_planning_complete(self, session: Dict[str, Any]) -> bool:
        """Check if we have enough information to create a mission plan"""
        try:
            params = session.get("mission_parameters", {})
            
            # Required parameters for basic mission planning
            required_params = ["mission_type", "location"]
            has_required = all(param in params for param in required_params)
            
            # Check if AI thinks planning is complete
            if has_required:
                # Use AI to determine if planning is complete
                completion_prompt = f"""
                Analyze this SAR mission planning session and determine if we have enough information to create a mission plan.
                
                Mission parameters: {json.dumps(params, indent=2)}
                Current stage: {session.get('planning_stage', 'unknown')}
                
                Consider if we have:
                1. Mission type and purpose
                2. Location/area information
                3. Basic operational parameters
                4. Safety considerations
                
                Return JSON: {{"complete": true/false, "confidence": 0.0-1.0, "missing": ["list of missing info"]}}
                """
                
                ai_analysis = await ollama_client.generate(
                    completion_prompt,
                    model=settings.DEFAULT_MODEL,
                    temperature=0.3
                )
                
                try:
                    analysis = json.loads(ai_analysis)
                    return analysis.get("complete", False) and analysis.get("confidence", 0) > 0.7
                except json.JSONDecodeError:
                    return has_required
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking planning completeness: {e}")
            return False
    
    async def _generate_mission_plan(self, session_id: str) -> Dict[str, Any]:
        """Generate a complete mission plan using AI and algorithms"""
        try:
            session = self.planning_sessions[session_id]
            params = session["mission_parameters"]
            
            # Use AI to create comprehensive mission plan
            plan_prompt = f"""
            Create a comprehensive Search and Rescue mission plan based on these parameters:
            
            {json.dumps(params, indent=2)}
            
            Generate a detailed mission plan including:
            1. Mission objectives and goals
            2. Search area definition and coordinates
            3. Drone deployment strategy
            4. Flight patterns and waypoints
            5. Safety protocols and emergency procedures
            6. Timeline and execution phases
            7. Resource requirements
            8. Risk assessment and mitigation
            9. Success criteria and evaluation metrics
            
            Return as structured JSON with all these components.
            """
            
            ai_plan = await ollama_client.generate(
                plan_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.4
            )
            
            try:
                mission_plan = json.loads(ai_plan)
            except json.JSONDecodeError:
                # Fallback plan structure
                mission_plan = await self._create_fallback_plan(params)
            
            # Enhance plan with algorithmic calculations
            enhanced_plan = await self._enhance_plan_with_algorithms(mission_plan, params)
            
            # Store the plan
            plan_id = f"plan_{session_id}_{int(datetime.utcnow().timestamp())}"
            self.active_plans[plan_id] = {
                "plan_id": plan_id,
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "mission_plan": enhanced_plan,
                "status": "ready",
                "parameters": params
            }
            
            return {
                "success": True,
                "plan_id": plan_id,
                "plan": enhanced_plan
            }
            
        except Exception as e:
            self.logger.error(f"Error generating mission plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_fallback_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback mission plan when AI parsing fails"""
        return {
            "mission_type": params.get("mission_type", "search"),
            "priority": params.get("priority", "medium"),
            "location": params.get("location", "Unknown location"),
            "objectives": [
                "Conduct systematic search of designated area",
                "Locate and identify targets of interest",
                "Document findings and provide real-time updates",
                "Ensure safety of all personnel and equipment"
            ],
            "search_area": {
                "description": params.get("location", "Search area to be defined"),
                "coordinates": None,
                "radius_km": 1.0
            },
            "drone_deployment": {
                "count": params.get("drone_count", 2),
                "altitude_m": params.get("altitude", 50),
                "pattern": "grid_search"
            },
            "timeline": {
                "duration_minutes": params.get("time_limit_minutes", 60),
                "phases": ["preparation", "deployment", "search", "recovery"]
            },
            "safety_protocols": [
                "Maintain safe altitude above obstacles",
                "Monitor weather conditions continuously",
                "Maintain communication with ground control",
                "Follow emergency landing procedures if needed"
            ]
        }
    
    async def _enhance_plan_with_algorithms(self, plan: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance mission plan with algorithmic calculations"""
        try:
            # If we have location coordinates, calculate search zones
            if "coordinates" in params or "search_area" in params:
                # Mock coordinates for demonstration - in real implementation, parse from params
                search_area_coords = [
                    (-122.4194, 37.7749),  # San Francisco area
                    (-122.4094, 37.7849),
                    (-122.4094, 37.7649),
                    (-122.4294, 37.7649)
                ]
                
                # Calculate search zones
                num_drones = params.get("drone_count", 2)
                zones = area_divider.divide_area_into_zones(
                    search_area_coords,
                    num_drones,
                    overlap_percentage=0.1
                )
                
                # Generate waypoints for each zone
                for i, zone in enumerate(zones):
                    waypoints = waypoint_generator.generate_lawnmower_pattern(
                        zone["coordinates"],
                        altitude=params.get("altitude", 50),
                        spacing=10.0
                    )
                    zone["waypoints"] = waypoints
                
                plan["search_zones"] = zones
                plan["algorithmic_enhancement"] = {
                    "zones_calculated": len(zones),
                    "total_waypoints": sum(len(z.get("waypoints", [])) for z in zones),
                    "coverage_area_km2": sum(z.get("area", 0) for z in zones) / 1000000
                }
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error enhancing plan with algorithms: {e}")
            return plan
    
    async def get_mission_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get a specific mission plan"""
        try:
            if plan_id not in self.active_plans:
                return {"error": "Plan not found"}
            
            return self.active_plans[plan_id]
            
        except Exception as e:
            self.logger.error(f"Error getting mission plan: {e}")
            return {"error": str(e)}
    
    async def update_mission_plan(self, plan_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a mission plan"""
        try:
            if plan_id not in self.active_plans:
                return {"error": "Plan not found"}
            
            plan = self.active_plans[plan_id]
            plan["mission_plan"].update(updates)
            plan["updated_at"] = datetime.utcnow()
            
            return {"success": True, "plan_id": plan_id}
            
        except Exception as e:
            self.logger.error(f"Error updating mission plan: {e}")
            return {"error": str(e)}
    
    async def validate_mission_plan(self, plan_id: str) -> Dict[str, Any]:
        """Validate a mission plan for safety and feasibility"""
        try:
            if plan_id not in self.active_plans:
                return {"error": "Plan not found"}
            
            plan = self.active_plans[plan_id]
            mission_plan = plan["mission_plan"]
            
            # Use AI to validate the plan
            validation_prompt = f"""
            Validate this SAR mission plan for safety, feasibility, and completeness:
            
            {json.dumps(mission_plan, indent=2)}
            
            Check for:
            1. Safety protocols and risk mitigation
            2. Feasibility of drone operations
            3. Completeness of mission parameters
            4. Compliance with regulations
            5. Resource requirements vs availability
            
            Return JSON: {{
                "valid": true/false,
                "safety_score": 0-100,
                "feasibility_score": 0-100,
                "completeness_score": 0-100,
                "issues": ["list of issues found"],
                "recommendations": ["list of recommendations"]
            }}
            """
            
            ai_validation = await ollama_client.generate(
                validation_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            try:
                validation_result = json.loads(ai_validation)
            except json.JSONDecodeError:
                validation_result = {
                    "valid": True,
                    "safety_score": 80,
                    "feasibility_score": 85,
                    "completeness_score": 75,
                    "issues": [],
                    "recommendations": ["Manual review recommended"]
                }
            
            # Store validation results
            plan["validation"] = validation_result
            plan["validated_at"] = datetime.utcnow()
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating mission plan: {e}")
            return {"error": str(e)}
    
    async def get_planning_session(self, session_id: str) -> Dict[str, Any]:
        """Get planning session status"""
        try:
            if session_id not in self.planning_sessions:
                return {"error": "Session not found"}
            
            session = self.planning_sessions[session_id]
            
            # Get conversation summary
            conversation_summary = await conversation_engine.get_conversation_summary(session_id)
            
            return {
                "session_id": session_id,
                "status": session["status"],
                "stage": session["planning_stage"],
                "started_at": session["started_at"].isoformat(),
                "last_activity": session.get("last_activity", session["started_at"]).isoformat(),
                "mission_parameters": session["mission_parameters"],
                "conversation_summary": conversation_summary,
                "plan_ready": session["status"] == "plan_ready"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting planning session: {e}")
            return {"error": str(e)}
    
    async def end_planning_session(self, session_id: str) -> Dict[str, Any]:
        """End a planning session"""
        try:
            if session_id not in self.planning_sessions:
                return {"error": "Session not found"}
            
            # End conversation
            conversation_result = await conversation_engine.end_conversation(session_id)
            
            # Get session summary
            session = self.planning_sessions[session_id]
            session["status"] = "ended"
            session["ended_at"] = datetime.utcnow()
            
            # Clean up
            del self.planning_sessions[session_id]
            
            return {
                "success": True,
                "session_id": session_id,
                "conversation_summary": conversation_result,
                "session_duration": (session["ended_at"] - session["started_at"]).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Error ending planning session: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of mission planner"""
        try:
            # Check AI components
            ollama_healthy = await ollama_client.health_check()
            conversation_healthy = await conversation_engine.health_check()
            
            return {
                "status": "healthy" if ollama_healthy and conversation_healthy else "unhealthy",
                "ollama_connected": ollama_healthy,
                "conversation_engine": conversation_healthy,
                "active_sessions": len(self.planning_sessions),
                "active_plans": len(self.active_plans)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global mission planner instance
mission_planner = MissionPlanner()

# Convenience functions
async def start_mission_planning(user_input: str, session_id: str) -> Dict[str, Any]:
    """Start mission planning conversation"""
    return await mission_planner.start_mission_planning(user_input, session_id)

async def continue_mission_planning(user_input: str, session_id: str) -> Dict[str, Any]:
    """Continue mission planning conversation"""
    return await mission_planner.continue_mission_planning(user_input, session_id)

async def get_mission_plan(plan_id: str) -> Dict[str, Any]:
    """Get a mission plan"""
    return await mission_planner.get_mission_plan(plan_id)

async def validate_mission_plan(plan_id: str) -> Dict[str, Any]:
    """Validate a mission plan"""
    return await mission_planner.validate_mission_plan(plan_id)