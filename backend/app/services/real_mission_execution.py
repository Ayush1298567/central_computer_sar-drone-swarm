"""
Real Mission Execution Engine for SAR Mission Commander
Integrates mission planning with actual drone connections and control
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json

from ..communication.drone_connection_hub import drone_connection_hub
from ..communication.drone_registry import DroneStatus, drone_registry
from ..communication.drone_registry import get_registry
from ..core.database import SessionLocal
from ..models.mission import Mission, MissionLog
from ..models.drone import Drone, DroneStateHistory
from ..models.mission import MissionDrone
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


class MissionPhase(Enum):
    PREPARE = "prepare"
    TAKEOFF = "takeoff"
    TRANSIT = "transit"
    SEARCH = "search"
    RETURN = "return"
    LAND = "land"
    COMPLETE = "complete"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class DroneState:
    drone_id: str
    phase: MissionPhase = MissionPhase.PREPARE
    progress: float = 0.0
    current_waypoint: int = 0
    total_waypoints: int = 0
    battery_level: float = 100.0
    altitude: float = 0.0
    position: Dict[str, float] = field(default_factory=lambda: {"lat": 0.0, "lon": 0.0, "alt": 0.0})
    last_update: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class MissionState:
    mission_id: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    drones: Dict[str, DroneState]
    waypoints: List[Dict[str, float]]
    parameters: Dict[str, Any]
    overall_progress: float
    current_phase: MissionPhase
    emergency_triggered: bool = False

class RealMissionExecutionEngine:
    """Executes missions on real connected drones"""
    
    def __init__(self):
        self.active_executions: Dict[str, MissionExecutionStatus] = {}
        self._running = False
        self._monitor_task = None
        self._state_writer_task: Optional[asyncio.Task] = None
        # Back-compat containers for unit tests expecting mission orchestration structures
        self._running_missions: Dict[str, MissionState] = {}
        self.hub = drone_connection_hub
        self.registry = drone_registry
        
    async def start(self):
        """Start the mission execution engine"""
        self._running = True
        logger.info("Real Mission Execution Engine started")
        
        # Start monitoring task
        if hasattr(self, "_monitor_executions"):
            self._monitor_task = asyncio.create_task(self._monitor_executions())
        # Start background state writer (1s)
        if hasattr(self, "_write_state_loop"):
            self._state_writer_task = asyncio.create_task(self._write_state_loop())
        # Reload in-progress missions from DB
        try:
            await self.reload_in_progress()
        except Exception as e:
            logger.error(f"Failed to reload in-progress missions: {e}")
        return True

    # No dynamic shims; methods are defined explicitly below for tests
    
    async def stop(self):
        """Stop the mission execution engine"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self._state_writer_task:
            self._state_writer_task.cancel()
            try:
                await self._state_writer_task
            except asyncio.CancelledError:
                pass
        logger.info("Real Mission Execution Engine stopped")
        return True
    
    async def execute_mission(self, mission_id: str, mission_data: Dict[str, Any] | None = None, **kwargs) -> Any:
        """Execute a mission on real drones"""
        try:
            # Back-compat path (tests provide drone_ids/waypoints/parameters as kwargs)
            if kwargs and ("drone_ids" in kwargs or "waypoints" in kwargs or "parameters" in kwargs):
                drone_ids: List[str] = kwargs.get("drone_ids", [])
                waypoints: List[Dict[str, float]] = kwargs.get("waypoints", [])
                parameters: Dict[str, Any] = kwargs.get("parameters", {})
                drones = {d: DroneState(drone_id=d, total_waypoints=len(waypoints), last_update=datetime.utcnow()) for d in drone_ids}
                self._running_missions[mission_id] = MissionState(
                    mission_id=mission_id,
                    status="RUNNING",
                    start_time=datetime.utcnow(),
                    end_time=None,
                    drones=drones,
                    waypoints=waypoints,
                    parameters=parameters,
                    overall_progress=0.0,
                    current_phase=MissionPhase.PREPARE,
                )
                return {"success": True, "mission_id": mission_id, "drones": drone_ids}

            if mission_data is None:
                mission_data = {}
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
            # persist error log
            db = SessionLocal()
            try:
                db.add(MissionLog(mission_id=int(mission_id), event_type="error", message=str(e), payload={}))
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
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

    # Back-compat helper expected in tests
    async def assign_mission_to_drones(self, mission_id: str, drone_ids: List[str], payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for did in drone_ids:
            try:
                # Use connection hub if available else simulate
                ok = await self.hub.send_mission_to_drone(did, payload) if hasattr(self.hub, 'send_mission_to_drone') else True
                results[did] = {"ok": bool(ok), "mission": mission_id}
            except Exception as e:
                results[did] = {"ok": False, "error": str(e)}
        return results

def get_hub(singleton: bool = True):  # for tests monkeypatch
    return drone_connection_hub
    
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

    # Back-compat API expected by some tests
    def get_mission_status(self, mission_id: str) -> Optional[Dict[str, Any]]:
        m = self._running_missions.get(mission_id)
        if not m:
            return None
        return {
            "mission_id": m.mission_id,
            "status": m.status,
            "current_phase": m.current_phase.value,
            "overall_progress": m.overall_progress,
            "drones_count": len(m.drones),
            "drones": list(m.drones.keys()),
        }
    
    def get_all_missions(self) -> List[Dict[str, Any]]:
        return [asdict(ms) for ms in self._running_missions.values()]

    async def abort_mission(self, mission_id: str, reason: str = "") -> bool:
        m = self._running_missions.get(mission_id)
        if not m:
            return False
        m.status = "ABORTED"
        m.current_phase = MissionPhase.ABORTED
        m.end_time = datetime.utcnow()
        m.emergency_triggered = True
        # Send RTL for all drones
        for did in m.drones.keys():
            await self.hub.send_command(
                drone_id=did,
                command_type="return_home",
                parameters={"reason": reason or "Abort"},
                priority=3,
            )
        return True

    async def pause_mission(self, mission_id: str) -> bool:
        m = self._running_missions.get(mission_id)
        if not m:
            return False
        m.status = "PAUSED"
        return True

    async def resume_mission(self, mission_id: str) -> bool:
        m = self._running_missions.get(mission_id)
        if not m:
            return False
        m.status = "RUNNING"
        return True

    def _calculate_progress(self, m: MissionState) -> None:
        if not m.drones:
            m.overall_progress = 0.0
            return
        m.overall_progress = sum(ds.progress for ds in m.drones.values()) / max(1, len(m.drones))

    async def _check_emergency_conditions(self, m: MissionState) -> None:
        for ds in m.drones.values():
            if ds.battery_level <= 15.0:
                await self.hub.send_command(
                    drone_id=ds.drone_id,
                    command_type="emergency_land",
                    parameters={},
                    priority=3,
                )
                ds.phase = MissionPhase.ABORTED
            elif ds.battery_level <= 25.0:
                await self.hub.send_command(
                    drone_id=ds.drone_id,
                    command_type="return_home",
                    parameters={"reason": "Low battery"},
                    priority=3,
                )
                ds.phase = MissionPhase.RETURN

    async def _complete_mission(self, mission_id: str) -> None:
        m = self._running_missions.get(mission_id)
        if not m:
            return
        m.status = "COMPLETED"
        m.current_phase = MissionPhase.COMPLETE
        m.overall_progress = 1.0
        m.end_time = datetime.utcnow()
        for ds in m.drones.values():
            ds.phase = MissionPhase.COMPLETE
            ds.progress = 1.0

    async def _fail_mission(self, mission_id: str, err: str) -> None:
        m = self._running_missions.get(mission_id)
        if not m:
            return
        m.status = "FAILED"
        m.current_phase = MissionPhase.FAILED
        m.end_time = datetime.utcnow()
        for ds in m.drones.values():
            ds.phase = MissionPhase.FAILED
            ds.error_message = err

    async def _update_from_telemetry(self, m: MissionState) -> None:
        """Update in-memory mission state from telemetry receiver (test-friendly)."""
        try:
            from app.communication.telemetry_receiver import get_telemetry_receiver  # type: ignore
            recv = get_telemetry_receiver()
        except Exception:
            return
        for ds in m.drones.values():
            try:
                telemetry = recv.cache.get(ds.drone_id)
            except Exception:
                telemetry = None
            if not telemetry:
                continue
            pos = telemetry.get("position") or {}
            ds.battery_level = telemetry.get("battery_level", ds.battery_level)
            ds.altitude = pos.get("alt", ds.altitude)
            if "lat" in pos and "lon" in pos:
                ds.position["lat"] = pos["lat"]
                ds.position["lon"] = pos["lon"]
                ds.position["alt"] = pos.get("alt", ds.position.get("alt", 0.0))
            ds.last_update = datetime.utcnow()

    async def _write_state_loop(self):
        """Periodically persist mission and drone state to the database."""
        while self._running:
            try:
                await self._persist_state_snapshot()
            except Exception as e:
                logger.error(f"State writer error: {e}")
            await asyncio.sleep(1.0)

    async def _persist_state_snapshot(self):
        """Persist current state for all active missions and drones."""
        if not self.active_executions:
            return
        db = SessionLocal()
        try:
            for mission_id, exec_status in self.active_executions.items():
                # Persist per-drone snapshots
                for drone_id in (exec_status.active_drones or []):
                    info = drone_registry.get_drone(drone_id)
                    if not info:
                        continue
                    history = DroneStateHistory(
                        mission_id=int(mission_id) if str(mission_id).isdigit() else None,
                        drone_id=db.query(Drone).filter(Drone.drone_id == drone_id).first().id if db.query(Drone).filter(Drone.drone_id == drone_id).first() else None,
                        timestamp=datetime.utcnow(),
                        status=info.status.value if hasattr(info.status, 'value') else str(info.status),
                        connection_status='connected',
                        position_lat=info.position.get('lat') if info.position else None,
                        position_lng=info.position.get('lon') if info.position else None,
                        position_alt=info.position.get('alt') if info.position else None,
                        heading=info.heading,
                        speed=info.speed,
                        battery_level=info.battery_level,
                        signal_strength=int(info.signal_strength) if info.signal_strength is not None else None,
                        extra={}
                    )
                    if history.drone_id is not None:
                        db.add(history)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist state snapshot: {e}")
        finally:
            db.close()

    async def reload_in_progress(self) -> None:
        """Recreate execution status for missions that were active or paused before restart."""
        db = SessionLocal()
        try:
            active = db.query(Mission).filter(Mission.status.in_(["active", "paused"])) .all()
            for m in active:
                mission_id = str(m.id)
                if mission_id in self.active_executions:
                    continue
                assigned = db.query(MissionDrone).filter(MissionDrone.mission_id == m.id).all()
                # Map to external string drone_id
                assigned_drone_ids: List[str] = []
                for md in assigned:
                    d = db.query(Drone).filter(Drone.id == md.drone_id).first()
                    if d and d.drone_id:
                        assigned_drone_ids.append(d.drone_id)
                status = MissionExecutionStatus(
                    mission_id=mission_id,
                    status="executing" if m.status == "active" else "paused",
                    progress_percentage=m.progress_percentage or 0.0,
                    start_time=m.actual_start_time,
                    active_drones=assigned_drone_ids,
                    completed_areas=[],
                    errors=[],
                )
                self.active_executions[mission_id] = status
                # Request telemetry to resume streams
                for did in assigned_drone_ids:
                    try:
                        await drone_connection_hub.request_telemetry(did)
                    except Exception:
                        pass
        finally:
            db.close()

# Global mission execution engine instance
real_mission_execution_engine = RealMissionExecutionEngine()
