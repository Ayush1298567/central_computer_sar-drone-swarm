"""
Drone management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models import Drone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_drones(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all drones with optional filtering."""
    query = db.query(Drone)

    if status:
        query = query.filter(Drone.status == status)

    drones = query.offset(skip).limit(limit).all()
    return drones


@router.get("/{drone_id}")
async def get_drone(drone_id: int, db: Session = Depends(get_db)):
    """Get a specific drone by ID."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    return drone


@router.post("/")
async def create_drone(drone_data: dict, db: Session = Depends(get_db)):
    """Create a new drone."""
    try:
        drone = Drone(**drone_data)
        db.add(drone)
        db.commit()
        db.refresh(drone)

        logger.info(f"Created drone: {drone.name} (ID: {drone.id})")
        return drone
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{drone_id}")
async def update_drone(
    drone_id: int,
    drone_data: dict,
    db: Session = Depends(get_db)
):
    """Update an existing drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        for key, value in drone_data.items():
            setattr(drone, key, value)

        drone.updated_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()
        db.refresh(drone)

        logger.info(f"Updated drone: {drone.name} (ID: {drone.id})")
        return drone
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{drone_id}")
async def delete_drone(drone_id: int, db: Session = Depends(get_db)):
    """Delete a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        db.delete(drone)
        db.commit()
        logger.info(f"Deleted drone: {drone.name} (ID: {drone.id})")
        return {"message": "Drone deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/connect")
async def connect_drone(drone_id: int, db: Session = Depends(get_db)):
    """Connect to a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        drone.is_connected = True
        drone.status = "available"
        drone.last_seen = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        logger.info(f"Connected drone: {drone.name} (ID: {drone.id})")
        return {"message": "Drone connected successfully", "drone": drone}
    except Exception as e:
        db.rollback()
        logger.error(f"Error connecting drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/disconnect")
async def disconnect_drone(drone_id: int, db: Session = Depends(get_db)):
    """Disconnect from a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    try:
        drone.is_connected = False
        drone.status = "offline"
        drone.last_seen = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        logger.info(f"Disconnected drone: {drone.name} (ID: {drone.id})")
        return {"message": "Drone disconnected successfully", "drone": drone}
    except Exception as e:
        db.rollback()
        logger.error(f"Error disconnecting drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{drone_id}/telemetry")
async def get_drone_telemetry(drone_id: int, db: Session = Depends(get_db)):
    """Get current telemetry data for a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    telemetry = {
        "drone_id": drone.id,
        "name": drone.name,
        "position": {
            "lat": drone.current_lat,
            "lng": drone.current_lng,
            "altitude": drone.altitude
        },
        "attitude": {
            "heading": drone.heading,
            "speed": drone.speed
        },
        "battery": {
            "level": drone.battery_level,
            "remaining": drone.battery_level * drone.max_flight_time / 100  # minutes
        },
        "status": drone.status,
        "is_connected": drone.is_connected,
        "last_seen": drone.last_seen,
        "flight_hours": drone.flight_hours
    }

    return telemetry


@router.post("/{drone_id}/command")
async def send_drone_command(
    drone_id: int,
    command: dict,
    db: Session = Depends(get_db)
):
    """Send a command to a drone."""
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")

    if not drone.is_connected:
        raise HTTPException(status_code=400, detail="Drone is not connected")

    try:
        # Here you would send the actual command to the drone
        # For now, we'll just log it and update the drone state
        command_type = command.get("type", "unknown")

        logger.info(f"Sending command '{command_type}' to drone: {drone.name} (ID: {drone.id})")

        # Simulate command execution
        if command_type == "takeoff":
            drone.status = "active"
            drone.altitude = 10.0  # Simulate taking off to 10m
        elif command_type == "land":
            drone.status = "available"
            drone.altitude = 0.0
            drone.current_lat = None
            drone.current_lng = None
        elif command_type == "return_home":
            drone.status = "returning"
        elif command_type == "emergency_stop":
            drone.status = "emergency_stop"

        db.commit()

        return {
            "message": f"Command '{command_type}' sent successfully",
            "drone": drone,
            "command": command
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending command to drone: {e}")
        raise HTTPException(status_code=400, detail=str(e))