"""
Mission API endpoints for the SAR drone system
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..models.mission import (
    Mission, MissionCreate, MissionUpdate, MissionResponse, 
    MissionListResponse, MissionStatus, MissionType, MissionPriority
)
from ..services.mission_planner import MissionPlannerService
from ..services.drone_manager import DroneManager
from ..services.notification_service import NotificationService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/missions", tags=["missions"])

# Service instances
mission_planner = MissionPlannerService()
drone_manager = DroneManager()
notification_service = NotificationService()

@router.post("/", response_model=MissionResponse, status_code=201)
async def create_mission(
    mission_data: MissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new mission with automatic planning"""
    try:
        # Generate unique mission ID
        mission_id = f"mission_{uuid.uuid4().hex[:8]}"
        
        # Get available drones
        available_drones = await drone_manager.get_available_drones()
        
        # Create mission plan using the planner service
        mission_plan = await mission_planner.create_mission_plan(
            mission_type=mission_data.mission_type,
            priority=mission_data.priority,
            search_area=mission_data.search_area,
            available_drones=available_drones,
            environmental_conditions={},  # TODO: Get from weather service
            mission_requirements=mission_data.requirements,
            created_by=mission_data.created_by
        )
        
        # Create database record
        db_mission = Mission(
            mission_id=mission_id,
            name=mission_data.name,
            description=mission_data.description,
            mission_type=mission_data.mission_type.value,
            priority=mission_data.priority.value,
            status=MissionStatus.PLANNED.value,
            search_area=mission_data.search_area.dict(),
            requirements=mission_data.requirements.dict() if mission_data.requirements else {},
            drone_assignments=[assignment.dict() for assignment in mission_plan.drone_assignments],
            timeline=mission_plan.timeline.dict(),
            created_by=mission_data.created_by,
            success_probability=mission_plan.success_probability,
            risk_assessment=mission_plan.risk_assessment
        )
        
        db.add(db_mission)
        db.commit()
        db.refresh(db_mission)
        
        # Send notification in background
        background_tasks.add_task(
            _send_mission_notification,
            "mission_created",
            db_mission,
            f"Mission '{mission_data.name}' created successfully"
        )
        
        logger.info(f"Mission created: {mission_id} by {mission_data.created_by}")
        return _convert_to_response(db_mission)
        
    except Exception as e:
        logger.error(f"Error creating mission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")

@router.get("/", response_model=MissionListResponse)
async def list_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[MissionStatus] = None,
    mission_type: Optional[MissionType] = None,
    priority: Optional[MissionPriority] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List missions with filtering and pagination"""
    try:
        query = db.query(Mission)
        
        # Apply filters
        if status:
            query = query.filter(Mission.status == status.value)
        if mission_type:
            query = query.filter(Mission.mission_type == mission_type.value)
        if priority:
            query = query.filter(Mission.priority == priority.value)
        if created_by:
            query = query.filter(Mission.created_by == created_by)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        missions = query.order_by(Mission.created_at.desc()).offset(skip).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return MissionListResponse(
            missions=[_convert_to_response(mission) for mission in missions],
            total=total,
            page=page,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing missions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list missions: {str(e)}")

@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get a specific mission by ID"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return _convert_to_response(mission)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mission: {str(e)}")

@router.patch("/{mission_id}", response_model=MissionResponse)
async def update_mission(
    mission_id: str,
    update_data: MissionUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update a mission"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Check if mission can be updated
        if mission.status in [MissionStatus.COMPLETED.value, MissionStatus.ABORTED.value]:
            raise HTTPException(status_code=400, detail="Cannot update completed or aborted mission")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(mission, field):
                if isinstance(value, Enum):
                    setattr(mission, field, value.value)
                else:
                    setattr(mission, field, value)
        
        mission.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(mission)
        
        # Send notification in background
        background_tasks.add_task(
            _send_mission_notification,
            "mission_updated",
            mission,
            f"Mission '{mission.name}' updated"
        )
        
        logger.info(f"Mission updated: {mission_id}")
        return _convert_to_response(mission)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update mission: {str(e)}")

@router.post("/{mission_id}/start")
async def start_mission(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a planned mission"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.PLANNED.value:
            raise HTTPException(status_code=400, detail=f"Cannot start mission in {mission.status} status")
        
        # Validate drones are available
        drone_assignments = mission.drone_assignments or []
        for assignment in drone_assignments:
            drone_id = assignment.get("drone_id")
            if drone_id:
                drone_status = await drone_manager.get_drone_status(drone_id)
                if drone_status != "idle":
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Drone {drone_id} is not available (status: {drone_status})"
                    )
        
        # Update mission status
        mission.status = MissionStatus.ACTIVE.value
        mission.started_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        db.commit()
        
        # Start mission execution in background
        background_tasks.add_task(_execute_mission, mission_id, drone_assignments)
        
        # Send notification
        background_tasks.add_task(
            _send_mission_notification,
            "mission_started",
            mission,
            f"Mission '{mission.name}' started"
        )
        
        logger.info(f"Mission started: {mission_id}")
        return {"message": "Mission started successfully", "mission_id": mission_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start mission: {str(e)}")

@router.post("/{mission_id}/pause")
async def pause_mission(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Pause an active mission"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail=f"Cannot pause mission in {mission.status} status")
        
        # Update mission status
        mission.status = MissionStatus.PAUSED.value
        mission.updated_at = datetime.utcnow()
        db.commit()
        
        # Pause all assigned drones
        drone_assignments = mission.drone_assignments or []
        background_tasks.add_task(_pause_mission_drones, drone_assignments)
        
        # Send notification
        background_tasks.add_task(
            _send_mission_notification,
            "mission_paused",
            mission,
            f"Mission '{mission.name}' paused"
        )
        
        logger.info(f"Mission paused: {mission_id}")
        return {"message": "Mission paused successfully", "mission_id": mission_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause mission: {str(e)}")

@router.post("/{mission_id}/resume")
async def resume_mission(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resume a paused mission"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.PAUSED.value:
            raise HTTPException(status_code=400, detail=f"Cannot resume mission in {mission.status} status")
        
        # Update mission status
        mission.status = MissionStatus.ACTIVE.value
        mission.updated_at = datetime.utcnow()
        db.commit()
        
        # Resume all assigned drones
        drone_assignments = mission.drone_assignments or []
        background_tasks.add_task(_resume_mission_drones, drone_assignments)
        
        # Send notification
        background_tasks.add_task(
            _send_mission_notification,
            "mission_resumed",
            mission,
            f"Mission '{mission.name}' resumed"
        )
        
        logger.info(f"Mission resumed: {mission_id}")
        return {"message": "Mission resumed successfully", "mission_id": mission_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume mission: {str(e)}")

@router.post("/{mission_id}/abort")
async def abort_mission(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    reason: Optional[str] = None
):
    """Abort a mission"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status in [MissionStatus.COMPLETED.value, MissionStatus.ABORTED.value]:
            raise HTTPException(status_code=400, detail=f"Mission is already {mission.status}")
        
        # Update mission status
        mission.status = MissionStatus.ABORTED.value
        mission.completed_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        
        # Add abort reason to results
        actual_results = mission.actual_results or {}
        actual_results["abort_reason"] = reason or "Manual abort"
        actual_results["aborted_at"] = datetime.utcnow().isoformat()
        mission.actual_results = actual_results
        
        db.commit()
        
        # Abort all assigned drones
        drone_assignments = mission.drone_assignments or []
        background_tasks.add_task(_abort_mission_drones, drone_assignments)
        
        # Send notification
        background_tasks.add_task(
            _send_mission_notification,
            "mission_aborted",
            mission,
            f"Mission '{mission.name}' aborted: {reason or 'Manual abort'}"
        )
        
        logger.info(f"Mission aborted: {mission_id}, reason: {reason}")
        return {"message": "Mission aborted successfully", "mission_id": mission_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to abort mission: {str(e)}")

@router.delete("/{mission_id}")
async def delete_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Delete a mission (only if not active)"""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status == MissionStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Cannot delete active mission")
        
        db.delete(mission)
        db.commit()
        
        logger.info(f"Mission deleted: {mission_id}")
        return {"message": "Mission deleted successfully", "mission_id": mission_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete mission: {str(e)}")

# Helper functions
def _convert_to_response(mission: Mission) -> MissionResponse:
    """Convert database mission to response model"""
    from ..models.mission import SearchArea, MissionRequirements, DroneAssignment, MissionTimeline
    
    # Convert JSON fields back to Pydantic models
    search_area = SearchArea(**mission.search_area) if mission.search_area else None
    requirements = MissionRequirements(**mission.requirements) if mission.requirements else None
    drone_assignments = [DroneAssignment(**assignment) for assignment in (mission.drone_assignments or [])]
    timeline = MissionTimeline(**mission.timeline) if mission.timeline else None
    
    return MissionResponse(
        id=mission.id,
        mission_id=mission.mission_id,
        name=mission.name,
        description=mission.description,
        mission_type=MissionType(mission.mission_type),
        priority=MissionPriority(mission.priority),
        status=MissionStatus(mission.status),
        search_area=search_area,
        requirements=requirements,
        drone_assignments=drone_assignments,
        timeline=timeline,
        created_by=mission.created_by,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        started_at=mission.started_at,
        completed_at=mission.completed_at,
        success_probability=mission.success_probability,
        risk_assessment=mission.risk_assessment,
        actual_results=mission.actual_results
    )

async def _send_mission_notification(event_type: str, mission: Mission, message: str):
    """Send mission notification"""
    try:
        await notification_service.create_notification(
            title=f"Mission {event_type.replace('_', ' ').title()}",
            message=message,
            notification_type="mission_update",
            priority="normal",
            metadata={
                "mission_id": mission.mission_id,
                "event_type": event_type,
                "mission_status": mission.status
            }
        )
    except Exception as e:
        logger.error(f"Failed to send mission notification: {str(e)}")

async def _execute_mission(mission_id: str, drone_assignments: List[dict]):
    """Execute mission by sending commands to drones"""
    try:
        for assignment in drone_assignments:
            drone_id = assignment.get("drone_id")
            if drone_id:
                # Send mission commands to drone
                await drone_manager.send_command(
                    drone_id,
                    "start_mission",
                    {
                        "mission_id": mission_id,
                        "flight_path": assignment.get("flight_path", []),
                        "search_zone": assignment.get("search_zone", {}),
                        "estimated_duration": assignment.get("estimated_duration", 0)
                    }
                )
        logger.info(f"Mission execution started for {mission_id}")
    except Exception as e:
        logger.error(f"Failed to execute mission {mission_id}: {str(e)}")

async def _pause_mission_drones(drone_assignments: List[dict]):
    """Pause all drones assigned to mission"""
    try:
        for assignment in drone_assignments:
            drone_id = assignment.get("drone_id")
            if drone_id:
                await drone_manager.send_command(drone_id, "pause", {})
    except Exception as e:
        logger.error(f"Failed to pause mission drones: {str(e)}")

async def _resume_mission_drones(drone_assignments: List[dict]):
    """Resume all drones assigned to mission"""
    try:
        for assignment in drone_assignments:
            drone_id = assignment.get("drone_id")
            if drone_id:
                await drone_manager.send_command(drone_id, "resume", {})
    except Exception as e:
        logger.error(f"Failed to resume mission drones: {str(e)}")

async def _abort_mission_drones(drone_assignments: List[dict]):
    """Abort all drones assigned to mission"""
    try:
        for assignment in drone_assignments:
            drone_id = assignment.get("drone_id")
            if drone_id:
                await drone_manager.send_command(drone_id, "return_to_base", {})
    except Exception as e:
        logger.error(f"Failed to abort mission drones: {str(e)}")