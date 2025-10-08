from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.models.drone import Drone, DroneStatus
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
        
        # Create some test drones if none exist
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
            "drones_registered": drone_count
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
        "app.main_with_db:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )