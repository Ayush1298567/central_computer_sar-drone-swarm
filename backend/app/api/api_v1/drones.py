from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models import Drone
from app.models.drone import TelemetryData

router = APIRouter()


@router.post("/register")
async def register_drone(drone_data: dict, db: Session = Depends(get_db)):
    """Register a new drone."""
    try:
        drone = Drone(
            name=drone_data.get("name"),
            model=drone_data.get("model"),
            serial_number=drone_data.get("serial_number"),
            status="online",
            connection_status="connected"
        )
        
        db.add(drone)
        db.commit()
        db.refresh(drone)
        
        return {
            "success": True,
            "drone": drone.to_dict(),
            "message": "Drone registered successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register drone: {str(e)}")


@router.get("/list")
async def list_drones(db: Session = Depends(get_db)):
    """List all drones."""
    try:
        drones = db.query(Drone).all()
        return {
            "success": True,
            "drones": [drone.to_dict() for drone in drones],
            "count": len(drones)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drones: {str(e)}")


@router.get("/{drone_id}")
async def get_drone(drone_id: int, db: Session = Depends(get_db)):
    """Get drone details by ID."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    return {
        "success": True,
        "drone": drone.to_dict()
    }


@router.put("/{drone_id}")
async def update_drone(drone_id: int, drone_data: dict, db: Session = Depends(get_db)):
    """Update drone details."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    try:
        for key, value in drone_data.items():
            if hasattr(drone, key):
                setattr(drone, key, value)
        
        drone.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(drone)
        
        return {
            "success": True,
            "drone": drone.to_dict(),
            "message": "Drone updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update drone: {str(e)}")


@router.post("/{drone_id}/telemetry")
async def update_telemetry(drone_id: int, telemetry_data: dict, db: Session = Depends(get_db)):
    """Update drone telemetry data."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    try:
        # Update drone's current position and status
        if "latitude" in telemetry_data and "longitude" in telemetry_data:
            drone.current_position = [
                telemetry_data["latitude"],
                telemetry_data["longitude"],
                telemetry_data.get("altitude", 0)
            ]
        
        if "battery_percentage" in telemetry_data:
            drone.battery_level = telemetry_data["battery_percentage"]
        
        if "signal_strength" in telemetry_data:
            drone.signal_strength = telemetry_data["signal_strength"]
        
        drone.last_seen = datetime.utcnow()
        
        # Store telemetry record
        telemetry = TelemetryData(
            drone_id=drone_id,
            mission_id=telemetry_data.get("mission_id"),
            latitude=telemetry_data.get("latitude", 0),
            longitude=telemetry_data.get("longitude", 0),
            altitude=telemetry_data.get("altitude", 0),
            heading=telemetry_data.get("heading"),
            ground_speed=telemetry_data.get("ground_speed"),
            battery_percentage=telemetry_data.get("battery_percentage"),
            battery_voltage=telemetry_data.get("battery_voltage"),
            signal_strength=telemetry_data.get("signal_strength"),
            flight_mode=telemetry_data.get("flight_mode"),
            armed_status=telemetry_data.get("armed_status")
        )
        
        db.add(telemetry)
        db.commit()
        
        return {
            "success": True,
            "message": "Telemetry updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update telemetry: {str(e)}")


@router.get("/{drone_id}/telemetry")
async def get_telemetry(drone_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get recent telemetry data for a drone."""
    telemetry_records = db.query(TelemetryData).filter(
        TelemetryData.drone_id == drone_id
    ).order_by(TelemetryData.timestamp.desc()).limit(limit).all()
    
    return {
        "success": True,
        "telemetry": [
            {
                "id": record.id,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "altitude": record.altitude,
                "battery_percentage": record.battery_percentage,
                "signal_strength": record.signal_strength,
                "timestamp": record.timestamp.isoformat()
            }
            for record in telemetry_records
        ],
        "count": len(telemetry_records)
    }


@router.delete("/{drone_id}")
async def delete_drone(drone_id: int, db: Session = Depends(get_db)):
    """Delete a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    
    try:
        db.delete(drone)
        db.commit()
        
        return {
            "success": True,
            "message": "Drone deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete drone: {str(e)}")

