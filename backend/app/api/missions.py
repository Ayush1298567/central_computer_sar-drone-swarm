"""
Mission management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..core.database import get_db
from ..models.mission import Mission, MissionStatus, MissionPriority
from ..services.mission_service import MissionService
from ..ai.conversation import ConversationalMissionPlanner
from ..ai.ollama_client import OllamaClient

router = APIRouter()

# Initialize services (these would normally be injected)
mission_service = MissionService()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of missions with optional filtering."""
    try:
        missions = await mission_service.get_missions(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            priority=priority
        )
        return [mission.to_dict() for mission in missions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve missions: {str(e)}")

@router.get("/{mission_id}", response_model=Dict[str, Any])
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific mission."""
    try:
        mission = await mission_service.get_mission_by_id(db, mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mission: {str(e)}")

@router.post("/", response_model=Dict[str, Any])
async def create_mission(
    mission_data: Dict[str, Any],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new SAR mission."""
    try:
        # Validate required fields
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            if field not in mission_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create mission through service
        mission = await mission_service.create_mission(db, mission_data)
        
        # Schedule background tasks for mission setup
        background_tasks.add_task(setup_mission_resources, mission.mission_id)
        
        return {
            "success": True,
            "mission": mission.to_dict(),
            "message": "Mission created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")

@router.put("/{mission_id}", response_model=Dict[str, Any])
async def update_mission(
    mission_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update mission parameters and status."""
    try:
        mission = await mission_service.update_mission(db, mission_id, update_data)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return {
            "success": True,
            "mission": mission.to_dict(),
            "message": "Mission updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mission: {str(e)}")

@router.post("/{mission_id}/start", response_model=Dict[str, Any])
async def start_mission(
    mission_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Start a mission and deploy drones."""
    try:
        # Validate mission is ready
        mission = await mission_service.get_mission_by_id(db, mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.READY:
            raise HTTPException(
                status_code=400, 
                detail=f"Mission must be in READY status to start. Current status: {mission.status.value}"
            )
        
        # Start mission
        result = await mission_service.start_mission(db, mission_id)
        
        # Schedule drone deployment
        background_tasks.add_task(deploy_mission_drones, mission_id)
        
        return {
            "success": True,
            "mission": result.to_dict(),
            "message": "Mission started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start mission: {str(e)}")

@router.post("/{mission_id}/pause", response_model=Dict[str, Any])
async def pause_mission(mission_id: str, db: Session = Depends(get_db)):
    """Pause an active mission."""
    try:
        result = await mission_service.pause_mission(db, mission_id)
        if not result:
            raise HTTPException(status_code=404, detail="Mission not found or cannot be paused")
        
        return {
            "success": True,
            "mission": result.to_dict(),
            "message": "Mission paused successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause mission: {str(e)}")

@router.post("/{mission_id}/resume", response_model=Dict[str, Any])
async def resume_mission(mission_id: str, db: Session = Depends(get_db)):
    """Resume a paused mission."""
    try:
        result = await mission_service.resume_mission(db, mission_id)
        if not result:
            raise HTTPException(status_code=404, detail="Mission not found or cannot be resumed")
        
        return {
            "success": True,
            "mission": result.to_dict(),
            "message": "Mission resumed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume mission: {str(e)}")

@router.post("/{mission_id}/abort", response_model=Dict[str, Any])
async def abort_mission(
    mission_id: str,
    abort_reason: str = Query(..., description="Reason for aborting the mission"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Abort a mission and return all drones."""
    try:
        result = await mission_service.abort_mission(db, mission_id, abort_reason)
        if not result:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Schedule emergency return of all drones
        background_tasks.add_task(emergency_return_drones, mission_id)
        
        return {
            "success": True,
            "mission": result.to_dict(),
            "message": f"Mission aborted: {abort_reason}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to abort mission: {str(e)}")

@router.get("/{mission_id}/status", response_model=Dict[str, Any])
async def get_mission_status(mission_id: str, db: Session = Depends(get_db)):
    """Get real-time mission status and progress."""
    try:
        status = await mission_service.get_mission_status(db, mission_id)
        if not status:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission status: {str(e)}")

@router.get("/{mission_id}/progress", response_model=Dict[str, Any])
async def get_mission_progress(mission_id: str, db: Session = Depends(get_db)):
    """Get detailed mission progress including area coverage and discoveries."""
    try:
        progress = await mission_service.get_mission_progress(db, mission_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission progress: {str(e)}")

@router.get("/{mission_id}/discoveries", response_model=List[Dict[str, Any]])
async def get_mission_discoveries(
    mission_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
):
    """Get discoveries made during the mission."""
    try:
        discoveries = await mission_service.get_mission_discoveries(
            db, mission_id, skip=skip, limit=limit
        )
        return discoveries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get discoveries: {str(e)}")

@router.post("/{mission_id}/discoveries", response_model=Dict[str, Any])
async def report_discovery(
    mission_id: str,
    discovery_data: Dict[str, Any],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Report a new discovery during the mission."""
    try:
        discovery = await mission_service.add_discovery(db, mission_id, discovery_data)
        
        # Schedule AI analysis of the discovery
        background_tasks.add_task(analyze_discovery, discovery.discovery_id)
        
        return {
            "success": True,
            "discovery": discovery.to_dict(),
            "message": "Discovery reported successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to report discovery: {str(e)}")

@router.get("/{mission_id}/analytics", response_model=Dict[str, Any])
async def get_mission_analytics(mission_id: str, db: Session = Depends(get_db)):
    """Get mission analytics and performance metrics."""
    try:
        analytics = await mission_service.get_mission_analytics(db, mission_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.post("/{mission_id}/ai-recommendations", response_model=Dict[str, Any])
async def get_ai_recommendations(
    mission_id: str,
    current_situation: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI recommendations for mission optimization."""
    try:
        recommendations = await mission_service.get_ai_recommendations(
            db, mission_id, current_situation
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI recommendations: {str(e)}")

@router.post("/{mission_id}/update-progress", response_model=Dict[str, Any])
async def update_mission_progress(
    mission_id: str,
    progress_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update mission progress (typically called by drones or system)."""
    try:
        result = await mission_service.update_progress(db, mission_id, progress_data)
        if not result:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return {
            "success": True,
            "message": "Progress updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

# Background task functions
async def setup_mission_resources(mission_id: str):
    """Background task to set up mission resources."""
    try:
        # This would typically:
        # 1. Validate drone availability
        # 2. Check weather conditions
        # 3. Prepare flight plans
        # 4. Set up communication channels
        pass
    except Exception as e:
        print(f"Mission setup failed for {mission_id}: {e}")

async def deploy_mission_drones(mission_id: str):
    """Background task to deploy drones for mission."""
    try:
        # This would typically:
        # 1. Send takeoff commands to assigned drones
        # 2. Monitor takeoff success
        # 3. Begin search patterns
        # 4. Start telemetry monitoring
        pass
    except Exception as e:
        print(f"Drone deployment failed for {mission_id}: {e}")

async def emergency_return_drones(mission_id: str):
    """Background task for emergency drone return."""
    try:
        # This would typically:
        # 1. Send immediate return-to-home commands
        # 2. Monitor drone status
        # 3. Ensure safe landing
        # 4. Update mission status
        pass
    except Exception as e:
        print(f"Emergency return failed for {mission_id}: {e}")

async def analyze_discovery(discovery_id: str):
    """Background task to analyze a discovery with AI."""
    try:
        # This would typically:
        # 1. Run AI analysis on discovery images/data
        # 2. Update confidence scores
        # 3. Generate recommendations
        # 4. Alert operators if high priority
        pass
    except Exception as e:
        print(f"Discovery analysis failed for {discovery_id}: {e}")