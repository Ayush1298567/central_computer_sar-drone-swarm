"""
Mission Execution Service for SAR Mission Commander
Handles automated mission coordination and execution
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

from ..core.database import SessionLocal
from ..models.mission import Mission, MissionStatus
from ..models.drone import Drone
from ..models.discovery import Discovery
from ..services.drone_manager import drone_manager, DroneCommand, DroneCommandType
from ..utils.logging import get_logger
from ..utils.geometry import calculate_search_pattern, calculate_area_coverage

logger = get_logger(__name__)

class ExecutionPhase(Enum):
    PLANNING = "planning"
    PREPARATION = "preparation"
    SEARCH = "search"
    INVESTIGATION = "investigation"
    COMPLETION = "completion"
    EMERGENCY = "emergency"

@dataclass
class MissionExecution:
    mission_id: str
    phase: ExecutionPhase
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    assigned_drones: List[str] = field(default_factory=list)
    search_progress: Dict[str, float] = field(default_factory=dict)  # drone_id -> coverage_percentage
    discoveries: List[str] = field(default_factory=list)  # discovery_ids
    status_updates: List[Dict] = field(default_factory=list)

class MissionExecutionService:
    """Manages mission execution and coordination"""
    
    def __init__(self):
        self.active_executions: Dict[str, MissionExecution] = {}
        self.execution_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        
    async def start(self):
        """Start the mission execution service"""
        self._running = True
        logger.info("Mission Execution service started")
        
        # Start background monitoring task
        asyncio.create_task(self._monitor_executions())
        
    async def stop(self):
        """Stop the mission execution service"""
        self._running = False
        
        # Cancel all active execution tasks
        for task in self.execution_tasks.values():
            task.cancel()
            
        logger.info("Mission Execution service stopped")
    
    async def start_mission(self, mission_id: str) -> bool:
        """Start executing a mission"""
        try:
            # Check if mission is already being executed
            if mission_id in self.active_executions:
                logger.warning(f"Mission {mission_id} is already being executed")
                return False
            
            # Get mission from database
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    logger.error(f"Mission {mission_id} not found")
                    return False

                if mission.status != MissionStatus.PLANNING:
                    logger.error(f"Mission {mission_id} is not in planning status")
                    return False
            finally:
                db.close()

            # Create execution plan
            execution = MissionExecution(
                mission_id=mission_id,
                phase=ExecutionPhase.PLANNING
            )
            
            self.active_executions[mission_id] = execution
            
            # Start execution task
            execution_task = asyncio.create_task(self._execute_mission(mission_id))
            self.execution_tasks[mission_id] = execution_task
            
            logger.info(f"Mission {mission_id} execution started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start mission {mission_id}: {e}")
            return False
    
    async def pause_mission(self, mission_id: str) -> bool:
        """Pause a mission execution"""
        try:
            if mission_id not in self.active_executions:
                logger.warning(f"Mission {mission_id} is not being executed")
                return False
            
            execution = self.active_executions[mission_id]
            
            # Pause all assigned drones
            for drone_id in execution.assigned_drones:
                await drone_manager.send_command(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.LAND,
                    priority=2
                ))
            
            # Update mission status
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = MissionStatus.PAUSED
                    db.commit()
            finally:
                db.close()

            logger.info(f"Mission {mission_id} paused")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause mission {mission_id}: {e}")
            return False
    
    async def resume_mission(self, mission_id: str) -> bool:
        """Resume a paused mission"""
        try:
            if mission_id not in self.active_executions:
                logger.warning(f"Mission {mission_id} is not being executed")
                return False
            
            execution = self.active_executions[mission_id]
            
            # Resume all assigned drones
            for drone_id in execution.assigned_drones:
                await drone_manager.send_command(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.START_MISSION,
                    priority=2
                ))
            
            # Update mission status
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = MissionStatus.ACTIVE
                    db.commit()
            finally:
                db.close()

            logger.info(f"Mission {mission_id} resumed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume mission {mission_id}: {e}")
            return False
    
    async def complete_mission(self, mission_id: str) -> bool:
        """Complete a mission execution"""
        try:
            if mission_id not in self.active_executions:
                logger.warning(f"Mission {mission_id} is not being executed")
                return False
            
            execution = self.active_executions[mission_id]
            
            # Return all drones home
            for drone_id in execution.assigned_drones:
                await drone_manager.send_command(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.RETURN_HOME,
                    priority=2
                ))
                await drone_manager.unassign_mission(drone_id)
            
            # Update mission status
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = MissionStatus.COMPLETED
                    mission.end_time = datetime.utcnow()
                    db.commit()
            finally:
                db.close()

            # Clean up execution
            if mission_id in self.execution_tasks:
                self.execution_tasks[mission_id].cancel()
                del self.execution_tasks[mission_id]
            
            del self.active_executions[mission_id]
            
            logger.info(f"Mission {mission_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete mission {mission_id}: {e}")
            return False
    
    async def emergency_stop_mission(self, mission_id: str) -> bool:
        """Emergency stop a mission"""
        try:
            if mission_id not in self.active_executions:
                logger.warning(f"Mission {mission_id} is not being executed")
                return False
            
            execution = self.active_executions[mission_id]
            execution.phase = ExecutionPhase.EMERGENCY
            
            # Emergency stop all assigned drones
            for drone_id in execution.assigned_drones:
                await drone_manager.send_command(DroneCommand(
                    drone_id=drone_id,
                    command_type=DroneCommandType.EMERGENCY_STOP,
                    priority=3
                ))
            
            # Update mission status
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = MissionStatus.CANCELLED
                    mission.end_time = datetime.utcnow()
                    db.commit()
            finally:
                db.close()

            logger.warning(f"Mission {mission_id} emergency stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to emergency stop mission {mission_id}: {e}")
            return False
    
    async def get_execution_status(self, mission_id: str) -> Optional[Dict]:
        """Get execution status of a mission"""
        if mission_id not in self.active_executions:
            return None
        
        execution = self.active_executions[mission_id]
        
        # Calculate overall progress
        total_coverage = sum(execution.search_progress.values())
        avg_coverage = total_coverage / len(execution.search_progress) if execution.search_progress else 0
        
        return {
            "mission_id": mission_id,
            "phase": execution.phase.value,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "estimated_completion": execution.estimated_completion.isoformat() if execution.estimated_completion else None,
            "assigned_drones": execution.assigned_drones,
            "search_progress": execution.search_progress,
            "overall_coverage": avg_coverage,
            "discoveries_count": len(execution.discoveries),
            "status_updates": execution.status_updates[-10:]  # Last 10 updates
        }
    
    async def _execute_mission(self, mission_id: str):
        """Execute a mission (main execution loop)"""
        try:
            execution = self.active_executions[mission_id]
            
            # Phase 1: Planning
            await self._planning_phase(mission_id)
            
            # Phase 2: Preparation
            await self._preparation_phase(mission_id)
            
            # Phase 3: Search
            await self._search_phase(mission_id)
            
            # Phase 4: Investigation (if discoveries found)
            if execution.discoveries:
                await self._investigation_phase(mission_id)
            
            # Phase 5: Completion
            await self._completion_phase(mission_id)
            
        except asyncio.CancelledError:
            logger.info(f"Mission {mission_id} execution cancelled")
        except Exception as e:
            logger.error(f"Error executing mission {mission_id}: {e}")
            await self._handle_execution_error(mission_id, str(e))
    
    async def _planning_phase(self, mission_id: str):
        """Planning phase - assign drones and create search pattern"""
        execution = self.active_executions[mission_id]
        execution.phase = ExecutionPhase.PLANNING
        
        logger.info(f"Mission {mission_id} - Planning phase started")
        
        # Get available drones
        available_drones = drone_manager.get_available_drones()
        
        if not available_drones:
            raise Exception("No available drones for mission")
        
        # Assign drones based on mission requirements
        db = SessionLocal()
        try:
            mission = db.query(Mission).filter(Mission.id == mission_id).first()
            if not mission:
                raise Exception("Mission not found")

            max_drones = mission.max_drones or len(available_drones)
            assigned_count = 0

            for drone in available_drones[:max_drones]:
                if await drone_manager.assign_mission(drone["id"], mission_id):
                    execution.assigned_drones.append(drone["id"])
                    execution.search_progress[drone["id"]] = 0.0
                    assigned_count += 1

            if assigned_count == 0:
                raise Exception("Failed to assign any drones to mission")

            # Update mission status
            mission.status = MissionStatus.ACTIVE
            mission.start_time = datetime.utcnow()
            db.commit()
        finally:
            db.close()

        execution.start_time = datetime.utcnow()
        
        # Estimate completion time
        if mission.time_limit_minutes:
            execution.estimated_completion = datetime.utcnow() + timedelta(minutes=mission.time_limit_minutes)
        
        self._add_status_update(execution, "Planning completed", f"Assigned {assigned_count} drones")
        logger.info(f"Mission {mission_id} - Planning completed with {assigned_count} drones")
    
    async def _preparation_phase(self, mission_id: str):
        """Preparation phase - prepare drones and systems"""
        execution = self.active_executions[mission_id]
        execution.phase = ExecutionPhase.PREPARATION
        
        logger.info(f"Mission {mission_id} - Preparation phase started")
        
        # Send preparation commands to all drones
        for drone_id in execution.assigned_drones:
            # Enable autonomous mode
            await drone_manager.send_command(DroneCommand(
                drone_id=drone_id,
                command_type=DroneCommandType.ENABLE_AUTONOMOUS,
                priority=1
            ))
            
            # Set mission altitude if specified
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission and mission.altitude:
                    await drone_manager.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.UPDATE_ALTITUDE,
                        parameters={"altitude": mission.altitude},
                        priority=1
                    ))
            finally:
                db.close()

        # Wait for drones to be ready
        await asyncio.sleep(5)
        
        self._add_status_update(execution, "Preparation completed", "All drones ready for search")
        logger.info(f"Mission {mission_id} - Preparation completed")
    
    async def _search_phase(self, mission_id: str):
        """Search phase - execute search pattern"""
        execution = self.active_executions[mission_id]
        execution.phase = ExecutionPhase.SEARCH
        
        logger.info(f"Mission {mission_id} - Search phase started")
        
        # Start search for all drones
        for drone_id in execution.assigned_drones:
            await drone_manager.send_command(DroneCommand(
                drone_id=drone_id,
                command_type=DroneCommandType.START_MISSION,
                priority=1
            ))
        
        # Monitor search progress
        search_start_time = datetime.utcnow()
        while execution.phase == ExecutionPhase.SEARCH:
            await asyncio.sleep(30)  # Check progress every 30 seconds
            
            # Update search progress (simulated)
            for drone_id in execution.assigned_drones:
                drone_status = drone_manager.get_drone_status(drone_id)
                if drone_status and drone_status["status"] == "mission":
                    # Simulate progress based on time elapsed
                    elapsed_minutes = (datetime.utcnow() - search_start_time).total_seconds() / 60
                    progress = min(elapsed_minutes * 2, 100)  # 2% per minute
                    execution.search_progress[drone_id] = progress
            
            # Check if search should continue
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    # Check time limit
                    if mission.time_limit_minutes:
                        elapsed = (datetime.utcnow() - execution.start_time).total_seconds() / 60
                        if elapsed >= mission.time_limit_minutes:
                            logger.info(f"Mission {mission_id} - Time limit reached")
                            break
                    
                    # Check area coverage
                    total_coverage = sum(execution.search_progress.values())
                    avg_coverage = total_coverage / len(execution.search_progress)
                    if avg_coverage >= 95:  # 95% coverage threshold
                        logger.info(f"Mission {mission_id} - Search area coverage completed")
                        break
            finally:
                db.close()

            # Check for discoveries
            db = SessionLocal()
            try:
                discoveries = db.query(Discovery).filter(
                    Discovery.mission_id == mission_id,
                    Discovery.timestamp >= execution.start_time
                ).all()

                for discovery in discoveries:
                    if discovery.id not in execution.discoveries:
                        execution.discoveries.append(discovery.id)
                        self._add_status_update(
                            execution,
                            "Discovery found",
                            f"Found {discovery.type} with {discovery.confidence*100:.1f}% confidence"
                        )
            finally:
                db.close()
        
        self._add_status_update(execution, "Search completed", f"Covered {sum(execution.search_progress.values())/len(execution.search_progress):.1f}% of area")
        logger.info(f"Mission {mission_id} - Search phase completed")
    
    async def _investigation_phase(self, mission_id: str):
        """Investigation phase - investigate discoveries"""
        execution = self.active_executions[mission_id]
        execution.phase = ExecutionPhase.INVESTIGATION
        
        logger.info(f"Mission {mission_id} - Investigation phase started")
        
        # For each discovery, send drones for closer investigation
        db = SessionLocal()
        try:
            discoveries = db.query(Discovery).filter(Discovery.id.in_(execution.discoveries)).all()

            for discovery in discoveries:
                # Find closest drone
                closest_drone = None
                min_distance = float('inf')
                
                for drone_id in execution.assigned_drones:
                    drone_status = drone_manager.get_drone_status(drone_id)
                    if drone_status:
                        # Calculate distance (simplified)
                        drone_pos = drone_status["position"]
                        discovery_pos = {"latitude": discovery.position_latitude, "longitude": discovery.position_longitude}
                        distance = self._calculate_distance(drone_pos, discovery_pos)
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_drone = drone_id
                
                if closest_drone:
                    # Send drone to investigate
                    await drone_manager.send_command(DroneCommand(
                        drone_id=closest_drone,
                        command_type=DroneCommandType.CHANGE_HEADING,
                        parameters={
                            "target_latitude": discovery.position_latitude,
                            "target_longitude": discovery.position_longitude
                        },
                        priority=2
                    ))
                    
                    self._add_status_update(
                        execution,
                        "Investigation started",
                        f"Drone {closest_drone} investigating {discovery.type}"
                    )
                    
                    # Wait for investigation
                    await asyncio.sleep(60)  # 1 minute investigation time
        finally:
            db.close()

        self._add_status_update(execution, "Investigation completed", f"Investigated {len(execution.discoveries)} discoveries")
        logger.info(f"Mission {mission_id} - Investigation phase completed")
    
    async def _completion_phase(self, mission_id: str):
        """Completion phase - finalize mission"""
        execution = self.active_executions[mission_id]
        execution.phase = ExecutionPhase.COMPLETION
        
        logger.info(f"Mission {mission_id} - Completion phase started")
        
        # Return all drones home
        for drone_id in execution.assigned_drones:
            await drone_manager.send_command(DroneCommand(
                drone_id=drone_id,
                command_type=DroneCommandType.RETURN_HOME,
                priority=2
            ))
        
        # Wait for all drones to return
        await asyncio.sleep(30)
        
        # Update mission in database
        db = SessionLocal()
        try:
            mission = db.query(Mission).filter(Mission.id == mission_id).first()
            if mission:
                mission.status = MissionStatus.COMPLETED
                mission.end_time = datetime.utcnow()

                # Calculate final statistics
                total_coverage = sum(execution.search_progress.values())
                mission.area_covered = total_coverage / len(execution.search_progress) if execution.search_progress else 0
                mission.discoveries_found = len(execution.discoveries)

                db.commit()
        finally:
            db.close()

        self._add_status_update(execution, "Mission completed", f"Found {len(execution.discoveries)} discoveries")
        logger.info(f"Mission {mission_id} - Mission completed successfully")
    
    async def _handle_execution_error(self, mission_id: str, error_message: str):
        """Handle execution errors"""
        try:
            # Emergency stop all drones
            if mission_id in self.active_executions:
                execution = self.active_executions[mission_id]
                for drone_id in execution.assigned_drones:
                    await drone_manager.send_command(DroneCommand(
                        drone_id=drone_id,
                        command_type=DroneCommandType.EMERGENCY_STOP,
                        priority=3
                    ))
            
            # Update mission status
            db = SessionLocal()
            try:
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.status = MissionStatus.CANCELLED
                    mission.end_time = datetime.utcnow()
                    db.commit()
            finally:
                db.close()

            # Clean up execution
            if mission_id in self.execution_tasks:
                self.execution_tasks[mission_id].cancel()
                del self.execution_tasks[mission_id]
            
            if mission_id in self.active_executions:
                del self.active_executions[mission_id]
            
            logger.error(f"Mission {mission_id} execution failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to handle execution error for mission {mission_id}: {e}")
    
    async def _monitor_executions(self):
        """Background task to monitor all executions"""
        while self._running:
            try:
                for mission_id, execution in list(self.active_executions.items()):
                    # Check for stuck executions
                    if execution.start_time:
                        elapsed = datetime.utcnow() - execution.start_time
                        if elapsed.total_seconds() > 3600:  # 1 hour timeout
                            logger.warning(f"Mission {mission_id} execution timeout")
                            await self.emergency_stop_mission(mission_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring executions: {e}")
                await asyncio.sleep(60)
    
    def _add_status_update(self, execution: MissionExecution, status: str, details: str):
        """Add status update to execution"""
        update = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "details": details
        }
        execution.status_updates.append(update)
    
    def _calculate_distance(self, pos1: Dict, pos2: Dict) -> float:
        """Calculate distance between two positions (simplified)"""
        # Simplified distance calculation - in real implementation use proper geodetic calculation
        lat_diff = abs(pos1["latitude"] - pos2["latitude"])
        lon_diff = abs(pos1["longitude"] - pos2["longitude"])
        return (lat_diff + lon_diff) * 111000  # Rough conversion to meters

# Global mission execution service instance
mission_execution_service = MissionExecutionService()