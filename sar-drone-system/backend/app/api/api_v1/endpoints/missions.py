"""
Mission management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ....models.mission import Mission, MissionStatus, MissionType
from ....core.database import get_db
from ....ai import create_ollama_intelligence_engine, MissionContext
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_missions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[MissionStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all missions with optional filtering"""
    try:
        query = db.query(Mission)
        
        if status:
            query = query.filter(Mission.status == status)
        
        missions = query.offset(skip).limit(limit).all()
        
        return {
            "missions": [mission.to_dict() for mission in missions],
            "total": len(missions),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{mission_id}")
async def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get specific mission by ID"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return mission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_mission(
    name: str,
    description: str = "",
    mission_type: MissionType = MissionType.MISSING_PERSON,
    priority: int = 5,
    search_area: dict = None,
    max_flight_time: int = 30,
    search_altitude: float = 100.0,
    db: Session = Depends(get_db)
):
    """Create new mission"""
    try:
        mission = Mission(
            name=name,
            description=description,
            mission_type=mission_type,
            priority=priority,
            search_area=search_area or {"size_km2": 1.0},
            max_flight_time=max_flight_time,
            search_altitude=search_altitude
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return mission.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to create mission: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{mission_id}")
async def update_mission(
    mission_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[MissionStatus] = None,
    priority: Optional[int] = None,
    progress_percentage: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update mission"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if name is not None:
            mission.name = name
        if description is not None:
            mission.description = description
        if status is not None:
            mission.status = status
        if priority is not None:
            mission.priority = priority
        if progress_percentage is not None:
            mission.progress_percentage = progress_percentage
        
        db.commit()
        db.refresh(mission)
        
        return mission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mission {mission_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Delete mission"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        db.delete(mission)
        db.commit()
        
        return {"message": "Mission deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mission {mission_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/analyze")
async def analyze_mission(mission_id: int, db: Session = Depends(get_db)):
    """Analyze mission using AI intelligence"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Create mission context for AI analysis
        context = MissionContext(
            mission_id=str(mission.id),
            mission_type=mission.mission_type.value,
            search_area=mission.search_area or {},
            weather_conditions={},
            available_drones=[{"id": drone_id} for drone_id in (mission.assigned_drones or [])],
            time_constraints={"remaining_minutes": mission.max_flight_time},
            priority_level=mission.priority,
            discovered_objects=mission.discovered_objects or [],
            current_progress=mission.progress_percentage
        )
        
        # Get AI analysis
        engine = await create_ollama_intelligence_engine()
        analysis = await engine.analyze_mission_context(context)
        strategy = await engine.plan_search_strategy(context)
        risk_assessment = await engine.assess_risks(context)
        
        # Update mission with AI analysis
        mission.search_strategy = strategy.__dict__
        mission.risk_assessment = risk_assessment.__dict__
        mission.estimated_duration = strategy.estimated_time
        
        db.commit()
        db.refresh(mission)
        
        return {
            "mission": mission.to_dict(),
            "ai_analysis": analysis,
            "search_strategy": strategy.__dict__,
            "risk_assessment": risk_assessment.__dict__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/start")
async def start_mission(mission_id: int, db: Session = Depends(get_db)):
    """Start mission execution"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.status != MissionStatus.READY:
            raise HTTPException(
                status_code=400, 
                detail=f"Mission must be in READY status to start, current status: {mission.status.value}"
            )
        
        mission.status = MissionStatus.ACTIVE
        from datetime import datetime
        mission.started_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mission)
        
        return mission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start mission {mission_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{mission_id}/complete")
async def complete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Complete mission"""
    try:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        mission.status = MissionStatus.COMPLETED
        mission.progress_percentage = 100.0
        from datetime import datetime
        mission.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mission)
        
        return mission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete mission {mission_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))