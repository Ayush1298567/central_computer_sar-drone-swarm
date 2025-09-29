"""
Drone API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.core.database import get_db
from app.models import Drone, DroneTelemetry
from app.services.coordination_engine import coordination_engine, DroneState, DroneStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_drones(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """Get all drones with optional filtering."""
    try:
        query = db.query(Drone)

        if status_filter:
            query = query.filter(Drone.status == status_filter)

        drones = query.offset(skip).limit(limit).all()

        return [
            {
                "id": drone.id,
                "drone_id": drone.drone_id,
                "name": drone.name,
                "model": drone.model,
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
                "capabilities": drone.capabilities,
                "max_flight_time": drone.max_flight_time,
                "last_seen": drone.last_seen.isoformat() if drone.last_seen else None,
                "created_at": drone.created_at.isoformat()
            }
            for drone in drones
        ]
    except Exception as e:
        logger.error(f"Error fetching drones: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{drone_id}", response_model=Dict[str, Any])
async def get_drone(
    drone_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific drone by ID."""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")

        return {
            "id": drone.id,
            "drone_id": drone.drone_id,
            "name": drone.name,
            "model": drone.model,
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
            "capabilities": drone.capabilities,
            "max_flight_time": drone.max_flight_time,
            "max_altitude": drone.max_altitude,
            "max_speed": drone.max_speed,
            "last_seen": drone.last_seen.isoformat() if drone.last_seen else None,
            "created_at": drone.created_at.isoformat(),
            "updated_at": drone.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{drone_id}/register")
async def register_drone(
    drone_id: str,
    drone_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Register a new drone."""
    try:
        # Check if drone already exists
        existing_drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if existing_drone:
            raise HTTPException(status_code=400, detail="Drone already registered")

        # Create new drone
        drone = Drone(
            drone_id=drone_id,
            name=drone_data.get("name", f"Drone-{drone_id}"),
            model=drone_data.get("model", "Unknown"),
            status="offline",
            battery_level=drone_data.get("battery_level", 100.0),
            position_lat=drone_data.get("position_lat"),
            position_lng=drone_data.get("position_lng"),
            position_alt=drone_data.get("position_alt", 0.0),
            heading=drone_data.get("heading", 0.0),
            speed=drone_data.get("speed", 0.0),
            altitude=drone_data.get("altitude", 0.0),
            is_active=True,
            capabilities=drone_data.get("capabilities", {}),
            max_flight_time=drone_data.get("max_flight_time", 30),
            max_altitude=drone_data.get("max_altitude", 120.0),
            max_speed=drone_data.get("max_speed", 15.0)
        )

        db.add(drone)
        db.commit()
        db.refresh(drone)

        # Register with coordination engine
        drone_state = DroneState(
            drone_id=drone_id,
            status=DroneStatus.OFFLINE,
            position=(drone.position_lat or 0, drone.position_lng or 0, drone.position_alt or 0),
            battery_level=drone.battery_level,
            heading=drone.heading,
            speed=drone.speed
        )
        await coordination_engine.register_drone(drone_state)

        logger.info(f"Registered new drone {drone_id}")
        return {"message": "Drone registered successfully", "drone_id": drone_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{drone_id}/update")
async def update_drone(
    drone_id: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update drone state."""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")

        # Update drone fields
        for key, value in updates.items():
            if hasattr(drone, key):
                setattr(drone, key, value)

        drone.last_seen = func.now()
        db.commit()

        # Update coordination engine
        await coordination_engine.update_drone_state(drone_id, updates)

        logger.info(f"Updated drone {drone_id}")
        return {"message": "Drone updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{drone_id}/telemetry")
async def add_telemetry(
    drone_id: str,
    telemetry_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Add telemetry data for a drone."""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")

        # Create telemetry record
        telemetry = DroneTelemetry(
            drone_id=drone.id,
            battery_level=telemetry_data.get("battery_level", drone.battery_level),
            position_lat=telemetry_data.get("position_lat", drone.position_lat),
            position_lng=telemetry_data.get("position_lng", drone.position_lng),
            position_alt=telemetry_data.get("position_alt", drone.position_alt),
            heading=telemetry_data.get("heading", drone.heading),
            speed=telemetry_data.get("speed", drone.speed),
            altitude=telemetry_data.get("altitude", drone.altitude),
            signal_strength=telemetry_data.get("signal_strength"),
            temperature=telemetry_data.get("temperature"),
            wind_speed=telemetry_data.get("wind_speed"),
            wind_direction=telemetry_data.get("wind_direction"),
            sensor_data=telemetry_data.get("sensor_data")
        )

        db.add(telemetry)
        db.commit()

        # Update drone state
        await coordination_engine.update_drone_state(drone_id, telemetry_data)

        return {"message": "Telemetry data added successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding telemetry for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{drone_id}/telemetry")
async def get_drone_telemetry(
    drone_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get telemetry history for a drone."""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")

        telemetry = db.query(DroneTelemetry).filter(
            DroneTelemetry.drone_id == drone.id
        ).order_by(DroneTelemetry.timestamp.desc()).limit(limit).all()

        return [
            {
                "timestamp": t.timestamp.isoformat(),
                "battery_level": t.battery_level,
                "position": {
                    "lat": t.position_lat,
                    "lng": t.position_lng,
                    "alt": t.position_alt
                },
                "heading": t.heading,
                "speed": t.speed,
                "altitude": t.altitude,
                "signal_strength": t.signal_strength,
                "temperature": t.temperature,
                "wind_speed": t.wind_speed,
                "wind_direction": t.wind_direction,
                "sensor_data": t.sensor_data
            }
            for t in telemetry
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching telemetry for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{drone_id}")
async def unregister_drone(
    drone_id: str,
    db: Session = Depends(get_db)
):
    """Unregister a drone."""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")

        # Unregister from coordination engine
        await coordination_engine.unregister_drone(drone_id)

        # Mark as inactive instead of deleting
        drone.is_active = False
        drone.status = "offline"
        db.commit()

        logger.info(f"Unregistered drone {drone_id}")
        return {"message": "Drone unregistered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")