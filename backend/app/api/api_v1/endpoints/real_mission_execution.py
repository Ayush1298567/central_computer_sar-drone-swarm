"""
Real Mission Execution API Endpoints
Provides REST API for executing missions on real drones
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

import asyncio
from app.services.real_mission_execution import real_mission_execution_engine
from app.core.database import get_db
from app.auth.dependencies import role_required
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/execute", response_model=Dict[str, Any])
async def execute_mission(
    mission_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _u=Depends(role_required("operator"))
):
    """Execute a mission on real connected drones"""
    try:
        mission_id = mission_data.get("mission_id")
        if not mission_id:
            raise HTTPException(status_code=400, detail="mission_id is required")
        
        # Start mission execution in background
        background_tasks.add_task(
            real_mission_execution_engine.execute_mission,
            mission_id,
            mission_data
        )
        
        return {
            "success": True,
            "message": f"Mission {mission_id} execution started",
            "mission_id": mission_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing mission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/pause", response_model=Dict[str, Any])
async def pause_mission(mission_id: str, _u=Depends(role_required("operator"))):
    """Pause an active mission"""
    try:
        success = await real_mission_execution_engine.pause_mission(mission_id)
        
        if success:
            return {
                "success": True,
                "message": f"Mission {mission_id} paused",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to pause mission")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/resume", response_model=Dict[str, Any])
async def resume_mission(mission_id: str, _u=Depends(role_required("operator"))):
    """Resume a paused mission"""
    try:
        success = await real_mission_execution_engine.resume_mission(mission_id)
        
        if success:
            return {
                "success": True,
                "message": f"Mission {mission_id} resumed",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to resume mission")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/abort", response_model=Dict[str, Any])
async def abort_mission(mission_id: str, _u=Depends(role_required("operator"))):
    """Abort an active mission"""
    try:
        success = await real_mission_execution_engine.abort_mission(mission_id)
        
        if success:
            return {
                "success": True,
                "message": f"Mission {mission_id} aborted",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to abort mission")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{mission_id}/status", response_model=Dict[str, Any])
async def get_mission_execution_status(mission_id: str):
    """Get execution status for a specific mission"""
    try:
        status = real_mission_execution_engine.get_execution_status(mission_id)
        
        if status:
            return {
                "success": True,
                "mission_id": mission_id,
                "execution_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Mission execution not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mission execution status {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=Dict[str, Any])
async def get_all_mission_execution_status():
    """Get execution status for all missions"""
    try:
        all_status = real_mission_execution_engine.get_all_execution_status()
        
        return {
            "success": True,
            "execution_status": all_status,
            "total_missions": len(all_status),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all mission execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/emergency-stop", response_model=Dict[str, Any])
async def emergency_stop_mission(mission_id: str, _u=Depends(role_required("operator"))):
    """Emergency stop a mission - immediately abort and return all drones"""
    try:
        # First abort the mission
        abort_success = await real_mission_execution_engine.abort_mission(mission_id)
        
        if abort_success:
            # Get execution status to find active drones
            execution_status = real_mission_execution_engine.get_execution_status(mission_id)
            
            if execution_status and execution_status.get("active_drones"):
                # Send emergency stop to all active drones
                from app.communication.drone_connection_hub import drone_connection_hub
                
                emergency_tasks = []
                for drone_id in execution_status["active_drones"]:
                    task = drone_connection_hub.send_command(
                        drone_id, "emergency_stop", {}, priority=3
                    )
                    emergency_tasks.append(task)
                
                # Wait for emergency stops to complete
                await asyncio.gather(*emergency_tasks, return_exceptions=True)
            
            return {
                "success": True,
                "message": f"Emergency stop executed for mission {mission_id}",
                "mission_id": mission_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to emergency stop mission")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error emergency stopping mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for mission execution engine"""
    try:
        # Check if engine is running
        engine_running = real_mission_execution_engine._running
        
        # Get active executions count
        active_executions = len(real_mission_execution_engine.active_executions)
        
        return {
            "success": True,
            "status": "healthy" if engine_running else "unhealthy",
            "engine_running": engine_running,
            "active_executions": active_executions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in mission execution health check: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
