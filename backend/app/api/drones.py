"""
Drone API endpoints for SAR Mission Commander
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ..services.drone_manager import drone_manager, DroneCommand, DroneCommandType
from ..services.emergency_service import emergency_service
from ..models.drone import Drone, DroneStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/drones", tags=["drones"])

# Pydantic models for API
class DroneRegistration(BaseModel):
    drone_id: str
    capabilities: Dict[str, Any]
    name: Optional[str] = None

class TelemetryUpdate(BaseModel):
    drone_id: str
    position: Dict[str, float]  # lat, lon, alt
    battery_level: float
    speed: float
    heading: float
    signal_strength: float
    gps_accuracy: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None

class DroneCommandRequest(BaseModel):
    drone_id: str
    command_type: str
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 1

class DroneResponse(BaseModel):
    id: str
    name: str
    status: str
    battery_level: float
    position: Dict[str, float]
    altitude: float
    speed: float
    heading: float
    mission_id: Optional[str]
    last_update: str
    capabilities: Dict[str, Any]

@router.get("/", response_model=List[DroneResponse])
async def get_all_drones():
    """Get all connected drones"""
    try:
        drones = drone_manager.get_all_drones()
        return [
            DroneResponse(
                id=drone["id"],
                name=drone.get("name", f"Drone-{drone['id']}"),
                status=drone["status"].value if hasattr(drone["status"], 'value') else str(drone["status"]),
                battery_level=drone["battery_level"],
                position=drone["position"],
                altitude=drone["position"]["altitude"],
                speed=drone["speed"],
                heading=drone["heading"],
                mission_id=drone.get("current_mission"),
                last_update=drone["last_heartbeat"].isoformat() if isinstance(drone["last_heartbeat"], datetime) else str(drone["last_heartbeat"]),
                capabilities=drone["capabilities"]
            )
            for drone in drones
        ]
    except Exception as e:
        logger.error(f"Failed to get drones: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drones")

@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str):
    """Get specific drone by ID"""
    try:
        drone_data = drone_manager.get_drone_status(drone_id)
        if not drone_data:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return DroneResponse(
            id=drone_data["id"],
            name=drone_data.get("name", f"Drone-{drone_data['id']}"),
            status=drone_data["status"].value if hasattr(drone_data["status"], 'value') else str(drone_data["status"]),
            battery_level=drone_data["battery_level"],
            position=drone_data["position"],
            altitude=drone_data["position"]["altitude"],
            speed=drone_data["speed"],
            heading=drone_data["heading"],
            mission_id=drone_data.get("current_mission"),
            last_update=drone_data["last_heartbeat"].isoformat() if isinstance(drone_data["last_heartbeat"], datetime) else str(drone_data["last_heartbeat"]),
            capabilities=drone_data["capabilities"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drone")

@router.post("/register")
async def register_drone(registration: DroneRegistration):
    """Register a new drone"""
    try:
        success = await drone_manager.register_drone(
            registration.drone_id,
            registration.capabilities
        )
        
        if success:
            return {"message": "Drone registered successfully", "drone_id": registration.drone_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to register drone")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register drone: {e}")
        raise HTTPException(status_code=500, detail="Failed to register drone")

@router.post("/{drone_id}/unregister")
async def unregister_drone(drone_id: str):
    """Unregister a drone"""
    try:
        success = await drone_manager.unregister_drone(drone_id)
        
        if success:
            return {"message": "Drone unregistered successfully", "drone_id": drone_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to unregister drone")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unregister drone")

@router.post("/{drone_id}/telemetry")
async def update_telemetry(drone_id: str, telemetry: TelemetryUpdate):
    """Update drone telemetry data"""
    try:
        from ..services.drone_manager import TelemetryData
        
        telemetry_data = TelemetryData(
            drone_id=drone_id,
            timestamp=datetime.utcnow(),
            position=telemetry.position,
            battery_level=telemetry.battery_level,
            speed=telemetry.speed,
            heading=telemetry.heading,
            signal_strength=telemetry.signal_strength,
            gps_accuracy=telemetry.gps_accuracy,
            temperature=telemetry.temperature,
            humidity=telemetry.humidity,
            wind_speed=telemetry.wind_speed
        )
        
        success = await drone_manager.update_telemetry(drone_id, telemetry_data)
        
        if success:
            return {"message": "Telemetry updated successfully", "drone_id": drone_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to update telemetry")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update telemetry for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update telemetry")

@router.post("/{drone_id}/command")
async def send_command(drone_id: str, command_request: DroneCommandRequest):
    """Send command to drone"""
    try:
        # Map command type string to enum
        command_type_map = {
            "start_mission": DroneCommandType.START_MISSION,
            "return_home": DroneCommandType.RETURN_HOME,
            "land": DroneCommandType.LAND,
            "emergency_stop": DroneCommandType.EMERGENCY_STOP,
            "update_altitude": DroneCommandType.UPDATE_ALTITUDE,
            "change_heading": DroneCommandType.CHANGE_HEADING,
            "enable_autonomous": DroneCommandType.ENABLE_AUTONOMOUS,
            "disable_autonomous": DroneCommandType.DISABLE_AUTONOMOUS,
        }
        
        command_type = command_type_map.get(command_request.command_type)
        if not command_type:
            raise HTTPException(status_code=400, detail=f"Invalid command type: {command_request.command_type}")
        
        command = DroneCommand(
            drone_id=drone_id,
            command_type=command_type,
            parameters=command_request.parameters,
            priority=command_request.priority
        )
        
        success = await drone_manager.send_command(command)
        
        if success:
            return {"message": "Command sent successfully", "drone_id": drone_id, "command": command_request.command_type}
        else:
            raise HTTPException(status_code=400, detail="Failed to send command")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send command to drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send command")

@router.get("/{drone_id}/telemetry/history")
async def get_telemetry_history(drone_id: str, limit: int = 100):
    """Get telemetry history for a drone"""
    try:
        history = drone_manager.telemetry_history.get(drone_id, [])
        
        # Limit the results
        limited_history = history[-limit:] if limit > 0 else history
        
        return {
            "drone_id": drone_id,
            "telemetry_history": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "position": t.position,
                    "battery_level": t.battery_level,
                    "speed": t.speed,
                    "heading": t.heading,
                    "signal_strength": t.signal_strength,
                    "gps_accuracy": t.gps_accuracy,
                    "temperature": t.temperature,
                    "humidity": t.humidity,
                    "wind_speed": t.wind_speed
                }
                for t in limited_history
            ],
            "total_records": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get telemetry history for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve telemetry history")

@router.get("/available/list")
async def get_available_drones():
    """Get list of available drones for mission assignment"""
    try:
        available_drones = drone_manager.get_available_drones()
        
        return {
            "available_drones": [
                {
                    "id": drone["id"],
                    "name": drone.get("name", f"Drone-{drone['id']}"),
                    "status": drone["status"].value if hasattr(drone["status"], 'value') else str(drone["status"]),
                    "battery_level": drone["battery_level"],
                    "capabilities": drone["capabilities"]
                }
                for drone in available_drones
            ],
            "count": len(available_drones)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available drones: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available drones")

@router.post("/emergency/stop-all")
async def emergency_stop_all():
    """Emergency stop all drones"""
    try:
        success = await emergency_service.emergency_stop_all()
        
        if success:
            return {"message": "Emergency stop activated for all drones"}
        else:
            raise HTTPException(status_code=500, detail="Failed to execute emergency stop")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute emergency stop: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute emergency stop")

@router.get("/status/fleet")
async def get_fleet_status():
    """Get overall fleet status"""
    try:
        all_drones = drone_manager.get_all_drones()
        
        # Calculate fleet statistics
        total_drones = len(all_drones)
        active_drones = len([d for d in all_drones if d["status"] in ["mission", "returning"]])
        idle_drones = len([d for d in all_drones if d["status"] == "idle"])
        charging_drones = len([d for d in all_drones if d["status"] == "charging"])
        error_drones = len([d for d in all_drones if d["status"] == "error"])
        
        # Calculate average battery level
        avg_battery = 0
        if all_drones:
            avg_battery = sum([d["battery_level"] for d in all_drones]) / len(all_drones)
        
        return {
            "fleet_summary": {
                "total_drones": total_drones,
                "active_drones": active_drones,
                "idle_drones": idle_drones,
                "charging_drones": charging_drones,
                "error_drones": error_drones,
                "average_battery_level": round(avg_battery, 2)
            },
            "drones": [
                {
                    "id": drone["id"],
                    "name": drone.get("name", f"Drone-{drone['id']}"),
                    "status": drone["status"].value if hasattr(drone["status"], 'value') else str(drone["status"]),
                    "battery_level": drone["battery_level"],
                    "mission_id": drone.get("current_mission")
                }
                for drone in all_drones
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get fleet status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fleet status")
