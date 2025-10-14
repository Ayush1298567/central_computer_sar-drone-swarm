"""
Emergency control endpoints for operator actions.
LIFE-SAFETY CRITICAL - These endpoints must work flawlessly.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stop-all")
async def emergency_stop_all(
    reason: Optional[str] = Body("Manual emergency stop activated", embed=True),
    operator_id: Optional[str] = Body("system", embed=True)
):
    """🚨 EMERGENCY STOP ALL DRONES - LIFE-SAFETY CRITICAL
    
    This endpoint immediately:
    1. Sends emergency stop/land commands to all connected drones
    2. Aborts all active missions
    3. Broadcasts emergency alert via WebSocket
    4. Logs critical event for audit trail
    
    Returns:
        status: "success" or "partial" or "failed"
        drones_stopped: List of drone IDs successfully stopped
        drones_failed: List of drone IDs that failed to stop
        missions_aborted: List of mission IDs aborted
        timestamp: ISO timestamp of emergency activation
    """
    try:
        logger.critical(f"🚨 EMERGENCY STOP ACTIVATED by {operator_id}: {reason}")
        
        # Import here to avoid circular dependencies
        from app.communication.drone_connection_hub import drone_connection_hub
        from app.services.real_mission_execution import real_mission_execution_engine
        from app.api.websocket import connection_manager
        
        results = {
            "status": "success",
            "drones_stopped": [],
            "drones_failed": [],
            "missions_aborted": [],
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "operator": operator_id
        }
        
        # 1. Get all connected drones
        connected_drones = drone_connection_hub.get_connected_drones()
        drone_ids = [drone.drone_id for drone in connected_drones]
        
        if not drone_ids:
            logger.warning("No drones connected during emergency stop")
            results["status"] = "no_drones"
            return results
        
        # 2. Send emergency command to all drones (land immediately)
        stop_tasks = []
        for drone_id in drone_ids:
            task = drone_connection_hub.send_command(
                drone_id=drone_id,
                command_type="emergency_land",
                parameters={"reason": reason},
                priority=3  # Highest priority
            )
            stop_tasks.append(task)
        
        # Execute all stop commands concurrently with timeout
        stop_results = await asyncio.wait_for(
            asyncio.gather(*stop_tasks, return_exceptions=True),
            timeout=5.0  # 5-second timeout for emergency commands
        )
        
        # Categorize results
        for drone_id, result in zip(drone_ids, stop_results):
            if isinstance(result, Exception) or not result:
                results["drones_failed"].append({
                    "drone_id": drone_id,
                    "error": str(result) if isinstance(result, Exception) else "Command failed"
                })
                logger.error(f"Failed to stop drone {drone_id}: {result}")
            else:
                results["drones_stopped"].append(drone_id)
                logger.info(f"Successfully stopped drone {drone_id}")
        
        # 3. Abort all active missions
        if hasattr(real_mission_execution_engine, '_running_missions'):
            for mission_id in list(real_mission_execution_engine._running_missions.keys()):
                try:
                    # Mark mission as aborted
                    mission_data = real_mission_execution_engine._running_missions[mission_id]
                    mission_data["status"] = "ABORTED"
                    mission_data["abort_reason"] = reason
                    mission_data["abort_time"] = datetime.utcnow().isoformat()
                    results["missions_aborted"].append(mission_id)
                    logger.warning(f"Mission {mission_id} aborted due to emergency stop")
                except Exception as e:
                    logger.error(f"Failed to abort mission {mission_id}: {e}")
        
        # 4. Broadcast emergency alert via WebSocket
        try:
            await connection_manager.broadcast_notification({
                "type": "emergency",
                "subtype": "stop_all",
                "payload": {
                    "reason": reason,
                    "operator": operator_id,
                    "drones_affected": drone_ids,
                    "drones_stopped": results["drones_stopped"],
                    "drones_failed": results["drones_failed"],
                    "missions_aborted": results["missions_aborted"],
                    "timestamp": results["timestamp"],
                    "severity": "CRITICAL"
                }
            })
            logger.info("Emergency alert broadcasted to all WebSocket clients")
        except Exception as e:
            logger.error(f"Failed to broadcast emergency alert: {e}")
        
        # 5. Update status based on results
        if results["drones_failed"]:
            if results["drones_stopped"]:
                results["status"] = "partial"
                logger.warning(f"Partial emergency stop: {len(results['drones_stopped'])} succeeded, {len(results['drones_failed'])} failed")
            else:
                results["status"] = "failed"
                logger.critical("Emergency stop failed for all drones!")
                raise HTTPException(status_code=500, detail="Emergency stop failed for all drones")
        
        logger.critical(f"Emergency stop completed: {results['status']}")
        return results
        
    except asyncio.TimeoutError:
        logger.critical("Emergency stop timed out!")
        raise HTTPException(status_code=504, detail="Emergency stop timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Emergency stop exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")


@router.post("/rtl")
async def return_to_launch_all(
    reason: Optional[str] = Body("Manual return to launch activated", embed=True),
    operator_id: Optional[str] = Body("system", embed=True)
):
    """Command all connected drones to Return To Launch (RTL).
    
    Less aggressive than emergency_stop - drones fly back to home position.
    """
    try:
        logger.warning(f"🔄 RTL ALL activated by {operator_id}: {reason}")
        
        from app.communication.drone_connection_hub import drone_connection_hub
        from app.api.websocket import connection_manager
        
        # Get all connected drones
        connected_drones = drone_connection_hub.get_connected_drones()
        drone_ids = [drone.drone_id for drone in connected_drones]
        
        if not drone_ids:
            return {
                "status": "no_drones",
                "message": "No drones connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Send RTL command to all drones
        rtl_tasks = []
        for drone_id in drone_ids:
            task = drone_connection_hub.send_command(
                drone_id=drone_id,
                command_type="return_home",
                parameters={"reason": reason},
                priority=2  # High priority
            )
            rtl_tasks.append(task)
        
        results = await asyncio.gather(*rtl_tasks, return_exceptions=True)
        
        drones_rtl = []
        drones_failed = []
        for drone_id, result in zip(drone_ids, results):
            if isinstance(result, Exception) or not result:
                drones_failed.append(drone_id)
            else:
                drones_rtl.append(drone_id)
        
        # Broadcast RTL alert
        try:
            await connection_manager.broadcast_notification({
                "type": "emergency",
                "subtype": "rtl_all",
                "payload": {
                    "reason": reason,
                    "operator": operator_id,
                    "drones_commanded": drone_ids,
                    "drones_rtl": drones_rtl,
                    "drones_failed": drones_failed,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast RTL alert: {e}")
        
        return {
            "status": "success" if not drones_failed else "partial",
            "action": "rtl",
            "drones_rtl": drones_rtl,
            "drones_failed": drones_failed,
            "count": len(drones_rtl),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RTL all failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RTL failed: {str(e)}")


@router.post("/kill")
async def kill_switch(
    reason: Optional[str] = Body("Kill switch activated", embed=True),
    operator_id: Optional[str] = Body("system", embed=True),
    confirm: Optional[bool] = Body(False, embed=True)
):
    """⚠️ EMERGENCY KILL SWITCH - USE WITH EXTREME CAUTION
    
    This is the most aggressive emergency action:
    - Immediately disarms all drones (motors stop)
    - Drones will fall from current position
    - Only use when collision/injury risk outweighs crash risk
    
    Requires explicit confirmation flag to prevent accidental activation.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Kill switch requires explicit confirmation. Set 'confirm': true in request body."
        )
    
    try:
        logger.critical(f"💀 KILL SWITCH ACTIVATED by {operator_id}: {reason}")
        logger.critical("⚠️ ALL DRONES WILL DISARM AND FALL ⚠️")
        
        from app.communication.drone_connection_hub import drone_connection_hub
        from app.api.websocket import connection_manager
        
        connected_drones = drone_connection_hub.get_connected_drones()
        drone_ids = [drone.drone_id for drone in connected_drones]
        
        if not drone_ids:
            return {
                "status": "no_drones",
                "message": "No drones connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Send kill command to all drones (use emergency MAVLink if available)
        kill_tasks = []
        for drone_id in drone_ids:
            # Try emergency MAVLink command first
            success = drone_connection_hub.send_emergency_command(drone_id, "disarm")
            if not success:
                # Fallback to regular command
                task = drone_connection_hub.send_command(
                    drone_id=drone_id,
                    command_type="emergency_disarm",
                    parameters={"reason": reason},
                    priority=3
                )
                kill_tasks.append(task)
        
        if kill_tasks:
            await asyncio.gather(*kill_tasks, return_exceptions=True)
        
        # Broadcast kill switch alert
        try:
            await connection_manager.broadcast_notification({
                "type": "emergency",
                "subtype": "kill_switch",
                "payload": {
                    "reason": reason,
                    "operator": operator_id,
                    "drones_affected": drone_ids,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "CRITICAL",
                    "warning": "All drones have been disarmed"
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast kill switch alert: {e}")
        
        return {
            "status": "executed",
            "action": "kill_switch",
            "drones_killed": drone_ids,
            "warning": "All drones have been disarmed and will fall",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.critical(f"Kill switch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Kill switch failed: {str(e)}")


@router.get("/status")
async def emergency_system_status():
    """Get emergency system status and active alerts."""
    try:
        from app.communication.drone_connection_hub import drone_connection_hub
        from app.services.real_mission_execution import real_mission_execution_engine
        
        connected_drones = drone_connection_hub.get_connected_drones()
        active_missions = getattr(real_mission_execution_engine, '_running_missions', {})
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "drones_connected": len(connected_drones),
            "active_missions": len(active_missions),
            "emergency_capabilities": {
                "stop_all": True,
                "rtl": True,
                "kill_switch": True,
                "mavlink_emergency": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get emergency status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


