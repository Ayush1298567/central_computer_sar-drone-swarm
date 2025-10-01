from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ...core.database import get_db
from ...models.mission import Mission, ChatMessageDB

router = APIRouter()


@router.post("/create")
async def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    """Create a new SAR mission."""
    try:
        mission = Mission(
            name=mission_data.get("name", "SAR Mission"),
            description=mission_data.get("description", ""),
            search_area=mission_data.get("search_area"),
            launch_point=mission_data.get("launch_point"),
            search_target=mission_data.get("search_target"),
            search_altitude=mission_data.get("search_altitude"),
            search_speed=mission_data.get("search_speed", "thorough"),
            recording_mode=mission_data.get("recording_mode", "continuous")
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return {
            "success": True,
            "mission": mission.to_dict(),
            "message": "Mission created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")


@router.get("/list")
async def list_missions(db: Session = Depends(get_db)):
    """List all missions."""
    try:
        missions = db.query(Mission).order_by(Mission.created_at.desc()).all()
        return {
            "success": True,
            "missions": [mission.to_dict() for mission in missions],
            "count": len(missions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve missions: {str(e)}")


@router.get("/{mission_id}")
async def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get mission details by ID."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return {
        "success": True,
        "mission": mission.to_dict()
    }


@router.put("/{mission_id}")
async def update_mission(mission_id: int, mission_data: dict, db: Session = Depends(get_db)):
    """Update mission details."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    try:
        for key, value in mission_data.items():
            if hasattr(mission, key):
                setattr(mission, key, value)
        
        db.commit()
        db.refresh(mission)
        
        return {
            "success": True,
            "mission": mission.to_dict(),
            "message": "Mission updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update mission: {str(e)}")


@router.put("/{mission_id}/start")
async def start_mission(mission_id: int, db: Session = Depends(get_db)):
    """Start mission execution."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission.status = "active"
    mission.started_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Mission started successfully",
        "mission": mission.to_dict()
    }


@router.put("/{mission_id}/pause")
async def pause_mission(mission_id: int, db: Session = Depends(get_db)):
    """Pause mission execution."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission.status = "paused"
    db.commit()
    
    return {
        "success": True,
        "message": "Mission paused successfully"
    }


@router.put("/{mission_id}/complete")
async def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Complete mission execution."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission.status = "completed"
    mission.completed_at = datetime.utcnow()
    
    if mission.started_at:
        duration = (datetime.utcnow() - mission.started_at).total_seconds() / 60
        mission.actual_duration = int(duration)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Mission completed successfully",
        "mission": mission.to_dict()
    }


@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Delete a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    try:
        db.delete(mission)
        db.commit()
        
        return {
            "success": True,
            "message": "Mission deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete mission: {str(e)}")


@router.get("/{mission_id}/chat")
async def get_mission_chat(mission_id: int, db: Session = Depends(get_db)):
    """Get chat history for a mission."""
    messages = db.query(ChatMessageDB).filter(
        ChatMessageDB.mission_id == mission_id
    ).order_by(ChatMessageDB.created_at.asc()).all()
    
    return {
        "success": True,
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "message_type": msg.message_type,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "count": len(messages)
    }
