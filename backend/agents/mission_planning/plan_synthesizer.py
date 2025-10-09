"""
Plan Synthesizer Agent
Synthesizes gathered information into a complete mission plan
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service
from ...services.database import db_service

logger = logging.getLogger(__name__)

class PlanSynthesizerAgent(BaseAgent):
    """Synthesizes mission information into a complete operational plan"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("plan_synthesizer", redis_service, websocket_manager)
        self.pending_plans: Dict[str, Dict[str, Any]] = {}
    
    async def start_agent(self) -> None:
        """Start the plan synthesizer"""
        await self.subscribe_to_channel("mission.plan_request")
        await self.subscribe_to_channel("mission.info_complete")
        await self.subscribe_to_channel("drone.fleet_status")
        logger.info("Plan Synthesizer Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the plan synthesizer"""
        logger.info("Plan Synthesizer Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "mission.plan_request":
                await self._handle_plan_request(message)
            elif channel == "mission.info_complete":
                await self._handle_info_complete(message)
            elif channel == "drone.fleet_status":
                await self._handle_fleet_status(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_plan_request(self, message: Dict[str, Any]) -> None:
        """Handle request to generate mission plan"""
        session_id = message.get("session_id")
        mission_data = message.get("mission_data", {})
        gathered_info = message.get("gathered_info", {})
        
        logger.info(f"Generating mission plan for session {session_id}")
        
        # Store pending plan
        self.pending_plans[session_id] = {
            "mission_data": mission_data,
            "gathered_info": gathered_info,
            "status": "generating"
        }
        
        # Get available drones
        available_drones = await self._get_available_drones()
        
        # Generate comprehensive mission plan
        plan = await self._generate_comprehensive_plan(mission_data, gathered_info, available_drones)
        
        if plan:
            # Update pending plan
            self.pending_plans[session_id]["plan"] = plan
            self.pending_plans[session_id]["status"] = "complete"
            
            # Publish plan ready
            await self.publish_message("mission.plan_ready", {
                "session_id": session_id,
                "plan": plan,
                "mission_data": mission_data
            })
            
            # Send to WebSocket
            await self.send_websocket_message("mission_plan_ready", {
                "session_id": session_id,
                "plan": plan
            })
            
            logger.info(f"Mission plan generated for session {session_id}")
        else:
            # Plan generation failed
            self.pending_plans[session_id]["status"] = "failed"
            await self.publish_message("mission.plan_failed", {
                "session_id": session_id,
                "error": "Failed to generate mission plan"
            })
    
    async def _handle_info_complete(self, message: Dict[str, Any]) -> None:
        """Handle completion of information gathering"""
        session_id = message.get("session_id")
        gathered_info = message.get("gathered_info", {})
        
        logger.info(f"Information gathering complete for session {session_id}")
        
        # Trigger plan generation
        await self.publish_message("mission.plan_request", {
            "session_id": session_id,
            "gathered_info": gathered_info,
            "mission_data": message.get("mission_data", {})
        })
    
    async def _handle_fleet_status(self, message: Dict[str, Any]) -> None:
        """Handle drone fleet status update"""
        # This could be used to adjust plans based on available drones
        pass
    
    async def _get_available_drones(self) -> List[Dict[str, Any]]:
        """Get list of available drones"""
        try:
            drones = await db_service.get_all_drones()
            available_drones = []
            
            for drone in drones:
                if drone.status == "available":
                    import json
                    capabilities = json.loads(drone.capabilities_json) if drone.capabilities_json else {}
                    available_drones.append({
                        "id": drone.id,
                        "name": drone.name,
                        "capabilities": capabilities,
                        "battery_capacity": drone.battery_capacity,
                        "battery_percent": drone.battery_percent
                    })
            
            return available_drones
        except Exception as e:
            logger.error(f"Error getting available drones: {e}")
            return []
    
    async def _generate_comprehensive_plan(self, mission_data: Dict[str, Any], 
                                         gathered_info: Dict[str, Any], 
                                         available_drones: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate comprehensive mission plan"""
        try:
            # Use Ollama to generate the plan
            plan = await ollama_service.generate_mission_plan(gathered_info)
            
            # Enhance plan with additional details
            enhanced_plan = await self._enhance_plan(plan, available_drones, gathered_info)
            
            return enhanced_plan
        
        except Exception as e:
            logger.error(f"Error generating mission plan: {e}")
            return self._create_fallback_plan(mission_data, gathered_info, available_drones)
    
    async def _enhance_plan(self, base_plan: Dict[str, Any], available_drones: List[Dict[str, Any]], 
                           gathered_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the base plan with additional operational details"""
        enhanced_plan = base_plan.copy()
        
        # Add drone assignments
        enhanced_plan["drone_assignments"] = await self._create_drone_assignments(
            base_plan.get("search_area", {}),
            available_drones,
            gathered_info
        )
        
        # Add detailed waypoints
        enhanced_plan["waypoints"] = await self._generate_waypoints(
            base_plan.get("search_area", {}),
            gathered_info
        )
        
        # Add timing estimates
        enhanced_plan["timing"] = await self._calculate_timing_estimates(
            base_plan.get("search_area", {}),
            available_drones,
            gathered_info
        )
        
        # Add safety procedures
        enhanced_plan["safety_procedures"] = await self._generate_safety_procedures(
            gathered_info
        )
        
        # Add communication protocols
        enhanced_plan["communication"] = await self._generate_communication_protocols()
        
        # Add contingency plans
        enhanced_plan["contingency_plans"] = await self._generate_contingency_plans(
            gathered_info
        )
        
        return enhanced_plan
    
    async def _create_drone_assignments(self, search_area: Dict[str, Any], 
                                      available_drones: List[Dict[str, Any]], 
                                      gathered_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create drone assignments for the search area"""
        if not available_drones:
            return []
        
        # Simple grid-based assignment
        assignments = []
        drone_count = len(available_drones)
        
        # Get search area bounds (simplified)
        bounds = self._get_search_area_bounds(search_area)
        
        if not bounds:
            # Default bounds if none provided
            bounds = {
                "north": 37.8,
                "south": 37.7,
                "east": -122.4,
                "west": -122.5
            }
        
        # Calculate grid zones
        lat_range = bounds["north"] - bounds["south"]
        lng_range = bounds["east"] - bounds["west"]
        
        # Determine grid size based on drone count
        grid_cols = min(drone_count, 3)
        grid_rows = (drone_count + grid_cols - 1) // grid_cols
        
        for i, drone in enumerate(available_drones):
            row = i // grid_cols
            col = i % grid_cols
            
            # Calculate zone bounds
            zone_north = bounds["south"] + (row + 1) * (lat_range / grid_rows)
            zone_south = bounds["south"] + row * (lat_range / grid_rows)
            zone_east = bounds["west"] + (col + 1) * (lng_range / grid_cols)
            zone_west = bounds["west"] + col * (lng_range / grid_cols)
            
            assignment = {
                "drone_id": drone["id"],
                "drone_name": drone["name"],
                "zone": {
                    "north": zone_north,
                    "south": zone_south,
                    "east": zone_east,
                    "west": zone_west
                },
                "search_pattern": "grid",
                "altitude": 50,  # meters
                "speed": 8,  # m/s
                "priority": "high" if i < 2 else "medium"
            }
            
            assignments.append(assignment)
        
        return assignments
    
    def _get_search_area_bounds(self, search_area: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract bounds from search area GeoJSON"""
        try:
            if search_area.get("type") == "Polygon":
                coordinates = search_area.get("coordinates", [[]])[0]
                if len(coordinates) >= 4:
                    lats = [coord[1] for coord in coordinates]
                    lngs = [coord[0] for coord in coordinates]
                    
                    return {
                        "north": max(lats),
                        "south": min(lats),
                        "east": max(lngs),
                        "west": min(lngs)
                    }
        except Exception as e:
            logger.error(f"Error extracting search area bounds: {e}")
        
        return None
    
    async def _generate_waypoints(self, search_area: Dict[str, Any], 
                                 gathered_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed waypoints for search pattern"""
        waypoints = []
        
        # Get search area bounds
        bounds = self._get_search_area_bounds(search_area)
        if not bounds:
            return waypoints
        
        # Generate grid waypoints
        lat_step = 0.001  # ~100m spacing
        lng_step = 0.001
        
        current_lat = bounds["south"]
        while current_lat <= bounds["north"]:
            current_lng = bounds["west"]
            while current_lng <= bounds["east"]:
                waypoints.append({
                    "lat": current_lat,
                    "lng": current_lng,
                    "alt": 50,
                    "type": "search_point"
                })
                current_lng += lng_step
            current_lat += lat_step
        
        return waypoints
    
    async def _calculate_timing_estimates(self, search_area: Dict[str, Any], 
                                        available_drones: List[Dict[str, Any]], 
                                        gathered_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate timing estimates for the mission"""
        # Estimate based on area size and drone count
        bounds = self._get_search_area_bounds(search_area)
        
        if bounds:
            area_km2 = ((bounds["north"] - bounds["south"]) * 111) * ((bounds["east"] - bounds["west"]) * 111)
        else:
            area_km2 = 1.0  # Default 1 km²
        
        drone_count = len(available_drones)
        if drone_count == 0:
            drone_count = 1
        
        # Estimate time based on area and drone count
        base_time_per_km2 = 30  # minutes per km²
        time_per_km2 = base_time_per_km2 / drone_count
        
        estimated_duration = int(area_km2 * time_per_km2)
        
        return {
            "estimated_duration_minutes": estimated_duration,
            "estimated_duration_hours": estimated_duration / 60,
            "area_km2": area_km2,
            "drone_count": drone_count,
            "time_per_drone_minutes": estimated_duration / drone_count if drone_count > 0 else 0
        }
    
    async def _generate_safety_procedures(self, gathered_info: Dict[str, Any]) -> List[str]:
        """Generate safety procedures based on gathered information"""
        procedures = [
            "All drones return to base if battery level drops below 30%",
            "Land immediately if weather conditions deteriorate",
            "Maintain minimum 20m altitude above ground level",
            "Report any structural hazards immediately",
            "Avoid flying over unstable structures"
        ]
        
        # Add specific procedures based on gathered info
        if "hazards" in gathered_info:
            hazards = gathered_info["hazards"].lower()
            if "gas" in hazards:
                procedures.append("Avoid low altitude flight due to potential gas hazards")
            if "fire" in hazards:
                procedures.append("Maintain safe distance from any fire or smoke")
            if "unstable" in hazards:
                procedures.append("Do not fly directly over unstable structures")
        
        if gathered_info.get("priority") == "high":
            procedures.append("Prioritize speed over thoroughness due to high priority")
        
        return procedures
    
    async def _generate_communication_protocols(self) -> Dict[str, Any]:
        """Generate communication protocols"""
        return {
            "telemetry_frequency": "2 seconds",
            "status_reports": "every 30 seconds",
            "discovery_alerts": "immediate",
            "emergency_communications": "immediate",
            "mission_updates": "every 5 minutes"
        }
    
    async def _generate_contingency_plans(self, gathered_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate contingency plans"""
        plans = [
            {
                "scenario": "Drone battery low",
                "action": "Return to base immediately",
                "priority": "high"
            },
            {
                "scenario": "Weather deterioration",
                "action": "Land all drones safely and wait",
                "priority": "high"
            },
            {
                "scenario": "Communication loss",
                "action": "Continue mission autonomously, return to base when complete",
                "priority": "medium"
            },
            {
                "scenario": "Discovery of survivors",
                "action": "Mark location, alert operator, continue search",
                "priority": "critical"
            }
        ]
        
        return plans
    
    def _create_fallback_plan(self, mission_data: Dict[str, Any], 
                            gathered_info: Dict[str, Any], 
                            available_drones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a fallback plan if LLM generation fails"""
        return {
            "mission_name": mission_data.get("description", "SAR Mission"),
            "search_area": {
                "type": "Polygon",
                "coordinates": [[
                    [-122.5, 37.7], [-122.4, 37.7], 
                    [-122.4, 37.8], [-122.5, 37.8], 
                    [-122.5, 37.7]
                ]]
            },
            "drone_assignments": [
                {
                    "drone_id": drone["id"],
                    "drone_name": drone["name"],
                    "zone": {"north": 37.8, "south": 37.7, "east": -122.4, "west": -122.5},
                    "search_pattern": "grid",
                    "altitude": 50,
                    "speed": 8,
                    "priority": "medium"
                } for drone in available_drones
            ],
            "estimated_duration": 120,
            "safety_parameters": {
                "min_battery": 30,
                "max_altitude": 100,
                "weather_limits": "clear conditions only"
            },
            "waypoints": [
                {"lat": 37.75, "lng": -122.45, "alt": 50, "type": "search_point"}
            ],
            "coverage_strategy": "Grid pattern with 100m spacing",
            "emergency_procedures": [
                "Return to base if battery < 30%",
                "Land immediately if weather deteriorates"
            ]
        }