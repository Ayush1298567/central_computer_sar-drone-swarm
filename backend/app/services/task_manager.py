"""
Background Task Management System for SAR Operations.

Manages background task queues, mission distribution, periodic health checks,
maintenance tasks, and data cleanup operations with proper scheduling and error handling.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import heapq
import threading
import time

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskType(Enum):
    """Types of background tasks."""
    HEALTH_CHECK = "health_check"
    DATA_CLEANUP = "data_cleanup"
    MISSION_DISTRIBUTION = "mission_distribution"
    MAINTENANCE = "maintenance"
    ANALYTICS_UPDATE = "analytics_update"
    BACKUP = "backup"
    SYSTEM_OPTIMIZATION = "system_optimization"
    NOTIFICATION_CLEANUP = "notification_cleanup"
    LOG_ROTATION = "log_rotation"
    CACHE_CLEANUP = "cache_cleanup"

@dataclass
class BackgroundTask:
    """Represents a background task."""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    name: str
    description: str
    scheduled_time: datetime
    max_execution_time: timedelta = timedelta(minutes=30)
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    task_function: Optional[Callable] = None
    task_args: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error_message: str = ""
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority.value > other.priority.value

    def is_ready(self) -> bool:
        """Check if task is ready to execute."""
        return (
            self.status == TaskStatus.PENDING and
            datetime.utcnow() >= self.scheduled_time and
            all(dep_status == TaskStatus.COMPLETED for dep in self.dependencies)
        )

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return False

        return datetime.utcnow() > (self.scheduled_time + timedelta(minutes=60))

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "name": self.name,
            "description": self.description,
            "scheduled_time": self.scheduled_time.isoformat(),
            "max_execution_time": self.max_execution_time.total_seconds(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "result": self.result,
            "error_message": self.error_message,
            "progress": self.progress,
            "metadata": self.metadata
        }

class TaskScheduler:
    """Manages task scheduling and priority queue."""

    def __init__(self):
        self.task_queue: List[BackgroundTask] = []
        self.running_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.task_lock = threading.Lock()

    def add_task(self, task: BackgroundTask):
        """Add a task to the scheduler."""
        with self.task_lock:
            heapq.heappush(self.task_queue, task)
            logger.info(f"Added task to queue: {task.name} (ID: {task.task_id})")

    def get_next_task(self) -> Optional[BackgroundTask]:
        """Get the next task ready for execution."""
        with self.task_lock:
            current_time = datetime.utcnow()

            # Find the highest priority ready task
            ready_tasks = []
            remaining_queue = []

            while self.task_queue:
                task = heapq.heappop(self.task_queue)
                if task.is_ready():
                    ready_tasks.append(task)
                else:
                    remaining_queue.append(task)

            # Restore remaining tasks to queue
            for task in remaining_queue:
                heapq.heappush(self.task_queue, task)

            # Return highest priority ready task
            if ready_tasks:
                return max(ready_tasks, key=lambda t: t.priority.value)

            return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        with self.task_lock:
            for i, task in enumerate(self.task_queue):
                if task.task_id == task_id and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Cancelled task: {task.name} (ID: {task_id})")
                    return True

            return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        with self.task_lock:
            # Check running tasks
            if task_id in self.running_tasks:
                return self.running_tasks[task_id].to_dict()

            # Check pending tasks
            for task in self.task_queue:
                if task.task_id == task_id:
                    return task.to_dict()

            # Check completed tasks
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id].to_dict()

            return None

    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        with self.task_lock:
            pending_count = len([t for t in self.task_queue if t.status == TaskStatus.PENDING])
            running_count = len(self.running_tasks)
            completed_count = len(self.completed_tasks)

            return {
                "total_tasks": len(self.task_queue) + len(self.running_tasks) + len(self.completed_tasks),
                "pending_tasks": pending_count,
                "running_tasks": running_count,
                "completed_tasks": completed_count,
                "overdue_tasks": len([t for t in self.task_queue if t.is_overdue()])
            }

class TaskExecutor:
    """Executes background tasks with timeout and error handling."""

    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}

    async def execute_task(self, task: BackgroundTask) -> bool:
        """Execute a single task."""
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Maximum concurrent tasks ({self.max_concurrent_tasks}) reached")
            return False

        # Create execution task
        exec_task = asyncio.create_task(self._run_task_with_timeout(task))
        self.running_tasks[task.task_id] = exec_task

        try:
            success = await exec_task
            return success
        except Exception as e:
            logger.error(f"Task execution failed for {task.task_id}: {e}")
            return False
        finally:
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

    async def _run_task_with_timeout(self, task: BackgroundTask) -> bool:
        """Run a task with timeout protection."""
        try:
            # Mark task as running
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()

            # Execute task with timeout
            try:
                if task.task_function:
                    result = await asyncio.wait_for(
                        task.task_function(**task.task_args),
                        timeout=task.max_execution_time.total_seconds()
                    )
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                else:
                    # Default task execution
                    result = await self._execute_default_task(task)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0

                task.completed_at = datetime.utcnow()
                return True

            except asyncio.TimeoutError:
                task.status = TaskStatus.TIMEOUT
                task.error_message = f"Task exceeded maximum execution time ({task.max_execution_time})"
                task.completed_at = datetime.utcnow()
                return False

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            logger.error(f"Task {task.task_id} failed: {e}")
            return False

    async def _execute_default_task(self, task: BackgroundTask) -> Any:
        """Execute default task types."""
        if task.task_type == TaskType.HEALTH_CHECK:
            return await self._execute_health_check(task)
        elif task.task_type == TaskType.DATA_CLEANUP:
            return await self._execute_data_cleanup(task)
        elif task.task_type == TaskType.MAINTENANCE:
            return await self._execute_maintenance(task)
        elif task.task_type == TaskType.ANALYTICS_UPDATE:
            return await self._execute_analytics_update(task)
        elif task.task_type == TaskType.BACKUP:
            return await self._execute_backup(task)
        else:
            return {"status": "completed", "message": f"Default execution for {task.task_type.value}"}

    async def _execute_health_check(self, task: BackgroundTask) -> Dict[str, Any]:
        """Execute health check tasks."""
        logger.info("Executing health check task")
        # Simulate health check execution
        await asyncio.sleep(2)  # Simulate work

        return {
            "status": "healthy",
            "components_checked": ["database", "api", "ai_system"],
            "issues_found": [],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_data_cleanup(self, task: BackgroundTask) -> Dict[str, Any]:
        """Execute data cleanup tasks."""
        logger.info("Executing data cleanup task")

        # Simulate cleanup operations
        await asyncio.sleep(5)  # Simulate work

        return {
            "status": "completed",
            "files_cleaned": 150,
            "space_freed_mb": 25.5,
            "old_records_removed": 500,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_maintenance(self, task: BackgroundTask) -> Dict[str, Any]:
        """Execute maintenance tasks."""
        logger.info("Executing maintenance task")

        # Simulate maintenance operations
        await asyncio.sleep(10)  # Simulate work

        return {
            "status": "completed",
            "maintenance_type": task.task_args.get("maintenance_type", "general"),
            "components_serviced": ["database", "file_system", "cache"],
            "issues_resolved": 3,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_analytics_update(self, task: BackgroundTask) -> Dict[str, Any]:
        """Execute analytics update tasks."""
        logger.info("Executing analytics update task")

        # Simulate analytics processing
        await asyncio.sleep(3)  # Simulate work

        return {
            "status": "completed",
            "metrics_updated": ["mission_analytics", "drone_performance", "system_health"],
            "data_points_processed": 1250,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _execute_backup(self, task: BackgroundTask) -> Dict[str, Any]:
        """Execute backup tasks."""
        logger.info("Executing backup task")

        # Simulate backup operations
        await asyncio.sleep(15)  # Simulate work

        return {
            "status": "completed",
            "backup_type": task.task_args.get("backup_type", "full"),
            "files_backed_up": 5000,
            "backup_size_mb": 150.5,
            "backup_location": "/backups/mission_data_backup.zip",
            "timestamp": datetime.utcnow().isoformat()
        }

class BackgroundTaskManager:
    """
    Comprehensive background task management system.

    Manages task queues, scheduling, execution, and monitoring for all
    background operations in the SAR system.
    """

    def __init__(self):
        self.scheduler = TaskScheduler()
        self.executor = TaskExecutor()
        self.task_templates: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self.executor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()

        # Initialize default task templates
        self._initialize_task_templates()

    def _initialize_task_templates(self):
        """Initialize default task templates."""
        self.task_templates = {
            "health_check_hourly": {
                "task_type": TaskType.HEALTH_CHECK,
                "priority": TaskPriority.NORMAL,
                "name": "Hourly Health Check",
                "description": "System health check performed every hour",
                "schedule_interval": timedelta(hours=1),
                "max_execution_time": timedelta(minutes=5)
            },
            "data_cleanup_daily": {
                "task_type": TaskType.DATA_CLEANUP,
                "priority": TaskPriority.LOW,
                "name": "Daily Data Cleanup",
                "description": "Clean up old data and temporary files",
                "schedule_interval": timedelta(days=1),
                "max_execution_time": timedelta(minutes=30)
            },
            "maintenance_weekly": {
                "task_type": TaskType.MAINTENANCE,
                "priority": TaskPriority.HIGH,
                "name": "Weekly Maintenance",
                "description": "Perform system maintenance tasks",
                "schedule_interval": timedelta(weeks=1),
                "max_execution_time": timedelta(hours=2)
            },
            "analytics_update_hourly": {
                "task_type": TaskType.ANALYTICS_UPDATE,
                "priority": TaskPriority.NORMAL,
                "name": "Hourly Analytics Update",
                "description": "Update analytics and performance metrics",
                "schedule_interval": timedelta(hours=1),
                "max_execution_time": timedelta(minutes=10)
            },
            "backup_daily": {
                "task_type": TaskType.BACKUP,
                "priority": TaskPriority.HIGH,
                "name": "Daily Backup",
                "description": "Create system backup",
                "schedule_interval": timedelta(days=1),
                "max_execution_time": timedelta(hours=1)
            }
        }

    def start(self):
        """Start the background task manager."""
        if self.is_running:
            logger.warning("Task manager already running")
            return

        self.is_running = True
        self.shutdown_event.clear()

        # Start task executor thread
        self.executor_thread = threading.Thread(target=self._executor_loop, daemon=True)
        self.executor_thread.start()

        logger.info("Background task manager started")

    def stop(self):
        """Stop the background task manager."""
        if not self.is_running:
            return

        self.is_running = False
        self.shutdown_event.set()

        # Wait for executor thread to finish
        if self.executor_thread and self.executor_thread.is_alive():
            self.executor_thread.join(timeout=30)

        logger.info("Background task manager stopped")

    def _executor_loop(self):
        """Main executor loop running in separate thread."""
        while not self.shutdown_event.is_set():
            try:
                # Get next task to execute
                task = self.scheduler.get_next_task()

                if task:
                    # Execute task asynchronously
                    asyncio.run(self.executor.execute_task(task))

                    # Move completed task to completed tasks
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                        self.scheduler.completed_tasks[task.task_id] = task
                else:
                    # No tasks ready, wait a bit
                    self.shutdown_event.wait(5)

            except Exception as e:
                logger.error(f"Error in executor loop: {e}")
                self.shutdown_event.wait(10)  # Wait longer on error

    def schedule_task(
        self,
        task_type: TaskType,
        name: str,
        description: str,
        scheduled_time: Optional[datetime] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_function: Optional[Callable] = None,
        task_args: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        max_execution_time: timedelta = timedelta(minutes=30)
    ) -> str:
        """
        Schedule a new background task.

        Args:
            task_type: Type of task
            name: Task name
            description: Task description
            scheduled_time: When to execute (default: now)
            priority: Task priority
            task_function: Custom function to execute
            task_args: Arguments for task function
            dependencies: Task IDs this task depends on
            max_execution_time: Maximum execution time

        Returns:
            Task ID
        """
        if scheduled_time is None:
            scheduled_time = datetime.utcnow()

        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            name=name,
            description=description,
            scheduled_time=scheduled_time,
            max_execution_time=max_execution_time,
            task_function=task_function,
            task_args=task_args or {},
            dependencies=dependencies or []
        )

        self.scheduler.add_task(task)
        logger.info(f"Scheduled task: {name} (ID: {task_id})")
        return task_id

    def schedule_recurring_task(
        self,
        template_name: str,
        start_time: Optional[datetime] = None,
        interval: Optional[timedelta] = None,
        **kwargs
    ) -> str:
        """
        Schedule a recurring task based on template.

        Args:
            template_name: Name of task template
            start_time: When to start recurring (default: now)
            interval: Custom interval (overrides template)
            **kwargs: Additional task parameters

        Returns:
            Task ID
        """
        if template_name not in self.task_templates:
            raise ValueError(f"Unknown task template: {template_name}")

        template = self.task_templates[template_name].copy()

        if start_time is None:
            start_time = datetime.utcnow()

        if interval is not None:
            template["schedule_interval"] = interval

        # Merge with provided kwargs
        template.update(kwargs)

        return self.schedule_task(
            task_type=template["task_type"],
            name=template["name"],
            description=template["description"],
            scheduled_time=start_time,
            priority=template["priority"],
            max_execution_time=template["max_execution_time"]
        )

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        return self.scheduler.cancel_task(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        return self.scheduler.get_task_status(task_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        return self.scheduler.get_queue_status()

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        queue_status = self.get_queue_status()

        return {
            "is_running": self.is_running,
            "queue_status": queue_status,
            "executor_status": {
                "max_concurrent_tasks": self.executor.max_concurrent_tasks,
                "running_tasks": len(self.executor.running_tasks)
            },
            "task_templates": len(self.task_templates),
            "last_activity": datetime.utcnow().isoformat()
        }

    def schedule_default_tasks(self):
        """Schedule default recurring tasks."""
        now = datetime.utcnow()

        # Schedule initial set of default tasks
        tasks_scheduled = []

        # Health check every hour
        tasks_scheduled.append(self.schedule_recurring_task(
            "health_check_hourly",
            start_time=now
        ))

        # Data cleanup daily at 2 AM
        cleanup_time = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
        tasks_scheduled.append(self.schedule_recurring_task(
            "data_cleanup_daily",
            start_time=cleanup_time
        ))

        # Analytics update every hour
        tasks_scheduled.append(self.schedule_recurring_task(
            "analytics_update_hourly",
            start_time=now + timedelta(minutes=5)
        ))

        logger.info(f"Scheduled {len(tasks_scheduled)} default recurring tasks")
        return tasks_scheduled

    def force_task_execution(self, task_type: TaskType, **kwargs) -> str:
        """Force immediate execution of a task type."""
        return self.schedule_task(
            task_type=task_type,
            name=f"Manual {task_type.value}",
            description=f"Manually triggered {task_type.value}",
            scheduled_time=datetime.utcnow(),
            priority=TaskPriority.HIGH,
            **kwargs
        )

    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        tasks_to_remove = []
        for task_id, task in self.scheduler.completed_tasks.items():
            if task.completed_at and task.completed_at < cutoff_time:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.scheduler.completed_tasks[task_id]

        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old completed tasks")

        return len(tasks_to_remove)