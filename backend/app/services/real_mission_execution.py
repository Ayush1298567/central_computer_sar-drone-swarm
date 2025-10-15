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
from ..models.advanced_models import AIDecisionLog
from ..models.logs import MissionLog, DroneStateHistory
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
        return True
    
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
        return True

    async def replan_mission(self, mission_id: str, new_plan: dict) -> bool:
        """Update mission plan in DB and restart execution cleanly."""
        try:
            # Persist new plan
            db = SessionLocal()
            try:
                mission: Optional[Mission] = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if not mission:
                    logger.error(f"Mission not found for replan: {mission_id}")
                    return False
                # Update basic fields if provided
                mission.search_area = new_plan.get("search_area", mission.search_area)
                mission.center_lat = new_plan.get("center_lat", mission.center_lat)
                mission.center_lng = new_plan.get("center_lng", mission.center_lng)
                mission.altitude = new_plan.get("altitude", mission.altitude)
                mission.search_altitude = new_plan.get("search_altitude", mission.search_altitude)
                mission.search_pattern = new_plan.get("search_pattern", mission.search_pattern)
                mission.overlap_percentage = new_plan.get("overlap", mission.overlap_percentage)
                mission.max_drones = new_plan.get("max_drones", mission.max_drones)
                db.add(mission)
                db.commit()
            finally:
                db.close()

            # If executing, abort and restart with new plan
            execution_status = self.active_executions.get(mission_id)
            if execution_status and execution_status.status in {"executing", "ready", "paused"}:
                # Pause guard: do not continue executing if paused
                if execution_status.status == "paused":
                    logger.info(f"Mission {mission_id} is paused; will not auto-restart after replan")
                else:
                    await self.abort_mission(mission_id)
                    # Small delay to allow clean unassign
                    await asyncio.sleep(0.2)
                    # Restart using new plan
                    await self.execute_mission(mission_id, new_plan)

            # Log replan in mission log
            try:
                db2 = SessionLocal()
                log = MissionLog(
                    mission_id=mission_id,
                    event_type="replan",
                    payload={"new_plan": new_plan},
                )
                db2.add(log)
                db2.commit()
            except Exception:
                logger.exception("Failed to write MissionLog for replan")
            finally:
                try:
                    db2.close()
                except Exception:
                    pass

            return True
        except Exception as e:
            logger.error(f"Error re-planning mission {mission_id}: {e}")
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

    async def emergency_rtl(self, drone_id: str) -> bool:
        """Public wrapper to trigger Return-To-Launch and log entries."""
        try:
            ok = drone_connection_hub.send_emergency_command(drone_id, "rtl")
            db = SessionLocal()
            try:
                db.add(MissionLog(mission_id="unknown", event_type="ai_decision", payload={"action": "emergency_rtl", "drone_id": drone_id, "result": bool(ok)}))
                db.add(AIDecisionLog(
                    decision_type="emergency_rtl",
                    decision_id=f"rtl_{drone_id}",
                    drone_id=drone_id,
                    decision_description="Emergency RTL invoked",
                    selected_option={"action": "rtl"},
                    confidence_score=1.0,
                    outcome="success" if ok else "failure",
                    outcome_timestamp=datetime.utcnow(),
                    timestamp=datetime.utcnow(),
                ))
                db.commit()
            finally:
                db.close()
            return bool(ok)
        except Exception as e:
            logger.error(f"Emergency RTL failed for {drone_id}: {e}")
            return False

    async def emergency_land(self, drone_id: str) -> bool:
        """Public wrapper to trigger Emergency Land and log entries."""
        try:
            ok = drone_connection_hub.send_emergency_command(drone_id, "land")
            db = SessionLocal()
            try:
                db.add(MissionLog(mission_id="unknown", event_type="ai_decision", payload={"action": "emergency_land", "drone_id": drone_id, "result": bool(ok)}))
                db.add(AIDecisionLog(
                    decision_type="emergency_land",
                    decision_id=f"land_{drone_id}",
                    drone_id=drone_id,
                    decision_description="Emergency Land invoked",
                    selected_option={"action": "land"},
                    confidence_score=1.0,
                    outcome="success" if ok else "failure",
                    outcome_timestamp=datetime.utcnow(),
                    timestamp=datetime.utcnow(),
                ))
                db.commit()
            finally:
                db.close()
            return bool(ok)
        except Exception as e:
            logger.error(f"Emergency Land failed for {drone_id}: {e}")
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
            # Safety guard: log pause
            try:
                db = SessionLocal()
                db.add(MissionLog(mission_id=mission_id, event_type="mission_update", payload={"action": "pause"}))
                db.commit()
            except Exception:
                logger.exception("Failed to log pause action")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
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
            try:
                db = SessionLocal()
                db.add(MissionLog(mission_id=mission_id, event_type="mission_update", payload={"action": "resume"}))
                db.commit()
            except Exception:
                logger.exception("Failed to log resume action")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
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
            try:
                db = SessionLocal()
                db.add(MissionLog(mission_id=mission_id, event_type="mission_update", payload={"action": "abort"}))
                db.commit()
            except Exception:
                logger.exception("Failed to log abort action")
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return True
            
        except Exception as e:
            logger.error(f"Error aborting mission {mission_id}: {e}")
            return False
    
    async def _monitor_executions(self):
        """Monitor active mission executions"""
        while self._running:
            try:
                for mission_id, execution_status in list(self.active_executions.items()):
                    if execution_status.status == "paused":
                        # Safety guard: do not execute flight updates
                        continue
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

                        # Persist per-second telemetry snapshot for active drones
                        try:
                            await self._persist_active_drone_states(mission_id, execution_status.active_drones)
                        except Exception as e:
                            logger.warning(f"Telemetry persistence error for mission {mission_id}: {e}")

                await asyncio.sleep(1)  # Check every 1 second for better persistence reliability
                
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

    async def emergency_rtl(self, drone_id: str) -> bool:
        """Public wrapper to trigger Return-To-Launch safely and log outcome."""
        try:
            ok = await self._send_mission_command(drone_id, {"command_type": "return_home", "parameters": {}})
            await self._append_logs(
                mission_id=self._mission_for_drone(drone_id),
                event_type="ai_decision",
                payload={
                    "action": "emergency_rtl",
                    "drone_id": drone_id,
                    "result": "success" if ok else "failure",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return ok
        except Exception as e:
            logger.error(f"Emergency RTL failed for {drone_id}: {e}")
            await self._append_logs(self._mission_for_drone(drone_id), "ai_decision", {
                "action": "emergency_rtl", "drone_id": drone_id, "result": "error", "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            return False

    async def emergency_land(self, drone_id: str) -> bool:
        """Public wrapper to trigger immediate land safely and log outcome."""
        try:
            ok = await self._send_mission_command(drone_id, {"command_type": "land", "parameters": {}})
            await self._append_logs(
                mission_id=self._mission_for_drone(drone_id),
                event_type="ai_decision",
                payload={
                    "action": "emergency_land",
                    "drone_id": drone_id,
                    "result": "success" if ok else "failure",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return ok
        except Exception as e:
            logger.error(f"Emergency land failed for {drone_id}: {e}")
            await self._append_logs(self._mission_for_drone(drone_id), "ai_decision", {
                "action": "emergency_land", "drone_id": drone_id, "result": "error", "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            return False

    async def apply_decision(self, decision_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an AI decision by executing the recommended action and logging outcome."""
        action = payload.get("action") or payload.get("recommended_action")
        mission_id = payload.get("mission_id")
        drone_id = payload.get("drone_id")
        params = payload.get("parameters", {})
        result: Dict[str, Any] = {"decision_id": decision_id, "action": action, "status": "unknown"}
        try:
            ok = False
            if action == "emergency_rtl" and drone_id:
                ok = await self.emergency_rtl(drone_id)
            elif action == "emergency_land" and drone_id:
                ok = await self.emergency_land(drone_id)
            elif action == "pause_mission" and mission_id:
                ok = await self.pause_mission(mission_id)
            elif action == "resume_mission" and mission_id:
                ok = await self.resume_mission(mission_id)
            elif action == "abort_mission" and mission_id:
                ok = await self.abort_mission(mission_id)
            elif action == "replan_mission" and mission_id:
                ok = await self.replan_mission(mission_id, params or {})
            else:
                result["status"] = "rejected"
                result["error"] = "unsupported_action_or_missing_ids"
                await self._append_logs(mission_id, "ai_decision", {
                    "decision_id": decision_id, "action": action, "result": "rejected", "reason": result.get("error")
                })
                return result

            result["status"] = "applied" if ok else "failed"
            await self._append_logs(mission_id or self._mission_for_drone(drone_id) if drone_id else None, "ai_decision", {
                "decision_id": decision_id, "action": action, "drone_id": drone_id, "result": result["status"],
                "timestamp": datetime.utcnow().isoformat(),
            })
            return result
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            await self._append_logs(mission_id or self._mission_for_drone(drone_id) if drone_id else None, "ai_decision", {
                "decision_id": decision_id, "action": action, "drone_id": drone_id, "result": "error", "error": str(e)
            })
            return result

    async def _append_logs(self, mission_id: Optional[str], event_type: str, payload: Dict[str, Any]) -> None:
        """Append entries to MissionLog and AIDecisionLog."""
        try:
            db = SessionLocal()
            try:
                if mission_id:
                    db.add(MissionLog(mission_id=mission_id, event_type=event_type, payload=payload))
                if event_type == "ai_decision":
                    db.add(AIDecisionLog(
                        decision_type="mission_engine",
                        decision_id=str(payload.get("decision_id") or payload.get("action") or "unknown"),
                        mission_id=mission_id,
                        drone_id=payload.get("drone_id"),
                        decision_description=json.dumps(payload),
                        decision_options=None,
                        selected_option=None,
                        confidence_score=payload.get("confidence_score"),
                        reasoning_chain=payload.get("reasoning"),
                        knowledge_sources=None,
                        model_predictions=None,
                        outcome=payload.get("result"),
                        outcome_metrics=None,
                        outcome_timestamp=datetime.utcnow(),
                    ))
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to append logs: {e}")

    async def _persist_active_drone_states(self, mission_id: str, drone_ids: List[str]) -> None:
        """Persist a telemetry snapshot per active drone."""
        if not drone_ids:
            return
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            for drone_id in drone_ids:
                info = drone_registry.get_drone(drone_id)
                latitude = None
                longitude = None
                altitude = None
                if info and hasattr(info, "position") and isinstance(info.position, dict):
                    latitude = info.position.get("lat")
                    longitude = info.position.get("lon")
                    altitude = info.position.get("alt")
                snap = DroneStateHistory(
                    drone_id=drone_id,
                    mission_id=mission_id,
                    timestamp=now,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=altitude,
                    battery_percentage=getattr(info, "battery_level", None) if info else None,
                    flight_mode=str(getattr(info, "status", "")) if info else None,
                    status=str(getattr(info, "status", "")) if info else None,
                    signal_strength=getattr(info, "signal_strength", None) if info else None,
                    payload={
                        "raw": {
                            "position": getattr(info, "position", None) if info else None,
                            "heading": getattr(info, "heading", None) if info else None,
                            "speed": getattr(info, "speed", None) if info else None,
                        }
                    }
                )
                db.add(snap)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist drone states: {e}")
        finally:
            db.close()

    def _mission_for_drone(self, drone_id: str) -> Optional[str]:
        """Lookup mission id for a given drone via registry."""
        try:
            info = drone_registry.get_drone(drone_id)
            return getattr(info, "current_mission_id", None) if info else None
        except Exception:
            return None

# Global mission execution engine instance
real_mission_execution_engine = RealMissionExecutionEngine()
