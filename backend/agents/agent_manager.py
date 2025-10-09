"""
Agent Manager
Manages all AI agents and their coordination
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .mission_planning.conversation_orchestrator import ConversationOrchestratorAgent
from .mission_planning.nlp_agent import NLPAgent
from .mission_planning.question_generator import QuestionGeneratorAgent
from .mission_planning.plan_synthesizer import PlanSynthesizerAgent
from .execution.task_assignment_agent import TaskAssignmentAgent
from .execution.route_optimizer import RouteOptimizerAgent
from .execution.progress_monitor import ProgressMonitorAgent
from .execution.command_dispatcher import CommandDispatcherAgent
from .intelligence.detection_analyzer import DetectionAnalyzerAgent
from .safety.battery_monitor import BatteryMonitorAgent
from .safety.collision_avoidance import CollisionAvoidanceAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages all AI agents and their coordination"""
    
    def __init__(self, redis_service, websocket_manager, drone_simulator):
        self.redis_service = redis_service
        self.websocket_manager = websocket_manager
        self.drone_simulator = drone_simulator
        self.agents: Dict[str, BaseAgent] = {}
        self._running = False
    
    async def start_all_agents(self) -> None:
        """Start all AI agents"""
        if self._running:
            return
        
        logger.info("Starting all AI agents...")
        
        # Mission Planning Cluster
        self.agents["conversation_orchestrator"] = ConversationOrchestratorAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["nlp_agent"] = NLPAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["question_generator"] = QuestionGeneratorAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["plan_synthesizer"] = PlanSynthesizerAgent(
            self.redis_service, self.websocket_manager
        )
        
        # Execution Cluster
        self.agents["task_assignment"] = TaskAssignmentAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["route_optimizer"] = RouteOptimizerAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["progress_monitor"] = ProgressMonitorAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["command_dispatcher"] = CommandDispatcherAgent(
            self.redis_service, self.websocket_manager
        )
        
        # Intelligence Cluster
        self.agents["detection_analyzer"] = DetectionAnalyzerAgent(
            self.redis_service, self.websocket_manager
        )
        
        # Safety Cluster
        self.agents["battery_monitor"] = BatteryMonitorAgent(
            self.redis_service, self.websocket_manager
        )
        self.agents["collision_avoidance"] = CollisionAvoidanceAgent(
            self.redis_service, self.websocket_manager
        )
        
        # Start all agents
        for agent_name, agent in self.agents.items():
            try:
                await agent.start()
                logger.info(f"Started agent: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to start agent {agent_name}: {e}")
        
        self._running = True
        logger.info(f"Started {len(self.agents)} AI agents")
    
    async def stop_all_agents(self) -> None:
        """Stop all AI agents"""
        if not self._running:
            return
        
        logger.info("Stopping all AI agents...")
        
        # Stop all agents
        for agent_name, agent in self.agents.items():
            try:
                await agent.stop()
                logger.info(f"Stopped agent: {agent_name}")
            except Exception as e:
                logger.error(f"Error stopping agent {agent_name}: {e}")
        
        self.agents.clear()
        self._running = False
        logger.info("All AI agents stopped")
    
    def is_running(self) -> bool:
        """Check if agent manager is running"""
        return self._running
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        status = {}
        for agent_name, agent in self.agents.items():
            status[agent_name] = agent.get_status()
        return status
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get specific agent by name"""
        return self.agents.get(agent_name)
    
    async def restart_agent(self, agent_name: str) -> bool:
        """Restart specific agent"""
        if agent_name not in self.agents:
            logger.error(f"Agent {agent_name} not found")
            return False
        
        try:
            # Stop agent
            await self.agents[agent_name].stop()
            
            # Recreate agent based on type
            if agent_name == "conversation_orchestrator":
                self.agents[agent_name] = ConversationOrchestratorAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "nlp_agent":
                self.agents[agent_name] = NLPAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "question_generator":
                self.agents[agent_name] = QuestionGeneratorAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "plan_synthesizer":
                self.agents[agent_name] = PlanSynthesizerAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "task_assignment":
                self.agents[agent_name] = TaskAssignmentAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "route_optimizer":
                self.agents[agent_name] = RouteOptimizerAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "progress_monitor":
                self.agents[agent_name] = ProgressMonitorAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "command_dispatcher":
                self.agents[agent_name] = CommandDispatcherAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "detection_analyzer":
                self.agents[agent_name] = DetectionAnalyzerAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "battery_monitor":
                self.agents[agent_name] = BatteryMonitorAgent(
                    self.redis_service, self.websocket_manager
                )
            elif agent_name == "collision_avoidance":
                self.agents[agent_name] = CollisionAvoidanceAgent(
                    self.redis_service, self.websocket_manager
                )
            else:
                logger.error(f"Unknown agent type: {agent_name}")
                return False
            
            # Start agent
            await self.agents[agent_name].start()
            logger.info(f"Restarted agent: {agent_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error restarting agent {agent_name}: {e}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health = {
            "total_agents": len(self.agents),
            "running_agents": 0,
            "failed_agents": 0,
            "agent_details": {}
        }
        
        for agent_name, agent in self.agents.items():
            agent_status = agent.get_status()
            health["agent_details"][agent_name] = agent_status
            
            if agent_status.get("running", False):
                health["running_agents"] += 1
            else:
                health["failed_agents"] += 1
        
        # Overall health score
        if health["total_agents"] > 0:
            health["health_score"] = (health["running_agents"] / health["total_agents"]) * 100
        else:
            health["health_score"] = 0
        
        return health
    
    async def send_message_to_agent(self, agent_name: str, channel: str, message: Any) -> bool:
        """Send message to specific agent"""
        if agent_name not in self.agents:
            logger.error(f"Agent {agent_name} not found")
            return False
        
        try:
            await self.redis_service.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_name}: {e}")
            return False
    
    def get_agent_clusters(self) -> Dict[str, List[str]]:
        """Get agents organized by cluster"""
        return {
            "mission_planning": [
                "conversation_orchestrator",
                "nlp_agent", 
                "question_generator",
                "plan_synthesizer"
            ],
            "execution": [
                "task_assignment",
                "route_optimizer",
                "progress_monitor",
                "command_dispatcher"
            ],
            "intelligence": [
                "detection_analyzer"
            ],
            "safety": [
                "battery_monitor",
                "collision_avoidance"
            ]
        }
    
    async def get_cluster_status(self, cluster_name: str) -> Dict[str, Any]:
        """Get status of specific cluster"""
        clusters = self.get_agent_clusters()
        if cluster_name not in clusters:
            return {"error": f"Cluster {cluster_name} not found"}
        
        cluster_agents = clusters[cluster_name]
        cluster_status = {
            "cluster_name": cluster_name,
            "total_agents": len(cluster_agents),
            "running_agents": 0,
            "agents": {}
        }
        
        for agent_name in cluster_agents:
            if agent_name in self.agents:
                agent_status = self.agents[agent_name].get_status()
                cluster_status["agents"][agent_name] = agent_status
                if agent_status.get("running", False):
                    cluster_status["running_agents"] += 1
        
        return cluster_status