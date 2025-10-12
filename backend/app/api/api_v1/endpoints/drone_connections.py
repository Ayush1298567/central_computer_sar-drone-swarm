"""
Drone Connection Management API Endpoints
Provides REST API for managing drone connections and communication
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from app.communication.drone_connection_hub import drone_connection_hub
from app.auth.dependencies import role_required
from app.communication.drone_registry import (
    DroneInfo, DroneCapabilities, DroneConnectionType, DroneStatus,
    drone_registry
)
from app.core.database import get_db
from app.models.drone import Drone
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/connections", response_model=Dict[str, Any])
async def get_all_connections():
    """Get status of all drone connections"""
    try:
        connections = drone_connection_hub.get_all_connection_status()
        statistics = drone_connection_hub.get_hub_statistics()
        
        return {
            "success": True,
            "connections": connections,
            "statistics": statistics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{drone_id}", response_model=Dict[str, Any])
async def get_drone_connection(drone_id: str):
    """Get connection status for specific drone"""
    try:
        status = drone_connection_hub.get_connection_status(drone_id)
        if not status:
            raise HTTPException(status_code=404, detail="Drone connection not found")
        
        return {
            "success": True,
            "drone_id": drone_id,
            "connection_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drone connection {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/connect", response_model=Dict[str, Any])
async def connect_drone(connection_request: Dict[str, Any], _u=Depends(role_required("operator"))):
    """Connect to a drone"""
    try:
        # Validate required fields
        required_fields = ["drone_id", "connection_type", "connection_params"]
        for field in required_fields:
            if field not in connection_request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create drone info
        capabilities = DroneCapabilities(
            max_flight_time=connection_request.get("max_flight_time", 30),
            max_speed=connection_request.get("max_speed", 15.0),
            max_altitude=connection_request.get("max_altitude", 120.0),
            payload_capacity=connection_request.get("payload_capacity", 0.5),
            camera_resolution=connection_request.get("camera_resolution", "1080p"),
            has_thermal_camera=connection_request.get("has_thermal_camera", False),
            has_gimbal=connection_request.get("has_gimbal", False),
            has_rtk_gps=connection_request.get("has_rtk_gps", False),
            has_collision_avoidance=connection_request.get("has_collision_avoidance", False),
            has_return_to_home=connection_request.get("has_return_to_home", True),
            communication_range=connection_request.get("communication_range", 1000.0),
            battery_capacity=connection_request.get("battery_capacity", 5200.0),
            supported_commands=["takeoff", "land", "return_home", "emergency_stop"]
        )
        
        drone_info = DroneInfo(
            drone_id=connection_request["drone_id"],
            name=connection_request.get("name", f"Drone {connection_request['drone_id']}"),
            model=connection_request.get("model", "Unknown"),
            manufacturer=connection_request.get("manufacturer", "Unknown"),
            firmware_version=connection_request.get("firmware_version", "Unknown"),
            serial_number=connection_request.get("serial_number", "Unknown"),
            capabilities=capabilities,
            connection_type=DroneConnectionType(connection_request["connection_type"]),
            connection_params=connection_request["connection_params"],
            status=DroneStatus.DISCONNECTED,
            last_seen=datetime.utcnow(),
            battery_level=100.0,
            position={"lat": 0.0, "lon": 0.0, "alt": 0.0},
            heading=0.0,
            speed=0.0,
            signal_strength=0.0
        )
        
        # Register drone in registry
        if not drone_registry.register_drone(drone_info):
            raise HTTPException(status_code=400, detail="Failed to register drone")
        
        # Connect to drone
        success = await drone_connection_hub.connect_drone(drone_info)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully connected to drone {drone_info.drone_id}",
                "drone_info": {
                    "drone_id": drone_info.drone_id,
                    "name": drone_info.name,
                    "connection_type": drone_info.connection_type.value,
                    "status": drone_info.status.value
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Clean up registry entry
            drone_registry.unregister_drone(drone_info.drone_id)
            raise HTTPException(status_code=500, detail="Failed to establish connection")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to drone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{drone_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_drone(drone_id: str, _u=Depends(role_required("operator"))):
    """Disconnect from a drone"""
    try:
        # Find connection ID for drone
        connection_id = None
        for conn_id in drone_connection_hub.connections.keys():
            if conn_id.startswith(drone_id):
                connection_id = conn_id
                break
        
        if not connection_id:
            raise HTTPException(status_code=404, detail="Drone connection not found")
        
        # Disconnect drone
        success = await drone_connection_hub.disconnect_drone(connection_id)
        
        if success:
            # Unregister from registry
            drone_registry.unregister_drone(drone_id)
            
            return {
                "success": True,
                "message": f"Successfully disconnected from drone {drone_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to disconnect drone")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{drone_id}/command", response_model=Dict[str, Any])
async def send_drone_command(
    drone_id: str, 
    command_request: Dict[str, Any],
    _u=Depends(role_required("operator"))
):
    """Send command to a drone"""
    try:
        # Validate required fields
        if "command_type" not in command_request:
            raise HTTPException(status_code=400, detail="Missing required field: command_type")
        
        command_type = command_request["command_type"]
        parameters = command_request.get("parameters", {})
        priority = command_request.get("priority", 1)
        
        # Send command
        success = await drone_connection_hub.send_command(
            drone_id, command_type, parameters, priority
        )
        
        if success:
            return {
                "success": True,
                "message": f"Command {command_type} sent to drone {drone_id}",
                "command": {
                    "drone_id": drone_id,
                    "command_type": command_type,
                    "parameters": parameters,
                    "priority": priority
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send command")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending command to drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{drone_id}/telemetry", response_model=Dict[str, Any])
async def request_telemetry(drone_id: str, _u=Depends(role_required("operator"))):
    """Request telemetry from a drone"""
    try:
        success = await drone_connection_hub.request_telemetry(drone_id)
        
        if success:
            return {
                "success": True,
                "message": f"Telemetry request sent to drone {drone_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to request telemetry")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting telemetry from drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drones", response_model=Dict[str, Any])
async def get_all_drones():
    """Get all registered drones"""
    try:
        all_drones = drone_registry.get_all_drones()
        connected_drones = drone_registry.get_drones_by_status(DroneStatus.CONNECTED)
        available_drones = drone_registry.get_available_drones()
        
        # Convert to serializable format
        def serialize_drone(drone_info: DroneInfo) -> Dict:
            return {
                "drone_id": drone_info.drone_id,
                "name": drone_info.name,
                "model": drone_info.model,
                "manufacturer": drone_info.manufacturer,
                "firmware_version": drone_info.firmware_version,
                "serial_number": drone_info.serial_number,
                "capabilities": {
                    "max_flight_time": drone_info.capabilities.max_flight_time,
                    "max_speed": drone_info.capabilities.max_speed,
                    "max_altitude": drone_info.capabilities.max_altitude,
                    "payload_capacity": drone_info.capabilities.payload_capacity,
                    "camera_resolution": drone_info.capabilities.camera_resolution,
                    "has_thermal_camera": drone_info.capabilities.has_thermal_camera,
                    "has_gimbal": drone_info.capabilities.has_gimbal,
                    "has_rtk_gps": drone_info.capabilities.has_rtk_gps,
                    "has_collision_avoidance": drone_info.capabilities.has_collision_avoidance,
                    "has_return_to_home": drone_info.capabilities.has_return_to_home,
                    "communication_range": drone_info.capabilities.communication_range,
                    "battery_capacity": drone_info.capabilities.battery_capacity,
                    "supported_commands": drone_info.capabilities.supported_commands
                },
                "connection_type": drone_info.connection_type.value,
                "status": drone_info.status.value,
                "last_seen": drone_info.last_seen.isoformat(),
                "battery_level": drone_info.battery_level,
                "position": drone_info.position,
                "heading": drone_info.heading,
                "speed": drone_info.speed,
                "signal_strength": drone_info.signal_strength,
                "current_mission_id": drone_info.current_mission_id,
                "assigned_operator": drone_info.assigned_operator
            }
        
        return {
            "success": True,
            "drones": {
                "all": [serialize_drone(drone) for drone in all_drones],
                "connected": [serialize_drone(drone) for drone in connected_drones],
                "available": [serialize_drone(drone) for drone in available_drones]
            },
            "statistics": drone_registry.get_connection_statistics(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting drones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drones/{drone_id}", response_model=Dict[str, Any])
async def get_drone_info(drone_id: str):
    """Get information for specific drone"""
    try:
        drone_info = drone_registry.get_drone(drone_id)
        if not drone_info:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        # Get connection status
        connection_status = drone_connection_hub.get_connection_status(drone_id)
        
        # Serialize drone info
        drone_data = {
            "drone_id": drone_info.drone_id,
            "name": drone_info.name,
            "model": drone_info.model,
            "manufacturer": drone_info.manufacturer,
            "firmware_version": drone_info.firmware_version,
            "serial_number": drone_info.serial_number,
            "capabilities": {
                "max_flight_time": drone_info.capabilities.max_flight_time,
                "max_speed": drone_info.capabilities.max_speed,
                "max_altitude": drone_info.capabilities.max_altitude,
                "payload_capacity": drone_info.capabilities.payload_capacity,
                "camera_resolution": drone_info.capabilities.camera_resolution,
                "has_thermal_camera": drone_info.capabilities.has_thermal_camera,
                "has_gimbal": drone_info.capabilities.has_gimbal,
                "has_rtk_gps": drone_info.capabilities.has_rtk_gps,
                "has_collision_avoidance": drone_info.capabilities.has_collision_avoidance,
                "has_return_to_home": drone_info.capabilities.has_return_to_home,
                "communication_range": drone_info.capabilities.communication_range,
                "battery_capacity": drone_info.capabilities.battery_capacity,
                "supported_commands": drone_info.capabilities.supported_commands
            },
            "connection_type": drone_info.connection_type.value,
            "connection_params": drone_info.connection_params,
            "status": drone_info.status.value,
            "last_seen": drone_info.last_seen.isoformat(),
            "battery_level": drone_info.battery_level,
            "position": drone_info.position,
            "heading": drone_info.heading,
            "speed": drone_info.speed,
            "signal_strength": drone_info.signal_strength,
            "current_mission_id": drone_info.current_mission_id,
            "assigned_operator": drone_info.assigned_operator,
            "maintenance_due": drone_info.maintenance_due.isoformat() if drone_info.maintenance_due else None
        }
        
        return {
            "success": True,
            "drone": drone_data,
            "connection_status": connection_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drone info {drone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/discovery/status", response_model=Dict[str, Any])
async def get_discovery_status():
    """Get drone discovery status"""
    try:
        statistics = drone_registry.get_connection_statistics()
        
        return {
            "success": True,
            "discovery_active": statistics["discovery_active"],
            "total_drones": statistics["total_drones"],
            "by_status": statistics["by_status"],
            "by_connection_type": statistics["by_connection_type"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting discovery status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discovery/start", response_model=Dict[str, Any])
async def start_discovery():
    """Start drone discovery"""
    try:
        await drone_registry.start_discovery()
        
        return {
            "success": True,
            "message": "Drone discovery started",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discovery/stop", response_model=Dict[str, Any])
async def stop_discovery():
    """Stop drone discovery"""
    try:
        await drone_registry.stop_discovery()
        
        return {
            "success": True,
            "message": "Drone discovery stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))
