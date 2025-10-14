"""
Real Mission Execution Engine for SAR Mission Commander
Integrates mission planning with actual drone connections and control
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from ..communication.drone_connection_hub import drone_connection_hub
from ..communication.drone_registry import DroneStatus, drone_registry
from ..core.database import SessionLocal
from ..models.mission import Mission
from ..models.drone import Drone
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MissionExecutionStatus:
    """Mission execution status tracking"""
    mission_id: str
    status: str  # planning, ready, executing, paused, completed, failed, aborted
    progress_percentage: float
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    active_drones: List[str] = None
    completed_areas: List[str] = None
    discoveries_count: int = 0
    errors: List[str] = None

class RealMissionExecutionEngine:
    """Executes missions on real connected drones"""
    
    def __init__(self):
        self.active_executions: Dict[str, MissionExecutionStatus] = {}
        self._running = False
        self._monitor_task = None
        
    async def start(self):
        """Start the mission execution engine"""
        self._running = True
        logger.info("Real Mission Execution Engine started")
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_executions())
    
    async def stop(self):
        """Stop the mission execution engine"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Real Mission Execution Engine stopped")

    # -------------------- AI Decision Hooks --------------------
    async def apply_decision(self, decision: Dict[str, Any]) -> bool:
        """Apply an AI decision in an idempotent and safe manner.

        Expected decision format contains selected_option.parameters.action and identifiers.
        Supported actions: pause (mission), resume (mission), rtl (drone), land (drone), reassign (mission/drone).
        """
        try:
            selected = decision.get("selected_option") or {}
            params = selected.get("parameters") or {}
            action = params.get("action")
            mission_id = decision.get("mission_id") or params.get("mission_id")
            drone_id = decision.get("drone_id") or params.get("drone_id")

            # Idempotency: check current state before acting
            if action == "pause" and mission_id:
                status = self.active_executions.get(mission_id)
                if status and status.status != "paused":
                    return await self.pause_mission(mission_id)
                return True
            if action == "resume" and mission_id:
                status = self.active_executions.get(mission_id)
                if status and status.status == "paused":
                    return await self.resume_mission(mission_id)
                return True
            if action == "rtl" and drone_id:
                return await self._emergency_rtl(drone_id)
            if action == "land" and drone_id:
                return await self._emergency_land(drone_id)
            if action == "reassign" and mission_id:
                from_drone = params.get("from_drone_id") or drone_id
                return await self._reassign_drone(from_drone, mission_id)

            logger.warning(f"Unknown or unsupported AI action: {action}")
            return False
        except Exception as e:
            logger.error(f"apply_decision failed: {e}")
            return False

    async def _reassign_drone(self, drone_id: Optional[str], mission_id: str) -> bool:
        """Reassign coverage from a failed drone to others (placeholder)."""
        try:
            if not mission_id:
                return False
            # Minimal safe behavior: pause mission and request return for affected drone
            if drone_id:
                await self._send_mission_command(drone_id, {
                    "command_type": "return_home",
                    "parameters": {}
                })
            await self.pause_mission(mission_id)
            # TODO: compute new allocation and resume mission
            return True
        except Exception as e:
            logger.error(f"_reassign_drone failed: {e}")
            return False

    async def _emergency_rtl(self, drone_id: str) -> bool:
        try:
            return await drone_connection_hub.send_command(drone_id, "return_home", {}, priority=1)
        except Exception as e:
            logger.error(f"emergency_rtl failed: {e}")
            return False

    async def _emergency_land(self, drone_id: str) -> bool:
        try:
            return await drone_connection_hub.send_command(drone_id, "land_now", {}, priority=1)
        except Exception as e:
            logger.error(f"emergency_land failed: {e}")
            return False
    
    async def execute_mission(self, mission_id: str, mission_data: Dict[str, Any]) -> bool:
        """Execute a mission on real drones"""
        try:
            logger.info(f"Starting real mission execution for {mission_id}")
            
            # Create execution status
            execution_status = MissionExecutionStatus(
                mission_id=mission_id,
                status="planning",
                progress_percentage=0.0,
                active_drones=[],
                completed_areas=[],
                errors=[]
            )
            self.active_executions[mission_id] = execution_status
            
            # Get available drones
            available_drones = drone_registry.get_available_drones()
            if not available_drones:
                execution_status.status = "failed"
                execution_status.errors.append("No available drones found")
                logger.error(f"No available drones for mission {mission_id}")
                return False
            
            # Assign drones to mission
            assigned_drones = await self._assign_drones_to_mission(mission_id, mission_data, available_drones)
            if not assigned_drones:
                execution_status.status = "failed"
                execution_status.errors.append("Failed to assign drones to mission")
                logger.error(f"Failed to assign drones for mission {mission_id}")
                return False
            
            execution_status.active_drones = assigned_drones
            execution_status.status = "ready"
            
            # Start mission execution
            execution_status.status = "executing"
            execution_status.start_time = datetime.utcnow()
            
            # Execute mission phases
            success = await self._execute_mission_phases(mission_id, mission_data, assigned_drones, execution_status)
            
            if success:
                execution_status.status = "completed"
                execution_status.progress_percentage = 100.0
                logger.info(f"Mission {mission_id} completed successfully")
            else:
                execution_status.status = "failed"
                logger.error(f"Mission {mission_id} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing mission {mission_id}: {e}")
            if mission_id in self.active_executions:
                self.active_executions[mission_id].status = "failed"
                self.active_executions[mission_id].errors.append(str(e))
            return False
    
    async def _assign_drones_to_mission(self, mission_id: str, mission_data: Dict[str, Any], 
                                      available_drones: List) -> List[str]:
        """Assign drones to mission based on requirements"""
        try:
            # Get mission requirements
            required_drones = mission_data.get("max_drones", 1)
            search_areas = mission_data.get("search_areas", [])
            
            # Calculate drones needed
            drones_needed = min(required_drones, len(available_drones), len(search_areas))
            
            assigned_drones = []
            for i in range(drones_needed):
                drone = available_drones[i]
                
                # Assign drone to mission
                if drone_registry.assign_mission(drone.drone_id, mission_id):
                    assigned_drones.append(drone.drone_id)
                    
                    # Send initial mission command
                    await self._send_mission_command(drone.drone_id, {
                        "command_type": "start_mission",
                        "parameters": {
                            "mission_id": mission_id,
                            "search_area": search_areas[i] if i < len(search_areas) else search_areas[0],
                            "altitude": mission_data.get("altitude", 50),
                            "speed": mission_data.get("speed", 5)
                        }
                    })
                    
                    logger.info(f"Assigned drone {drone.drone_id} to mission {mission_id}")
                else:
                    logger.warning(f"Failed to assign drone {drone.drone_id} to mission {mission_id}")
            
            return assigned_drones
            
        except Exception as e:
            logger.error(f"Error assigning drones to mission: {e}")
            return []
    
    async def _execute_mission_phases(self, mission_id: str, mission_data: Dict[str, Any], 
                                    assigned_drones: List[str], execution_status: MissionExecutionStatus) -> bool:
        """Execute mission phases on assigned drones"""
        try:
            # Phase 1: Takeoff
            logger.info(f"Phase 1: Taking off drones for mission {mission_id}")
            takeoff_success = await self._execute_takeoff_phase(assigned_drones, execution_status)
            if not takeoff_success:
                return False
            
            # Phase 2: Navigate to search areas
            logger.info(f"Phase 2: Navigating to search areas for mission {mission_id}")
            navigation_success = await self._execute_navigation_phase(mission_data, assigned_drones, execution_status)
            if not navigation_success:
                return False
            
            # Phase 3: Execute search pattern
            logger.info(f"Phase 3: Executing search pattern for mission {mission_id}")
            search_success = await self._execute_search_phase(mission_data, assigned_drones, execution_status)
            if not search_success:
                return False
            
            # Phase 4: Return to base
            logger.info(f"Phase 4: Returning to base for mission {mission_id}")
            return_success = await self._execute_return_phase(assigned_drones, execution_status)
            
            return return_success
            
        except Exception as e:
            logger.error(f"Error executing mission phases: {e}")
            return False
    
    async def _execute_takeoff_phase(self, drone_ids: List[str], execution_status: MissionExecutionStatus) -> bool:
        """Execute takeoff phase for all drones"""
        try:
            takeoff_tasks = []
            
            for drone_id in drone_ids:
                task = self._send_mission_command(drone_id, {
                    "command_type": "takeoff",
                    "parameters": {
                        "altitude": 50.0
                    }
                })
                takeoff_tasks.append(task)
            
            # Wait for all takeoffs to complete
            results = await asyncio.gather(*takeoff_tasks, return_exceptions=True)
            
            # Check results
            successful_takeoffs = 0
            for i, result in enumerate(results):
                if result is True:
                    successful_takeoffs += 1
                else:
                    execution_status.errors.append(f"Drone {drone_ids[i]} takeoff failed: {result}")
            
            if successful_takeoffs == len(drone_ids):
                execution_status.progress_percentage = 25.0
                return True
            else:
                logger.error(f"Only {successful_takeoffs}/{len(drone_ids)} drones took off successfully")
                return False
                
        except Exception as e:
            logger.error(f"Error in takeoff phase: {e}")
            return False
    
    async def _execute_navigation_phase(self, mission_data: Dict[str, Any], drone_ids: List[str], 
                                      execution_status: MissionExecutionStatus) -> bool:
        """Execute navigation to search areas"""
        try:
            search_areas = mission_data.get("search_areas", [])
            
            navigation_tasks = []
            for i, drone_id in enumerate(drone_ids):
                if i < len(search_areas):
                    area = search_areas[i]
                    task = self._send_mission_command(drone_id, {
                        "command_type": "navigate_to_area",
                        "parameters": {
                            "target_lat": area.get("center_lat", 0),
                            "target_lon": area.get("center_lon", 0),
                            "target_alt": mission_data.get("altitude", 50)
                        }
                    })
                    navigation_tasks.append(task)
            
            # Wait for navigation to complete
            if navigation_tasks:
                results = await asyncio.gather(*navigation_tasks, return_exceptions=True)
                
                successful_navigations = sum(1 for result in results if result is True)
                if successful_navigations == len(navigation_tasks):
                    execution_status.progress_percentage = 50.0
                    return True
                else:
                    logger.error(f"Only {successful_navigations}/{len(navigation_tasks)} drones navigated successfully")
                    return False
            
            execution_status.progress_percentage = 50.0
            return True
            
        except Exception as e:
            logger.error(f"Error in navigation phase: {e}")
            return False
    
    async def _execute_search_phase(self, mission_data: Dict[str, Any], drone_ids: List[str], 
                                  execution_status: MissionExecutionStatus) -> bool:
        """Execute search pattern"""
        try:
            search_pattern = mission_data.get("search_pattern", "grid")
            
            search_tasks = []
            for drone_id in drone_ids:
                task = self._send_mission_command(drone_id, {
                    "command_type": "execute_search_pattern",
                    "parameters": {
                        "pattern": search_pattern,
                        "speed": mission_data.get("speed", 5),
                        "overlap": mission_data.get("overlap", 0.1)
                    }
                })
                search_tasks.append(task)
            
            # Wait for search pattern execution
            if search_tasks:
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                successful_searches = sum(1 for result in results if result is True)
                if successful_searches == len(search_tasks):
                    execution_status.progress_percentage = 75.0
                    return True
                else:
                    logger.error(f"Only {successful_searches}/{len(search_tasks)} drones executed search successfully")
                    return False
            
            execution_status.progress_percentage = 75.0
            return True
            
        except Exception as e:
            logger.error(f"Error in search phase: {e}")
            return False
    
    async def _execute_return_phase(self, drone_ids: List[str], execution_status: MissionExecutionStatus) -> bool:
        """Execute return to base phase"""
        try:
            return_tasks = []
            
            for drone_id in drone_ids:
                task = self._send_mission_command(drone_id, {
                    "command_type": "return_home",
                    "parameters": {}
                })
                return_tasks.append(task)
            
            # Wait for return to complete
            results = await asyncio.gather(*return_tasks, return_exceptions=True)
            
            successful_returns = sum(1 for result in results if result is True)
            if successful_returns == len(drone_ids):
                execution_status.progress_percentage = 100.0
                
                # Unassign drones from mission
                for drone_id in drone_ids:
                    drone_registry.unassign_mission(drone_id)
                
                return True
            else:
                logger.error(f"Only {successful_returns}/{len(drone_ids)} drones returned successfully")
                return False
                
        except Exception as e:
            logger.error(f"Error in return phase: {e}")
            return False
    
    async def _send_mission_command(self, drone_id: str, command_data: Dict[str, Any]) -> bool:
        """Send mission command to drone"""
        try:
            command_type = command_data["command_type"]
            parameters = command_data.get("parameters", {})
            
            return await drone_connection_hub.send_command(
                drone_id, command_type, parameters, priority=2
            )
            
        except Exception as e:
            logger.error(f"Error sending mission command to {drone_id}: {e}")
            return False
    
    async def pause_mission(self, mission_id: str) -> bool:
        """Pause an active mission"""
        try:
            if mission_id not in self.active_executions:
                return False
            
            execution_status = self.active_executions[mission_id]
            if execution_status.status != "executing":
                return False
            
            # Send pause commands to all active drones
            for drone_id in execution_status.active_drones:
                await self._send_mission_command(drone_id, {
                    "command_type": "pause_mission",
                    "parameters": {}
                })
            
            execution_status.status = "paused"
            logger.info(f"Mission {mission_id} paused")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing mission {mission_id}: {e}")
            return False
    
    async def resume_mission(self, mission_id: str) -> bool:
        """Resume a paused mission"""
        try:
            if mission_id not in self.active_executions:
                return False
            
            execution_status = self.active_executions[mission_id]
            if execution_status.status != "paused":
                return False
            
            # Send resume commands to all active drones
            for drone_id in execution_status.active_drones:
                await self._send_mission_command(drone_id, {
                    "command_type": "resume_mission",
                    "parameters": {}
                })
            
            execution_status.status = "executing"
            logger.info(f"Mission {mission_id} resumed")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming mission {mission_id}: {e}")
            return False
    
    async def abort_mission(self, mission_id: str) -> bool:
        """Abort an active mission"""
        try:
            if mission_id not in self.active_executions:
                return False
            
            execution_status = self.active_executions[mission_id]
            
            # Send abort commands to all active drones
            for drone_id in execution_status.active_drones:
                await self._send_mission_command(drone_id, {
                    "command_type": "abort_mission",
                    "parameters": {}
                })
                
                # Unassign drone from mission
                drone_registry.unassign_mission(drone_id)
            
            execution_status.status = "aborted"
            logger.info(f"Mission {mission_id} aborted")
            return True
            
        except Exception as e:
            logger.error(f"Error aborting mission {mission_id}: {e}")
            return False
    
    async def _monitor_executions(self):
        """Monitor active mission executions"""
        while self._running:
            try:
                for mission_id, execution_status in list(self.active_executions.items()):
                    if execution_status.status == "executing":
                        # Check drone status
                        active_count = 0
                        for drone_id in execution_status.active_drones:
                            drone_info = drone_registry.get_drone(drone_id)
                            if drone_info and drone_info.status in [DroneStatus.FLYING, DroneStatus.CONNECTED]:
                                active_count += 1
                        
                        # Update progress based on active drones
                        if execution_status.start_time:
                            elapsed = datetime.utcnow() - execution_status.start_time
                            estimated_duration = timedelta(minutes=30)  # Default 30 minutes
                            
                            if elapsed < estimated_duration:
                                time_progress = (elapsed.total_seconds() / estimated_duration.total_seconds()) * 100
                                execution_status.progress_percentage = min(time_progress, 95.0)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring executions: {e}")
                await asyncio.sleep(5)
    
    def get_execution_status(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status for a mission"""
        if mission_id in self.active_executions:
            return asdict(self.active_executions[mission_id])
        return None
    
    def get_all_execution_status(self) -> Dict[str, Dict[str, Any]]:
        """Get execution status for all missions"""
        return {
            mission_id: asdict(execution_status)
            for mission_id, execution_status in self.active_executions.items()
        }

# Global mission execution engine instance
real_mission_execution_engine = RealMissionExecutionEngine()
