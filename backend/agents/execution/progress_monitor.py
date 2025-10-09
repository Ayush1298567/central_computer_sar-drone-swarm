"""
Progress Monitor Agent
Monitors mission progress and coverage
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.database import db_service

logger = logging.getLogger(__name__)

class ProgressMonitorAgent(BaseAgent):
    """Monitors mission progress and coverage statistics"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("progress_monitor", redis_service, websocket_manager)
        self.active_missions: Dict[str, Dict[str, Any]] = {}
        self.drone_progress: Dict[int, Dict[str, Any]] = {}
    
    async def start_agent(self) -> None:
        """Start the progress monitor"""
        await self.subscribe_to_channel("mission.started")
        await self.subscribe_to_channel("drone.telemetry")
        await self.subscribe_to_channel("drone.assignment_completed")
        await self.subscribe_to_channel("mission.completed")
        logger.info("Progress Monitor Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the progress monitor"""
        logger.info("Progress Monitor Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "mission.started":
                await self._handle_mission_started(message)
            elif channel == "drone.telemetry":
                await self._handle_drone_telemetry(message)
            elif channel == "drone.assignment_completed":
                await self._handle_assignment_completed(message)
            elif channel == "mission.completed":
                await self._handle_mission_completed(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_mission_started(self, message: Dict[str, Any]) -> None:
        """Handle mission started event"""
        session_id = message.get("session_id")
        mission_id = message.get("mission_id")
        assignments = message.get("assignments", [])
        
        logger.info(f"Monitoring progress for mission {mission_id}")
        
        # Initialize mission tracking
        self.active_missions[session_id] = {
            "mission_id": mission_id,
            "assignments": assignments,
            "start_time": asyncio.get_event_loop().time(),
            "total_waypoints": sum(len(a.get("waypoints", [])) for a in assignments),
            "completed_waypoints": 0,
            "coverage_percentage": 0.0,
            "drones_active": len(assignments),
            "drones_completed": 0,
            "status": "active"
        }
        
        # Initialize drone progress tracking
        for assignment in assignments:
            drone_id = assignment.get("drone_id")
            self.drone_progress[drone_id] = {
                "assignment_id": assignment.get("assignment_id"),
                "total_waypoints": len(assignment.get("waypoints", [])),
                "completed_waypoints": 0,
                "current_waypoint": 0,
                "coverage_percentage": 0.0,
                "last_position": None,
                "status": "active"
            }
        
        # Start progress monitoring loop
        asyncio.create_task(self._monitor_progress_loop(session_id))
    
    async def _handle_drone_telemetry(self, message: Dict[str, Any]) -> None:
        """Handle drone telemetry updates"""
        drone_id = message.get("drone_id")
        telemetry = message.get("telemetry", {})
        
        if drone_id not in self.drone_progress:
            return
        
        # Update drone progress
        drone_progress = self.drone_progress[drone_id]
        
        # Update position
        drone_progress["last_position"] = {
            "lat": telemetry.get("lat"),
            "lng": telemetry.get("lng"),
            "alt": telemetry.get("alt")
        }
        
        # Update waypoint progress if available
        if "current_waypoint" in telemetry:
            drone_progress["current_waypoint"] = telemetry["current_waypoint"]
            drone_progress["completed_waypoints"] = telemetry["current_waypoint"]
            drone_progress["coverage_percentage"] = (
                drone_progress["completed_waypoints"] / drone_progress["total_waypoints"] * 100
                if drone_progress["total_waypoints"] > 0 else 0
            )
        
        # Update status
        drone_progress["status"] = telemetry.get("status", "active")
        
        # Update mission progress
        await self._update_mission_progress(drone_id)
    
    async def _handle_assignment_completed(self, message: Dict[str, Any]) -> None:
        """Handle drone assignment completion"""
        drone_id = message.get("drone_id")
        assignment_id = message.get("assignment_id")
        
        if drone_id in self.drone_progress:
            self.drone_progress[drone_id]["status"] = "completed"
            self.drone_progress[drone_id]["coverage_percentage"] = 100.0
            
            # Find mission for this drone
            for session_id, mission_data in self.active_missions.items():
                if mission_data["status"] == "active":
                    mission_data["drones_completed"] += 1
                    await self._update_mission_progress(drone_id)
                    break
    
    async def _handle_mission_completed(self, message: Dict[str, Any]) -> None:
        """Handle mission completion"""
        session_id = message.get("session_id")
        mission_id = message.get("mission_id")
        
        if session_id in self.active_missions:
            mission_data = self.active_missions[session_id]
            mission_data["status"] = "completed"
            mission_data["completion_time"] = asyncio.get_event_loop().time()
            mission_data["coverage_percentage"] = 100.0
            
            # Send final progress update
            await self._send_progress_update(session_id, mission_data)
            
            logger.info(f"Mission {mission_id} completed with {mission_data['coverage_percentage']:.1f}% coverage")
    
    async def _monitor_progress_loop(self, session_id: str) -> None:
        """Monitor progress in a loop"""
        while session_id in self.active_missions:
            mission_data = self.active_missions[session_id]
            
            if mission_data["status"] == "completed":
                break
            
            # Calculate current progress
            await self._calculate_mission_progress(session_id)
            
            # Send progress update
            await self._send_progress_update(session_id, mission_data)
            
            # Wait before next update
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def _calculate_mission_progress(self, session_id: str) -> None:
        """Calculate overall mission progress"""
        if session_id not in self.active_missions:
            return
        
        mission_data = self.active_missions[session_id]
        
        # Calculate total completed waypoints
        total_completed = 0
        total_waypoints = 0
        active_drones = 0
        
        for assignment in mission_data["assignments"]:
            drone_id = assignment.get("drone_id")
            if drone_id in self.drone_progress:
                drone_progress = self.drone_progress[drone_id]
                total_completed += drone_progress["completed_waypoints"]
                total_waypoints += drone_progress["total_waypoints"]
                
                if drone_progress["status"] == "active":
                    active_drones += 1
        
        # Update mission data
        mission_data["completed_waypoints"] = total_completed
        mission_data["total_waypoints"] = total_waypoints
        mission_data["drones_active"] = active_drones
        
        if total_waypoints > 0:
            mission_data["coverage_percentage"] = (total_completed / total_waypoints) * 100
        else:
            mission_data["coverage_percentage"] = 0.0
    
    async def _update_mission_progress(self, drone_id: int) -> None:
        """Update mission progress based on drone update"""
        # Find mission for this drone
        for session_id, mission_data in self.active_missions.items():
            if mission_data["status"] == "active":
                # Check if this drone belongs to this mission
                for assignment in mission_data["assignments"]:
                    if assignment.get("drone_id") == drone_id:
                        await self._calculate_mission_progress(session_id)
                        await self._send_progress_update(session_id, mission_data)
                        return
    
    async def _send_progress_update(self, session_id: str, mission_data: Dict[str, Any]) -> None:
        """Send progress update via WebSocket and Redis"""
        progress_data = {
            "session_id": session_id,
            "mission_id": mission_data["mission_id"],
            "coverage_percentage": mission_data["coverage_percentage"],
            "completed_waypoints": mission_data["completed_waypoints"],
            "total_waypoints": mission_data["total_waypoints"],
            "drones_active": mission_data["drones_active"],
            "drones_completed": mission_data["drones_completed"],
            "status": mission_data["status"],
            "elapsed_time": asyncio.get_event_loop().time() - mission_data["start_time"]
        }
        
        # Send via WebSocket
        await self.send_websocket_message("mission_progress", progress_data)
        
        # Publish to Redis
        await self.publish_message("mission.progress_update", progress_data)
    
    async def get_mission_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a mission"""
        return self.active_missions.get(session_id)
    
    async def get_drone_progress(self, drone_id: int) -> Optional[Dict[str, Any]]:
        """Get current progress for a drone"""
        return self.drone_progress.get(drone_id)
    
    async def get_all_active_missions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active missions"""
        return {k: v for k, v in self.active_missions.items() if v["status"] == "active"}
    
    async def generate_progress_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Generate detailed progress report"""
        if session_id not in self.active_missions:
            return None
        
        mission_data = self.active_missions[session_id]
        
        # Calculate additional metrics
        elapsed_time = asyncio.get_event_loop().time() - mission_data["start_time"]
        estimated_total_time = mission_data.get("estimated_total_time", 0)
        
        if estimated_total_time > 0:
            estimated_completion = (elapsed_time / estimated_total_time) * 100
        else:
            estimated_completion = 0
        
        # Calculate efficiency metrics
        waypoints_per_minute = 0
        if elapsed_time > 0:
            waypoints_per_minute = (mission_data["completed_waypoints"] / elapsed_time) * 60
        
        report = {
            "session_id": session_id,
            "mission_id": mission_data["mission_id"],
            "overall_progress": {
                "coverage_percentage": mission_data["coverage_percentage"],
                "completed_waypoints": mission_data["completed_waypoints"],
                "total_waypoints": mission_data["total_waypoints"],
                "estimated_completion": estimated_completion
            },
            "drone_status": {
                "active": mission_data["drones_active"],
                "completed": mission_data["drones_completed"],
                "total": len(mission_data["assignments"])
            },
            "timing": {
                "elapsed_time": elapsed_time,
                "estimated_total_time": estimated_total_time,
                "waypoints_per_minute": waypoints_per_minute
            },
            "status": mission_data["status"]
        }
        
        return report