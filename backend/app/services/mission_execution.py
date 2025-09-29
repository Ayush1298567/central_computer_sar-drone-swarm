"""
Mission execution service for managing mission lifecycle and state.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import SessionLocal
from app.models import Mission, Drone, Discovery, MissionDrone
from app.services.coordination_engine import coordination_engine, CoordinationCommand
from app.services.weather_service import weather_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class MissionExecutionStatus(str, Enum):
    """Mission execution status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EMERGENCY = "emergency"


@dataclass
class MissionExecutionState:
    """Current state of mission execution."""
    mission_id: str
    status: MissionExecutionStatus
    progress_percentage: float
    active_drones: int
    completed_drones: int
    discoveries_found: int
    estimated_completion: Optional[datetime]
    current_phase: str
    last_update: datetime


class MissionExecutionService:
    """
    Mission execution service for managing mission lifecycle and state.
    """

    def __init__(self):
        self.active_executions: Dict[str, MissionExecutionState] = {}
        self.execution_history: List[Dict] = []
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def start_mission_execution(self, mission_id: str) -> bool:
        """
        Start mission execution for a given mission.

        Args:
            mission_id: ID of the mission to start

        Returns:
            True if execution started successfully, False otherwise
        """
        try:
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if not mission:
                    logger.error(f"Mission {mission_id} not found")
                    return False

                # Check if mission is ready to start
                if mission.status not in ["ready", "planning"]:
                    logger.error(f"Mission {mission_id} is not ready to start (status: {mission.status})")
                    return False

                # Initialize execution state
                execution_state = MissionExecutionState(
                    mission_id=mission_id,
                    status=MissionExecutionStatus.INITIALIZING,
                    progress_percentage=0.0,
                    active_drones=0,
                    completed_drones=0,
                    discoveries_found=0,
                    estimated_completion=None,
                    current_phase="initialization",
                    last_update=datetime.utcnow()
                )

                self.active_executions[mission_id] = execution_state

                # Update mission status
                mission.status = "active"
                mission.actual_start_time = datetime.utcnow()
                db.commit()

                # Start coordination
                await coordination_engine.start_mission(mission_id)

                # Start monitoring task
                monitoring_task = asyncio.create_task(
                    self._monitor_mission_execution(mission_id)
                )
                self.monitoring_tasks[mission_id] = monitoring_task

                logger.info(f"Mission execution started for {mission_id}")
                return True

        except Exception as e:
            logger.error(f"Error starting mission execution: {e}")
            return False

    async def pause_mission_execution(self, mission_id: str) -> bool:
        """
        Pause mission execution.

        Args:
            mission_id: ID of the mission to pause

        Returns:
            True if paused successfully, False otherwise
        """
        try:
            if mission_id not in self.active_executions:
                logger.error(f"No active execution found for mission {mission_id}")
                return False

            execution_state = self.active_executions[mission_id]
            execution_state.status = MissionExecutionStatus.PAUSED
            execution_state.current_phase = "paused"
            execution_state.last_update = datetime.utcnow()

            # Update database
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if mission:
                    mission.status = "paused"
                    db.commit()

            logger.info(f"Mission execution paused for {mission_id}")
            return True

        except Exception as e:
            logger.error(f"Error pausing mission execution: {e}")
            return False

    async def resume_mission_execution(self, mission_id: str) -> bool:
        """
        Resume mission execution.

        Args:
            mission_id: ID of the mission to resume

        Returns:
            True if resumed successfully, False otherwise
        """
        try:
            if mission_id not in self.active_executions:
                logger.error(f"No execution state found for mission {mission_id}")
                return False

            execution_state = self.active_executions[mission_id]
            if execution_state.status != MissionExecutionStatus.PAUSED:
                logger.error(f"Mission {mission_id} is not paused")
                return False

            execution_state.status = MissionExecutionStatus.ACTIVE
            execution_state.current_phase = "active"
            execution_state.last_update = datetime.utcnow()

            # Update database
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if mission:
                    mission.status = "active"
                    db.commit()

            logger.info(f"Mission execution resumed for {mission_id}")
            return True

        except Exception as e:
            logger.error(f"Error resuming mission execution: {e}")
            return False

    async def complete_mission_execution(self, mission_id: str, success: bool = True) -> bool:
        """
        Complete mission execution.

        Args:
            mission_id: ID of the mission to complete
            success: Whether the mission completed successfully

        Returns:
            True if completed successfully, False otherwise
        """
        try:
            if mission_id not in self.active_executions:
                logger.error(f"No execution state found for mission {mission_id}")
                return False

            execution_state = self.active_executions[mission_id]
            execution_state.status = MissionExecutionStatus.COMPLETED if success else MissionExecutionStatus.FAILED
            execution_state.current_phase = "completed"
            execution_state.last_update = datetime.utcnow()

            # Update database
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if mission:
                    mission.status = "completed" if success else "failed"
                    mission.actual_end_time = datetime.utcnow()
                    mission.progress_percentage = 100.0

                    # Calculate final metrics
                    mission.area_covered = self._calculate_area_covered(mission)
                    mission.discoveries_count = len(mission.discoveries)

                    db.commit()

            # Stop monitoring
            if mission_id in self.monitoring_tasks:
                self.monitoring_tasks[mission_id].cancel()
                del self.monitoring_tasks[mission_id]

            # Remove from active executions
            del self.active_executions[mission_id]

            # Log completion
            self._log_execution_event(mission_id, "mission_completed", {
                "success": success,
                "final_progress": execution_state.progress_percentage
            })

            logger.info(f"Mission execution completed for {mission_id} (success: {success})")
            return True

        except Exception as e:
            logger.error(f"Error completing mission execution: {e}")
            return False

    async def process_drone_command_response(self, drone_id: str, command_id: str, response: Dict) -> None:
        """
        Process response from drone command execution.

        Args:
            drone_id: ID of the drone that executed the command
            command_id: ID of the executed command
            response: Response data from the drone
        """
        try:
            # Update drone state based on command response
            updates = {}

            if response.get("status") == "completed":
                updates["status"] = "flying"  # Assuming successful command completion

            if "position" in response:
                pos = response["position"]
                updates["lat"] = pos.get("lat")
                updates["lng"] = pos.get("lng")
                updates["alt"] = pos.get("alt")

            if "battery" in response:
                updates["battery_level"] = response["battery"]

            if updates:
                await coordination_engine.update_drone_state(drone_id, updates)

            # Update mission progress
            with SessionLocal() as db:
                # Find mission for this drone
                mission_drone = db.query(MissionDrone).filter(
                    MissionDrone.drone_id == db.query(Drone.id).filter(Drone.drone_id == drone_id).first().id
                ).first()

                if mission_drone:
                    # Update waypoint progress
                    if "waypoint_reached" in response:
                        mission_drone.current_waypoint = response["waypoint_reached"]

                    if response.get("status") == "completed":
                        mission_drone.status = "completed"
                        mission_drone.completed_at = datetime.utcnow()

                    db.commit()

            logger.info(f"Processed command response for drone {drone_id}: {response.get('status', 'unknown')}")

        except Exception as e:
            logger.error(f"Error processing drone command response: {e}")

    async def _monitor_mission_execution(self, mission_id: str) -> None:
        """
        Monitor mission execution progress in the background.

        Args:
            mission_id: ID of the mission to monitor
        """
        try:
            while mission_id in self.active_executions:
                execution_state = self.active_executions[mission_id]

                # Update progress
                await self._update_execution_progress(mission_id)

                # Check for completion conditions
                if await self._check_completion_conditions(mission_id):
                    await self.complete_mission_execution(mission_id, success=True)
                    break

                # Check for timeout
                if await self._check_timeout_conditions(mission_id):
                    await self.complete_mission_execution(mission_id, success=False)
                    break

                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds

        except asyncio.CancelledError:
            logger.info(f"Mission monitoring cancelled for {mission_id}")
        except Exception as e:
            logger.error(f"Error in mission monitoring for {mission_id}: {e}")

    async def _update_execution_progress(self, mission_id: str) -> None:
        """Update mission execution progress."""
        try:
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if not mission:
                    return

                # Calculate progress based on drone completion and discoveries
                mission_drones = db.query(MissionDrone).filter(MissionDrone.mission_id == mission.id).all()

                total_drones = len(mission_drones)
                completed_drones = len([md for md in mission_drones if md.status == "completed"])

                # Calculate progress percentage
                drone_progress = (completed_drones / max(1, total_drones)) * 100
                discovery_progress = min(20, len(mission.discoveries) * 2)  # Up to 20% for discoveries

                progress = min(100, drone_progress + discovery_progress)

                # Update execution state
                if mission_id in self.active_executions:
                    execution_state = self.active_executions[mission_id]
                    execution_state.progress_percentage = progress
                    execution_state.active_drones = total_drones - completed_drones
                    execution_state.completed_drones = completed_drones
                    execution_state.discoveries_found = len(mission.discoveries)
                    execution_state.last_update = datetime.utcnow()

                    # Update database
                    mission.progress_percentage = progress
                    db.commit()

        except Exception as e:
            logger.error(f"Error updating execution progress: {e}")

    async def _check_completion_conditions(self, mission_id: str) -> bool:
        """Check if mission completion conditions are met."""
        try:
            with SessionLocal() as db:
                mission_drones = db.query(MissionDrone).filter(
                    MissionDrone.mission_id == db.query(Mission.id).filter(Mission.mission_id == mission_id).first().id
                ).all()

                # Mission is complete if all drones have finished their tasks
                return all(md.status == "completed" for md in mission_drones)

        except Exception as e:
            logger.error(f"Error checking completion conditions: {e}")
            return False

    async def _check_timeout_conditions(self, mission_id: str) -> bool:
        """Check if mission has timed out."""
        try:
            with SessionLocal() as db:
                mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
                if not mission or not mission.actual_start_time:
                    return False

                elapsed_time = datetime.utcnow() - mission.actual_start_time
                max_duration = timedelta(minutes=settings.MAX_MISSION_DURATION)

                return elapsed_time > max_duration

        except Exception as e:
            logger.error(f"Error checking timeout conditions: {e}")
            return False

    def _calculate_area_covered(self, mission: Mission) -> float:
        """Calculate total area covered by the mission."""
        # This is a simplified calculation
        # In a real implementation, you'd track actual coverage from drone telemetry
        return mission.search_area.get("area", 0.0) * (mission.progress_percentage / 100)

    def _log_execution_event(self, mission_id: str, event_type: str, data: Dict) -> None:
        """Log mission execution events."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "mission_id": mission_id,
            "event_type": event_type,
            "data": data
        }

        self.execution_history.append(event)

        # Keep only last 1000 events
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def get_execution_status(self, mission_id: str) -> Optional[Dict]:
        """
        Get current execution status for a mission.

        Args:
            mission_id: ID of the mission

        Returns:
            Execution status dictionary or None if not found
        """
        if mission_id not in self.active_executions:
            return None

        execution_state = self.active_executions[mission_id]

        return {
            "mission_id": mission_id,
            "status": execution_state.status.value,
            "progress_percentage": execution_state.progress_percentage,
            "active_drones": execution_state.active_drones,
            "completed_drones": execution_state.completed_drones,
            "discoveries_found": execution_state.discoveries_found,
            "estimated_completion": execution_state.estimated_completion.isoformat() if execution_state.estimated_completion else None,
            "current_phase": execution_state.current_phase,
            "last_update": execution_state.last_update.isoformat()
        }

    def get_all_active_executions(self) -> List[Dict]:
        """Get status of all active mission executions."""
        return [
            self.get_execution_status(mission_id)
            for mission_id in self.active_executions.keys()
        ]


# Global mission execution service instance
mission_execution_service = MissionExecutionService()