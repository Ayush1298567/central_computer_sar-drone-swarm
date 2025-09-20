"""
Drone API endpoints for the SAR drone system
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..models.drone import (
    Drone, DroneRegister, DroneUpdate, DroneResponse, DroneListResponse,
    DroneStatus, DroneType, TelemetryData, TelemetryResponse,
    DroneHealth, HealthCheckResponse, DroneCommand, CommandResponse
)
from ..services.drone_manager import DroneManager
from ..services.notification_service import NotificationService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drones", tags=["drones"])

# Service instances
drone_manager = DroneManager()
notification_service = NotificationService()

@router.post("/discover")
async def discover_drones(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    discovery_method: str = "network_scan",
    timeout_seconds: int = 30
):
    """Discover drones on the network"""
    try:
        discovered_drones = await drone_manager.discover_drones(
            discovery_method, 
            timeout_seconds=timeout_seconds
        )
        
        # Register discovered drones in background
        background_tasks.add_task(_register_discovered_drones, discovered_drones, db)
        
        logger.info(f"Discovered {len(discovered_drones)} drones using {discovery_method}")
        return {
            "message": f"Discovered {len(discovered_drones)} drones",
            "drones": discovered_drones,
            "discovery_method": discovery_method
        }
        
    except Exception as e:
        logger.error(f"Error discovering drones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discover drones: {str(e)}")

@router.post("/register", response_model=DroneResponse, status_code=201)
async def register_drone(
    drone_data: DroneRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new drone"""
    try:
        # Check if drone already exists
        existing_drone = db.query(Drone).filter(Drone.drone_id == drone_data.drone_id).first()
        if existing_drone:
            raise HTTPException(status_code=400, detail="Drone already registered")
        
        # Create database record
        db_drone = Drone(
            drone_id=drone_data.drone_id,
            name=drone_data.name,
            drone_type=drone_data.drone_type.value,
            ip_address=drone_data.ip_address,
            port=drone_data.port,
            mac_address=drone_data.mac_address,
            capabilities=drone_data.capabilities.dict(),
            firmware_version=drone_data.firmware_version,
            hardware_version=drone_data.hardware_version,
            status=DroneStatus.IDLE.value
        )
        
        db.add(db_drone)
        db.commit()
        db.refresh(db_drone)
        
        # Register with drone manager
        await drone_manager.register_drone(drone_data)
        
        # Send notification in background
        background_tasks.add_task(
            _send_drone_notification,
            "drone_registered",
            db_drone,
            f"Drone '{drone_data.name}' registered successfully"
        )
        
        logger.info(f"Drone registered: {drone_data.drone_id}")
        return _convert_to_response(db_drone)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering drone: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register drone: {str(e)}")

@router.get("/", response_model=DroneListResponse)
async def list_drones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[DroneStatus] = None,
    drone_type: Optional[DroneType] = None,
    mission_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List drones with filtering and pagination"""
    try:
        query = db.query(Drone)
        
        # Apply filters
        if status:
            query = query.filter(Drone.status == status.value)
        if drone_type:
            query = query.filter(Drone.drone_type == drone_type.value)
        if mission_id:
            query = query.filter(Drone.current_mission_id == mission_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        drones = query.order_by(Drone.registered_at.desc()).offset(skip).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return DroneListResponse(
            drones=[_convert_to_response(drone) for drone in drones],
            total=total,
            page=page,
            per_page=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing drones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list drones: {str(e)}")

@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str, db: Session = Depends(get_db)):
    """Get a specific drone by ID"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return _convert_to_response(drone)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drone {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get drone: {str(e)}")

@router.patch("/{drone_id}", response_model=DroneResponse)
async def update_drone(
    drone_id: str,
    update_data: DroneUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update a drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(drone, field):
                if field == "capabilities" and value:
                    setattr(drone, field, value.dict())
                elif isinstance(value, Enum):
                    setattr(drone, field, value.value)
                else:
                    setattr(drone, field, value)
        
        drone.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(drone)
        
        # Send notification in background
        background_tasks.add_task(
            _send_drone_notification,
            "drone_updated",
            drone,
            f"Drone '{drone.name}' updated"
        )
        
        logger.info(f"Drone updated: {drone_id}")
        return _convert_to_response(drone)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating drone {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update drone: {str(e)}")

@router.delete("/{drone_id}")
async def unregister_drone(
    drone_id: str,
    force: bool = Query(False, description="Force unregister even if drone is active"),
    db: Session = Depends(get_db)
):
    """Unregister a drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        if drone.status == DroneStatus.ACTIVE.value and not force:
            raise HTTPException(status_code=400, detail="Cannot unregister active drone (use force=true to override)")
        
        # Unregister from drone manager
        await drone_manager.unregister_drone(drone_id)
        
        # Remove from database
        db.delete(drone)
        db.commit()
        
        logger.info(f"Drone unregistered: {drone_id}")
        return {"message": "Drone unregistered successfully", "drone_id": drone_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering drone {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unregister drone: {str(e)}")

@router.get("/{drone_id}/status")
async def get_drone_status(drone_id: str, db: Session = Depends(get_db)):
    """Get current drone status"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Get real-time status from drone manager
        live_status = await drone_manager.get_drone_status(drone_id)
        
        return {
            "drone_id": drone_id,
            "status": live_status,
            "last_updated": drone.last_seen,
            "current_mission": drone.current_mission_id,
            "battery_level": drone.last_telemetry.get("battery_percent") if drone.last_telemetry else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drone status {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get drone status: {str(e)}")

@router.post("/{drone_id}/telemetry", response_model=TelemetryResponse)
async def submit_telemetry(
    drone_id: str,
    telemetry: TelemetryData,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit telemetry data from drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Process telemetry through drone manager
        processed_telemetry = await drone_manager.process_telemetry(drone_id, telemetry)
        
        # Update drone record
        drone.last_telemetry = telemetry.dict()
        drone.last_seen = datetime.utcnow()
        db.commit()
        
        # Process in background for performance analytics
        background_tasks.add_task(_process_telemetry_analytics, drone_id, telemetry)
        
        return TelemetryResponse(
            drone_id=drone_id,
            telemetry=telemetry,
            received_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing telemetry for {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process telemetry: {str(e)}")

@router.get("/{drone_id}/telemetry")
async def get_telemetry_history(
    drone_id: str,
    hours: int = Query(1, ge=1, le=168, description="Hours of history to retrieve"),
    db: Session = Depends(get_db)
):
    """Get telemetry history for a drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Get telemetry history from drone manager
        since = datetime.utcnow() - timedelta(hours=hours)
        history = await drone_manager.get_telemetry_history(drone_id, since)
        
        return {
            "drone_id": drone_id,
            "history": history,
            "period_hours": hours,
            "total_records": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting telemetry history for {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get telemetry history: {str(e)}")

@router.post("/{drone_id}/health", response_model=HealthCheckResponse)
async def perform_health_check(
    drone_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Perform health check on drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Perform health check through drone manager
        health_status = await drone_manager.perform_health_check(drone_id)
        
        # Update drone record
        drone.health_status = health_status.dict()
        drone.last_seen = datetime.utcnow()
        db.commit()
        
        # Send alerts for critical issues
        if health_status.overall_status in ["poor", "critical"]:
            background_tasks.add_task(
                _send_health_alert,
                drone_id,
                health_status
            )
        
        return HealthCheckResponse(
            drone_id=drone_id,
            health=health_status,
            checked_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing health check for {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")

@router.post("/{drone_id}/command", response_model=CommandResponse)
async def send_command(
    drone_id: str,
    command: DroneCommand,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send command to drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Generate command ID
        command_id = f"cmd_{uuid.uuid4().hex[:8]}"
        
        # Send command through drone manager
        response = await drone_manager.send_command(
            drone_id, 
            command.command_type, 
            command.parameters,
            timeout=command.timeout_seconds
        )
        
        # Log command execution
        background_tasks.add_task(
            _log_command_execution,
            command_id,
            drone_id,
            command,
            response
        )
        
        return CommandResponse(
            command_id=command_id,
            drone_id=drone_id,
            command=command,
            status="sent",
            sent_at=datetime.utcnow(),
            response=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending command to {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send command: {str(e)}")

@router.post("/{drone_id}/emergency-stop")
async def emergency_stop(
    drone_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    reason: Optional[str] = None
):
    """Emergency stop for drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Send emergency stop command
        response = await drone_manager.send_command(
            drone_id, 
            "emergency_stop", 
            {"reason": reason or "Manual emergency stop"},
            timeout=10  # Short timeout for emergency
        )
        
        # Update drone status
        drone.status = DroneStatus.ERROR.value
        drone.last_seen = datetime.utcnow()
        db.commit()
        
        # Send urgent notification
        background_tasks.add_task(
            _send_drone_notification,
            "emergency_stop",
            drone,
            f"Emergency stop activated for drone '{drone.name}': {reason or 'Manual stop'}"
        )
        
        logger.warning(f"Emergency stop activated for drone {drone_id}: {reason}")
        return {
            "message": "Emergency stop activated",
            "drone_id": drone_id,
            "reason": reason,
            "response": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing emergency stop for {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform emergency stop: {str(e)}")

@router.get("/{drone_id}/diagnostics")
async def get_diagnostics(
    drone_id: str,
    include_logs: bool = Query(False, description="Include recent log entries"),
    db: Session = Depends(get_db)
):
    """Get comprehensive diagnostics for drone"""
    try:
        drone = db.query(Drone).filter(Drone.drone_id == drone_id).first()
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Get diagnostics from drone manager
        diagnostics = await drone_manager.get_diagnostics(drone_id, include_logs)
        
        return {
            "drone_id": drone_id,
            "diagnostics": diagnostics,
            "generated_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagnostics for {drone_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get diagnostics: {str(e)}")

# Helper functions
def _convert_to_response(drone: Drone) -> DroneResponse:
    """Convert database drone to response model"""
    from ..models.drone import DroneCapabilities, TelemetryData, DroneHealth
    
    # Convert JSON fields back to Pydantic models
    capabilities = DroneCapabilities(**drone.capabilities) if drone.capabilities else None
    telemetry = TelemetryData(**drone.last_telemetry) if drone.last_telemetry else None
    health = DroneHealth(**drone.health_status) if drone.health_status else None
    
    return DroneResponse(
        id=drone.id,
        drone_id=drone.drone_id,
        name=drone.name,
        drone_type=DroneType(drone.drone_type),
        status=DroneStatus(drone.status),
        ip_address=drone.ip_address,
        port=drone.port,
        mac_address=drone.mac_address,
        capabilities=capabilities,
        current_mission_id=drone.current_mission_id,
        last_telemetry=telemetry,
        health_status=health,
        registered_at=drone.registered_at,
        last_seen=drone.last_seen,
        firmware_version=drone.firmware_version,
        hardware_version=drone.hardware_version,
        total_flight_time_minutes=drone.total_flight_time_minutes,
        total_missions=drone.total_missions,
        successful_missions=drone.successful_missions
    )

async def _register_discovered_drones(discovered_drones: List[dict], db: Session):
    """Register discovered drones in background"""
    try:
        for drone_info in discovered_drones:
            # Check if already registered
            existing = db.query(Drone).filter(Drone.drone_id == drone_info["drone_id"]).first()
            if not existing:
                # Create basic registration
                db_drone = Drone(
                    drone_id=drone_info["drone_id"],
                    name=drone_info.get("name", f"Drone {drone_info['drone_id']}"),
                    drone_type=drone_info.get("type", "quadcopter"),
                    ip_address=drone_info.get("ip_address"),
                    port=drone_info.get("port"),
                    status=DroneStatus.IDLE.value,
                    capabilities=drone_info.get("capabilities", {})
                )
                db.add(db_drone)
        
        db.commit()
        logger.info(f"Registered {len(discovered_drones)} discovered drones")
    except Exception as e:
        logger.error(f"Failed to register discovered drones: {str(e)}")
        db.rollback()

async def _send_drone_notification(event_type: str, drone: Drone, message: str):
    """Send drone notification"""
    try:
        priority = "urgent" if event_type == "emergency_stop" else "normal"
        await notification_service.create_notification(
            title=f"Drone {event_type.replace('_', ' ').title()}",
            message=message,
            notification_type="drone_update",
            priority=priority,
            metadata={
                "drone_id": drone.drone_id,
                "event_type": event_type,
                "drone_status": drone.status
            }
        )
    except Exception as e:
        logger.error(f"Failed to send drone notification: {str(e)}")

async def _send_health_alert(drone_id: str, health_status: DroneHealth):
    """Send health alert for critical issues"""
    try:
        await notification_service.create_notification(
            title="Drone Health Alert",
            message=f"Drone {drone_id} health status: {health_status.overall_status}",
            notification_type="health_alert",
            priority="urgent",
            metadata={
                "drone_id": drone_id,
                "health_status": health_status.overall_status,
                "issues": health_status.issues
            }
        )
    except Exception as e:
        logger.error(f"Failed to send health alert: {str(e)}")

async def _process_telemetry_analytics(drone_id: str, telemetry: TelemetryData):
    """Process telemetry for analytics in background"""
    try:
        # TODO: Implement telemetry analytics
        # - Performance tracking
        # - Pattern recognition
        # - Predictive maintenance
        logger.debug(f"Processing telemetry analytics for {drone_id}")
    except Exception as e:
        logger.error(f"Failed to process telemetry analytics: {str(e)}")

async def _log_command_execution(command_id: str, drone_id: str, command: DroneCommand, response: dict):
    """Log command execution for audit trail"""
    try:
        # TODO: Implement command logging
        logger.info(f"Command {command_id} sent to {drone_id}: {command.command_type}")
    except Exception as e:
        logger.error(f"Failed to log command execution: {str(e)}")