from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create database
Base = declarative_base()

class Drone(Base):
    __tablename__ = "drones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    status = Column(String(50), default="offline")
    battery_level = Column(Float, default=0.0)
    position_lat = Column(Float)
    position_lng = Column(Float)
    position_alt = Column(Float)
    heading = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)
    altitude = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    max_flight_time = Column(Integer, default=25)
    max_altitude = Column(Float)
    max_speed = Column(Float)
    cruise_speed = Column(Float, default=10.0)
    max_range = Column(Float, default=5000.0)
    last_heartbeat = Column(DateTime)
    total_flight_hours = Column(Float, default=0.0)
    missions_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="planning")
    mission_type = Column(String(50), default="search")
    priority = Column(Integer, default=3)
    center_lat = Column(Float)
    center_lng = Column(Float)
    radius = Column(Float)
    search_altitude = Column(Float, default=30.0)
    search_pattern = Column(String(50), default="lawnmower")
    max_drones = Column(Integer, default=1)
    estimated_duration = Column(Integer)
    discoveries_count = Column(Integer, default=0)
    area_covered = Column(Float, default=0.0)
    progress_percentage = Column(Float, default=0.0)
    time_limit_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_by = Column(String(100))

# Create engine and session
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
@app.get("/api/v1/drones")
async def get_drones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all drones with pagination"""
    drones = db.query(Drone).offset(skip).limit(limit).all()
    return [{
        "id": drone.id,
        "drone_id": drone.drone_id,
        "name": drone.name,
        "model": drone.model,
        "status": drone.status,
        "battery_level": drone.battery_level,
        "position_lat": drone.position_lat,
        "position_lng": drone.position_lng,
        "position_alt": drone.position_alt,
        "heading": drone.heading,
        "speed": drone.speed,
        "altitude": drone.altitude,
        "is_active": drone.is_active,
        "max_flight_time": drone.max_flight_time,
        "max_altitude": drone.max_altitude,
        "max_speed": drone.max_speed,
        "cruise_speed": drone.cruise_speed,
        "max_range": drone.max_range,
        "last_heartbeat": drone.last_heartbeat.isoformat() if drone.last_heartbeat else None,
        "total_flight_hours": drone.total_flight_hours,
        "missions_completed": drone.missions_completed
    } for drone in drones]

# Drone API endpoints
@app.post("/api/v1/drones")
async def create_drone(drone_data: dict, db: Session = Depends(get_db)):
    """Create a new drone"""
    try:
        # Check if drone_id already exists
        existing = db.query(Drone).filter(Drone.drone_id == drone_data.get('drone_id')).first()
        if existing:
            raise HTTPException(status_code=400, detail="Drone ID already exists")
        
        db_drone = Drone(
            name=drone_data.get('name'),
            drone_id=drone_data.get('drone_id'),
            model=drone_data.get('model'),
            max_altitude=drone_data.get('max_altitude'),
            max_speed=drone_data.get('max_speed'),
            max_flight_time=drone_data.get('max_flight_time', 25),
            cruise_speed=drone_data.get('cruise_speed', 10.0),
            max_range=drone_data.get('max_range', 5000.0),
            status="offline",
            is_active=True
        )
        
        db.add(db_drone)
        db.commit()
        db.refresh(db_drone)
        
        logger.info(f"Created drone: {drone_data.get('drone_id')}")
        return {
            "id": db_drone.id,
            "drone_id": db_drone.drone_id,
            "name": db_drone.name,
            "model": db_drone.model,
            "status": db_drone.status,
            "battery_level": db_drone.battery_level,
            "position_lat": db_drone.position_lat,
            "position_lng": db_drone.position_lng,
            "position_alt": db_drone.position_alt,
            "heading": db_drone.heading,
            "speed": db_drone.speed,
            "altitude": db_drone.altitude,
            "is_active": db_drone.is_active,
            "max_flight_time": db_drone.max_flight_time,
            "max_altitude": db_drone.max_altitude,
            "max_speed": db_drone.max_speed,
            "cruise_speed": db_drone.cruise_speed,
            "max_range": db_drone.max_range,
            "last_heartbeat": db_drone.last_heartbeat.isoformat() if db_drone.last_heartbeat else None,
            "total_flight_hours": db_drone.total_flight_hours,
            "missions_completed": db_drone.missions_completed
        }
    except Exception as e:
        logger.error(f"Error creating drone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mission API endpoints
@app.get("/api/v1/missions")
async def get_missions(skip: int = 0, limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all missions with optional status filter"""
    try:
        query = db.query(Mission)
        if status:
            query = query.filter(Mission.status == status)
        missions = query.offset(skip).limit(limit).all()
        
        return [{
            "id": mission.id,
            "mission_id": mission.mission_id,
            "name": mission.name,
            "description": mission.description,
            "status": mission.status,
            "mission_type": mission.mission_type,
            "priority": mission.priority,
            "center_lat": mission.center_lat,
            "center_lng": mission.center_lng,
            "radius": mission.radius,
            "search_altitude": mission.search_altitude,
            "search_pattern": mission.search_pattern,
            "max_drones": mission.max_drones,
            "estimated_duration": mission.estimated_duration,
            "discoveries_count": mission.discoveries_count,
            "area_covered": mission.area_covered,
            "progress_percentage": mission.progress_percentage,
            "time_limit_minutes": mission.time_limit_minutes,
            "created_at": mission.created_at.isoformat() if mission.created_at else None,
            "updated_at": mission.updated_at.isoformat() if mission.updated_at else None,
            "start_time": mission.start_time.isoformat() if mission.start_time else None,
            "end_time": mission.end_time.isoformat() if mission.end_time else None,
            "created_by": mission.created_by
        } for mission in missions]
    except Exception as e:
        logger.error(f"Error getting missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/missions")
async def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    """Create a new mission"""
    try:
        # Generate unique mission ID
        import uuid
        mission_id = f"MISS{str(uuid.uuid4())[:8].upper()}"
        
        db_mission = Mission(
            mission_id=mission_id,
            name=mission_data.get('name'),
            description=mission_data.get('description'),
            mission_type=mission_data.get('mission_type', 'search'),
            priority=mission_data.get('priority', 3),
            center_lat=mission_data.get('center_lat'),
            center_lng=mission_data.get('center_lng'),
            radius=mission_data.get('radius'),
            search_altitude=mission_data.get('search_altitude', 30.0),
            search_pattern=mission_data.get('search_pattern', 'lawnmower'),
            max_drones=mission_data.get('max_drones', 1),
            time_limit_minutes=mission_data.get('time_limit_minutes'),
            created_by=mission_data.get('created_by', 'system'),
            status="planning"
        )
        
        db.add(db_mission)
        db.commit()
        db.refresh(db_mission)
        
        logger.info(f"Created mission: {mission_id}")
        return {
            "id": db_mission.id,
            "mission_id": db_mission.mission_id,
            "name": db_mission.name,
            "description": db_mission.description,
            "status": db_mission.status,
            "mission_type": db_mission.mission_type,
            "priority": db_mission.priority,
            "center_lat": db_mission.center_lat,
            "center_lng": db_mission.center_lng,
            "radius": db_mission.radius,
            "search_altitude": db_mission.search_altitude,
            "search_pattern": db_mission.search_pattern,
            "max_drones": db_mission.max_drones,
            "estimated_duration": db_mission.estimated_duration,
            "discoveries_count": db_mission.discoveries_count,
            "area_covered": db_mission.area_covered,
            "progress_percentage": db_mission.progress_percentage,
            "time_limit_minutes": db_mission.time_limit_minutes,
            "created_at": db_mission.created_at.isoformat() if db_mission.created_at else None,
            "updated_at": db_mission.updated_at.isoformat() if db_mission.updated_at else None,
            "start_time": db_mission.start_time.isoformat() if db_mission.start_time else None,
            "end_time": db_mission.end_time.isoformat() if db_mission.end_time else None,
            "created_by": db_mission.created_by
        }
    except Exception as e:
        logger.error(f"Error creating mission: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/missions/{mission_id}")
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get a specific mission by ID"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return {
        "id": mission.id,
        "mission_id": mission.mission_id,
        "name": mission.name,
        "description": mission.description,
        "status": mission.status,
        "mission_type": mission.mission_type,
        "priority": mission.priority,
        "center_lat": mission.center_lat,
        "center_lng": mission.center_lng,
        "radius": mission.radius,
        "search_altitude": mission.search_altitude,
        "search_pattern": mission.search_pattern,
        "max_drones": mission.max_drones,
        "estimated_duration": mission.estimated_duration,
        "discoveries_count": mission.discoveries_count,
        "area_covered": mission.area_covered,
        "progress_percentage": mission.progress_percentage,
        "time_limit_minutes": mission.time_limit_minutes,
        "created_at": mission.created_at.isoformat() if mission.created_at else None,
        "updated_at": mission.updated_at.isoformat() if mission.updated_at else None,
        "start_time": mission.start_time.isoformat() if mission.start_time else None,
        "end_time": mission.end_time.isoformat() if mission.end_time else None,
        "created_by": mission.created_by
    }

@app.get("/api/v1/missions/{mission_id}/status")
async def get_mission_status(mission_id: str, db: Session = Depends(get_db)):
    """Get detailed status of a mission"""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return {
        "mission_id": mission.mission_id,
        "name": mission.name,
        "status": mission.status,
        "progress_percentage": mission.progress_percentage,
        "area_covered": mission.area_covered,
        "discoveries_count": mission.discoveries_count,
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
        "app.main_debug:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )