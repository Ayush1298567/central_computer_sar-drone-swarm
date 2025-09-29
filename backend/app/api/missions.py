"""
Mission management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models import Mission, Drone, Discovery
from ..services import mission_planner, drone_manager
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_missions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all missions with optional filtering."""
    query = db.query(Mission)

    if status:
        query = query.filter(Mission.status == status)

    missions = query.offset(skip).limit(limit).all()
    return missions


@router.get("/{mission_id}")
async def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get a specific mission by ID."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.post("/")
async def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    """Create a new mission."""
    try:
        # Create mission from mission_data
        mission = Mission(**mission_data)
        db.add(mission)
        db.commit()
        db.refresh(mission)

        logger.info(f"Created mission: {mission.name} (ID: {mission.id})")
        return mission
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating mission: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{mission_id}")
async def update_mission(
    mission_id: int,
    mission_data: dict,
    db: Session = Depends(get_db)
):
    """Update an existing mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    try:
        for key, value in mission_data.items():
            setattr(mission, key, value)

        db.commit()
        db.refresh(mission)

        logger.info(f"Updated mission: {mission.name} (ID: {mission.id})")
        return mission
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating mission: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Delete a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    try:
        db.delete(mission)
        db.commit()
        logger.info(f"Deleted mission: {mission.name} (ID: {mission.id})")
        return {"message": "Mission deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting mission: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mission_id}/start")
async def start_mission(mission_id: int, db: Session = Depends(get_db)):
    """Start a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.status != "planning":
        raise HTTPException(status_code=400, detail="Can only start missions in planning status")

    try:
        mission.status = "active"
        mission.started_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        # Here you would trigger drone deployment, AI planning activation, etc.
        logger.info(f"Started mission: {mission.name} (ID: {mission.id})")
        return {"message": "Mission started successfully", "mission": mission}
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting mission: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mission_id}/complete")
async def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Complete a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.status not in ["active", "planning"]:
        raise HTTPException(status_code=400, detail="Can only complete active or planning missions")

    try:
        mission.status = "completed"
        mission.completed_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        logger.info(f"Completed mission: {mission.name} (ID: {mission.id})")
        return {"message": "Mission completed successfully", "mission": mission}
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing mission: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{mission_id}/drones")
async def get_mission_drones(mission_id: int, db: Session = Depends(get_db)):
    """Get all drones assigned to a mission."""
    drones = db.query(Drone).filter(Drone.current_mission_id == mission_id).all()
    return drones


@router.get("/{mission_id}/discoveries")
async def get_mission_discoveries(mission_id: int, db: Session = Depends(get_db)):
    """Get all discoveries for a mission."""
    discoveries = db.query(Discovery).filter(Discovery.mission_id == mission_id).all()
    return discoveries


@router.websocket("/{mission_id}/live")
async def mission_live_updates(websocket: WebSocket, mission_id: int):
    """WebSocket endpoint for real-time mission updates."""
    await websocket.accept()

    try:
        # Send initial mission state
        # This would include current drone positions, recent discoveries, etc.
        initial_data = {
            "type": "mission_state",
            "mission_id": mission_id,
            "status": "active",
            "drones": [],  # Would be populated with real data
            "discoveries": [],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        await websocket.send_text(json.dumps(initial_data))

        # Keep connection alive and send periodic updates
        while True:
            # Simulate real-time updates
            update_data = {
                "type": "drone_update",
                "mission_id": mission_id,
                "timestamp": "2024-01-01T00:00:01Z",
                "updates": []
            }
            await websocket.send_text(json.dumps(update_data))
            await asyncio.sleep(5)  # Send update every 5 seconds

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for mission {mission_id}")
    except Exception as e:
        logger.error(f"WebSocket error for mission {mission_id}: {e}")
        await websocket.close()