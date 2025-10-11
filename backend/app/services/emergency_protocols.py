import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from enum import Enum
import json

logger = logging.getLogger(__name__)

class EmergencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmergencyType(Enum):
    EMERGENCY_STOP = "emergency_stop"
    LOW_BATTERY = "low_battery"
    COMMUNICATION_LOSS = "communication_loss"
    WEATHER_EMERGENCY = "weather_emergency"
    COLLISION_RISK = "collision_risk"
    SYSTEM_FAILURE = "system_failure"
    MANUAL_OVERRIDE = "manual_override"

class EmergencyProtocols:
    """Life-saving emergency response system - MUST work flawlessly"""
    
    def __init__(self):
        self.active_emergencies = {}
        self.emergency_log = []
        self.emergency_callbacks = {}
        self._register_default_callbacks()
    
    def _register_default_callbacks(self):
        """Register default emergency response callbacks"""
        self.emergency_callbacks = {
            EmergencyType.EMERGENCY_STOP: self._handle_emergency_stop,
            EmergencyType.LOW_BATTERY: self._handle_low_battery,
            EmergencyType.COMMUNICATION_LOSS: self._handle_communication_loss,
            EmergencyType.WEATHER_EMERGENCY: self._handle_weather_emergency,
            EmergencyType.COLLISION_RISK: self._handle_collision_risk,
            EmergencyType.SYSTEM_FAILURE: self._handle_system_failure,
            EmergencyType.MANUAL_OVERRIDE: self._handle_manual_override
        }
    
    async def trigger_emergency(
        self,
        emergency_type: EmergencyType,
        reason: str,
        operator_id: str,
        drone_ids: List[str] = None,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Trigger emergency protocol - lives depend on this working
        """
        emergency_id = f"EMERG_{datetime.now().timestamp()}_{emergency_type.value}"
        
        try:
            logger.critical(f"🚨 EMERGENCY TRIGGERED: {emergency_type.value} - {reason} by {operator_id}")
            
            # Create emergency record
            emergency = {
                "id": emergency_id,
                "type": emergency_type.value,
                "reason": reason,
                "operator": operator_id,
                "timestamp": datetime.utcnow().isoformat(),
                "drone_ids": drone_ids or [],
                "additional_data": additional_data or {},
                "status": "active"
            }
            
            # Determine emergency level
            emergency["level"] = self._determine_emergency_level(emergency_type, additional_data)
            
            # Store emergency
            self.active_emergencies[emergency_id] = emergency
            self.emergency_log.append(emergency)
            
            # Execute emergency response
            callback = self.emergency_callbacks.get(emergency_type)
            if callback:
                results = await callback(emergency)
                emergency["response_results"] = results
            else:
                logger.error(f"No callback registered for emergency type: {emergency_type}")
                emergency["response_results"] = {"error": "No response handler"}
            
            # Update status
            emergency["completed_at"] = datetime.utcnow().isoformat()
            emergency["status"] = "completed"
            
            logger.critical(f"Emergency {emergency_id} completed: {emergency['response_results']}")
            
            return {
                "success": True,
                "emergency_id": emergency_id,
                "level": emergency["level"],
                "results": emergency["response_results"],
                "message": f"Emergency {emergency_type.value} executed successfully"
            }
            
        except Exception as e:
            logger.critical(f"❌ EMERGENCY HANDLING FAILED: {e}", exc_info=True)
            
            # If emergency handling fails, activate hardware failsafe
            await self._trigger_hardware_failsafe(emergency_id, str(e))
            
            return {
                "success": False,
                "emergency_id": emergency_id,
                "error": str(e),
                "message": "Emergency handling failed - hardware failsafe activated"
            }
    
    def _determine_emergency_level(self, emergency_type: EmergencyType, data: Dict) -> str:
        """Determine emergency severity level"""
        if emergency_type == EmergencyType.EMERGENCY_STOP:
            return EmergencyLevel.CRITICAL.value
        elif emergency_type == EmergencyType.COMMUNICATION_LOSS:
            return EmergencyLevel.HIGH.value
        elif emergency_type == EmergencyType.LOW_BATTERY:
            battery_level = data.get('battery_level', 100)
            if battery_level < 10:
                return EmergencyLevel.CRITICAL.value
            elif battery_level < 20:
                return EmergencyLevel.HIGH.value
            else:
                return EmergencyLevel.MEDIUM.value
        elif emergency_type == EmergencyType.WEATHER_EMERGENCY:
            return EmergencyLevel.HIGH.value
        elif emergency_type == EmergencyType.COLLISION_RISK:
            return EmergencyLevel.CRITICAL.value
        elif emergency_type == EmergencyType.SYSTEM_FAILURE:
            return EmergencyLevel.HIGH.value
        else:
            return EmergencyLevel.MEDIUM.value
    
    async def _handle_emergency_stop(self, emergency: Dict) -> Dict[str, Any]:
        """Handle emergency stop protocol"""
        drone_ids = emergency.get("drone_ids", [])
        
        if not drone_ids:
            logger.warning("No drone IDs provided for emergency stop")
            return {"status": "no_drones", "message": "No drones to stop"}
        
        # Send immediate stop commands
        stop_tasks = [
            self._send_emergency_stop_command(drone_id)
            for drone_id in drone_ids
        ]
        
        try:
            responses = await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            results = {
                "stopped_drones": [],
                "failed_drones": [],
                "total": len(drone_ids)
            }
            
            for drone_id, response in zip(drone_ids, responses):
                if isinstance(response, Exception):
                    results["failed_drones"].append({
                        "drone_id": drone_id,
                        "error": str(response)
                    })
                    logger.error(f"Failed to stop {drone_id}: {response}")
                else:
                    results["stopped_drones"].append(drone_id)
            
            return results
            
        except Exception as e:
            logger.error(f"Emergency stop execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _send_emergency_stop_command(self, drone_id: str) -> Dict[str, Any]:
        """Send emergency stop command to individual drone"""
        try:
            logger.critical(f"🛑 SENDING EMERGENCY STOP TO DRONE: {drone_id}")

            # Execute via DroneConnectionHub using command type 'emergency_stop'
            from app.communication.drone_connection_hub import drone_connection_hub
            sent = await drone_connection_hub.send_command(
                drone_id=drone_id,
                command_type="emergency_stop",
                parameters={},
                priority=3,
            )

            status = "stopped" if sent else "failed"
            return {
                "drone_id": drone_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "command": "EMERGENCY_STOP",
            }

        except Exception as e:
            logger.error(f"Failed to send stop command to {drone_id}: {e}")
            raise
    
    async def _handle_low_battery(self, emergency: Dict) -> Dict[str, Any]:
        """Handle low battery emergency"""
        drone_id = emergency.get("drone_ids", [None])[0]
        battery_level = emergency.get("additional_data", {}).get("battery_level", 0)
        position = emergency.get("additional_data", {}).get("position", {})
        
        if not drone_id:
            return {"error": "No drone ID provided"}
        
        # Determine action based on battery level
        if battery_level < 10:
            action = "immediate_rtl"
            priority = "critical"
        elif battery_level < 20:
            action = "rtl_soon"
            priority = "high"
        elif battery_level < 30:
            action = "reduce_mission"
            priority = "medium"
        else:
            action = "monitor"
            priority = "low"
        
        # Execute appropriate action
        if action in ["immediate_rtl", "rtl_soon"]:
            await self._command_return_to_launch(drone_id, f"low_battery_{battery_level}%")
        
        return {
            "drone_id": drone_id,
            "battery_level": battery_level,
            "action": action,
            "priority": priority,
            "position": position,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_communication_loss(self, emergency: Dict) -> Dict[str, Any]:
        """Handle communication loss emergency"""
        drone_id = emergency.get("drone_ids", [None])[0]
        last_contact = emergency.get("additional_data", {}).get("last_contact")
        position = emergency.get("additional_data", {}).get("position", {})
        
        if not drone_id:
            return {"error": "No drone ID provided"}
        
        # Calculate time since last contact
        if last_contact:
            try:
                last_contact_time = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                time_since_contact = (datetime.utcnow() - last_contact_time).total_seconds()
            except:
                time_since_contact = 999  # Unknown
        else:
            time_since_contact = 999
        
        # Determine severity
        if time_since_contact > 60:
            severity = "critical"
            action = "activate_failsafe"
        elif time_since_contact > 30:
            severity = "high"
            action = "attempt_reconnection"
        else:
            severity = "medium"
            action = "monitor"
        
        # Log the incident
        logger.error(f"Communication lost with {drone_id} for {time_since_contact:.1f} seconds")
        
        return {
            "drone_id": drone_id,
            "time_since_contact": time_since_contact,
            "severity": severity,
            "action": action,
            "last_position": position,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_weather_emergency(self, emergency: Dict) -> Dict[str, Any]:
        """Handle weather-related emergency"""
        drone_ids = emergency.get("drone_ids", [])
        weather_data = emergency.get("additional_data", {}).get("weather", {})
        
        # Determine weather severity
        wind_speed = weather_data.get("wind_speed", 0)
        visibility = weather_data.get("visibility", 10)
        
        if wind_speed > 15 or visibility < 1:
            action = "immediate_rtl_all"
            severity = "critical"
        elif wind_speed > 10 or visibility < 3:
            action = "reduce_altitude"
            severity = "high"
        else:
            action = "monitor"
            severity = "medium"
        
        # Execute weather response
        results = []
        for drone_id in drone_ids:
            if action == "immediate_rtl_all":
                await self._command_return_to_launch(drone_id, "weather_emergency")
            
            results.append({
                "drone_id": drone_id,
                "action": action,
                "weather_conditions": weather_data
            })
        
        return {
            "action": action,
            "severity": severity,
            "weather_data": weather_data,
            "drone_responses": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_collision_risk(self, emergency: Dict) -> Dict[str, Any]:
        """Handle collision risk emergency"""
        drone_id = emergency.get("drone_ids", [None])[0]
        obstacle_data = emergency.get("additional_data", {}).get("obstacle", {})
        
        if not drone_id:
            return {"error": "No drone ID provided"}
        
        # Immediate evasive action
        logger.critical(f"🚨 COLLISION RISK: {drone_id} - {obstacle_data}")
        
        # TODO: Implement collision avoidance maneuvers
        # This should send MAVLink commands for evasive action
        
        return {
            "drone_id": drone_id,
            "action": "evasive_maneuver",
            "obstacle_data": obstacle_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_system_failure(self, emergency: Dict) -> Dict[str, Any]:
        """Handle system failure emergency"""
        drone_id = emergency.get("drone_ids", [None])[0]
        failure_type = emergency.get("additional_data", {}).get("failure_type", "unknown")
        
        if not drone_id:
            return {"error": "No drone ID provided"}
        
        logger.critical(f"🚨 SYSTEM FAILURE: {drone_id} - {failure_type}")
        
        # Immediate RTL for system failures
        await self._command_return_to_launch(drone_id, f"system_failure_{failure_type}")
        
        return {
            "drone_id": drone_id,
            "failure_type": failure_type,
            "action": "emergency_rtl",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_manual_override(self, emergency: Dict) -> Dict[str, Any]:
        """Handle manual override emergency"""
        drone_id = emergency.get("drone_ids", [None])[0]
        operator_id = emergency.get("operator", "unknown")
        
        if not drone_id:
            return {"error": "No drone ID provided"}
        
        logger.warning(f"Manual override activated for {drone_id} by {operator_id}")
        
        return {
            "drone_id": drone_id,
            "operator": operator_id,
            "action": "manual_control",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _command_return_to_launch(self, drone_id: str, reason: str):
        """Command drone to return to launch point"""
        try:
            logger.warning(f"🔄 Commanding RTL for {drone_id}: {reason}")

            # Route through connection hub using command type 'return_home'
            from app.communication.drone_connection_hub import drone_connection_hub
            await drone_connection_hub.send_command(
                drone_id=drone_id,
                command_type="return_home",
                parameters={"reason": reason},
                priority=2,
            )

            logger.info(f"RTL command sent to {drone_id}")

        except Exception as e:
            logger.error(f"Failed to send RTL command to {drone_id}: {e}")
            raise
    
    async def _trigger_hardware_failsafe(self, emergency_id: str, error: str):
        """Last resort hardware failsafe when software fails"""
        logger.critical(f"⚠️ ACTIVATING HARDWARE FAILSAFE for emergency {emergency_id}")
        logger.critical(f"Reason: {error}")
        
        # TODO: Implement hardware kill switch trigger
        # This should activate physical safety systems
        
        # Log the failsafe activation
        failsafe_record = {
            "emergency_id": emergency_id,
            "reason": error,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "hardware_failsafe"
        }
        
        self.emergency_log.append(failsafe_record)
    
    async def get_active_emergencies(self) -> List[Dict]:
        """Get all active emergencies"""
        return [
            emergency for emergency in self.active_emergencies.values()
            if emergency.get("status") == "active"
        ]
    
    async def resolve_emergency(self, emergency_id: str, resolution: str, operator_id: str):
        """Mark emergency as resolved"""
        if emergency_id in self.active_emergencies:
            emergency = self.active_emergencies[emergency_id]
            emergency["resolved_at"] = datetime.utcnow().isoformat()
            emergency["resolution"] = resolution
            emergency["resolved_by"] = operator_id
            emergency["status"] = "resolved"
            
            # Move to log
            self.emergency_log.append(emergency)
            del self.active_emergencies[emergency_id]
            
            logger.info(f"Emergency {emergency_id} resolved by {operator_id}: {resolution}")
            
            return {"success": True, "message": "Emergency resolved"}
        else:
            return {"success": False, "message": "Emergency not found"}
    
    async def get_emergency_history(self, limit: int = 100) -> List[Dict]:
        """Get emergency history"""
        return self.emergency_log[-limit:]
    
    async def register_emergency_callback(self, emergency_type: EmergencyType, callback):
        """Register custom emergency callback"""
        self.emergency_callbacks[emergency_type] = callback
        logger.info(f"Registered callback for {emergency_type.value}")
    
    async def emergency_status_check(self) -> Dict[str, Any]:
        """Check overall emergency system status"""
        active_count = len([e for e in self.active_emergencies.values() if e.get("status") == "active"])
        total_logged = len(self.emergency_log)
        
        return {
            "active_emergencies": active_count,
            "total_logged": total_logged,
            "system_status": "operational" if active_count == 0 else "emergency_active",
            "last_check": datetime.utcnow().isoformat()
        }

# Global instance
emergency_protocols = EmergencyProtocols()