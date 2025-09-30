from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime

import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from appcore.database import get_db
from ..models.mission import Mission, DroneAssignment, ChatMessage

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create")
async def create_mission(
    mission_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new SAR mission."""
    try:
        mission = Mission(
            name=mission_data.get("name", "SAR Mission"),
            description=mission_data.get("description", ""),
            search_area=mission_data.get("search_area"),
            launch_point=mission_data.get("launch_point"),
            search_target=mission_data.get("search_target"),
            search_altitude=mission_data.get("search_altitude"),
            search_speed=mission_data.get("search_speed", "thorough")
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
        logger.error(f"Failed to create mission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")

@router.get("/{mission_id}")
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get mission details by ID."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    return {
        "success": True,
        "mission": mission.to_dict()
    }

@router.put("/{mission_id}/start")
async def start_mission(mission_id: str, db: Session = Depends(get_db)):
    """Start mission execution."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission.status = "active"
    mission.started_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "Mission started successfully"
    }