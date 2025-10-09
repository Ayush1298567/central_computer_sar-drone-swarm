"""
Task Assignment Agent
Assigns drones to specific search zones and tasks
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.database import db_service

logger = logging.getLogger(__name__)

class TaskAssignmentAgent(BaseAgent):
    """Assigns drones to specific tasks and search zones"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("task_assignment", redis_service, websocket_manager)
        self.active_assignments: Dict[str, Dict[str, Any]] = {}
        self.drone_status: Dict[int, str] = {}
    
    async def start_agent(self) -> None:
        """Start the task assignment agent"""
        await self.subscribe_to_channel("mission.plan_ready")
        await self.subscribe_to_channel("drone.status_update")
        await self.subscribe_to_channel("mission.start_request")
        await self.subscribe_to_channel("mission.pause_request")
        await self.subscribe_to_channel("mission.resume_request")
        logger.info("Task Assignment Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the task assignment agent"""
        logger.info("Task Assignment Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "mission.plan_ready":
                await self._handle_plan_ready(message)
            elif channel == "drone.status_update":
                await self._handle_drone_status_update(message)
            elif channel == "mission.start_request":
                await self._handle_start_request(message)
            elif channel == "mission.pause_request":
                await self._handle_pause_request(message)
            elif channel == "mission.resume_request":
                await self._handle_resume_request(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_plan_ready(self, message: Dict[str, Any]) -> None:
        """Handle mission plan ready for assignment"""
        session_id = message.get("session_id")
        plan = message.get("plan", {})
        mission_id = message.get("mission_id")
        
        logger.info(f"Processing mission plan for session {session_id}")
        
        # Extract drone assignments from plan
        drone_assignments = plan.get("drone_assignments", [])
        
        if not drone_assignments:
            logger.warning(f"No drone assignments in plan for session {session_id}")
            return
        
        # Create task assignments
        assignments = await self._create_task_assignments(drone_assignments, mission_id)
        
        # Store assignments
        self.active_assignments[session_id] = {
            "mission_id": mission_id,
            "assignments": assignments,
            "status": "ready"
        }
        
        # Publish assignments ready
        await self.publish_message("task.assignments_ready", {
            "session_id": session_id,
            "mission_id": mission_id,
            "assignments": assignments
        })
        
        logger.info(f"Created {len(assignments)} task assignments for session {session_id}")
    
    async def _create_task_assignments(self, drone_assignments: List[Dict[str, Any]], 
                                     mission_id: int) -> List[Dict[str, Any]]:
        """Create detailed task assignments for drones"""
        assignments = []
        
        for i, drone_assignment in enumerate(drone_assignments):
            drone_id = drone_assignment.get("drone_id")
            drone_name = drone_assignment.get("drone_name", f"Drone {drone_id}")
            
            # Create detailed assignment
            assignment = {
                "assignment_id": f"assign_{mission_id}_{drone_id}",
                "mission_id": mission_id,
                "drone_id": drone_id,
                "drone_name": drone_name,
                "zone": drone_assignment.get("zone", {}),
                "search_pattern": drone_assignment.get("search_pattern", "grid"),
                "altitude": drone_assignment.get("altitude", 50),
                "speed": drone_assignment.get("speed", 8),
                "priority": drone_assignment.get("priority", "medium"),
                "status": "assigned",
                "created_at": asyncio.get_event_loop().time(),
                "waypoints": await self._generate_zone_waypoints(drone_assignment.get("zone", {})),
                "search_parameters": {
                    "grid_spacing": 50,  # meters
                    "overlap_percentage": 20,
                    "search_height": drone_assignment.get("altitude", 50)
                }
            }
            
            assignments.append(assignment)
            
            # Update drone status
            self.drone_status[drone_id] = "assigned"
        
        return assignments
    
    async def _generate_zone_waypoints(self, zone: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate waypoints for a specific zone"""
        waypoints = []
        
        if not zone:
            return waypoints
        
        # Calculate zone bounds
        north = zone.get("north", 37.8)
        south = zone.get("south", 37.7)
        east = zone.get("east", -122.4)
        west = zone.get("west", -122.5)
        
        # Generate grid waypoints
        lat_step = 0.0005  # ~50m spacing
        lng_step = 0.0005
        
        current_lat = south
        while current_lat <= north:
            current_lng = west
            while current_lng <= east:
                waypoints.append({
                    "lat": current_lat,
                    "lng": current_lng,
                    "alt": 50,
                    "type": "search_point",
                    "sequence": len(waypoints)
                })
                current_lng += lng_step
            current_lat += lat_step
        
        return waypoints
    
    async def _handle_drone_status_update(self, message: Dict[str, Any]) -> None:
        """Handle drone status updates"""
        drone_id = message.get("drone_id")
        status = message.get("status")
        
        if drone_id:
            self.drone_status[drone_id] = status
            
            # Check if drone completed its assignment
            if status == "completed":
                await self._handle_drone_completion(drone_id)
            elif status == "error":
                await self._handle_drone_error(drone_id)
    
    async def _handle_drone_completion(self, drone_id: int) -> None:
        """Handle drone completing its assignment"""
        logger.info(f"Drone {drone_id} completed its assignment")
        
        # Find assignment for this drone
        for session_id, assignment_data in self.active_assignments.items():
            assignments = assignment_data.get("assignments", [])
            for assignment in assignments:
                if assignment["drone_id"] == drone_id:
                    assignment["status"] = "completed"
                    assignment["completed_at"] = asyncio.get_event_loop().time()
                    
                    # Check if all assignments are complete
                    all_complete = all(a["status"] == "completed" for a in assignments)
                    if all_complete:
                        await self._handle_mission_complete(session_id)
                    
                    break
    
    async def _handle_drone_error(self, drone_id: int) -> None:
        """Handle drone error"""
        logger.warning(f"Drone {drone_id} encountered an error")
        
        # Find assignment for this drone and mark as error
        for session_id, assignment_data in self.active_assignments.items():
            assignments = assignment_data.get("assignments", [])
            for assignment in assignments:
                if assignment["drone_id"] == drone_id:
                    assignment["status"] = "error"
                    assignment["error_at"] = asyncio.get_event_loop().time()
                    
                    # Try to reassign if possible
                    await self._try_reassign_task(session_id, assignment)
                    break
    
    async def _try_reassign_task(self, session_id: str, failed_assignment: Dict[str, Any]) -> None:
        """Try to reassign a failed task to another drone"""
        # Get available drones
        available_drones = await self._get_available_drones()
        
        if not available_drones:
            logger.warning(f"No available drones to reassign task for session {session_id}")
            return
        
        # Find a suitable replacement drone
        replacement_drone = None
        for drone in available_drones:
            if drone["id"] not in [a["drone_id"] for a in self.active_assignments[session_id]["assignments"]]:
                replacement_drone = drone
                break
        
        if replacement_drone:
            # Create new assignment
            new_assignment = failed_assignment.copy()
            new_assignment["drone_id"] = replacement_drone["id"]
            new_assignment["drone_name"] = replacement_drone["name"]
            new_assignment["status"] = "assigned"
            new_assignment["reassigned_at"] = asyncio.get_event_loop().time()
            
            # Add to assignments
            self.active_assignments[session_id]["assignments"].append(new_assignment)
            
            # Publish reassignment
            await self.publish_message("task.reassigned", {
                "session_id": session_id,
                "original_drone_id": failed_assignment["drone_id"],
                "new_drone_id": replacement_drone["id"],
                "assignment": new_assignment
            })
            
            logger.info(f"Reassigned task from drone {failed_assignment['drone_id']} to {replacement_drone['id']}")
    
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
    
    async def _handle_start_request(self, message: Dict[str, Any]) -> None:
        """Handle request to start mission"""
        session_id = message.get("session_id")
        mission_id = message.get("mission_id")
        
        if session_id not in self.active_assignments:
            logger.warning(f"No assignments found for session {session_id}")
            return
        
        assignments = self.active_assignments[session_id]["assignments"]
        
        # Start all assigned drones
        for assignment in assignments:
            if assignment["status"] == "assigned":
                await self._start_drone_assignment(assignment)
        
        # Update status
        self.active_assignments[session_id]["status"] = "active"
        
        # Publish mission started
        await self.publish_message("mission.started", {
            "session_id": session_id,
            "mission_id": mission_id,
            "assignments": assignments
        })
        
        logger.info(f"Started mission for session {session_id}")
    
    async def _start_drone_assignment(self, assignment: Dict[str, Any]) -> None:
        """Start a specific drone assignment"""
        drone_id = assignment["drone_id"]
        
        # Update assignment status
        assignment["status"] = "active"
        assignment["started_at"] = asyncio.get_event_loop().time()
        
        # Update drone status in database
        await db_service.update_drone_status(
            drone_id, 
            "in_mission",
            assignment["zone"]["south"] + (assignment["zone"]["north"] - assignment["zone"]["south"]) / 2,
            assignment["zone"]["west"] + (assignment["zone"]["east"] - assignment["zone"]["west"]) / 2,
            50
        )
        
        # Send assignment to drone
        await self.publish_message("drone.assignment", {
            "drone_id": drone_id,
            "assignment": assignment
        })
        
        logger.info(f"Started assignment for drone {drone_id}")
    
    async def _handle_pause_request(self, message: Dict[str, Any]) -> None:
        """Handle request to pause mission"""
        session_id = message.get("session_id")
        
        if session_id not in self.active_assignments:
            return
        
        assignments = self.active_assignments[session_id]["assignments"]
        
        # Pause all active drones
        for assignment in assignments:
            if assignment["status"] == "active":
                await self.publish_message("drone.pause", {
                    "drone_id": assignment["drone_id"]
                })
                assignment["status"] = "paused"
        
        # Update status
        self.active_assignments[session_id]["status"] = "paused"
        
        logger.info(f"Paused mission for session {session_id}")
    
    async def _handle_resume_request(self, message: Dict[str, Any]) -> None:
        """Handle request to resume mission"""
        session_id = message.get("session_id")
        
        if session_id not in self.active_assignments:
            return
        
        assignments = self.active_assignments[session_id]["assignments"]
        
        # Resume all paused drones
        for assignment in assignments:
            if assignment["status"] == "paused":
                await self.publish_message("drone.resume", {
                    "drone_id": assignment["drone_id"]
                })
                assignment["status"] = "active"
        
        # Update status
        self.active_assignments[session_id]["status"] = "active"
        
        logger.info(f"Resumed mission for session {session_id}")
    
    async def _handle_mission_complete(self, session_id: str) -> None:
        """Handle mission completion"""
        assignment_data = self.active_assignments.get(session_id)
        if not assignment_data:
            return
        
        mission_id = assignment_data["mission_id"]
        
        # Update status
        assignment_data["status"] = "completed"
        assignment_data["completed_at"] = asyncio.get_event_loop().time()
        
        # Publish mission complete
        await self.publish_message("mission.completed", {
            "session_id": session_id,
            "mission_id": mission_id,
            "assignments": assignment_data["assignments"]
        })
        
        # Send to WebSocket
        await self.send_websocket_message("mission_completed", {
            "session_id": session_id,
            "mission_id": mission_id
        })
        
        logger.info(f"Mission completed for session {session_id}")
    
    def get_assignment_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get assignment status for a session"""
        return self.active_assignments.get(session_id)
    
    def get_drone_status(self, drone_id: int) -> str:
        """Get status of a specific drone"""
        return self.drone_status.get(drone_id, "unknown")