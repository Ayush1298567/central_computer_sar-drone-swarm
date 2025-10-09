"""
Command Dispatcher Agent
Dispatches commands to drones and manages command execution
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service
from ...services.database import db_service

logger = logging.getLogger(__name__)

class CommandDispatcherAgent(BaseAgent):
    """Dispatches and manages drone commands"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("command_dispatcher", redis_service, websocket_manager)
        self.active_commands: Dict[str, Dict[str, Any]] = {}
        self.command_queue: List[Dict[str, Any]] = []
        self.drone_commands: Dict[int, List[str]] = {}
    
    async def start_agent(self) -> None:
        """Start the command dispatcher"""
        await self.subscribe_to_channel("command.drone_control")
        await self.subscribe_to_channel("command.emergency")
        await self.subscribe_to_channel("command.manual")
        await self.subscribe_to_channel("drone.command_response")
        await self.subscribe_to_channel("drone.status_update")
        logger.info("Command Dispatcher Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the command dispatcher"""
        logger.info("Command Dispatcher Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "command.drone_control":
                await self._handle_drone_control_command(message)
            elif channel == "command.emergency":
                await self._handle_emergency_command(message)
            elif channel == "command.manual":
                await self._handle_manual_command(message)
            elif channel == "drone.command_response":
                await self._handle_command_response(message)
            elif channel == "drone.status_update":
                await self._handle_drone_status_update(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_drone_control_command(self, message: Dict[str, Any]) -> None:
        """Handle drone control command"""
        command = message.get("command", {})
        user_input = message.get("user_input", "")
        session_id = message.get("session_id", "default")
        
        logger.info(f"Processing drone control command: {user_input}")
        
        # Parse command using LLM
        parsed_command = await self._parse_command(user_input, command)
        
        if parsed_command:
            # Create command record
            command_id = f"cmd_{asyncio.get_event_loop().time()}"
            command_record = {
                "command_id": command_id,
                "session_id": session_id,
                "user_input": user_input,
                "parsed_command": parsed_command,
                "status": "pending",
                "created_at": asyncio.get_event_loop().time(),
                "target_drones": parsed_command.get("target_drones", []),
                "action": parsed_command.get("action", "unknown")
            }
            
            # Store command
            self.active_commands[command_id] = command_record
            
            # Execute command
            await self._execute_command(command_record)
        else:
            logger.warning(f"Could not parse command: {user_input}")
            await self._send_command_feedback(session_id, "error", "Could not understand command")
    
    async def _handle_emergency_command(self, message: Dict[str, Any]) -> None:
        """Handle emergency command"""
        command = message.get("command", {})
        user_input = message.get("user_input", "")
        session_id = message.get("session_id", "default")
        
        logger.warning(f"Processing emergency command: {user_input}")
        
        # Emergency commands are executed immediately
        command_id = f"emergency_{asyncio.get_event_loop().time()}"
        command_record = {
            "command_id": command_id,
            "session_id": session_id,
            "user_input": user_input,
            "parsed_command": command,
            "status": "executing",
            "priority": "critical",
            "created_at": asyncio.get_event_loop().time(),
            "target_drones": command.get("target_drones", "all"),
            "action": command.get("action", "emergency_stop")
        }
        
        self.active_commands[command_id] = command_record
        
        # Execute emergency command immediately
        await self._execute_emergency_command(command_record)
    
    async def _handle_manual_command(self, message: Dict[str, Any]) -> None:
        """Handle manual command from operator"""
        command_text = message.get("command", "")
        drone_id = message.get("drone_id")
        session_id = message.get("session_id", "default")
        
        logger.info(f"Processing manual command for drone {drone_id}: {command_text}")
        
        # Parse manual command
        parsed_command = await self._parse_manual_command(command_text, drone_id)
        
        if parsed_command:
            command_id = f"manual_{asyncio.get_event_loop().time()}"
            command_record = {
                "command_id": command_id,
                "session_id": session_id,
                "user_input": command_text,
                "parsed_command": parsed_command,
                "status": "pending",
                "created_at": asyncio.get_event_loop().time(),
                "target_drones": [drone_id] if drone_id else [],
                "action": parsed_command.get("action", "manual_control")
            }
            
            self.active_commands[command_id] = command_record
            await self._execute_command(command_record)
        else:
            await self._send_command_feedback(session_id, "error", f"Could not parse manual command: {command_text}")
    
    async def _parse_command(self, user_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse user command using LLM"""
        try:
            # Get available drones for context
            available_drones = await self._get_available_drones()
            
            # Use Ollama to parse command
            parsed_command = await ollama_service.parse_command(user_input, {
                "available_drones": available_drones,
                "current_mission": context.get("current_mission", "None")
            })
            
            return parsed_command
        
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return self._parse_command_fallback(user_input)
    
    async def _parse_manual_command(self, command_text: str, drone_id: int) -> Optional[Dict[str, Any]]:
        """Parse manual command for specific drone"""
        try:
            # Simple manual command parsing
            command_lower = command_text.lower()
            
            if "return" in command_lower and "base" in command_lower:
                return {
                    "action": "return_to_base",
                    "target_drones": [drone_id],
                    "parameters": {},
                    "priority": "high"
                }
            elif "pause" in command_lower:
                return {
                    "action": "pause",
                    "target_drones": [drone_id],
                    "parameters": {},
                    "priority": "medium"
                }
            elif "resume" in command_lower:
                return {
                    "action": "resume",
                    "target_drones": [drone_id],
                    "parameters": {},
                    "priority": "medium"
                }
            elif "investigate" in command_lower:
                return {
                    "action": "investigate",
                    "target_drones": [drone_id],
                    "parameters": {"area": "specified location"},
                    "priority": "high"
                }
            elif "land" in command_lower:
                return {
                    "action": "land",
                    "target_drones": [drone_id],
                    "parameters": {},
                    "priority": "high"
                }
            else:
                return {
                    "action": "custom",
                    "target_drones": [drone_id],
                    "parameters": {"command": command_text},
                    "priority": "medium"
                }
        
        except Exception as e:
            logger.error(f"Error parsing manual command: {e}")
            return None
    
    def _parse_command_fallback(self, user_input: str) -> Dict[str, Any]:
        """Fallback command parsing"""
        command_lower = user_input.lower()
        
        if "return" in command_lower and "base" in command_lower:
            return {
                "action": "return_to_base",
                "target_drones": "all",
                "parameters": {},
                "priority": "high"
            }
        elif "pause" in command_lower:
            return {
                "action": "pause",
                "target_drones": "all",
                "parameters": {},
                "priority": "medium"
            }
        elif "resume" in command_lower:
            return {
                "action": "resume",
                "target_drones": "all",
                "parameters": {},
                "priority": "medium"
            }
        else:
            return {
                "action": "unknown",
                "target_drones": "all",
                "parameters": {},
                "priority": "low"
            }
    
    async def _execute_command(self, command_record: Dict[str, Any]) -> None:
        """Execute a command"""
        command_id = command_record["command_id"]
        action = command_record["parsed_command"].get("action")
        target_drones = command_record["parsed_command"].get("target_drones", [])
        
        logger.info(f"Executing command {command_id}: {action}")
        
        # Update command status
        command_record["status"] = "executing"
        command_record["executed_at"] = asyncio.get_event_loop().time()
        
        # Determine target drones
        if target_drones == "all":
            target_drones = await self._get_all_active_drones()
        elif isinstance(target_drones, str):
            target_drones = [target_drones]
        
        # Execute based on action type
        if action == "return_to_base":
            await self._execute_return_to_base(target_drones, command_record)
        elif action == "pause":
            await self._execute_pause(target_drones, command_record)
        elif action == "resume":
            await self._execute_resume(target_drones, command_record)
        elif action == "investigate":
            await self._execute_investigate(target_drones, command_record)
        elif action == "land":
            await self._execute_land(target_drones, command_record)
        else:
            await self._execute_custom_command(target_drones, command_record)
    
    async def _execute_emergency_command(self, command_record: Dict[str, Any]) -> None:
        """Execute emergency command"""
        action = command_record["parsed_command"].get("action")
        target_drones = command_record["parsed_command"].get("target_drones", "all")
        
        if target_drones == "all":
            target_drones = await self._get_all_active_drones()
        
        if action == "emergency_stop" or action == "abort":
            # Emergency stop all drones
            for drone_id in target_drones:
                await self._send_drone_command(drone_id, {
                    "action": "emergency_stop",
                    "priority": "critical",
                    "command_id": command_record["command_id"]
                })
        
        # Mark command as executed
        command_record["status"] = "executed"
        command_record["executed_at"] = asyncio.get_event_loop().time()
    
    async def _execute_return_to_base(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute return to base command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "return_to_base",
                "priority": "high",
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Return to base command sent to {len(target_drones)} drones"
        )
    
    async def _execute_pause(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute pause command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "pause",
                "priority": "medium",
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Pause command sent to {len(target_drones)} drones"
        )
    
    async def _execute_resume(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute resume command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "resume",
                "priority": "medium",
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Resume command sent to {len(target_drones)} drones"
        )
    
    async def _execute_investigate(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute investigate command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "investigate",
                "priority": "high",
                "parameters": command_record["parsed_command"].get("parameters", {}),
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Investigate command sent to {len(target_drones)} drones"
        )
    
    async def _execute_land(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute land command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "land",
                "priority": "high",
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Land command sent to {len(target_drones)} drones"
        )
    
    async def _execute_custom_command(self, target_drones: List[int], command_record: Dict[str, Any]) -> None:
        """Execute custom command"""
        for drone_id in target_drones:
            await self._send_drone_command(drone_id, {
                "action": "custom",
                "priority": "medium",
                "parameters": command_record["parsed_command"].get("parameters", {}),
                "command_id": command_record["command_id"]
            })
        
        command_record["status"] = "executed"
        await self._send_command_feedback(
            command_record["session_id"], 
            "success", 
            f"Custom command sent to {len(target_drones)} drones"
        )
    
    async def _send_drone_command(self, drone_id: int, command: Dict[str, Any]) -> None:
        """Send command to specific drone"""
        await self.publish_message("drone.command", {
            "drone_id": drone_id,
            "command": command
        })
        
        # Track command for this drone
        if drone_id not in self.drone_commands:
            self.drone_commands[drone_id] = []
        self.drone_commands[drone_id].append(command["command_id"])
    
    async def _handle_command_response(self, message: Dict[str, Any]) -> None:
        """Handle response from drone command"""
        drone_id = message.get("drone_id")
        command_id = message.get("command_id")
        response = message.get("response", {})
        
        logger.info(f"Command response from drone {drone_id}: {response}")
        
        # Find command record
        command_record = None
        for cmd_id, cmd_record in self.active_commands.items():
            if cmd_id == command_id:
                command_record = cmd_record
                break
        
        if command_record:
            # Update command status based on response
            if response.get("status") == "success":
                command_record["status"] = "completed"
            elif response.get("status") == "error":
                command_record["status"] = "failed"
                command_record["error"] = response.get("error", "Unknown error")
            
            # Send feedback to user
            await self._send_command_feedback(
                command_record["session_id"],
                response.get("status", "unknown"),
                response.get("message", "Command executed")
            )
    
    async def _handle_drone_status_update(self, message: Dict[str, Any]) -> None:
        """Handle drone status update"""
        drone_id = message.get("drone_id")
        status = message.get("status")
        
        # Update drone command tracking
        if drone_id in self.drone_commands:
            # Remove completed commands
            self.drone_commands[drone_id] = [
                cmd_id for cmd_id in self.drone_commands[drone_id]
                if cmd_id in self.active_commands and 
                self.active_commands[cmd_id]["status"] not in ["completed", "failed"]
            ]
    
    async def _get_available_drones(self) -> List[Dict[str, Any]]:
        """Get list of available drones"""
        try:
            drones = await db_service.get_all_drones()
            available_drones = []
            
            for drone in drones:
                if drone.status in ["available", "in_mission"]:
                    import json
                    capabilities = json.loads(drone.capabilities_json) if drone.capabilities_json else {}
                    available_drones.append({
                        "id": drone.id,
                        "name": drone.name,
                        "status": drone.status,
                        "capabilities": capabilities
                    })
            
            return available_drones
        except Exception as e:
            logger.error(f"Error getting available drones: {e}")
            return []
    
    async def _get_all_active_drones(self) -> List[int]:
        """Get all active drone IDs"""
        drones = await self._get_available_drones()
        return [drone["id"] for drone in drones if drone["status"] == "in_mission"]
    
    async def _send_command_feedback(self, session_id: str, status: str, message: str) -> None:
        """Send command feedback to user"""
        feedback = {
            "session_id": session_id,
            "status": status,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Send via WebSocket
        await self.send_websocket_message("command_feedback", feedback)
        
        # Publish to Redis
        await self.publish_message("command.feedback", feedback)
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific command"""
        return self.active_commands.get(command_id)
    
    def get_drone_commands(self, drone_id: int) -> List[str]:
        """Get active commands for a drone"""
        return self.drone_commands.get(drone_id, [])