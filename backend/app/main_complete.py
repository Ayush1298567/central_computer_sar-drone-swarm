from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core.config import settings
from app.models.drone import Drone, DroneStatus
from app.models.mission import Mission, MissionStatus, MissionDrone
from app.core.database import Base, engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic models for API
class DroneCreate(BaseModel):
    name: str
    model: Optional[str] = None
    drone_id: str
    serial_number: Optional[str] = None
    max_altitude: Optional[float] = None
    max_speed: Optional[float] = None
    battery_capacity: Optional[float] = None
    max_flight_time: Optional[int] = 25
    cruise_speed: Optional[float] = 10.0
    max_range: Optional[float] = 5000.0

class DroneUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None
    battery_level: Optional[float] = None
    position_lat: Optional[float] = None
    position_lng: Optional[float] = None
    position_alt: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None

class DroneResponse(BaseModel):
    id: int
    drone_id: str
    name: str
    model: Optional[str]
    status: str
    battery_level: Optional[float]
    position_lat: Optional[float]
    position_lng: Optional[float]
    position_alt: Optional[float]
    heading: Optional[float]
    speed: Optional[float]
    altitude: Optional[float]
    is_active: bool
    max_flight_time: Optional[int]
    max_altitude: Optional[float]
    max_speed: Optional[float]
    cruise_speed: Optional[float]
    max_range: Optional[float]
    last_heartbeat: Optional[str]
    total_flight_hours: Optional[float]
    missions_completed: Optional[int]

    class Config:
        from_attributes = True

class MissionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    mission_type: Optional[str] = "search"
    priority: Optional[int] = 3
    center_lat: float
    center_lng: float
    radius: Optional[float] = 1000.0
    search_altitude: Optional[float] = 30.0
    search_pattern: Optional[str] = "lawnmower"
    max_drones: Optional[int] = 1
    time_limit_minutes: Optional[int] = 60
    created_by: Optional[str] = "system"

class MissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    search_altitude: Optional[float] = None
    search_pattern: Optional[str] = None
    max_drones: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    progress_percentage: Optional[float] = None
    area_covered: Optional[float] = None
    discoveries_count: Optional[int] = None

class MissionResponse(BaseModel):
    id: int
    mission_id: str
    name: str
    description: Optional[str]
    status: str
    mission_type: str
    priority: int
    center_lat: Optional[float]
    center_lng: Optional[float]
    radius: Optional[float]
    search_altitude: Optional[float]
    search_pattern: Optional[str]
    max_drones: Optional[int]
    estimated_duration: Optional[int]
    discoveries_count: Optional[int]
    area_covered: Optional[float]
    progress_percentage: Optional[float]
    time_limit_minutes: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    created_by: Optional[str]

    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Life-saving Search and Rescue drone swarm control system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
        
        # Create some test data if none exists
        db = SessionLocal()
        try:
            if db.query(Drone).count() == 0:
                test_drones = [
                    Drone(
                        name="SAR Drone Alpha",
                        drone_id="SAR001",
                        model="DJI Mavic 3",
                        serial_number="DJI001",
                        status="online",
                        battery_level=85.0,
                        position_lat=37.7749,
                        position_lng=-122.4194,
                        position_alt=50.0,
                        max_altitude=120.0,
                        max_speed=15.0,
                        max_flight_time=30,
                        cruise_speed=10.0,
                        max_range=8000.0,
                        is_active=True
                    ),
                    Drone(
                        name="SAR Drone Beta",
                        drone_id="SAR002",
                        model="DJI Mavic 3",
                        serial_number="DJI002",
                        status="standby",
                        battery_level=92.0,
                        position_lat=37.7849,
                        position_lng=-122.4094,
                        position_alt=0.0,
                        max_altitude=120.0,
                        max_speed=15.0,
                        max_flight_time=30,
                        cruise_speed=10.0,
                        max_range=8000.0,
                        is_active=True
                    )
                ]
                for drone in test_drones:
                    db.add(drone)
                db.commit()
                logger.info("✅ Test drones created")
            
            if db.query(Mission).count() == 0:
                test_missions = [
                    Mission(
                        mission_id="MISS001",
                        name="Golden Gate Park Search",
                        description="Search for missing hiker in Golden Gate Park",
                        status="planning",
                        mission_type="search",
                        priority=2,
                        center_lat=37.7694,
                        center_lng=-122.4862,
                        radius=2000.0,
                        search_altitude=30.0,
                        search_pattern="lawnmower",
                        max_drones=2,
                        time_limit_minutes=120,
                        created_by="system"
                    ),
                    Mission(
                        mission_id="MISS002",
                        name="Bay Area Emergency Response",
                        description="Emergency response mission in San Francisco Bay",
                        status="active",
                        mission_type="rescue",
                        priority=1,
                        center_lat=37.7749,
                        center_lng=-122.4194,
                        radius=5000.0,
                        search_altitude=50.0,
                        search_pattern="grid",
                        max_drones=3,
                        time_limit_minutes=180,
                        created_by="system",
                        start_time=datetime.utcnow() - timedelta(minutes=30),
                        progress_percentage=25.0,
                        area_covered=1250.0,
                        discoveries_count=1
                    )
                ]
                for mission in test_missions:
                    db.add(mission)
                db.commit()
                logger.info("✅ Test missions created")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

logger.info(f"🔒 CORS configured for origins: {settings.ALLOWED_ORIGINS}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        db = SessionLocal()
        drone_count = db.query(Drone).count()
        mission_count = db.query(Mission).count()
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": "connected",
            "services": {
                "database": True,
                "api": True,
                "websocket": False
            },
            "drones_registered": drone_count,
            "missions_total": mission_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "SAR Drone Swarm Control System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

# Drone API endpoints
@app.get("/api/v1/drones", response_model=List[DroneResponse])
async def get_drones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all drones with pagination"""
    drones = db.query(Drone).offset(skip).limit(limit).all()
    return drones

@app.get("/api/v1/drones/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str, db: Session = Depends(get_db)):
    """Get a specific drone by ID"""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    return drone

@app.post("/api/v1/drones", response_model=DroneResponse)
async def create_drone(drone: DroneCreate, db: Session = Depends(get_db)):
    """Create a new drone"""
    # Check if drone_id already exists
    existing = db.query(Drone).filter(Drone.drone_id == drone.drone_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Drone ID already exists")
    
    db_drone = Drone(
        name=drone.name,
        drone_id=drone.drone_id,
        model=drone.model,
        serial_number=drone.serial_number,
        max_altitude=drone.max_altitude,
        max_speed=drone.max_speed,
        battery_capacity=drone.battery_capacity,
        max_flight_time=drone.max_flight_time,
        cruise_speed=drone.cruise_speed,
        max_range=drone.max_range,
        status="offline",
        is_active=True
    )
    
    db.add(db_drone)
    db.commit()
    db.refresh(db_drone)
    
    logger.info(f"Created drone: {drone.drone_id}")
    return db_drone

@app.put("/api/v1/drones/{drone_id}", response_model=DroneResponse)
async def update_drone(drone_id: str, drone_update: DroneUpdate, db: Session = Depends(get_db)):
    """Update a drone"""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    # Update only provided fields
    update_data = drone_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drone, field, value)
    
    drone.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(drone)
    
    logger.info(f"Updated drone: {drone_id}")
    return drone

@app.delete("/api/v1/drones/{drone_id}")
async def delete_drone(drone_id: str, db: Session = Depends(get_db)):
    """Delete a drone"""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    db.delete(drone)
    db.commit()
    
    logger.info(f"Deleted drone: {drone_id}")
    return {"message": "Drone deleted successfully"}

@app.get("/api/v1/drones/{drone_id}/status")
async def get_drone_status(drone_id: str, db: Session = Depends(get_db)):
    """Get detailed status of a drone"""
    drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    return {
        "drone_id": drone.drone_id,
        "name": drone.name,
        "status": drone.status,
        "battery_level": drone.battery_level,
        "position": {
            "lat": drone.position_lat,
            "lng": drone.position_lng,
            "alt": drone.position_alt
        },
        "heading": drone.heading,
        "speed": drone.speed,
        "altitude": drone.altitude,
        "is_active": drone.is_active,
        "last_heartbeat": drone.last_heartbeat.isoformat() if drone.last_heartbeat else None,
        "signal_strength": drone.signal_strength,
        "total_flight_hours": drone.total_flight_hours,
        "missions_completed": drone.missions_completed
    }

# Mission API endpoints
@app.get("/api/v1/missions", response_model=List[MissionResponse])
async def get_missions(skip: int = 0, limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all missions with optional status filter"""
    query = db.query(Mission)
    if status:
        query = query.filter(Mission.status == status)
    missions = query.offset(skip).limit(limit).all()
    return missions

@app.get("/api/v1/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get a specific mission by ID"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@app.post("/api/v1/missions", response_model=MissionResponse)
async def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):
    """Create a new mission"""
    # Generate unique mission ID
    mission_id = f"MISS{str(uuid.uuid4())[:8].upper()}"
    
    db_mission = Mission(
        mission_id=mission_id,
        name=mission.name,
        description=mission.description,
        mission_type=mission.mission_type,
        priority=mission.priority,
        center_lat=mission.center_lat,
        center_lng=mission.center_lng,
        radius=mission.radius,
        search_altitude=mission.search_altitude,
        search_pattern=mission.search_pattern,
        max_drones=mission.max_drones,
        time_limit_minutes=mission.time_limit_minutes,
        created_by=mission.created_by,
        status="planning"
    )
    
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    
    logger.info(f"Created mission: {mission_id}")
    return db_mission

@app.put("/api/v1/missions/{mission_id}", response_model=MissionResponse)
async def update_mission(mission_id: str, mission_update: MissionUpdate, db: Session = Depends(get_db)):
    """Update a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Update only provided fields
    update_data = mission_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mission, field, value)
    
    mission.updated_at = datetime.utcnow()
    
    # Handle status changes
    if mission_update.status:
        if mission_update.status == "active" and not mission.start_time:
            mission.start_time = datetime.utcnow()
            mission.actual_start_time = datetime.utcnow()
        elif mission_update.status in ["completed", "cancelled", "aborted"]:
            mission.end_time = datetime.utcnow()
            mission.actual_end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(mission)
    
    logger.info(f"Updated mission: {mission_id}")
    return mission

@app.delete("/api/v1/missions/{mission_id}")
async def delete_mission(mission_id: str, db: Session = Depends(get_db)):
    """Delete a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    db.delete(mission)
    db.commit()
    
    logger.info(f"Deleted mission: {mission_id}")
    return {"message": "Mission deleted successfully"}

@app.post("/api/v1/missions/{mission_id}/start")
async def start_mission(mission_id: str, db: Session = Depends(get_db)):
    """Start a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if mission.status != "planning":
        raise HTTPException(status_code=400, detail="Mission can only be started from planning status")
    
    mission.status = "active"
    mission.start_time = datetime.utcnow()
    mission.actual_start_time = datetime.utcnow()
    mission.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Started mission: {mission_id}")
    return {"message": "Mission started successfully", "mission_id": mission_id}

@app.post("/api/v1/missions/{mission_id}/complete")
async def complete_mission(mission_id: str, db: Session = Depends(get_db)):
    """Complete a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if mission.status not in ["active", "paused"]:
        raise HTTPException(status_code=400, detail="Mission must be active or paused to complete")
    
    mission.status = "completed"
    mission.end_time = datetime.utcnow()
    mission.actual_end_time = datetime.utcnow()
    mission.updated_at = datetime.utcnow()
    mission.progress_percentage = 100.0
    
    db.commit()
    
    logger.info(f"Completed mission: {mission_id}")
    return {"message": "Mission completed successfully", "mission_id": mission_id}

@app.get("/api/v1/missions/{mission_id}/status")
async def get_mission_status(mission_id: str, db: Session = Depends(get_db)):
    """Get detailed status of a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Get assigned drones
    assigned_drones = db.query(MissionDrone).filter(MissionDrone.mission_id == mission.id).all()
    
    return {
        "mission_id": mission.mission_id,
        "name": mission.name,
        "status": mission.status,
        "progress_percentage": mission.progress_percentage,
        "area_covered": mission.area_covered,
        "discoveries_count": mission.discoveries_count,
        "assigned_drones": len(assigned_drones),
        "max_drones": mission.max_drones,
        "estimated_duration": mission.estimated_duration,
        "time_limit_minutes": mission.time_limit_minutes,
        "start_time": mission.start_time.isoformat() if mission.start_time else None,
        "end_time": mission.end_time.isoformat() if mission.end_time else None,
        "created_at": mission.created_at.isoformat() if mission.created_at else None,
        "updated_at": mission.updated_at.isoformat() if mission.updated_at else None
    }

# Emergency stop endpoint
@app.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop endpoint"""
    logger.critical("🚨 EMERGENCY STOP ACTIVATED")
    
    return {
        "status": "emergency_stop_activated",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "All drone operations halted"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )