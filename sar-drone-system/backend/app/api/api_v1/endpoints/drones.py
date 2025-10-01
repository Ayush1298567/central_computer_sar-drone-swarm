"""
Drone management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ....models.drone import Drone, DroneStatus, DroneType
from ....core.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_drones(
    skip: int = 0,
    limit: int = 100,
    status: Optional[DroneStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all drones with optional filtering"""
    try:
        query = db.query(Drone)
        
        if status:
            query = query.filter(Drone.status == status)
        
        drones = query.offset(skip).limit(limit).all()
        
        return {
            "drones": [drone.to_dict() for drone in drones],
            "total": len(drones),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get drones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{drone_id}")
async def get_drone(drone_id: int, db: Session = Depends(get_db)):
    """Get specific drone by ID"""
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return drone.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_drone(
    name: str,
    model: str,
    battery_level: float = 100.0,
    max_flight_time: int = 30,
    status: DroneStatus = DroneStatus.IDLE,
    db: Session = Depends(get_db)
):
    """Create new drone"""
    try:
        drone = Drone(
            name=name,
            drone_type=DroneType.MULTI_PURPOSE,  # Default type
            battery_level=battery_level,
            max_flight_time=max_flight_time,
            status=status
        )
        
        db.add(drone)
        db.commit()
        db.refresh(drone)
        
        return drone.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to create drone: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{drone_id}")
async def update_drone(
    drone_id: int,
    name: Optional[str] = None,
    battery_level: Optional[float] = None,
    status: Optional[DroneStatus] = None,
    current_mission_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update drone"""
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        if name is not None:
            drone.name = name
        if battery_level is not None:
            drone.battery_level = battery_level
        if status is not None:
            drone.status = status
        if current_mission_id is not None:
            drone.current_mission_id = current_mission_id
        
        db.commit()
        db.refresh(drone)
        
        return drone.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update drone {drone_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{drone_id}")
async def delete_drone(drone_id: int, db: Session = Depends(get_db)):
    """Delete drone"""
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        db.delete(drone)
        db.commit()
        
        return {"message": "Drone deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete drone {drone_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{drone_id}/deploy")
async def deploy_drone(drone_id: int, mission_id: int, db: Session = Depends(get_db)):
    """Deploy drone to mission"""
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        if drone.status != DroneStatus.IDLE:
            raise HTTPException(
                status_code=400, 
                detail=f"Drone must be available to deploy, current status: {drone.status.value}"
            )
        
        drone.status = DroneStatus.DEPLOYED
        drone.current_mission_id = mission_id
        
        db.commit()
        db.refresh(drone)
        
        return drone.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy drone {drone_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{drone_id}/return")
async def return_drone(drone_id: int, db: Session = Depends(get_db)):
    """Return drone from mission"""
    try:
        drone = db.query(Drone).filter(Drone.id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        drone.status = DroneStatus.IDLE
        drone.current_mission_id = None
        
        db.commit()
        db.refresh(drone)
        
        return drone.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to return drone {drone_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))