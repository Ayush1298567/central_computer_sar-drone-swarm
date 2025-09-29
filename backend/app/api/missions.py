"""
Missions API Router

Handles mission-related endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.mission import Mission

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_missions(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all missions with optional filtering"""
    query = db.query(Mission)

    if status:
        query = query.filter(Mission.status == status)

    # Simple pagination
    offset = (page - 1) * per_page
    missions = query.offset(offset).limit(per_page).all()

    return [mission.to_dict() for mission in missions]

@router.get("/{mission_id}", response_model=dict)
async def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get mission by ID"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    return mission.to_dict()

@router.post("/", response_model=dict)
async def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    """Create new mission"""
    try:
        mission = Mission(**mission_data)
        db.add(mission)
        db.commit()
        db.refresh(mission)

        return mission.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{mission_id}", response_model=dict)
async def update_mission(mission_id: int, mission_data: dict, db: Session = Depends(get_db)):
    """Update existing mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    try:
        for key, value in mission_data.items():
            if hasattr(mission, key):
                setattr(mission, key, value)

        db.commit()
        db.refresh(mission)

        return mission.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Delete mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    try:
        db.delete(mission)
        db.commit()
        return {"message": "Mission deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{mission_id}/start")
async def start_mission(mission_id: int, db: Session = Depends(get_db)):
    """Start mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission.status = "active"
    db.commit()

    return mission.to_dict()

@router.post("/{mission_id}/stop")
async def stop_mission(mission_id: int, db: Session = Depends(get_db)):
    """Stop mission"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission.status = "completed"
    db.commit()

    return mission.to_dict()