"""
Task management API endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.services.task_manager import task_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_system_task_status():
    """Get overall system task status."""
    try:
        status = await task_manager.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error fetching task status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pending")
async def get_pending_tasks():
    """Get all pending tasks."""
    try:
        tasks = task_manager.get_pending_tasks()
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error fetching pending tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task."""
    try:
        task = task_manager.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_task(task_data: Dict[str, Any]):
    """Create a new task."""
    try:
        task_type = task_data["task_type"]
        parameters = task_data.get("parameters", {})
        priority = task_data.get("priority", "medium")
        dependencies = task_data.get("dependencies", [])
        deadline = task_data.get("deadline")

        task_id = await task_manager.create_task(
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            dependencies=dependencies,
            deadline=deadline
        )

        return {
            "message": "Task created successfully",
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{task_id}/assign")
async def assign_task(task_id: str, assignee: str):
    """Assign a task to a resource."""
    try:
        success = await task_manager.assign_task(task_id, assignee)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to assign task")

        return {"message": "Task assigned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """Start executing a task."""
    try:
        success = await task_manager.start_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to start task")

        return {"message": "Task started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, result: Dict[str, Any] = None):
    """Mark a task as completed."""
    try:
        success = await task_manager.complete_task(task_id, result)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete task")

        return {"message": "Task completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{task_id}/fail")
async def fail_task(task_id: str, error: str):
    """Mark a task as failed."""
    try:
        success = await task_manager.fail_task(task_id, error)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to mark task as failed")

        return {"message": "Task marked as failed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error failing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")