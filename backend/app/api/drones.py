"""
Drones API Router

Handles drone-related endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.drone import Drone

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_drones(
    status: Optional[str] = Query(None),
    mission_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all drones with optional filtering"""
    query = db.query(Drone)

    if status:
        query = query.filter(Drone.status == status)
    if mission_id:
        query = query.filter(Drone.assigned_mission_id == mission_id)

    drones = query.all()
    return [drone.to_dict() for drone in drones]

@router.get("/{drone_id}", response_model=dict)
async def get_drone(drone_id: int, db: Session = Depends(get_db)):
    """Get drone by ID"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    return drone.to_dict()

@router.post("/", response_model=dict)
async def create_drone(drone_data: dict, db: Session = Depends(get_db)):
    """Create new drone"""
    try:
        drone = Drone(**drone_data)
        db.add(drone)
        db.commit()
        db.refresh(drone)

        return drone.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{drone_id}", response_model=dict)
async def update_drone(drone_id: int, drone_data: dict, db: Session = Depends(get_db)):
    """Update existing drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        for key, value in drone_data.items():
            if hasattr(drone, key):
                setattr(drone, key, value)

        db.commit()
        db.refresh(drone)

        return drone.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{drone_id}")
async def delete_drone(drone_id: int, db: Session = Depends(get_db)):
    """Delete drone"""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        db.delete(drone)
        db.commit()
        return {"message": "Drone deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))