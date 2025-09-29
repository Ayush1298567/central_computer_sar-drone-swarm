"""
Discoveries API Router

Handles discovery/detection-related endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.discovery import Discovery

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_discoveries(
    mission_id: Optional[int] = Query(None),
    drone_id: Optional[int] = Query(None),
    discovery_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all discoveries with optional filtering"""
    query = db.query(Discovery)

    if mission_id:
        query = query.filter(Discovery.mission_id == mission_id)
    if drone_id:
        query = query.filter(Discovery.drone_id == drone_id)
    if discovery_type:
        query = query.filter(Discovery.discovery_type == discovery_type)
    if priority:
        query = query.filter(Discovery.priority == priority)
    if is_verified is not None:
        query = query.filter(Discovery.is_verified == is_verified)

    discoveries = query.all()
    return [discovery.to_dict() for discovery in discoveries]

@router.get("/{discovery_id}", response_model=dict)
async def get_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Get discovery by ID"""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    return discovery.to_dict()

@router.post("/", response_model=dict)
async def create_discovery(discovery_data: dict, db: Session = Depends(get_db)):
    """Create new discovery"""
    try:
        discovery = Discovery(**discovery_data)
        db.add(discovery)
        db.commit()
        db.refresh(discovery)

        return discovery.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{discovery_id}", response_model=dict)
async def update_discovery(discovery_id: int, discovery_data: dict, db: Session = Depends(get_db)):
    """Update existing discovery"""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        for key, value in discovery_data.items():
            if hasattr(discovery, key):
                setattr(discovery, key, value)

        db.commit()
        db.refresh(discovery)

        return discovery.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{discovery_id}")
async def delete_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Delete discovery"""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        db.delete(discovery)
        db.commit()
        return {"message": "Discovery deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))