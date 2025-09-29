"""
Task manager for progress tracking and resource allocation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import SessionLocal
from app.models import Mission, Drone, Discovery, MissionDrone
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data structure."""
    task_id: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    assigned_to: Optional[str]  # drone_id or service name
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None


class TaskManager:
    """
    Task manager for coordinating mission tasks and resource allocation.
    """

    def __init__(self):
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.resource_allocation: Dict[str, Any] = {}
        self.task_history: List[Dict] = []

        # Task type configurations
        self.task_configurations = {
            "search_area": {
                "estimated_duration": 30,  # minutes
                "resource_requirements": {"drone": 1, "battery": 50}
            },
            "investigate_discovery": {
                "estimated_duration": 15,
                "resource_requirements": {"drone": 1, "battery": 30}
            },
            "return_to_base": {
                "estimated_duration": 10,
                "resource_requirements": {"drone": 1, "battery": 20}
            },
            "weather_check": {
                "estimated_duration": 2,
                "resource_requirements": {"service": "weather"}
            },
            "data_analysis": {
                "estimated_duration": 5,
                "resource_requirements": {"service": "analytics"}
            }
        }

    async def create_task(self, task_type: str, parameters: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         dependencies: List[str] = None,
                         deadline: Optional[datetime] = None) -> str:
        """
        Create a new task.

        Args:
            task_type: Type of task to create
            parameters: Task parameters
            priority: Task priority
            dependencies: List of task IDs this task depends on
            deadline: Task deadline

        Returns:
            Task ID of the created task
        """
        task_id = f"task_{datetime.utcnow().timestamp()}_{len(self.active_tasks)}"

        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            assigned_to=None,
            parameters=parameters,
            dependencies=dependencies or [],
            deadline=deadline
        )

        self.active_tasks[task_id] = task
        self.task_queue.append(task)

        # Sort queue by priority and deadline
        self.task_queue.sort(key=lambda t: (
            4 - list(TaskPriority).index(t.priority),  # Higher priority first
            t.deadline.timestamp() if t.deadline else float('inf')
        ))

        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id

    async def assign_task(self, task_id: str, assignee: str) -> bool:
        """
        Assign a task to a resource (drone or service).

        Args:
            task_id: ID of the task to assign
            assignee: Resource to assign the task to

        Returns:
            True if assigned successfully, False otherwise
        """
        if task_id not in self.active_tasks:
            logger.error(f"Task {task_id} not found")
            return False

        task = self.active_tasks[task_id]

        # Check if all dependencies are completed
        if not self._check_dependencies_completed(task):
            logger.info(f"Task {task_id} dependencies not completed yet")
            return False

        # Check resource availability
        if not await self._check_resource_availability(task, assignee):
            logger.info(f"Resource {assignee} not available for task {task_id}")
            return False

        # Assign task
        task.assigned_to = assignee
        task.status = TaskStatus.ASSIGNED

        # Allocate resources
        await self._allocate_resources(task, assignee)

        logger.info(f"Assigned task {task_id} to {assignee}")
        return True

    async def start_task(self, task_id: str) -> bool:
        """
        Start executing a task.

        Args:
            task_id: ID of the task to start

        Returns:
            True if started successfully, False otherwise
        """
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]
        if task.status != TaskStatus.ASSIGNED:
            return False

        task.status = TaskStatus.IN_PROGRESS

        # Log task start
        self._log_task_event(task_id, "started", {"assignee": task.assigned_to})

        logger.info(f"Started task {task_id}")
        return True

    async def complete_task(self, task_id: str, result: Dict = None) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: ID of the task to complete
            result: Task execution result

        Returns:
            True if completed successfully, False otherwise
        """
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = result or {}

        # Free up resources
        await self._free_resources(task)

        # Trigger dependent tasks
        await self._trigger_dependent_tasks(task_id)

        # Log task completion
        self._log_task_event(task_id, "completed", result)

        logger.info(f"Completed task {task_id}")
        return True

    async def fail_task(self, task_id: str, error: str) -> bool:
        """
        Mark a task as failed.

        Args:
            task_id: ID of the task that failed
            error: Error description

        Returns:
            True if marked as failed, False otherwise
        """
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]
        task.status = TaskStatus.FAILED
        task.result = {"error": error}

        # Free up resources
        await self._free_resources(task)

        # Log task failure
        self._log_task_event(task_id, "failed", {"error": error})

        logger.error(f"Task {task_id} failed: {error}")
        return True

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Get status of a specific task.

        Args:
            task_id: ID of the task

        Returns:
            Task status dictionary or None if not found
        """
        if task_id not in self.active_tasks:
            return None

        task = self.active_tasks[task_id]
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "status": task.status.value,
            "assigned_to": task.assigned_to,
            "progress": self._calculate_task_progress(task),
            "created_at": task.created_at.isoformat(),
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result
        }

    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks."""
        return [
            self.get_task_status(task_id)
            for task_id in self.active_tasks
            if self.active_tasks[task_id].status == TaskStatus.PENDING
        ]

    async def process_task_queue(self) -> None:
        """Process the task queue and assign available tasks."""
        while self.task_queue:
            task = self.task_queue[0]

            # Find available resources for this task type
            available_resources = await self._find_available_resources(task.task_type)

            if available_resources:
                # Assign to first available resource
                assignee = available_resources[0]
                if await self.assign_task(task.task_id, assignee):
                    if await self.start_task(task.task_id):
                        self.task_queue.pop(0)
                        continue

            # If no resources available, wait and try again
            await asyncio.sleep(10)

    async def _check_dependencies_completed(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id in self.active_tasks:
                dep_task = self.active_tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True

    async def _check_resource_availability(self, task: Task, resource_id: str) -> bool:
        """Check if a resource is available for the task."""
        config = self.task_configurations.get(task.task_type)
        if not config:
            return False

        requirements = config["resource_requirements"]

        if requirements.get("drone"):
            # Check drone availability
            with SessionLocal() as db:
                drone = db.query(Drone).filter(Drone.drone_id == resource_id).first()
                if not drone or drone.status != "online":
                    return False

                if drone.battery_level < requirements["battery"]:
                    return False

        # Add other resource checks here (weather service, analytics service, etc.)

        return True

    async def _allocate_resources(self, task: Task, assignee: str) -> None:
        """Allocate resources for a task."""
        if task.task_type == "search_area":
            # Mark drone as busy
            self.resource_allocation[assignee] = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "allocated_at": datetime.utcnow()
            }

    async def _free_resources(self, task: Task) -> None:
        """Free resources allocated to a task."""
        if task.assigned_to and task.assigned_to in self.resource_allocation:
            del self.resource_allocation[task.assigned_to]

    async def _trigger_dependent_tasks(self, completed_task_id: str) -> None:
        """Trigger tasks that depend on the completed task."""
        for task in self.task_queue:
            if completed_task_id in task.dependencies:
                # Remove dependency and re-queue
                task.dependencies.remove(completed_task_id)
                if not task.dependencies:  # All dependencies completed
                    # Move to front of queue
                    self.task_queue.remove(task)
                    self.task_queue.insert(0, task)

    async def _find_available_resources(self, task_type: str) -> List[str]:
        """Find available resources for a task type."""
        available = []

        config = self.task_configurations.get(task_type)
        if not config:
            return available

        requirements = config["resource_requirements"]

        if requirements.get("drone"):
            # Find available drones
            with SessionLocal() as db:
                available_drones = db.query(Drone).filter(
                    and_(
                        Drone.status == "online",
                        Drone.battery_level >= requirements.get("battery", 0),
                        ~Drone.drone_id.in_([
                            alloc["task_id"] for alloc in self.resource_allocation.values()
                            if alloc.get("task_type") in ["search_area", "investigate_discovery"]
                        ])
                    )
                ).all()

                available.extend([drone.drone_id for drone in available_drones])

        elif requirements.get("service"):
            # Service resources are always available
            service_name = requirements["service"]
            available.append(service_name)

        return available

    def _calculate_task_progress(self, task: Task) -> float:
        """Calculate task progress percentage."""
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        elif task.status == TaskStatus.FAILED:
            return 0.0
        elif task.status == TaskStatus.IN_PROGRESS:
            # Estimate progress based on elapsed time
            if task.deadline:
                elapsed = datetime.utcnow() - task.created_at
                total = task.deadline - task.created_at
                return min(90.0, (elapsed.total_seconds() / total.total_seconds()) * 100)
            return 50.0  # Default 50% if no deadline
        else:
            return 0.0

    def _log_task_event(self, task_id: str, event: str, data: Dict) -> None:
        """Log task events."""
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "event": event,
            "data": data
        }

        self.task_history.append(event_data)

        # Keep only last 1000 events
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system task status."""
        total_tasks = len(self.active_tasks)
        completed_tasks = len([t for t in self.active_tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.active_tasks.values() if t.status == TaskStatus.FAILED])
        pending_tasks = len(self.task_queue)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "pending_tasks": pending_tasks,
            "active_tasks": total_tasks - completed_tasks - failed_tasks,
            "resource_utilization": len(self.resource_allocation),
            "queue_length": len(self.task_queue)
        }


# Global task manager instance
task_manager = TaskManager()