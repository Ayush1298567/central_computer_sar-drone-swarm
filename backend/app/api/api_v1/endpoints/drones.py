"""
Drone management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ...models import Drone
from ...schemas import DroneCreate, DroneResponse, DroneUpdate

router = APIRouter()


@router.get("/", response_model=List[DroneResponse])
async def get_drones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all drones with optional filtering."""
    query = db.query(Drone)

    if status:
        query = query.filter(Drone.status == status)

    drones = query.offset(skip).limit(limit).all()
    return drones


@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str, db: Session = Depends(get_db)):
    """Get a specific drone by ID."""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    return drone


@router.post("/", response_model=DroneResponse)
async def create_drone(drone: DroneCreate, db: Session = Depends(get_db)):
    """Create a new drone."""
    db_drone = Drone(**drone.dict())
    db.add(db_drone)
    db.commit()
    db.refresh(db_drone)
    return db_drone


@router.put("/{drone_id}", response_model=DroneResponse)
async def update_drone(
    drone_id: str,
    drone_update: DroneUpdate,
    db: Session = Depends(get_db)
):
    """Update a drone."""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    for field, value in drone_update.dict(exclude_unset=True).items():
        setattr(drone, field, value)

    db.commit()
    db.refresh(drone)
    return drone


@router.delete("/{drone_id}")
async def delete_drone(drone_id: str, db: Session = Depends(get_db)):
    """Delete a drone."""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    db.delete(drone)
    db.commit()
    return {"message": "Drone deleted successfully"}