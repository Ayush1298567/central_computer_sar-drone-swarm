"""
Discovery management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ....models.discovery import Discovery, DiscoveryType
from ....core.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_discoveries(
    skip: int = 0,
    limit: int = 100,
    discovery_type: Optional[DiscoveryType] = None,
    mission_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all discoveries with optional filtering"""
    try:
        query = db.query(Discovery)
        
        if discovery_type:
            query = query.filter(Discovery.discovery_type == discovery_type)
        
        if mission_id:
            query = query.filter(Discovery.mission_id == mission_id)
        
        discoveries = query.offset(skip).limit(limit).all()
        
        return {
            "discoveries": [discovery.to_dict() for discovery in discoveries],
            "total": len(discoveries),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get discoveries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{discovery_id}")
async def get_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Get specific discovery by ID"""
    try:
        discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
        
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")
        
        return discovery.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_discovery(
    mission_id: int,
    drone_id: int,
    discovery_type: DiscoveryType,
    coordinates: dict,
    confidence: float = 0.5,
    description: str = "",
    image_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create new discovery"""
    try:
        discovery = Discovery(
            mission_id=mission_id,
            drone_id=drone_id,
            discovery_type=discovery_type,
            coordinates=coordinates,
            confidence=confidence,
            description=description,
            image_url=image_url
        )
        
        db.add(discovery)
        db.commit()
        db.refresh(discovery)
        
        return discovery.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to create discovery: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{discovery_id}")
async def update_discovery(
    discovery_id: int,
    discovery_type: Optional[DiscoveryType] = None,
    confidence: Optional[float] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update discovery"""
    try:
        discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
        
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")
        
        if discovery_type is not None:
            discovery.discovery_type = discovery_type
        if confidence is not None:
            discovery.confidence = confidence
        if description is not None:
            discovery.description = description
        if status is not None:
            discovery.status = status
        
        db.commit()
        db.refresh(discovery)
        
        return discovery.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update discovery {discovery_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{discovery_id}")
async def delete_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Delete discovery"""
    try:
        discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
        
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")
        
        db.delete(discovery)
        db.commit()
        
        return {"message": "Discovery deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete discovery {discovery_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{discovery_id}/verify")
async def verify_discovery(discovery_id: int, verified: bool, db: Session = Depends(get_db)):
    """Verify discovery"""
    try:
        discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
        
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")
        
        discovery.verified = verified
        discovery.status = "verified" if verified else "false_positive"
        
        db.commit()
        db.refresh(discovery)
        
        return discovery.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify discovery {discovery_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))