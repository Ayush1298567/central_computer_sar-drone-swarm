"""
SAR Drone Swarm - Main FastAPI Application
Central command and control system for Search and Rescue drone operations.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from typing import Dict, List
import json

from .core.database import init_database
from .core.config import settings
from .api import missions, drones, ai_planner, real_time
from .core.websocket_manager import ConnectionManager
from .ai.conversation import ConversationalMissionPlanner
from .ai.ollama_client import OllamaClient
from .services.mission_service import MissionService
from .services.drone_service import DroneService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SAR Drone Swarm Command Center",
    description="Advanced AI-powered Search and Rescue drone coordination system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
connection_manager = ConnectionManager()
ollama_client = OllamaClient()
mission_planner = ConversationalMissionPlanner(ollama_client)
mission_service = MissionService()
drone_service = DroneService()

# Global state for active missions
active_missions: Dict[str, dict] = {}
connected_drones: Dict[str, dict] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize database and core services on startup."""
    logger.info("Starting SAR Drone Swarm Command Center...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize AI services
        await ollama_client.initialize()
        logger.info("AI services initialized successfully")
        
        # Start background services
        asyncio.create_task(monitor_drone_health())
        asyncio.create_task(process_mission_updates())
        
        logger.info("SAR Command Center startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down SAR Command Center...")
    await connection_manager.disconnect_all()
    await ollama_client.cleanup()

# Include API routers
app.include_router(missions.router, prefix="/api/missions", tags=["missions"])
app.include_router(drones.router, prefix="/api/drones", tags=["drones"])
app.include_router(ai_planner.router, prefix="/api/ai", tags=["ai"])
app.include_router(real_time.router, prefix="/api/realtime", tags=["realtime"])

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint for real-time communication."""
    await connection_manager.connect(websocket, client_id)
    logger.info(f"Client {client_id} connected via WebSocket")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message based on type
            await handle_websocket_message(client_id, message)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)

async def handle_websocket_message(client_id: str, message: dict):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "mission_planning":
        # Handle AI mission planning conversation
        response = await mission_planner.process_message(
            message.get("content", ""),
            client_id
        )
        await connection_manager.send_personal_message(
            json.dumps({"type": "ai_response", "content": response}),
            client_id
        )
        
    elif message_type == "drone_command":
        # Handle drone commands
        await handle_drone_command(message, client_id)
        
    elif message_type == "mission_update":
        # Handle mission status updates
        await handle_mission_update(message, client_id)
        
    else:
        logger.warning(f"Unknown message type: {message_type}")

async def handle_drone_command(message: dict, client_id: str):
    """Process drone commands from the operator."""
    drone_id = message.get("drone_id")
    command = message.get("command")
    
    if not drone_id or not command:
        await connection_manager.send_personal_message(
            json.dumps({"type": "error", "message": "Invalid drone command"}),
            client_id
        )
        return
    
    # Execute drone command through service
    result = await drone_service.send_command(drone_id, command, message.get("params", {}))
    
    # Send response back to client
    await connection_manager.send_personal_message(
        json.dumps({
            "type": "command_response",
            "drone_id": drone_id,
            "command": command,
            "result": result
        }),
        client_id
    )

async def handle_mission_update(message: dict, client_id: str):
    """Handle mission status updates."""
    mission_id = message.get("mission_id")
    update_data = message.get("data", {})
    
    if mission_id in active_missions:
        # Update mission state
        active_missions[mission_id].update(update_data)
        
        # Broadcast update to all connected clients
        await connection_manager.broadcast(json.dumps({
            "type": "mission_status",
            "mission_id": mission_id,
            "data": active_missions[mission_id]
        }))

async def monitor_drone_health():
    """Background task to monitor drone health and status."""
    while True:
        try:
            # Check each connected drone
            for drone_id, drone_data in connected_drones.items():
                health_status = await drone_service.check_health(drone_id)
                
                if health_status.get("critical_alert"):
                    # Broadcast critical alerts immediately
                    await connection_manager.broadcast(json.dumps({
                        "type": "critical_alert",
                        "drone_id": drone_id,
                        "alert": health_status
                    }))
                
                # Update drone status
                connected_drones[drone_id]["last_health_check"] = health_status
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Drone health monitoring error: {e}")
            await asyncio.sleep(10)

async def process_mission_updates():
    """Background task to process mission updates and AI decisions."""
    while True:
        try:
            # Process each active mission
            for mission_id, mission_data in active_missions.items():
                # Check if mission needs AI intervention
                if mission_data.get("requires_ai_decision"):
                    ai_decision = await mission_planner.make_autonomous_decision(
                        mission_id, mission_data
                    )
                    
                    if ai_decision:
                        # Execute AI decision
                        await execute_ai_decision(mission_id, ai_decision)
                        
                        # Broadcast decision to operators
                        await connection_manager.broadcast(json.dumps({
                            "type": "ai_decision",
                            "mission_id": mission_id,
                            "decision": ai_decision
                        }))
            
            await asyncio.sleep(2)  # Process every 2 seconds
            
        except Exception as e:
            logger.error(f"Mission processing error: {e}")
            await asyncio.sleep(5)

async def execute_ai_decision(mission_id: str, decision: dict):
    """Execute an AI-made decision for a mission."""
    decision_type = decision.get("type")
    
    if decision_type == "adjust_search_pattern":
        # Adjust drone search patterns
        for drone_adjustment in decision.get("drone_adjustments", []):
            await drone_service.send_command(
                drone_adjustment["drone_id"],
                "update_search_pattern",
                drone_adjustment["parameters"]
            )
    
    elif decision_type == "emergency_response":
        # Handle emergency situations
        await handle_emergency_response(mission_id, decision)
    
    elif decision_type == "resource_reallocation":
        # Reallocate drones or resources
        await handle_resource_reallocation(mission_id, decision)

async def handle_emergency_response(mission_id: str, decision: dict):
    """Handle emergency response decisions."""
    emergency_type = decision.get("emergency_type")
    
    if emergency_type == "weather_abort":
        # Abort mission due to weather
        await mission_service.abort_mission(mission_id, "Weather conditions unsafe")
    
    elif emergency_type == "drone_malfunction":
        # Handle drone malfunction
        affected_drone = decision.get("affected_drone")
        await drone_service.emergency_return(affected_drone)
    
    elif emergency_type == "target_found":
        # Handle target discovery
        await mission_service.handle_target_discovery(mission_id, decision.get("discovery_data"))

async def handle_resource_reallocation(mission_id: str, decision: dict):
    """Handle resource reallocation decisions."""
    reallocations = decision.get("reallocations", [])
    
    for reallocation in reallocations:
        drone_id = reallocation["drone_id"]
        new_assignment = reallocation["new_assignment"]
        
        await drone_service.reassign_drone(drone_id, new_assignment)

@app.get("/")
async def root():
    """Root endpoint providing system status."""
    return {
        "system": "SAR Drone Swarm Command Center",
        "status": "operational",
        "version": "1.0.0",
        "active_missions": len(active_missions),
        "connected_drones": len(connected_drones),
        "ai_status": await ollama_client.get_status()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "database": "connected",
            "ai": await ollama_client.get_status(),
            "websocket_connections": connection_manager.get_connection_count()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )