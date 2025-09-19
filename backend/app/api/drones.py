"""
Drone management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..core.database import get_db
from ..models.drone import Drone, DroneStatus, DroneType
from ..services.drone_service import DroneService

router = APIRouter()

# Initialize services
drone_service = DroneService()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_drones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    drone_type: Optional[str] = Query(None),
    available_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get list of drones with optional filtering."""
    try:
        drones = await drone_service.get_drones(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            drone_type=drone_type,
            available_only=available_only
        )
        return [drone.to_dict() for drone in drones]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drones: {str(e)}")

@router.get("/{drone_id}", response_model=Dict[str, Any])
async def get_drone(drone_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific drone."""
    try:
        drone = await drone_service.get_drone_by_id(db, drone_id)
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        return drone.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drone: {str(e)}")

@router.post("/", response_model=Dict[str, Any])
async def register_drone(
    drone_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Register a new drone in the fleet."""
    try:
        # Validate required fields
        required_fields = ["drone_id", "name", "model", "serial_number", "drone_type"]
        for field in required_fields:
            if field not in drone_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Register drone through service
        drone = await drone_service.register_drone(db, drone_data)
        
        return {
            "success": True,
            "drone": drone.to_dict(),
            "message": "Drone registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register drone: {str(e)}")

@router.put("/{drone_id}", response_model=Dict[str, Any])
async def update_drone(
    drone_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update drone information and status."""
    try:
        drone = await drone_service.update_drone(db, drone_id, update_data)
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "success": True,
            "drone": drone.to_dict(),
            "message": "Drone updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update drone: {str(e)}")

@router.post("/{drone_id}/heartbeat", response_model=Dict[str, Any])
async def drone_heartbeat(
    drone_id: str,
    telemetry_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update drone telemetry and heartbeat."""
    try:
        result = await drone_service.update_telemetry(db, drone_id, telemetry_data)
        if not result:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Heartbeat received"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process heartbeat: {str(e)}")

@router.post("/{drone_id}/command", response_model=Dict[str, Any])
async def send_drone_command(
    drone_id: str,
    command_data: Dict[str, Any],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Send a command to a drone."""
    try:
        # Validate command
        if "command" not in command_data:
            raise HTTPException(status_code=400, detail="Missing command field")
        
        command = command_data["command"]
        parameters = command_data.get("parameters", {})
        
        # Send command through service
        result = await drone_service.send_command(db, drone_id, command, parameters)
        
        # Schedule command monitoring
        background_tasks.add_task(monitor_command_execution, drone_id, command, result.get("command_id"))
        
        return {
            "success": True,
            "command_id": result.get("command_id"),
            "message": f"Command '{command}' sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send command: {str(e)}")

@router.get("/{drone_id}/status", response_model=Dict[str, Any])
async def get_drone_status(drone_id: str, db: Session = Depends(get_db)):
    """Get real-time drone status and telemetry."""
    try:
        status = await drone_service.get_drone_status(db, drone_id)
        if not status:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drone status: {str(e)}")

@router.get("/{drone_id}/health", response_model=Dict[str, Any])
async def check_drone_health(drone_id: str, db: Session = Depends(get_db)):
    """Perform health check on drone systems."""
    try:
        health = await drone_service.check_health(db, drone_id)
        if not health:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check drone health: {str(e)}")

@router.post("/{drone_id}/assign", response_model=Dict[str, Any])
async def assign_drone_to_mission(
    drone_id: str,
    assignment_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Assign a drone to a mission."""
    try:
        if "mission_id" not in assignment_data:
            raise HTTPException(status_code=400, detail="Missing mission_id")
        
        mission_id = assignment_data["mission_id"]
        task = assignment_data.get("task", "search")
        
        result = await drone_service.assign_to_mission(db, drone_id, mission_id, task)
        if not result:
            raise HTTPException(status_code=400, detail="Drone cannot be assigned (unavailable or already assigned)")
        
        return {
            "success": True,
            "drone": result.to_dict(),
            "message": f"Drone assigned to mission {mission_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign drone: {str(e)}")

@router.post("/{drone_id}/unassign", response_model=Dict[str, Any])
async def unassign_drone(drone_id: str, db: Session = Depends(get_db)):
    """Unassign a drone from its current mission."""
    try:
        result = await drone_service.unassign_from_mission(db, drone_id)
        if not result:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "success": True,
            "drone": result.to_dict(),
            "message": "Drone unassigned successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unassign drone: {str(e)}")

@router.post("/{drone_id}/emergency-return", response_model=Dict[str, Any])
async def emergency_return(
    drone_id: str,
    emergency_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Command drone to perform emergency return to home."""
    try:
        result = await drone_service.emergency_return(db, drone_id, emergency_data or {})
        if not result:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Monitor emergency return
        background_tasks.add_task(monitor_emergency_return, drone_id)
        
        return {
            "success": True,
            "message": "Emergency return command sent",
            "estimated_return_time": result.get("estimated_return_time")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate emergency return: {str(e)}")

@router.get("/{drone_id}/capabilities", response_model=Dict[str, Any])
async def get_drone_capabilities(drone_id: str, db: Session = Depends(get_db)):
    """Get drone capabilities and equipment specifications."""
    try:
        capabilities = await drone_service.get_capabilities(db, drone_id)
        if not capabilities:
            raise HTTPException(status_code=404, detail="Drone or capabilities not found")
        
        return capabilities
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

@router.post("/{drone_id}/maintenance", response_model=Dict[str, Any])
async def schedule_maintenance(
    drone_id: str,
    maintenance_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Schedule maintenance for a drone."""
    try:
        result = await drone_service.schedule_maintenance(db, drone_id, maintenance_data)
        if not result:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "success": True,
            "message": "Maintenance scheduled successfully",
            "maintenance_date": result.get("maintenance_date")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule maintenance: {str(e)}")

@router.get("/{drone_id}/mission-history", response_model=List[Dict[str, Any]])
async def get_drone_mission_history(
    drone_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get drone's mission history."""
    try:
        history = await drone_service.get_mission_history(db, drone_id, skip=skip, limit=limit)
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission history: {str(e)}")

@router.get("/fleet/status", response_model=Dict[str, Any])
async def get_fleet_status(db: Session = Depends(get_db)):
    """Get overall fleet status and statistics."""
    try:
        status = await drone_service.get_fleet_status(db)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fleet status: {str(e)}")

@router.get("/fleet/available", response_model=List[Dict[str, Any]])
async def get_available_drones(
    mission_requirements: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Get drones available for mission assignment, optionally filtered by requirements."""
    try:
        drones = await drone_service.get_available_drones(db, mission_requirements)
        return [drone.to_dict() for drone in drones]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available drones: {str(e)}")

@router.post("/fleet/optimize-assignment", response_model=Dict[str, Any])
async def optimize_drone_assignment(
    mission_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI-optimized drone assignment recommendations for a mission."""
    try:
        recommendations = await drone_service.optimize_assignment(db, mission_data)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize assignment: {str(e)}")

# Background task functions
async def monitor_command_execution(drone_id: str, command: str, command_id: str):
    """Monitor command execution status."""
    try:
        # This would typically:
        # 1. Poll drone for command status
        # 2. Update command tracking
        # 3. Handle command failures
        # 4. Notify operators of issues
        pass
    except Exception as e:
        print(f"Command monitoring failed for {drone_id}: {e}")

async def monitor_emergency_return(drone_id: str):
    """Monitor emergency return progress."""
    try:
        # This would typically:
        # 1. Track drone position during return
        # 2. Monitor battery levels
        # 3. Ensure safe landing
        # 4. Alert if issues arise
        pass
    except Exception as e:
        print(f"Emergency return monitoring failed for {drone_id}: {e}")