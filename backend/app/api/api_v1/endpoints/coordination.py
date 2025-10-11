"""
Coordination API endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.services.coordination_engine import coordination_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_coordination_status(mission_id: str = None):
    """Get current coordination status."""
    try:
        status = coordination_engine.get_coordination_status(mission_id)
        return status
    except Exception as e:
        logger.error(f"Error fetching coordination status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/emergency")
async def process_emergency(emergency_data: Dict[str, Any]):
    """Process an emergency situation."""
    try:
        emergency_type = emergency_data["emergency_type"]
        drone_id = emergency_data["drone_id"]
        details = emergency_data.get("details", {})

        commands = await coordination_engine.process_emergency(emergency_type, drone_id, details)

        return {
            "message": "Emergency processed successfully",
            "commands_generated": len(commands),
            "commands": [
                {
                    "drone_id": cmd.drone_id,
                    "command_type": cmd.command_type,
                    "parameters": cmd.parameters,
                    "priority": cmd.priority.value,
                    "reason": cmd.reason
                }
                for cmd in commands
            ]
        }
    except Exception as e:
        logger.error(f"Error processing emergency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
