"""
Real-time operations API endpoints for live tracking, video monitoring, and emergency response.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from ..core.database import get_db
from ..core.websocket_manager import ConnectionManager
from ..services.real_time_service import RealTimeService

router = APIRouter()

# Initialize services
real_time_service = RealTimeService()
connection_manager = ConnectionManager()

@router.websocket("/mission-tracking/{mission_id}")
async def mission_tracking_websocket(websocket: WebSocket, mission_id: str):
    """WebSocket endpoint for real-time mission tracking."""
    client_id = f"mission_track_{mission_id}_{datetime.utcnow().timestamp()}"
    await connection_manager.connect(websocket, client_id)
    
    try:
        # Join mission tracking room
        connection_manager.join_room(client_id, f"mission_{mission_id}")
        
        # Send initial mission status
        initial_status = await real_time_service.get_mission_status(mission_id)
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "mission_status",
                "data": initial_status,
                "timestamp": datetime.utcnow().isoformat()
            }),
            client_id
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_tracking_message(message, client_id, mission_id)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        print(f"Mission tracking WebSocket error: {e}")
        connection_manager.disconnect(client_id)

@router.websocket("/drone-telemetry/{drone_id}")
async def drone_telemetry_websocket(websocket: WebSocket, drone_id: str):
    """WebSocket endpoint for real-time drone telemetry."""
    client_id = f"drone_telemetry_{drone_id}_{datetime.utcnow().timestamp()}"
    await connection_manager.connect(websocket, client_id)
    
    try:
        # Join drone telemetry room
        connection_manager.join_room(client_id, f"drone_{drone_id}")
        
        # Send initial drone status
        initial_status = await real_time_service.get_drone_telemetry(drone_id)
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "drone_telemetry",
                "data": initial_status,
                "timestamp": datetime.utcnow().isoformat()
            }),
            client_id
        )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_telemetry_message(message, client_id, drone_id)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        print(f"Drone telemetry WebSocket error: {e}")
        connection_manager.disconnect(client_id)

@router.websocket("/video-stream/{drone_id}")
async def video_stream_websocket(websocket: WebSocket, drone_id: str):
    """WebSocket endpoint for real-time video streaming."""
    client_id = f"video_stream_{drone_id}_{datetime.utcnow().timestamp()}"
    await connection_manager.connect(websocket, client_id)
    
    try:
        # Join video stream room
        connection_manager.join_room(client_id, f"video_{drone_id}")
        
        # Start video streaming
        await real_time_service.start_video_stream(drone_id, client_id)
        
        while True:
            # Handle video stream control messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_video_message(message, client_id, drone_id)
            
    except WebSocketDisconnect:
        await real_time_service.stop_video_stream(drone_id, client_id)
        connection_manager.disconnect(client_id)
    except Exception as e:
        print(f"Video stream WebSocket error: {e}")
        await real_time_service.stop_video_stream(drone_id, client_id)
        connection_manager.disconnect(client_id)

@router.post("/emergency-alert", response_model=Dict[str, Any])
async def trigger_emergency_alert(
    alert_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger an emergency alert and broadcast to all operators."""
    try:
        alert_type = alert_data.get("type", "general")
        message = alert_data.get("message", "Emergency situation detected")
        mission_id = alert_data.get("mission_id")
        drone_id = alert_data.get("drone_id")
        severity = alert_data.get("severity", "high")
        
        # Process emergency alert
        alert_result = await real_time_service.process_emergency_alert(
            alert_type, message, mission_id, drone_id, severity
        )
        
        # Broadcast to all connected clients
        alert_broadcast = {
            "type": "emergency_alert",
            "alert": alert_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await connection_manager.broadcast(json.dumps(alert_broadcast))
        
        # Schedule emergency response procedures
        background_tasks.add_task(execute_emergency_procedures, alert_result)
        
        return {
            "success": True,
            "alert_id": alert_result.get("alert_id"),
            "message": "Emergency alert triggered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger emergency alert: {str(e)}")

@router.post("/discovery-notification", response_model=Dict[str, Any])
async def notify_discovery(
    discovery_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Notify operators of a new discovery."""
    try:
        discovery_id = discovery_data.get("discovery_id")
        mission_id = discovery_data.get("mission_id")
        drone_id = discovery_data.get("drone_id")
        confidence = discovery_data.get("confidence", 0.5)
        
        if not discovery_id:
            raise HTTPException(status_code=400, detail="discovery_id is required")
        
        # Process discovery notification
        notification = await real_time_service.process_discovery_notification(discovery_data)
        
        # Broadcast to mission room
        if mission_id:
            await connection_manager.broadcast_to_room(
                f"mission_{mission_id}",
                json.dumps({
                    "type": "discovery_notification",
                    "discovery": notification,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
        
        # Schedule discovery analysis if high confidence
        if confidence > 0.7:
            background_tasks.add_task(analyze_high_confidence_discovery, discovery_id)
        
        return {
            "success": True,
            "notification_id": notification.get("notification_id"),
            "message": "Discovery notification sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to notify discovery: {str(e)}")

@router.get("/mission-status/{mission_id}", response_model=Dict[str, Any])
async def get_real_time_mission_status(mission_id: str, db: Session = Depends(get_db)):
    """Get real-time mission status and progress."""
    try:
        status = await real_time_service.get_mission_status(mission_id)
        if not status:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return {
            "success": True,
            "mission_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission status: {str(e)}")

@router.get("/drone-telemetry/{drone_id}", response_model=Dict[str, Any])
async def get_drone_telemetry(drone_id: str, db: Session = Depends(get_db)):
    """Get current drone telemetry data."""
    try:
        telemetry = await real_time_service.get_drone_telemetry(drone_id)
        if not telemetry:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "success": True,
            "telemetry": telemetry,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drone telemetry: {str(e)}")

@router.post("/override-command", response_model=Dict[str, Any])
async def emergency_override_command(
    override_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send emergency override command to drone or mission."""
    try:
        target_type = override_data.get("target_type")  # "drone" or "mission"
        target_id = override_data.get("target_id")
        command = override_data.get("command")
        reason = override_data.get("reason", "Emergency override")
        operator = override_data.get("operator", "System")
        
        if not all([target_type, target_id, command]):
            raise HTTPException(status_code=400, detail="target_type, target_id, and command are required")
        
        # Execute override command
        result = await real_time_service.execute_override_command(
            target_type, target_id, command, reason, operator
        )
        
        # Broadcast override notification
        override_notification = {
            "type": "emergency_override",
            "target_type": target_type,
            "target_id": target_id,
            "command": command,
            "reason": reason,
            "operator": operator,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await connection_manager.broadcast(json.dumps(override_notification))
        
        # Monitor override execution
        background_tasks.add_task(monitor_override_execution, target_type, target_id, result.get("override_id"))
        
        return {
            "success": True,
            "override_id": result.get("override_id"),
            "message": "Emergency override command sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute override command: {str(e)}")

@router.get("/active-alerts", response_model=List[Dict[str, Any]])
async def get_active_alerts(db: Session = Depends(get_db)):
    """Get all active emergency alerts."""
    try:
        alerts = await real_time_service.get_active_alerts()
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active alerts: {str(e)}")

@router.post("/acknowledge-alert/{alert_id}", response_model=Dict[str, Any])
async def acknowledge_alert(
    alert_id: str,
    acknowledgment_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Acknowledge an emergency alert."""
    try:
        operator = acknowledgment_data.get("operator", "Unknown")
        notes = acknowledgment_data.get("notes", "")
        
        result = await real_time_service.acknowledge_alert(alert_id, operator, notes)
        if not result:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Broadcast acknowledgment
        await connection_manager.broadcast(json.dumps({
            "type": "alert_acknowledged",
            "alert_id": alert_id,
            "operator": operator,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return {
            "success": True,
            "message": "Alert acknowledged successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/system-health", response_model=Dict[str, Any])
async def get_system_health():
    """Get overall system health status."""
    try:
        health = await real_time_service.get_system_health()
        
        return {
            "success": True,
            "system_health": health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@router.get("/connection-stats", response_model=Dict[str, Any])
async def get_connection_statistics():
    """Get WebSocket connection statistics."""
    try:
        stats = connection_manager.get_system_stats()
        
        return {
            "success": True,
            "connection_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection stats: {str(e)}")

# WebSocket message handlers
async def handle_tracking_message(message: Dict[str, Any], client_id: str, mission_id: str):
    """Handle mission tracking WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "request_update":
        # Send current mission status
        status = await real_time_service.get_mission_status(mission_id)
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "mission_status",
                "data": status,
                "timestamp": datetime.utcnow().isoformat()
            }),
            client_id
        )
    
    elif message_type == "subscribe_discoveries":
        # Subscribe to discovery notifications for this mission
        connection_manager.join_room(client_id, f"discoveries_{mission_id}")

async def handle_telemetry_message(message: Dict[str, Any], client_id: str, drone_id: str):
    """Handle drone telemetry WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "request_telemetry":
        # Send current telemetry
        telemetry = await real_time_service.get_drone_telemetry(drone_id)
        await connection_manager.send_personal_message(
            json.dumps({
                "type": "drone_telemetry",
                "data": telemetry,
                "timestamp": datetime.utcnow().isoformat()
            }),
            client_id
        )
    
    elif message_type == "set_update_rate":
        # Adjust telemetry update rate
        rate = message.get("rate", 1.0)
        await real_time_service.set_telemetry_rate(drone_id, client_id, rate)

async def handle_video_message(message: Dict[str, Any], client_id: str, drone_id: str):
    """Handle video stream WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "adjust_quality":
        quality = message.get("quality", "medium")
        await real_time_service.adjust_video_quality(drone_id, client_id, quality)
    
    elif message_type == "request_snapshot":
        await real_time_service.capture_video_snapshot(drone_id, client_id)
    
    elif message_type == "start_recording":
        await real_time_service.start_video_recording(drone_id, client_id)
    
    elif message_type == "stop_recording":
        await real_time_service.stop_video_recording(drone_id, client_id)

# Background task functions
async def execute_emergency_procedures(alert_data: Dict[str, Any]):
    """Execute emergency response procedures."""
    try:
        alert_type = alert_data.get("type")
        severity = alert_data.get("severity")
        
        # Execute appropriate emergency procedures based on alert type
        if alert_type == "drone_malfunction":
            await handle_drone_malfunction_emergency(alert_data)
        elif alert_type == "weather_emergency":
            await handle_weather_emergency(alert_data)
        elif alert_type == "communication_loss":
            await handle_communication_loss_emergency(alert_data)
        
    except Exception as e:
        print(f"Emergency procedures execution failed: {e}")

async def analyze_high_confidence_discovery(discovery_id: str):
    """Analyze high confidence discovery for immediate action."""
    try:
        # This would typically:
        # 1. Run additional AI analysis
        # 2. Generate detailed reports
        # 3. Notify relevant authorities
        # 4. Coordinate ground response
        pass
    except Exception as e:
        print(f"High confidence discovery analysis failed: {e}")

async def monitor_override_execution(target_type: str, target_id: str, override_id: str):
    """Monitor emergency override command execution."""
    try:
        # This would typically:
        # 1. Track command execution status
        # 2. Ensure compliance with override
        # 3. Handle non-compliance scenarios
        # 4. Update operators on progress
        pass
    except Exception as e:
        print(f"Override monitoring failed: {e}")

async def handle_drone_malfunction_emergency(alert_data: Dict[str, Any]):
    """Handle drone malfunction emergency procedures."""
    # Implementation for drone malfunction response
    pass

async def handle_weather_emergency(alert_data: Dict[str, Any]):
    """Handle weather emergency procedures."""
    # Implementation for weather emergency response
    pass

async def handle_communication_loss_emergency(alert_data: Dict[str, Any]):
    """Handle communication loss emergency procedures."""
    # Implementation for communication loss response
    pass