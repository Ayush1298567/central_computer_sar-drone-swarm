import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MissionStatus(Enum):
    """Mission execution status."""
    PLANNING = "planning"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"

class ExecutionPhase(Enum):
    """Current execution phase of a mission."""
    INITIALIZING = "initializing"
    LAUNCHING = "launching"
    SEARCHING = "searching"
    DISCOVERY_INVESTIGATION = "discovery_investigation"
    COMPLETING = "completing"
    RETURNING = "returning"

@dataclass
class MissionProgress:
    """Detailed progress information for a mission."""
    mission_id: str
    overall_progress: float  # 0-1
    phase: ExecutionPhase
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None

    # Area coverage
    total_area_km2: float = 0.0
    covered_area_km2: float = 0.0
    coverage_percentage: float = 0.0

    # Discoveries
    discoveries_found: int = 0
    discoveries_investigated: int = 0
    discoveries_verified: int = 0

    # Drone status
    active_drones: int = 0
    total_drones: int = 0
    drones_returned: int = 0

    # Performance metrics
    average_speed_ms: float = 0.0
    total_distance_km: float = 0.0
    battery_consumed: float = 0.0

    # Timeline events
    events: List[Dict] = field(default_factory=list)

@dataclass
class ExecutionCommand:
    """Command for mission execution control."""
    command_type: str
    target: str  # mission_id, drone_id, or 'all'
    parameters: Dict[str, Any]
    priority: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)

class MissionExecutionEngine:
    """
    Mission execution engine for SAR operations.

    Manages mission state, monitors progress, validates completion,
    and coordinates the overall execution lifecycle.
    """

    def __init__(self):
        self.active_missions: Dict[str, MissionProgress] = {}
        self.execution_history: Dict[str, List[Dict]] = {}
        self.completion_callbacks: Dict[str, List[Callable]] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}

        # Execution parameters
        self.min_coverage_threshold = 0.85  # 85% coverage required
        self.max_mission_duration = 180  # minutes
        self.progress_update_interval = 30  # seconds
        self.completion_check_interval = 60  # seconds

        # Performance tracking
        self.execution_metrics: Dict[str, Any] = {}

    def start_mission(self, mission_id: str, mission_config: Dict) -> bool:
        """
        Initialize mission execution tracking.

        Args:
            mission_id: Unique mission identifier
            mission_config: Mission configuration data

        Returns:
            True if mission started successfully
        """
        try:
            # Calculate mission parameters
            total_area = mission_config.get("total_area_km2", 0.0)
            drone_count = len(mission_config.get("assigned_drones", []))

            # Estimate completion time based on area and drone count
            estimated_duration = self._calculate_estimated_duration(total_area, drone_count)

            progress = MissionProgress(
                mission_id=mission_id,
                overall_progress=0.0,
                phase=ExecutionPhase.INITIALIZING,
                start_time=datetime.utcnow(),
                estimated_completion=datetime.utcnow() + timedelta(minutes=estimated_duration),
                total_area_km2=total_area,
                total_drones=drone_count,
                active_drones=drone_count
            )

            self.active_missions[mission_id] = progress
            self.execution_history[mission_id] = []

            # Log mission start
            self._log_execution_event(mission_id, "mission_started", {
                "config": mission_config,
                "estimated_duration": estimated_duration
            })

            logger.info(f"Mission {mission_id} execution started")
            return True

        except Exception as e:
            logger.error(f"Failed to start mission {mission_id}: {e}")
            return False

    def update_mission_progress(self, mission_id: str, updates: Dict) -> None:
        """
        Update mission progress information.

        Args:
            mission_id: Mission identifier
            updates: Progress update data
        """
        if mission_id not in self.active_missions:
            logger.warning(f"Progress update for unknown mission {mission_id}")
            return

        progress = self.active_missions[mission_id]

        # Update progress fields
        for key, value in updates.items():
            if hasattr(progress, key):
                setattr(progress, key, value)

        # Recalculate derived metrics
        self._recalculate_progress_metrics(progress)

        # Check for phase transitions
        self._check_phase_transitions(progress)

        # Log progress update
        self._log_execution_event(mission_id, "progress_updated", updates)

        # Notify progress callbacks
        self._notify_progress_callbacks(mission_id, progress)

    def _recalculate_progress_metrics(self, progress: MissionProgress) -> None:
        """Recalculate derived progress metrics."""
        # Calculate coverage percentage
        if progress.total_area_km2 > 0:
            progress.coverage_percentage = (progress.covered_area_km2 / progress.total_area_km2) * 100

        # Calculate overall progress (weighted combination)
        coverage_weight = 0.4
        discovery_weight = 0.3
        drone_weight = 0.3

        coverage_score = progress.coverage_percentage / 100
        discovery_score = progress.discoveries_verified / max(progress.discoveries_found, 1)
        drone_score = progress.drones_returned / max(progress.total_drones, 1)

        progress.overall_progress = (
            coverage_score * coverage_weight +
            discovery_score * discovery_weight +
            drone_score * drone_weight
        )

    def _check_phase_transitions(self, progress: MissionProgress) -> None:
        """Check if mission should transition to a new phase."""
        current_time = datetime.utcnow()

        if progress.phase == ExecutionPhase.INITIALIZING:
            # Check if all drones are launched
            if progress.active_drones == progress.total_drones:
                progress.phase = ExecutionPhase.LAUNCHING
                self._log_execution_event(progress.mission_id, "phase_transition", {
                    "from": "initializing",
                    "to": "launching"
                })

        elif progress.phase == ExecutionPhase.LAUNCHING:
            # Check if drones have reached search areas
            if progress.covered_area_km2 > 0:
                progress.phase = ExecutionPhase.SEARCHING
                self._log_execution_event(progress.mission_id, "phase_transition", {
                    "from": "launching",
                    "to": "searching"
                })

        elif progress.phase == ExecutionPhase.SEARCHING:
            # Check for discoveries requiring investigation
            if progress.discoveries_found > progress.discoveries_investigated:
                progress.phase = ExecutionPhase.DISCOVERY_INVESTIGATION
                self._log_execution_event(progress.mission_id, "phase_transition", {
                    "from": "searching",
                    "to": "discovery_investigation"
                })

        elif progress.phase == ExecutionPhase.DISCOVERY_INVESTIGATION:
            # Check if all discoveries are investigated
            if progress.discoveries_found == progress.discoveries_investigated:
                progress.phase = ExecutionPhase.SEARCHING
                self._log_execution_event(progress.mission_id, "phase_transition", {
                    "from": "discovery_investigation",
                    "to": "searching"
                })

    def check_mission_completion(self, mission_id: str) -> Dict:
        """
        Check if mission meets completion criteria.

        Args:
            mission_id: Mission identifier

        Returns:
            Completion assessment
        """
        if mission_id not in self.active_missions:
            return {"completed": False, "reason": "Mission not found"}

        progress = self.active_missions[mission_id]

        completion_criteria = {
            "coverage_threshold": progress.coverage_percentage >= (self.min_coverage_threshold * 100),
            "all_drones_returned": progress.drones_returned == progress.total_drones,
            "max_duration_exceeded": (datetime.utcnow() - progress.start_time).total_seconds() > (self.max_mission_duration * 60),
            "all_discoveries_investigated": progress.discoveries_found == progress.discoveries_investigated
        }

        # Mission is complete if coverage threshold is met OR max duration exceeded
        is_complete = (
            completion_criteria["coverage_threshold"] or
            completion_criteria["max_duration_exceeded"]
        )

        # Mission is successful if coverage threshold is met AND all discoveries investigated
        is_successful = (
            completion_criteria["coverage_threshold"] and
            completion_criteria["all_discoveries_investigated"]
        )

        assessment = {
            "completed": is_complete,
            "successful": is_successful,
            "criteria": completion_criteria,
            "progress": progress.overall_progress,
            "coverage_percentage": progress.coverage_percentage,
            "recommendations": self._get_completion_recommendations(progress, completion_criteria)
        }

        if is_complete:
            self._finalize_mission(mission_id, assessment)

        return assessment

    def _get_completion_recommendations(self, progress: MissionProgress, criteria: Dict) -> List[str]:
        """Get recommendations for mission completion."""
        recommendations = []

        if not criteria["coverage_threshold"]:
            remaining_coverage = (self.min_coverage_threshold * 100) - progress.coverage_percentage
            recommendations.append(f"Continue mission to achieve {remaining_coverage".1f"}% additional coverage")

        if not criteria["all_discoveries_investigated"]:
            pending_investigations = progress.discoveries_found - progress.discoveries_investigated
            recommendations.append(f"Investigate {pending_investigations} remaining discoveries")

        if not criteria["all_drones_returned"]:
            active_drones = progress.active_drones - progress.drones_returned
            recommendations.append(f"Ensure {active_drones} remaining drones return safely")

        if criteria["max_duration_exceeded"]:
            recommendations.append("Mission exceeded maximum duration - consider extending or aborting")

        return recommendations

    def _finalize_mission(self, mission_id: str, assessment: Dict) -> None:
        """Finalize mission execution."""
        if mission_id not in self.active_missions:
            return

        progress = self.active_missions[mission_id]
        progress.actual_completion = datetime.utcnow()

        # Determine final status
        if assessment["successful"]:
            final_status = MissionStatus.COMPLETED
        elif assessment["completed"]:
            final_status = MissionStatus.COMPLETED  # Still completed, just not fully successful
        else:
            final_status = MissionStatus.ABORTED

        # Update mission status
        progress.phase = ExecutionPhase.COMPLETING

        # Log mission completion
        self._log_execution_event(mission_id, "mission_completed", {
            "status": final_status.value,
            "successful": assessment["successful"],
            "final_progress": progress.overall_progress,
            "completion_time": progress.actual_completion.isoformat()
        })

        # Calculate final metrics
        final_metrics = self._calculate_final_metrics(progress)

        # Notify completion callbacks
        self._notify_completion_callbacks(mission_id, {
            "status": final_status.value,
            "assessment": assessment,
            "metrics": final_metrics
        })

        # Move to completed missions (keep for historical data)
        # In a real implementation, you might move this to a completed_missions dict

        logger.info(f"Mission {mission_id} finalized with status: {final_status.value}")

    def _calculate_final_metrics(self, progress: MissionProgress) -> Dict:
        """Calculate comprehensive final mission metrics."""
        if not progress.start_time or not progress.actual_completion:
            return {}

        actual_duration = (progress.actual_completion - progress.start_time).total_seconds() / 60  # minutes
        estimated_duration = (progress.estimated_completion - progress.start_time).total_seconds() / 60 if progress.estimated_completion else 0

        metrics = {
            "actual_duration_minutes": actual_duration,
            "estimated_duration_minutes": estimated_duration,
            "duration_variance": ((actual_duration - estimated_duration) / estimated_duration * 100) if estimated_duration > 0 else 0,
            "coverage_efficiency": (progress.covered_area_km2 / actual_duration) if actual_duration > 0 else 0,
            "discovery_rate": (progress.discoveries_found / actual_duration) if actual_duration > 0 else 0,
            "investigation_success_rate": (progress.discoveries_verified / progress.discoveries_found) if progress.discoveries_found > 0 else 0,
            "drone_utilization_rate": (progress.active_drones / progress.total_drones) if progress.total_drones > 0 else 0,
            "average_speed_ms": progress.average_speed_ms,
            "total_distance_km": progress.total_distance_km,
            "battery_efficiency": (progress.total_distance_km / progress.battery_consumed) if progress.battery_consumed > 0 else 0
        }

        return metrics

    def pause_mission(self, mission_id: str, reason: str) -> bool:
        """
        Pause mission execution.

        Args:
            mission_id: Mission identifier
            reason: Reason for pausing

        Returns:
            True if paused successfully
        """
        if mission_id not in self.active_missions:
            return False

        progress = self.active_missions[mission_id]
        if progress.phase in [ExecutionPhase.COMPLETING, ExecutionPhase.RETURNING]:
            return False  # Cannot pause in final phases

        # Update status (in real implementation, this would signal drones)
        progress.phase = ExecutionPhase.RETURNING

        self._log_execution_event(mission_id, "mission_paused", {"reason": reason})

        logger.info(f"Mission {mission_id} paused: {reason}")
        return True

    def resume_mission(self, mission_id: str) -> bool:
        """
        Resume paused mission.

        Args:
            mission_id: Mission identifier

        Returns:
            True if resumed successfully
        """
        if mission_id not in self.active_missions:
            return False

        progress = self.active_missions[mission_id]
        if progress.phase != ExecutionPhase.RETURNING:
            return False  # Can only resume from paused state

        # Resume searching
        progress.phase = ExecutionPhase.SEARCHING

        self._log_execution_event(mission_id, "mission_resumed", {})

        logger.info(f"Mission {mission_id} resumed")
        return True

    def abort_mission(self, mission_id: str, reason: str, emergency: bool = False) -> bool:
        """
        Abort mission execution.

        Args:
            mission_id: Mission identifier
            reason: Reason for aborting
            emergency: Whether this is an emergency abort

        Returns:
            True if aborted successfully
        """
        if mission_id not in self.active_missions:
            return False

        progress = self.active_missions[mission_id]
        progress.phase = ExecutionPhase.RETURNING

        # Update final status
        progress.actual_completion = datetime.utcnow()

        self._log_execution_event(mission_id, "mission_aborted", {
            "reason": reason,
            "emergency": emergency,
            "final_progress": progress.overall_progress
        })

        # Notify completion callbacks
        self._notify_completion_callbacks(mission_id, {
            "status": "aborted",
            "reason": reason,
            "emergency": emergency,
            "final_progress": progress.overall_progress
        })

        logger.warning(f"Mission {mission_id} aborted: {reason}")
        return True

    def get_mission_status(self, mission_id: str) -> Optional[Dict]:
        """
        Get detailed mission execution status.

        Args:
            mission_id: Mission identifier

        Returns:
            Mission status information or None if not found
        """
        if mission_id not in self.active_missions:
            return None

        progress = self.active_missions[mission_id]

        # Get recent events
        recent_events = [
            event for event in self.execution_history.get(mission_id, [])
            if (datetime.utcnow() - datetime.fromisoformat(event["timestamp"])).total_seconds() < 300
        ]

        status = {
            "mission_id": mission_id,
            "status": progress.phase.value,
            "overall_progress": progress.overall_progress,
            "start_time": progress.start_time.isoformat() if progress.start_time else None,
            "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None,
            "coverage_percentage": progress.coverage_percentage,
            "discoveries": {
                "found": progress.discoveries_found,
                "investigated": progress.discoveries_investigated,
                "verified": progress.discoveries_verified
            },
            "drones": {
                "active": progress.active_drones,
                "total": progress.total_drones,
                "returned": progress.drones_returned
            },
            "performance": {
                "average_speed_ms": progress.average_speed_ms,
                "total_distance_km": progress.total_distance_km,
                "battery_consumed": progress.battery_consumed
            },
            "recent_events": recent_events[-10:],  # Last 10 events
            "completion_assessment": self.check_mission_completion(mission_id)
        }

        return status

    def _calculate_estimated_duration(self, area_km2: float, drone_count: int) -> int:
        """Calculate estimated mission duration based on area and drone count."""
        # Base calculation: assume 0.5 km² per minute per drone
        base_coverage_rate = 0.5  # km²/minute per drone

        if drone_count > 0:
            total_coverage_rate = base_coverage_rate * drone_count
            estimated_minutes = area_km2 / total_coverage_rate
        else:
            estimated_minutes = area_km2 * 2  # Fallback: 2 minutes per km²

        # Add buffer time for launch, return, and transitions
        buffer_time = 15  # minutes
        estimated_minutes += buffer_time

        return min(int(estimated_minutes), self.max_mission_duration)

    def _log_execution_event(self, mission_id: str, event_type: str, data: Dict) -> None:
        """Log mission execution event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }

        if mission_id not in self.execution_history:
            self.execution_history[mission_id] = []

        self.execution_history[mission_id].append(event)

        # Keep only last 1000 events per mission
        if len(self.execution_history[mission_id]) > 1000:
            self.execution_history[mission_id] = self.execution_history[mission_id][-1000:]

    def _notify_progress_callbacks(self, mission_id: str, progress: MissionProgress) -> None:
        """Notify registered progress callbacks."""
        if mission_id in self.progress_callbacks:
            for callback in self.progress_callbacks[mission_id]:
                try:
                    callback(progress)
                except Exception as e:
                    logger.error(f"Error in progress callback for mission {mission_id}: {e}")

    def _notify_completion_callbacks(self, mission_id: str, result: Dict) -> None:
        """Notify registered completion callbacks."""
        if mission_id in self.completion_callbacks:
            for callback in self.completion_callbacks[mission_id]:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Error in completion callback for mission {mission_id}: {e}")

    def register_progress_callback(self, mission_id: str, callback: Callable) -> None:
        """Register callback for mission progress updates."""
        if mission_id not in self.progress_callbacks:
            self.progress_callbacks[mission_id] = []
        self.progress_callbacks[mission_id].append(callback)

    def register_completion_callback(self, mission_id: str, callback: Callable) -> None:
        """Register callback for mission completion."""
        if mission_id not in self.completion_callbacks:
            self.completion_callbacks[mission_id] = []
        self.completion_callbacks[mission_id].append(callback)

    def get_execution_summary(self, mission_id: Optional[str] = None) -> Dict:
        """Get execution summary for missions."""
        if mission_id:
            if mission_id in self.active_missions:
                return {
                    "mission_id": mission_id,
                    "status": self.get_mission_status(mission_id),
                    "metrics": self._calculate_final_metrics(self.active_missions[mission_id])
                }
            else:
                return {"error": "Mission not found"}
        else:
            # Return summary for all active missions
            summary = {
                "total_active_missions": len(self.active_missions),
                "missions": {}
            }

            for mid, progress in self.active_missions.items():
                summary["missions"][mid] = {
                    "status": progress.phase.value,
                    "progress": progress.overall_progress,
                    "coverage": progress.coverage_percentage,
                    "active_drones": progress.active_drones
                }

            return summary

    async def run_completion_monitor(self) -> None:
        """Background task to monitor mission completion."""
        while True:
            try:
                for mission_id in list(self.active_missions.keys()):
                    completion_status = self.check_mission_completion(mission_id)
                    if completion_status["completed"]:
                        logger.info(f"Mission {mission_id} completed: {completion_status['successful']}")

                await asyncio.sleep(self.completion_check_interval)

            except Exception as e:
                logger.error(f"Error in completion monitor: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def run_progress_monitor(self) -> None:
        """Background task to update mission progress."""
        while True:
            try:
                for mission_id, progress in self.active_missions.items():
                    # Update estimated completion based on current progress
                    if progress.start_time and progress.overall_progress > 0:
                        elapsed = (datetime.utcnow() - progress.start_time).total_seconds() / 60
                        if elapsed > 0:
                            estimated_remaining = elapsed / progress.overall_progress * (1 - progress.overall_progress)
                            progress.estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_remaining)

                await asyncio.sleep(self.progress_update_interval)

            except Exception as e:
                logger.error(f"Error in progress monitor: {e}")
                await asyncio.sleep(60)

# Global mission execution engine instance
mission_execution_engine = MissionExecutionEngine()