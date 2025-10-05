"""
AI Decision Integration Layer
Integrates all AI components to make intelligent decisions with user approval workflow
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

# Import AI components
from app.ai.decision_framework import (
    AdvancedDecisionFramework, 
    DecisionType, 
    DecisionContext, 
    DecisionOption,
    AIDecision,
    ConfidenceLevel,
    DecisionAuthority
)
from app.ai.llm_intelligence import llm_intelligence
from app.ai.ai_governance import ai_governance, create_ai_decision, AIDecision as GovernanceDecision
from app.ai.real_computer_vision import RealComputerVisionEngine, DetectionType
from app.ai.real_ml_models import RealMLModels
from app.integration.real_system_integration import real_system_integration

logger = logging.getLogger(__name__)

class DecisionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class IntegratedAIDecision:
    """Complete AI decision with integration context"""
    decision_id: str
    decision_type: DecisionType
    status: DecisionStatus
    confidence_score: float
    authority_level: DecisionAuthority
    human_approval_required: bool
    reasoning_chain: List[str]
    risk_assessment: Dict[str, Any]
    expected_impact: Dict[str, Any]
    input_data: Dict[str, Any]
    recommendation: str
    alternative_options: List[DecisionOption]
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

@dataclass
class DecisionApprovalRequest:
    """Request for human approval of AI decision"""
    decision_id: str
    decision_type: str
    confidence_score: float
    recommendation: str
    reasoning: List[str]
    risk_assessment: Dict[str, Any]
    expected_impact: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    urgency_level: str
    created_at: datetime
    expires_at: datetime

class AIDecisionIntegration:
    """Main integration layer for AI decision making"""
    
    def __init__(self):
        self.decision_framework = AdvancedDecisionFramework()
        self.llm_intelligence = llm_intelligence
        self.ai_governance = ai_governance
        self.computer_vision = RealComputerVisionEngine()
        self.ml_models = RealMLModels()
        self.system_integration = real_system_integration
        
        # Decision tracking
        self.pending_decisions: Dict[str, IntegratedAIDecision] = {}
        self.approval_requests: Dict[str, DecisionApprovalRequest] = {}
        self.decision_history: List[IntegratedAIDecision] = []
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[Any] = []
        
        logger.info("AI Decision Integration initialized")
    
    async def initialize(self):
        """Initialize all AI components"""
        try:
            await asyncio.gather(
                self.computer_vision.initialize(),
                self.ml_models.initialize(),
                self.system_integration.initialize()
            )
            logger.info("AI Decision Integration components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI Decision Integration: {e}")
            raise
    
    async def make_intelligent_decision(
        self,
        decision_type: DecisionType,
        context_data: Dict[str, Any],
        mission_id: str,
        user_id: Optional[str] = None
    ) -> IntegratedAIDecision:
        """Make an intelligent decision with full integration"""
        try:
            decision_id = str(uuid.uuid4())
            
            # Create decision context
            decision_context = DecisionContext(
                mission_id=mission_id,
                current_state=context_data,
                constraints=context_data.get('constraints', {}),
                objectives=context_data.get('objectives', ['safety', 'efficiency']),
                urgency_level=context_data.get('urgency_level', 'medium'),
                available_resources=context_data.get('resources', {}),
                historical_data=context_data.get('historical_data', {})
            )
            
            # Generate decision options using AI
            options = await self._generate_decision_options(decision_type, decision_context)
            
            # Make decision using framework
            ai_decision = await self.decision_framework.make_decision(
                decision_type=decision_type,
                context=decision_context,
                options=options
            )
            
            # Create integrated decision
            integrated_decision = IntegratedAIDecision(
                decision_id=decision_id,
                decision_type=decision_type,
                status=DecisionStatus.PENDING,
                confidence_score=ai_decision.confidence_level.value,
                authority_level=ai_decision.authority_level,
                human_approval_required=ai_decision.authority_level != DecisionAuthority.AI_AUTONOMOUS,
                reasoning_chain=ai_decision.reasoning_chain,
                risk_assessment=ai_decision.risk_assessment,
                expected_impact=ai_decision.expected_impact,
                input_data=context_data,
                recommendation=ai_decision.selected_option.description,
                alternative_options=ai_decision.alternative_options,
                created_at=datetime.utcnow()
            )
            
            # Store decision
            self.pending_decisions[decision_id] = integrated_decision
            
            # Create governance decision
            governance_decision = create_ai_decision(
                component="ai_decision_integration",
                decision_type=decision_type.value,
                confidence_score=ai_decision.confidence_level.value,
                input_data=context_data,
                recommendation=ai_decision.selected_option.description
            )
            
            # Check if human approval is required
            if integrated_decision.human_approval_required:
                await self._create_approval_request(integrated_decision, user_id)
            else:
                # Execute autonomously
                await self._execute_decision(integrated_decision)
            
            # Notify frontend
            await self._notify_frontend(integrated_decision)
            
            logger.info(f"Created intelligent decision {decision_id} for {decision_type.value}")
            return integrated_decision
            
        except Exception as e:
            logger.error(f"Failed to make intelligent decision: {e}")
            raise
    
    async def _generate_decision_options(
        self, 
        decision_type: DecisionType, 
        context: DecisionContext
    ) -> List[DecisionOption]:
        """Generate decision options using AI components"""
        options = []
        
        try:
            # Use LLM to generate options
            if decision_type == DecisionType.MISSION_PLANNING:
                options = await self._generate_mission_planning_options(context)
            elif decision_type == DecisionType.SEARCH_PATTERN:
                options = await self._generate_search_pattern_options(context)
            elif decision_type == DecisionType.DRONE_DEPLOYMENT:
                options = await self._generate_drone_deployment_options(context)
            elif decision_type == DecisionType.EMERGENCY_RESPONSE:
                options = await self._generate_emergency_response_options(context)
            else:
                options = await self._generate_generic_options(context)
            
            return options
            
        except Exception as e:
            logger.error(f"Failed to generate decision options: {e}")
            return []
    
    async def _generate_mission_planning_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate mission planning options using AI"""
        try:
            # Use LLM to generate mission plans
            mission_context = {
                'mission_type': context.current_state.get('mission_type', 'search'),
                'terrain_type': context.current_state.get('terrain_type', 'unknown'),
                'weather': context.current_state.get('weather', {}),
                'area_size': context.current_state.get('area_size', 0),
                'available_drones': context.available_resources.get('drones', [])
            }
            
            ai_response = await self.llm_intelligence.generate_mission_plan(
                mission_context, 
                "Generate multiple mission planning options"
            )
            
            if ai_response['success']:
                # Parse AI response to create options
                options = []
                for i, plan in enumerate(ai_response.get('structured_plan', {}).get('recommendations', [])):
                    option = DecisionOption(
                        option_id=f"mission_plan_{i}",
                        description=plan,
                        parameters={'plan_type': 'ai_generated'},
                        expected_outcomes={'success_rate': 0.7 + (i * 0.1)},
                        risk_factors=[],
                        resource_requirements={'cost': 100 + (i * 50)},
                        confidence_score=0.6 + (i * 0.1),
                        reasoning=f"AI-generated mission plan option {i+1}"
                    )
                    options.append(option)
                
                return options
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to generate mission planning options: {e}")
            return []
    
    async def _generate_search_pattern_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate search pattern options"""
        patterns = [
            {
                'id': 'grid_pattern',
                'description': 'Grid search pattern for systematic coverage',
                'success_rate': 0.8,
                'efficiency': 0.7,
                'risk': 0.2
            },
            {
                'id': 'spiral_pattern',
                'description': 'Spiral search pattern for focused area search',
                'success_rate': 0.75,
                'efficiency': 0.8,
                'risk': 0.3
            },
            {
                'id': 'sector_pattern',
                'description': 'Sector search pattern for large area coverage',
                'success_rate': 0.7,
                'efficiency': 0.9,
                'risk': 0.1
            }
        ]
        
        options = []
        for pattern in patterns:
            option = DecisionOption(
                option_id=pattern['id'],
                description=pattern['description'],
                parameters={'pattern_type': pattern['id']},
                expected_outcomes={'success_rate': pattern['success_rate']},
                risk_factors=[],
                resource_requirements={'cost': 50},
                confidence_score=pattern['success_rate'],
                reasoning=f"Search pattern optimized for {context.current_state.get('terrain_type', 'unknown')} terrain"
            )
            options.append(option)
        
        return options
    
    async def _generate_drone_deployment_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate drone deployment options"""
        available_drones = context.available_resources.get('drones', [])
        
        options = []
        
        # Single drone deployment
        if available_drones:
            option = DecisionOption(
                option_id='single_drone',
                description=f'Deploy single drone: {available_drones[0].get("name", "Drone 1")}',
                parameters={'drone_count': 1, 'drones': [available_drones[0]]},
                expected_outcomes={'success_rate': 0.6, 'coverage': 0.5},
                risk_factors=['single_point_failure'],
                resource_requirements={'cost': 100},
                confidence_score=0.7,
                reasoning='Single drone deployment for focused search'
            )
            options.append(option)
        
        # Multi-drone deployment
        if len(available_drones) > 1:
            option = DecisionOption(
                option_id='multi_drone',
                description=f'Deploy {len(available_drones)} drones in coordinated formation',
                parameters={'drone_count': len(available_drones), 'drones': available_drones},
                expected_outcomes={'success_rate': 0.85, 'coverage': 0.9},
                risk_factors=['coordination_complexity'],
                resource_requirements={'cost': 200},
                confidence_score=0.8,
                reasoning='Multi-drone deployment for maximum coverage and redundancy'
            )
            options.append(option)
        
        return options
    
    async def _generate_emergency_response_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate emergency response options"""
        emergency_type = context.current_state.get('emergency_type', 'unknown')
        
        options = [
            DecisionOption(
                option_id='immediate_landing',
                description='Immediate emergency landing at nearest safe location',
                parameters={'action': 'land', 'priority': 'critical'},
                expected_outcomes={'safety_rate': 0.95, 'equipment_loss': 0.1},
                risk_factors=['terrain_hazards'],
                resource_requirements={'cost': 0},
                confidence_score=0.9,
                reasoning='Immediate landing to ensure safety'
            ),
            DecisionOption(
                option_id='return_to_base',
                description='Return to base using emergency protocols',
                parameters={'action': 'return_home', 'priority': 'high'},
                expected_outcomes={'safety_rate': 0.8, 'equipment_loss': 0.05},
                risk_factors=['battery_depletion', 'weather_conditions'],
                resource_requirements={'cost': 50},
                confidence_score=0.7,
                reasoning='Return to base for equipment safety'
            )
        ]
        
        return options
    
    async def _generate_generic_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate generic options when specific type not handled"""
        return [
            DecisionOption(
                option_id='default_option',
                description='Default AI recommendation',
                parameters={},
                expected_outcomes={'success_rate': 0.5},
                risk_factors=[],
                resource_requirements={'cost': 100},
                confidence_score=0.5,
                reasoning='Generic AI recommendation'
            )
        ]
    
    async def _create_approval_request(
        self, 
        decision: IntegratedAIDecision, 
        user_id: Optional[str]
    ) -> None:
        """Create human approval request"""
        try:
            approval_request = DecisionApprovalRequest(
                decision_id=decision.decision_id,
                decision_type=decision.decision_type.value,
                confidence_score=decision.confidence_score,
                recommendation=decision.recommendation,
                reasoning=decision.reasoning_chain,
                risk_assessment=decision.risk_assessment,
                expected_impact=decision.expected_impact,
                alternatives=[asdict(opt) for opt in decision.alternative_options],
                urgency_level=decision.input_data.get('urgency_level', 'medium'),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59)
            )
            
            self.approval_requests[decision.decision_id] = approval_request
            
            # Notify frontend of approval request
            await self._notify_approval_request(approval_request)
            
            logger.info(f"Created approval request for decision {decision.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
    
    async def approve_decision(
        self, 
        decision_id: str, 
        user_id: str, 
        approval: bool,
        override_reason: Optional[str] = None
    ) -> bool:
        """Approve or reject an AI decision"""
        try:
            if decision_id not in self.pending_decisions:
                logger.error(f"Decision {decision_id} not found")
                return False
            
            decision = self.pending_decisions[decision_id]
            
            if approval:
                decision.status = DecisionStatus.APPROVED
                decision.approved_at = datetime.utcnow()
                decision.approved_by = user_id
                
                # Execute the decision
                await self._execute_decision(decision)
                
                logger.info(f"Decision {decision_id} approved by {user_id}")
            else:
                decision.status = DecisionStatus.REJECTED
                decision.approved_at = datetime.utcnow()
                decision.approved_by = user_id
                
                logger.info(f"Decision {decision_id} rejected by {user_id}")
            
            # Remove from pending
            del self.pending_decisions[decision_id]
            
            # Remove approval request
            if decision_id in self.approval_requests:
                del self.approval_requests[decision_id]
            
            # Add to history
            self.decision_history.append(decision)
            
            # Notify frontend
            await self._notify_decision_update(decision)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve decision: {e}")
            return False
    
    async def _execute_decision(self, decision: IntegratedAIDecision) -> None:
        """Execute an approved decision"""
        try:
            decision.status = DecisionStatus.EXECUTING
            
            # Execute based on decision type
            if decision.decision_type == DecisionType.MISSION_PLANNING:
                result = await self._execute_mission_planning(decision)
            elif decision.decision_type == DecisionType.SEARCH_PATTERN:
                result = await self._execute_search_pattern(decision)
            elif decision.decision_type == DecisionType.DRONE_DEPLOYMENT:
                result = await self._execute_drone_deployment(decision)
            elif decision.decision_type == DecisionType.EMERGENCY_RESPONSE:
                result = await self._execute_emergency_response(decision)
            else:
                result = await self._execute_generic_decision(decision)
            
            decision.execution_result = result
            decision.status = DecisionStatus.COMPLETED
            
            logger.info(f"Decision {decision.decision_id} executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute decision: {e}")
            decision.status = DecisionStatus.FAILED
            decision.execution_result = {'error': str(e)}
    
    async def _execute_mission_planning(self, decision: IntegratedAIDecision) -> Dict[str, Any]:
        """Execute mission planning decision"""
        # This would integrate with the mission planning system
        return {
            'mission_created': True,
            'mission_id': f"mission_{decision.decision_id}",
            'status': 'planned'
        }
    
    async def _execute_search_pattern(self, decision: IntegratedAIDecision) -> Dict[str, Any]:
        """Execute search pattern decision"""
        # This would integrate with the search pattern system
        return {
            'pattern_applied': True,
            'pattern_type': decision.input_data.get('pattern_type', 'grid'),
            'status': 'active'
        }
    
    async def _execute_drone_deployment(self, decision: IntegratedAIDecision) -> Dict[str, Any]:
        """Execute drone deployment decision"""
        # This would integrate with the drone management system
        return {
            'drones_deployed': True,
            'drone_count': decision.input_data.get('drone_count', 1),
            'status': 'deployed'
        }
    
    async def _execute_emergency_response(self, decision: IntegratedAIDecision) -> Dict[str, Any]:
        """Execute emergency response decision"""
        # This would integrate with the emergency system
        return {
            'emergency_action_taken': True,
            'action_type': decision.input_data.get('action', 'land'),
            'status': 'completed'
        }
    
    async def _execute_generic_decision(self, decision: IntegratedAIDecision) -> Dict[str, Any]:
        """Execute generic decision"""
        return {
            'decision_executed': True,
            'status': 'completed'
        }
    
    async def _notify_frontend(self, decision: IntegratedAIDecision) -> None:
        """Notify frontend of decision updates"""
        try:
            # This would send WebSocket messages to frontend
            message = {
                'type': 'ai_decision',
                'decision': asdict(decision),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to all connected WebSocket clients
            for connection in self.websocket_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {e}")
            
        except Exception as e:
            logger.error(f"Failed to notify frontend: {e}")
    
    async def _notify_approval_request(self, request: DecisionApprovalRequest) -> None:
        """Notify frontend of approval request"""
        try:
            message = {
                'type': 'approval_request',
                'request': asdict(request),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for connection in self.websocket_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send approval request: {e}")
            
        except Exception as e:
            logger.error(f"Failed to notify approval request: {e}")
    
    async def _notify_decision_update(self, decision: IntegratedAIDecision) -> None:
        """Notify frontend of decision status update"""
        try:
            message = {
                'type': 'decision_update',
                'decision': asdict(decision),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for connection in self.websocket_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send decision update: {e}")
            
        except Exception as e:
            logger.error(f"Failed to notify decision update: {e}")
    
    def add_websocket_connection(self, connection: Any) -> None:
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.append(connection)
    
    def remove_websocket_connection(self, connection: Any) -> None:
        """Remove WebSocket connection"""
        if connection in self.websocket_connections:
            self.websocket_connections.remove(connection)
    
    async def get_pending_decisions(self) -> List[IntegratedAIDecision]:
        """Get all pending decisions"""
        return list(self.pending_decisions.values())
    
    async def get_approval_requests(self) -> List[DecisionApprovalRequest]:
        """Get all pending approval requests"""
        return list(self.approval_requests.values())
    
    async def get_decision_history(self, limit: int = 50) -> List[IntegratedAIDecision]:
        """Get decision history"""
        return self.decision_history[-limit:]
    
    async def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Get AI performance metrics"""
        total_decisions = len(self.decision_history)
        approved_decisions = len([d for d in self.decision_history if d.status == DecisionStatus.APPROVED])
        executed_decisions = len([d for d in self.decision_history if d.status == DecisionStatus.COMPLETED])
        
        return {
            'total_decisions': total_decisions,
            'approved_decisions': approved_decisions,
            'executed_decisions': executed_decisions,
            'approval_rate': approved_decisions / max(total_decisions, 1),
            'execution_rate': executed_decisions / max(approved_decisions, 1),
            'pending_decisions': len(self.pending_decisions),
            'pending_approvals': len(self.approval_requests)
        }

# Global instance
ai_decision_integration = AIDecisionIntegration()