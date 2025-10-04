import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from app.core.config import settings
from app.ai.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class LLMIntelligence:
    """Real AI intelligence system for SAR operations - NO SIMULATIONS"""
    
    def __init__(self):
        self.ollama_client = None
        self.openai_available = False
        self._init_ai_services()
    
    def _init_ai_services(self):
        """Initialize AI services with fallbacks"""
        try:
            self.ollama_client = OllamaClient()
            logger.info("✅ Ollama client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Ollama client failed to initialize: {e}")
            self.ollama_client = None
        
        # Check OpenAI availability
        if settings.OPENAI_API_KEY:
            try:
                import openai
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_available = True
                logger.info("✅ OpenAI client available")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client failed to initialize: {e}")
                self.openai_available = False
        
        if not self.ollama_client and not self.openai_available:
            logger.critical("❌ No AI services available! Mission planning will be limited.")
    
    async def generate_mission_plan(
        self,
        mission_context: Dict[str, Any],
        user_input: str
    ) -> Dict[str, Any]:
        """
        Generate intelligent mission plan using real AI
        """
        try:
            prompt = self._build_mission_prompt(mission_context, user_input)
            
            # Get AI response
            ai_response = await self._get_real_ai_response(prompt)
            
            # Parse and structure the response
            structured_plan = await self._parse_mission_response(ai_response, mission_context)
            
            return {
                "success": True,
                "ai_response": ai_response,
                "structured_plan": structured_plan,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Mission plan generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": self._generate_fallback_plan(mission_context)
            }
    
    async def analyze_detection_data(
        self,
        detection_data: List[Dict[str, Any]],
        mission_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze detection data using AI
        """
        try:
            prompt = self._build_detection_analysis_prompt(detection_data, mission_context)
            
            ai_response = await self._get_real_ai_response(prompt)
            
            # Parse analysis
            analysis = await self._parse_detection_analysis(ai_response, detection_data)
            
            return {
                "success": True,
                "analysis": analysis,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Detection analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": self._generate_fallback_analysis(detection_data)
            }
    
    async def generate_emergency_response(
        self,
        emergency_type: str,
        emergency_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI-powered emergency response recommendations
        """
        try:
            prompt = self._build_emergency_prompt(emergency_type, emergency_data)
            
            ai_response = await self._get_real_ai_response(prompt)
            
            # Parse emergency response
            response_plan = await self._parse_emergency_response(ai_response, emergency_data)
            
            return {
                "success": True,
                "response_plan": response_plan,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Emergency response generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self._generate_fallback_emergency_response(emergency_type, emergency_data)
            }
    
    async def _get_real_ai_response(self, prompt: str) -> str:
        """
        Get REAL AI response - NO SIMULATION
        """
        try:
            # Try Ollama first (local)
            if self.ollama_client:
                try:
                    response = await self.ollama_client.generate(
                        prompt=prompt,
                        model=settings.DEFAULT_MODEL,
                        system="You are an expert SAR mission commander AI assistant with extensive experience in search and rescue operations."
                    )
                    logger.info("Got real response from Ollama")
                    return response
                except Exception as e:
                    logger.warning(f"Ollama failed: {e}, trying fallback")
            
            # Fallback to OpenAI if configured
            if self.openai_available:
                try:
                    import openai
                    
                    response = await openai.ChatCompletion.acreate(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are an expert SAR mission commander AI assistant with extensive experience in search and rescue operations."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    logger.info("Got real response from OpenAI")
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"OpenAI failed: {e}")
            
            # No AI available - this is a critical error for production
            logger.critical("No AI service available! Cannot generate intelligent responses.")
            raise RuntimeError("AI service unavailable - mission planning cannot proceed")
            
        except Exception as e:
            logger.error(f"AI response failed: {e}", exc_info=True)
            raise
    
    def _build_mission_prompt(self, context: Dict[str, Any], user_input: str) -> str:
        """Build comprehensive mission planning prompt"""
        return f"""You are an expert Search and Rescue mission commander with 20+ years of experience.

MISSION CONTEXT:
- Mission Type: {context.get('mission_type', 'search_and_rescue')}
- Terrain: {context.get('terrain_type', 'unknown')}
- Missing Persons: {context.get('missing_count', 'unknown')}
- Weather: {context.get('weather', 'unknown')}
- Available Drones: {context.get('drone_count', 5)}
- Search Area: {context.get('area', 'not specified')}
- Time Constraints: {context.get('time_constraints', 'none')}

USER REQUEST: {user_input}

TASK: Create a comprehensive SAR mission plan including:

1. SEARCH STRATEGY:
   - Recommended search pattern (grid, spiral, sector, etc.)
   - Optimal altitude and speed
   - Search area prioritization

2. DRONE DEPLOYMENT:
   - How to distribute drones across the search area
   - Flight paths and waypoints
   - Communication protocols

3. SAFETY CONSIDERATIONS:
   - Weather limitations
   - Battery management
   - Emergency procedures

4. SUCCESS METRICS:
   - How to measure mission progress
   - When to expand or modify search

5. CONTINGENCY PLANS:
   - What to do if weather changes
   - Backup search strategies
   - Emergency protocols

Provide specific, actionable recommendations based on SAR best practices. Be concise but comprehensive."""
    
    def _build_detection_analysis_prompt(self, detections: List[Dict], context: Dict) -> str:
        """Build detection analysis prompt"""
        detection_summary = "\n".join([
            f"- {det.get('class', 'unknown')} (confidence: {det.get('confidence', 0):.2f}) at {det.get('bbox', 'unknown location')}"
            for det in detections[:10]  # Limit to first 10 detections
        ])
        
        return f"""You are analyzing real-time detection data from SAR drones.

MISSION CONTEXT:
- Mission Type: {context.get('mission_type', 'search_and_rescue')}
- Terrain: {context.get('terrain_type', 'unknown')}
- Missing Persons: {context.get('missing_count', 'unknown')}

DETECTION DATA:
{detection_summary}

TASK: Analyze these detections and provide:

1. RELEVANCE ASSESSMENT:
   - Which detections are most relevant to the mission?
   - Are there any false positives to ignore?

2. PRIORITY RANKING:
   - Rank detections by importance
   - Explain reasoning for each ranking

3. ACTION RECOMMENDATIONS:
   - Should drones investigate specific detections?
   - Should search pattern be modified?
   - Any immediate actions required?

4. PATTERN ANALYSIS:
   - Do detections suggest a pattern?
   - Should search area be expanded or focused?

Provide specific, actionable analysis based on SAR expertise."""
    
    def _build_emergency_prompt(self, emergency_type: str, data: Dict) -> str:
        """Build emergency response prompt"""
        return f"""You are an emergency response coordinator for SAR drone operations.

EMERGENCY TYPE: {emergency_type}

EMERGENCY DATA:
{data}

TASK: Provide immediate emergency response recommendations:

1. IMMEDIATE ACTIONS:
   - What should be done right now?
   - Which drones need immediate attention?

2. SAFETY PRIORITIES:
   - How to protect personnel and equipment
   - Risk assessment and mitigation

3. COMMUNICATION:
   - Who needs to be notified?
   - What information should be shared?

4. RECOVERY PLANNING:
   - How to resume operations safely
   - Lessons learned for future missions

Provide clear, prioritized action items based on emergency response best practices."""
    
    async def _parse_mission_response(self, response: str, context: Dict) -> Dict[str, Any]:
        """Parse AI mission response into structured data"""
        # Simple parsing - in production, this would use more sophisticated NLP
        structured = {
            "search_strategy": self._extract_section(response, "SEARCH STRATEGY"),
            "drone_deployment": self._extract_section(response, "DRONE DEPLOYMENT"),
            "safety_considerations": self._extract_section(response, "SAFETY CONSIDERATIONS"),
            "success_metrics": self._extract_section(response, "SUCCESS METRICS"),
            "contingency_plans": self._extract_section(response, "CONTINGENCY PLANS"),
            "raw_response": response
        }
        
        # Extract specific recommendations
        structured["recommendations"] = self._extract_recommendations(response)
        
        return structured
    
    async def _parse_detection_analysis(self, response: str, detections: List[Dict]) -> Dict[str, Any]:
        """Parse detection analysis response"""
        return {
            "relevance_assessment": self._extract_section(response, "RELEVANCE ASSESSMENT"),
            "priority_ranking": self._extract_section(response, "PRIORITY RANKING"),
            "action_recommendations": self._extract_section(response, "ACTION RECOMMENDATIONS"),
            "pattern_analysis": self._extract_section(response, "PATTERN ANALYSIS"),
            "raw_response": response,
            "detection_count": len(detections)
        }
    
    async def _parse_emergency_response(self, response: str, data: Dict) -> Dict[str, Any]:
        """Parse emergency response"""
        return {
            "immediate_actions": self._extract_section(response, "IMMEDIATE ACTIONS"),
            "safety_priorities": self._extract_section(response, "SAFETY PRIORITIES"),
            "communication": self._extract_section(response, "COMMUNICATION"),
            "recovery_planning": self._extract_section(response, "RECOVERY PLANNING"),
            "raw_response": response
        }
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from AI response"""
        lines = text.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if section_name in line.upper():
                in_section = True
                continue
            elif in_section:
                if line.strip() and not line.startswith(' '):
                    # New section started
                    break
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract specific recommendations from text"""
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                recommendations.append(line[1:].strip())
        
        return recommendations
    
    def _generate_fallback_plan(self, context: Dict) -> Dict[str, Any]:
        """Generate fallback plan when AI is unavailable"""
        return {
            "search_strategy": "Grid search pattern recommended",
            "drone_deployment": f"Deploy {context.get('drone_count', 5)} drones in grid formation",
            "safety_considerations": "Monitor battery levels, maintain communication",
            "success_metrics": "Track coverage percentage and detection rate",
            "contingency_plans": "Return to base if weather deteriorates",
            "fallback": True
        }
    
    def _generate_fallback_analysis(self, detections: List[Dict]) -> Dict[str, Any]:
        """Generate fallback detection analysis"""
        person_detections = [d for d in detections if d.get('class') == 'person']
        
        return {
            "relevance_assessment": f"Found {len(person_detections)} person detections",
            "priority_ranking": "Prioritize high-confidence detections",
            "action_recommendations": "Investigate detections with confidence > 0.7",
            "pattern_analysis": "No clear pattern detected",
            "fallback": True
        }
    
    def _generate_fallback_emergency_response(self, emergency_type: str, data: Dict) -> Dict[str, Any]:
        """Generate fallback emergency response"""
        return {
            "immediate_actions": f"Activate emergency protocols for {emergency_type}",
            "safety_priorities": "Ensure drone and personnel safety",
            "communication": "Notify all team members immediately",
            "recovery_planning": "Assess damage and plan recovery",
            "fallback": True
        }
    
    async def get_ai_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        status = {
            "ollama_available": self.ollama_client is not None,
            "openai_available": self.openai_available,
            "overall_status": "operational"
        }
        
        if self.ollama_client:
            try:
                ollama_status = await self.ollama_client.test_connection()
                status["ollama_status"] = ollama_status
            except Exception as e:
                status["ollama_status"] = {"error": str(e)}
        
        if not status["ollama_available"] and not status["openai_available"]:
            status["overall_status"] = "degraded"
        
        return status

# Global instance
llm_intelligence = LLMIntelligence()