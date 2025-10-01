from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ...core.database import get_db
from ...models.discovery import Discovery

router = APIRouter()


@router.post("/create")
async def create_discovery(discovery_data: dict, db: Session = Depends(get_db)):
    """Create a new discovery record."""
    try:
        discovery = Discovery(
            mission_id=discovery_data.get("mission_id"),
            drone_id=discovery_data.get("drone_id"),
            object_type=discovery_data.get("object_type"),
            confidence_score=discovery_data.get("confidence_score"),
            latitude=discovery_data.get("latitude"),
            longitude=discovery_data.get("longitude"),
            altitude=discovery_data.get("altitude"),
            detection_method=discovery_data.get("detection_method", "visual"),
            primary_image_url=discovery_data.get("primary_image_url"),
            detection_context=discovery_data.get("detection_context")
        )
        
        # Calculate priority
        discovery.priority_level = discovery.calculate_priority()
        
        db.add(discovery)
        db.commit()
        db.refresh(discovery)
        
        return {
            "success": True,
            "discovery": discovery.to_dict(),
            "message": "Discovery created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create discovery: {str(e)}")


@router.get("/list")
async def list_discoveries(mission_id: int = None, db: Session = Depends(get_db)):
    """List all discoveries, optionally filtered by mission."""
    try:
        query = db.query(Discovery)
        
        if mission_id:
            query = query.filter(Discovery.mission_id == mission_id)
        
        discoveries = query.order_by(Discovery.discovered_at.desc()).all()
        
        return {
            "success": True,
            "discoveries": [discovery.to_dict() for discovery in discoveries],
            "count": len(discoveries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve discoveries: {str(e)}")


@router.get("/{discovery_id}")
async def get_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Get discovery details by ID."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    
    return {
        "success": True,
        "discovery": discovery.to_dict()
    }


@router.put("/{discovery_id}")
async def update_discovery(discovery_id: int, discovery_data: dict, db: Session = Depends(get_db)):
    """Update discovery details."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    
    try:
        for key, value in discovery_data.items():
            if hasattr(discovery, key):
                setattr(discovery, key, value)
        
        db.commit()
        db.refresh(discovery)
        
        return {
            "success": True,
            "discovery": discovery.to_dict(),
            "message": "Discovery updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update discovery: {str(e)}")


@router.put("/{discovery_id}/verify")
async def verify_discovery(discovery_id: int, verification_data: dict, db: Session = Depends(get_db)):
    """Verify a discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    
    discovery.human_verified = True
    discovery.verified_at = datetime.utcnow()
    discovery.verified_by_operator = verification_data.get("operator_name")
    discovery.verification_notes = verification_data.get("notes")
    discovery.investigation_status = "verified"
    
    db.commit()
    
    return {
        "success": True,
        "message": "Discovery verified successfully",
        "discovery": discovery.to_dict()
    }


@router.delete("/{discovery_id}")
async def delete_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Delete a discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    
    try:
        db.delete(discovery)
        db.commit()
        
        return {
            "success": True,
            "message": "Discovery deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete discovery: {str(e)}")
