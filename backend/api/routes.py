"""
FastAPI routes for SAR Drone Central Computer System
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db_session, db_service
from ..services.websocket_manager import WebSocketManager
from ..services.ollama_service import ollama_service
from ..agents.agent_manager import AgentManager

logger = logging.getLogger(__name__)

# Global instances (will be injected)
websocket_manager: Optional[WebSocketManager] = None
agent_manager: Optional[AgentManager] = None

def set_global_instances(ws_manager: WebSocketManager, ag_manager: AgentManager):
    """Set global instances for dependency injection"""
    global websocket_manager, agent_manager
    websocket_manager = ws_manager
    agent_manager = ag_manager

router = APIRouter()

# Health and Status Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/status")
async def system_status():
    """Get system status"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not available")
    
    try:
        health = await agent_manager.get_system_health()
        return {
            "status": "operational" if health["health_score"] > 80 else "degraded",
            "health_score": health["health_score"],
            "agents": health["agent_details"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Error getting system status")

# Mission Management Endpoints
@router.post("/missions")
async def create_mission(
    name: str,
    description: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new mission"""
    try:
        mission = await db_service.create_mission(name, description)
        return {
            "id": mission.id,
            "name": mission.name,
            "description": mission.description,
            "status": mission.status,
            "created_at": mission.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating mission: {e}")
        raise HTTPException(status_code=500, detail="Error creating mission")

@router.get("/missions")
async def get_missions(db: AsyncSession = Depends(get_db_session)):
    """Get all missions"""
    try:
        from ..services.database import Mission
        from sqlalchemy import select
        
        result = await db.execute(select(Mission).order_by(Mission.created_at.desc()))
        missions = result.scalars().all()
        
        return [
            {
                "id": mission.id,
                "name": mission.name,
                "description": mission.description,
                "status": mission.status,
                "created_at": mission.created_at.isoformat(),
                "started_at": mission.started_at.isoformat() if mission.started_at else None,
                "completed_at": mission.completed_at.isoformat() if mission.completed_at else None
            }
            for mission in missions
        ]
    except Exception as e:
        logger.error(f"Error getting missions: {e}")
        raise HTTPException(status_code=500, detail="Error getting missions")

@router.get("/missions/{mission_id}")
async def get_mission(mission_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get specific mission"""
    try:
        mission = await db_service.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return {
            "id": mission.id,
            "name": mission.name,
            "description": mission.description,
            "status": mission.status,
            "search_area_json": mission.search_area_json,
            "conversation_context": mission.conversation_context,
            "mission_plan": mission.mission_plan,
            "created_at": mission.created_at.isoformat(),
            "started_at": mission.started_at.isoformat() if mission.started_at else None,
            "completed_at": mission.completed_at.isoformat() if mission.completed_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting mission")

@router.post("/missions/{mission_id}/start")
async def start_mission(mission_id: int):
    """Start a mission"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        # Send start request to task assignment agent
        await agent_manager.send_message_to_agent(
            "task_assignment",
            "mission.start_request",
            {
                "mission_id": mission_id,
                "session_id": f"mission_{mission_id}"
            }
        )
        
        return {"message": "Mission start request sent", "mission_id": mission_id}
    except Exception as e:
        logger.error(f"Error starting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error starting mission")

@router.post("/missions/{mission_id}/pause")
async def pause_mission(mission_id: int):
    """Pause a mission"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        # Send pause request to task assignment agent
        await agent_manager.send_message_to_agent(
            "task_assignment",
            "mission.pause_request",
            {
                "mission_id": mission_id,
                "session_id": f"mission_{mission_id}"
            }
        )
        
        return {"message": "Mission pause request sent", "mission_id": mission_id}
    except Exception as e:
        logger.error(f"Error pausing mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error pausing mission")

@router.post("/missions/{mission_id}/resume")
async def resume_mission(mission_id: int):
    """Resume a mission"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        # Send resume request to task assignment agent
        await agent_manager.send_message_to_agent(
            "task_assignment",
            "mission.resume_request",
            {
                "mission_id": mission_id,
                "session_id": f"mission_{mission_id}"
            }
        )
        
        return {"message": "Mission resume request sent", "mission_id": mission_id}
    except Exception as e:
        logger.error(f"Error resuming mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error resuming mission")

# Drone Management Endpoints
@router.post("/drones")
async def create_drone(
    name: str,
    capabilities: Dict[str, Any],
    battery_capacity: int = 5000,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new drone"""
    try:
        drone = await db_service.create_drone(name, capabilities, battery_capacity)
        return {
            "id": drone.id,
            "name": drone.name,
            "capabilities": capabilities,
            "battery_capacity": drone.battery_capacity,
            "status": drone.status,
            "created_at": drone.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating drone: {e}")
        raise HTTPException(status_code=500, detail="Error creating drone")

@router.get("/drones")
async def get_drones(db: AsyncSession = Depends(get_db_session)):
    """Get all drones"""
    try:
        drones = await db_service.get_all_drones()
        return [
            {
                "id": drone.id,
                "name": drone.name,
                "capabilities": json.loads(drone.capabilities_json) if drone.capabilities_json else {},
                "battery_capacity": drone.battery_capacity,
                "status": drone.status,
                "current_lat": drone.current_lat,
                "current_lng": drone.current_lng,
                "current_alt": drone.current_alt,
                "battery_percent": drone.battery_percent,
                "created_at": drone.created_at.isoformat(),
                "last_seen": drone.last_seen.isoformat()
            }
            for drone in drones
        ]
    except Exception as e:
        logger.error(f"Error getting drones: {e}")
        raise HTTPException(status_code=500, detail="Error getting drones")

@router.get("/drones/{drone_id}")
async def get_drone(drone_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get specific drone"""
    try:
        from ..services.database import Drone
        from sqlalchemy import select
        
        result = await db.execute(select(Drone).where(Drone.id == drone_id))
        drone = result.scalar_one_or_none()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        return {
            "id": drone.id,
            "name": drone.name,
            "capabilities": json.loads(drone.capabilities_json) if drone.capabilities_json else {},
            "battery_capacity": drone.battery_capacity,
            "status": drone.status,
            "current_lat": drone.current_lat,
            "current_lng": drone.current_lng,
            "current_alt": drone.current_alt,
            "battery_percent": drone.battery_percent,
            "created_at": drone.created_at.isoformat(),
            "last_seen": drone.last_seen.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting drone")

@router.put("/drones/{drone_id}")
async def update_drone(
    drone_id: int,
    name: str = None,
    capabilities: Dict[str, Any] = None,
    battery_capacity: int = None,
    status: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Update drone"""
    try:
        from ..services.database import Drone
        from sqlalchemy import select
        
        result = await db.execute(select(Drone).where(Drone.id == drone_id))
        drone = result.scalar_one_or_none()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        if name:
            drone.name = name
        if capabilities:
            drone.capabilities_json = json.dumps(capabilities)
        if battery_capacity:
            drone.battery_capacity = battery_capacity
        if status:
            drone.status = status
        
        await db.commit()
        await db.refresh(drone)
        
        return {
            "id": drone.id,
            "name": drone.name,
            "capabilities": json.loads(drone.capabilities_json) if drone.capabilities_json else {},
            "battery_capacity": drone.battery_capacity,
            "status": drone.status,
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating drone")

@router.delete("/drones/{drone_id}")
async def delete_drone(drone_id: int, db: AsyncSession = Depends(get_db_session)):
    """Delete drone"""
    try:
        from ..services.database import Drone
        from sqlalchemy import select
        
        result = await db.execute(select(Drone).where(Drone.id == drone_id))
        drone = result.scalar_one_or_none()
        
        if not drone:
            raise HTTPException(status_code=404, detail="Drone not found")
        
        await db.delete(drone)
        await db.commit()
        
        return {"message": "Drone deleted successfully", "drone_id": drone_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting drone")

# Mission Planning Endpoints
@router.post("/mission-planning/start")
async def start_mission_planning(
    description: str,
    session_id: str = None
):
    """Start mission planning conversation"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        if not session_id:
            session_id = f"session_{asyncio.get_event_loop().time()}"
        
        # Send mission intent to NLP agent
        await agent_manager.send_message_to_agent(
            "nlp_agent",
            "user.input",
            {
                "input": description,
                "session_id": session_id
            }
        )
        
        return {
            "message": "Mission planning started",
            "session_id": session_id,
            "description": description
        }
    except Exception as e:
        logger.error(f"Error starting mission planning: {e}")
        raise HTTPException(status_code=500, detail="Error starting mission planning")

@router.post("/mission-planning/respond")
async def respond_to_question(
    session_id: str,
    response: str
):
    """Respond to mission planning question"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        # Send response to conversation orchestrator
        await agent_manager.send_message_to_agent(
            "conversation_orchestrator",
            "mission.user_response",
            {
                "session_id": session_id,
                "response": response
            }
        )
        
        return {
            "message": "Response received",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        raise HTTPException(status_code=500, detail="Error processing response")

@router.get("/mission-planning/status/{session_id}")
async def get_planning_status(session_id: str):
    """Get mission planning status"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        orchestrator = agent_manager.get_agent("conversation_orchestrator")
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Conversation orchestrator not available")
        
        status = orchestrator.get_conversation_status(session_id)
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting planning status: {e}")
        raise HTTPException(status_code=500, detail="Error getting planning status")

# Command Endpoints
@router.post("/commands/send")
async def send_command(
    command: str,
    drone_id: int = None,
    session_id: str = None
):
    """Send command to drone(s)"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        if not session_id:
            session_id = f"session_{asyncio.get_event_loop().time()}"
        
        # Send command to command dispatcher
        await agent_manager.send_message_to_agent(
            "command_dispatcher",
            "command.drone_control",
            {
                "command": {"target_drones": [drone_id] if drone_id else "all"},
                "user_input": command,
                "session_id": session_id
            }
        )
        
        return {
            "message": "Command sent",
            "command": command,
            "drone_id": drone_id,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        raise HTTPException(status_code=500, detail="Error sending command")

@router.post("/commands/emergency")
async def emergency_command(
    command: str,
    session_id: str = None
):
    """Send emergency command"""
    try:
        if not agent_manager:
            raise HTTPException(status_code=503, detail="Agent manager not available")
        
        if not session_id:
            session_id = f"emergency_{asyncio.get_event_loop().time()}"
        
        # Send emergency command
        await agent_manager.send_message_to_agent(
            "command_dispatcher",
            "command.emergency",
            {
                "command": {"action": "emergency_stop", "target_drones": "all"},
                "user_input": command,
                "session_id": session_id
            }
        )
        
        return {
            "message": "Emergency command sent",
            "command": command,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error sending emergency command: {e}")
        raise HTTPException(status_code=500, detail="Error sending emergency command")

# Telemetry Endpoints
@router.get("/telemetry/drone/{drone_id}")
async def get_drone_telemetry(
    drone_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get telemetry data for specific drone"""
    try:
        from ..services.database import Telemetry
        from sqlalchemy import select, desc
        
        result = await db.execute(
            select(Telemetry)
            .where(Telemetry.drone_id == drone_id)
            .order_by(desc(Telemetry.timestamp))
            .limit(limit)
        )
        telemetry_records = result.scalars().all()
        
        return [
            {
                "id": record.id,
                "drone_id": record.drone_id,
                "mission_id": record.mission_id,
                "timestamp": record.timestamp.isoformat(),
                "lat": record.lat,
                "lng": record.lng,
                "alt": record.alt,
                "battery_percent": record.battery_percent,
                "status": record.status,
                "heading": record.heading,
                "speed": record.speed,
                "coverage_progress": record.coverage_progress
            }
            for record in telemetry_records
        ]
    except Exception as e:
        logger.error(f"Error getting telemetry for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting telemetry")

@router.get("/telemetry/mission/{mission_id}")
async def get_mission_telemetry(
    mission_id: int,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db_session)
):
    """Get telemetry data for specific mission"""
    try:
        from ..services.database import Telemetry
        from sqlalchemy import select, desc
        
        result = await db.execute(
            select(Telemetry)
            .where(Telemetry.mission_id == mission_id)
            .order_by(desc(Telemetry.timestamp))
            .limit(limit)
        )
        telemetry_records = result.scalars().all()
        
        return [
            {
                "id": record.id,
                "drone_id": record.drone_id,
                "mission_id": record.mission_id,
                "timestamp": record.timestamp.isoformat(),
                "lat": record.lat,
                "lng": record.lng,
                "alt": record.alt,
                "battery_percent": record.battery_percent,
                "status": record.status,
                "heading": record.heading,
                "speed": record.speed,
                "coverage_progress": record.coverage_progress
            }
            for record in telemetry_records
        ]
    except Exception as e:
        logger.error(f"Error getting telemetry for mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting telemetry")

# Discovery Endpoints
@router.get("/discoveries/mission/{mission_id}")
async def get_mission_discoveries(
    mission_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get discoveries for specific mission"""
    try:
        from ..services.database import Discovery
        from sqlalchemy import select, desc
        
        result = await db.execute(
            select(Discovery)
            .where(Discovery.mission_id == mission_id)
            .order_by(desc(Discovery.timestamp))
        )
        discoveries = result.scalars().all()
        
        return [
            {
                "id": discovery.id,
                "mission_id": discovery.mission_id,
                "drone_id": discovery.drone_id,
                "timestamp": discovery.timestamp.isoformat(),
                "lat": discovery.lat,
                "lng": discovery.lng,
                "discovery_type": discovery.discovery_type,
                "confidence": discovery.confidence,
                "description": discovery.description
            }
            for discovery in discoveries
        ]
    except Exception as e:
        logger.error(f"Error getting discoveries for mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting discoveries")

# Agent Management Endpoints
@router.get("/agents")
async def get_agents():
    """Get all agents status"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not available")
    
    try:
        status = agent_manager.get_agent_status()
        return {
            "agents": status,
            "total_agents": len(status),
            "running_agents": len([a for a in status.values() if a.get("running", False)])
        }
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail="Error getting agents status")

@router.get("/agents/clusters")
async def get_agent_clusters():
    """Get agents organized by cluster"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not available")
    
    try:
        clusters = agent_manager.get_agent_clusters()
        cluster_status = {}
        
        for cluster_name in clusters:
            cluster_status[cluster_name] = await agent_manager.get_cluster_status(cluster_name)
        
        return cluster_status
    except Exception as e:
        logger.error(f"Error getting agent clusters: {e}")
        raise HTTPException(status_code=500, detail="Error getting agent clusters")

@router.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str):
    """Restart specific agent"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="Agent manager not available")
    
    try:
        success = await agent_manager.restart_agent(agent_name)
        if success:
            return {"message": f"Agent {agent_name} restarted successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to restart agent {agent_name}")
    except Exception as e:
        logger.error(f"Error restarting agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error restarting agent {agent_name}")

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    if not websocket_manager:
        await websocket.close(code=1003, reason="WebSocket manager not available")
        return
    
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)