"""
Mission API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models import Mission, Drone, MissionDrone
from app.services.mission_execution import mission_execution_service
from app.services.coordination_engine import coordination_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_missions(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all missions with optional filtering."""
    try:
        query = db.query(Mission)

        if status_filter:
            query = query.filter(Mission.status == status_filter)

        missions = query.order_by(Mission.created_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": mission.id,
                "mission_id": mission.mission_id,
                "name": mission.name,
                "description": mission.description,
                "status": mission.status,
                "priority": mission.priority,
                "mission_type": mission.mission_type,
                "center": {
                    "lat": mission.center_lat,
                    "lng": mission.center_lng
                },
                "search_area": mission.search_area,
                "search_altitude": mission.search_altitude,
                "estimated_duration": mission.estimated_duration,
                "max_drones": mission.max_drones,
                "progress_percentage": mission.progress_percentage,
                "discoveries_count": mission.discoveries_count,
                "area_covered": mission.area_covered,
                "planned_start_time": mission.planned_start_time.isoformat() if mission.planned_start_time else None,
                "actual_start_time": mission.actual_start_time.isoformat() if mission.actual_start_time else None,
                "planned_end_time": mission.planned_end_time.isoformat() if mission.planned_end_time else None,
                "actual_end_time": mission.actual_end_time.isoformat() if mission.actual_end_time else None,
                "weather_conditions": mission.weather_conditions,
                "created_by": mission.created_by,
                "created_at": mission.created_at.isoformat(),
                "updated_at": mission.updated_at.isoformat()
            }
            for mission in missions
        ]
    except Exception as e:
        logger.error(f"Error fetching missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{mission_id}", response_model=Dict[str, Any])
async def get_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific mission by ID."""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        # Get assigned drones
        mission_drones = db.query(MissionDrone).filter(MissionDrone.mission_id == mission.id).all()
        assigned_drones = []
        for md in mission_drones:
            drone = db.query(Drone).filter(Drone.id == md.drone_id).first()
            if drone:
                assigned_drones.append({
                    "drone_id": drone.drone_id,
                    "assigned_area": md.assigned_area,
                    "status": md.status,
                    "current_waypoint": md.current_waypoint
                })

        return {
            "id": mission.id,
            "mission_id": mission.mission_id,
            "name": mission.name,
            "description": mission.description,
            "status": mission.status,
            "priority": mission.priority,
            "mission_type": mission.mission_type,
            "center": {
                "lat": mission.center_lat,
                "lng": mission.center_lng
            },
            "search_area": mission.search_area,
            "search_altitude": mission.search_altitude,
            "estimated_duration": mission.estimated_duration,
            "max_drones": mission.max_drones,
            "search_pattern": mission.search_pattern,
            "overlap_percentage": mission.overlap_percentage,
            "progress_percentage": mission.progress_percentage,
            "discoveries_count": mission.discoveries_count,
            "area_covered": mission.area_covered,
            "assigned_drones": assigned_drones,
            "planned_start_time": mission.planned_start_time.isoformat() if mission.planned_start_time else None,
            "actual_start_time": mission.actual_start_time.isoformat() if mission.actual_start_time else None,
            "planned_end_time": mission.planned_end_time.isoformat() if mission.planned_end_time else None,
            "actual_end_time": mission.actual_end_time.isoformat() if mission.actual_end_time else None,
            "weather_conditions": mission.weather_conditions,
            "created_by": mission.created_by,
            "created_at": mission.created_at.isoformat(),
            "updated_at": mission.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_mission(
    mission_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new mission."""
    try:
        # Generate unique mission ID
        mission_id = f"mission_{uuid.uuid4().hex[:8]}"

        # Create new mission
        mission = Mission(
            mission_id=mission_id,
            name=mission_data["name"],
            description=mission_data.get("description"),
            status="planning",
            priority=mission_data.get("priority", 3),
            mission_type=mission_data.get("mission_type", "search"),
            center_lat=mission_data["center"]["lat"],
            center_lng=mission_data["center"]["lng"],
            search_area=mission_data["search_area"],
            search_altitude=mission_data.get("search_altitude", 30.0),
            estimated_duration=mission_data.get("estimated_duration"),
            max_drones=mission_data.get("max_drones", 1),
            search_pattern=mission_data.get("search_pattern", "lawnmower"),
            overlap_percentage=mission_data.get("overlap_percentage", 10.0),
            planned_start_time=mission_data.get("planned_start_time"),
            planned_end_time=mission_data.get("planned_end_time"),
            weather_conditions=mission_data.get("weather_conditions"),
            created_by=mission_data.get("created_by")
        )

        db.add(mission)
        db.commit()
        db.refresh(mission)

        logger.info(f"Created new mission {mission_id}")
        return {
            "message": "Mission created successfully",
            "mission_id": mission_id,
            "id": mission.id
        }

    except Exception as e:
        logger.error(f"Error creating mission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{mission_id}/start")
async def start_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Start mission execution."""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status not in ["ready", "planning"]:
            raise HTTPException(status_code=400, detail=f"Mission cannot be started in status: {mission.status}")

        # Update mission status
        mission.status = "active"
        mission.actual_start_time = datetime.utcnow()
        db.commit()

        # Start mission execution
        success = await mission_execution_service.start_mission_execution(mission_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to start mission execution")

        logger.info(f"Started mission execution for {mission_id}")
        return {"message": "Mission started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{mission_id}/pause")
async def pause_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Pause mission execution."""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status != "active":
            raise HTTPException(status_code=400, detail=f"Only active missions can be paused")

        # Update mission status
        mission.status = "paused"
        db.commit()

        # Pause mission execution
        success = await mission_execution_service.pause_mission_execution(mission_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to pause mission execution")

        logger.info(f"Paused mission {mission_id}")
        return {"message": "Mission paused successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{mission_id}/resume")
async def resume_mission(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Resume mission execution."""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status != "paused":
            raise HTTPException(status_code=400, detail=f"Only paused missions can be resumed")

        # Update mission status
        mission.status = "active"
        db.commit()

        # Resume mission execution
        success = await mission_execution_service.resume_mission_execution(mission_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to resume mission execution")

        logger.info(f"Resumed mission {mission_id}")
        return {"message": "Mission resumed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{mission_id}/complete")
async def complete_mission(
    mission_id: str,
    success: bool = True,
    db: Session = Depends(get_db)
):
    """Complete mission execution."""
    try:
        mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status not in ["active", "paused"]:
            raise HTTPException(status_code=400, detail=f"Mission cannot be completed in status: {mission.status}")

        # Complete mission execution
        execution_success = await mission_execution_service.complete_mission_execution(mission_id, success)

        if not execution_success:
            raise HTTPException(status_code=500, detail="Failed to complete mission execution")

        # Update mission status
        mission.status = "completed" if success else "failed"
        mission.actual_end_time = datetime.utcnow()
        mission.progress_percentage = 100.0
        db.commit()

        logger.info(f"Completed mission {mission_id} (success: {success})")
        return {"message": "Mission completed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{mission_id}/status")
async def get_mission_status(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """Get real-time mission execution status."""
    try:
        # Get execution status from service
        execution_status = mission_execution_service.get_execution_status(mission_id)

        if not execution_status:
            raise HTTPException(status_code=404, detail="Mission execution not found")

        # Get coordination status
        coordination_status = coordination_engine.get_coordination_status(mission_id)

        return {
            "execution_status": execution_status,
            "coordination_status": coordination_status,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching mission status for {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")