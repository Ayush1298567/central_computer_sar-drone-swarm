"""
Ollama Intelligence Engine for SAR Mission Commander
Handles Ollama-specific AI operations and model management
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .ollama_client import OllamaClient

class ModelType(Enum):
    """Types of Ollama models"""
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"

class TaskType(Enum):
    """Types of AI tasks"""
    MISSION_PLANNING = "mission_planning"
    TEXT_ANALYSIS = "text_analysis"
    CODE_GENERATION = "code_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"

@dataclass
class ModelInfo:
    """Information about an Ollama model"""
    name: str
    model_type: ModelType
    size: str
    last_modified: str
    is_available: bool = True

@dataclass
class TaskRequest:
    """Request for an AI task"""
    task_type: TaskType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResponse:
    """Response from an AI task"""
    task_type: TaskType
    response: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class OllamaIntelligenceEngine:
    """Main Ollama intelligence processing engine"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.available_models: List[ModelInfo] = []
        self.task_history: List[TaskResponse] = []
        self.model_preferences: Dict[TaskType, str] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the Ollama intelligence engine"""
        try:
            # Initialize Ollama client
            await self.ollama_client.initialize()
            
            # Load available models
            await self._load_available_models()
            
            # Set up model preferences
            await self._setup_model_preferences()
            
            self.is_initialized = True
            print("✅ Ollama Intelligence Engine initialized")
            
        except Exception as e:
            print(f"⚠️ Ollama Intelligence Engine initialization failed: {e}")
            self.is_initialized = False
    
    async def _load_available_models(self):
        """Load information about available Ollama models"""
        try:
            # Get list of available models from Ollama
            models_data = await self.ollama_client.list_models()
            
            self.available_models = []
            
            # Parse model information
            for model_data in models_data.get("models", []):
                model_info = ModelInfo(
                    name=model_data.get("name", "unknown"),
                    model_type=self._determine_model_type(model_data.get("name", "")),
                    size=model_data.get("size", "unknown"),
                    last_modified=model_data.get("modified_at", ""),
                    is_available=True
                )
                self.available_models.append(model_info)
            
            print(f"Loaded {len(self.available_models)} available models")
            
        except Exception as e:
            print(f"Failed to load available models: {e}")
            # Add default models if loading fails
            self.available_models = [
                ModelInfo(
                    name="phi3:mini",
                    model_type=ModelType.CHAT,
                    size="2.3GB",
                    last_modified="",
                    is_available=True
                )
            ]
    
    def _determine_model_type(self, model_name: str) -> ModelType:
        """Determine model type based on name"""
        model_name_lower = model_name.lower()
        
        if "code" in model_name_lower:
            return ModelType.CODE
        elif "vision" in model_name_lower or "clip" in model_name_lower:
            return ModelType.VISION
        elif "embedding" in model_name_lower or "embed" in model_name_lower:
            return ModelType.EMBEDDING
        else:
            return ModelType.CHAT
    
    async def _setup_model_preferences(self):
        """Set up preferred models for different task types"""
        self.model_preferences = {
            TaskType.MISSION_PLANNING: "phi3:mini",
            TaskType.TEXT_ANALYSIS: "phi3:mini",
            TaskType.CODE_GENERATION: "phi3:mini",
            TaskType.QUESTION_ANSWERING: "phi3:mini",
            TaskType.SUMMARIZATION: "phi3:mini"
        }
        
        # Try to find better models if available
        for task_type in TaskType:
            preferred_model = self._find_best_model_for_task(task_type)
            if preferred_model:
                self.model_preferences[task_type] = preferred_model.name
    
    def _find_best_model_for_task(self, task_type: TaskType) -> Optional[ModelInfo]:
        """Find the best model for a specific task type"""
        if task_type == TaskType.CODE_GENERATION:
            # Look for code-specific models
            for model in self.available_models:
                if model.model_type == ModelType.CODE:
                    return model
        
        elif task_type == TaskType.VISION:
            # Look for vision models
            for model in self.available_models:
                if model.model_type == ModelType.VISION:
                    return model
        
        # Default to first available chat model
        for model in self.available_models:
            if model.model_type == ModelType.CHAT and model.is_available:
                return model
        
        return None
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """
        Execute an AI task using Ollama
        
        Args:
            task_request: The task to execute
        
        Returns:
            TaskResponse with results
        """
        try:
            # Get preferred model for task type
            model_name = self.model_preferences.get(task_request.task_type, "phi3:mini")
            
            # Prepare prompt based on task type
            prompt = await self._prepare_prompt(task_request)
            
            # Execute the task
            response_text = await self.ollama_client.generate_response(
                prompt, 
                model=model_name,
                max_tokens=task_request.parameters.get("max_tokens", 1000)
            )
            
            # Calculate confidence (simplified)
            confidence = await self._calculate_confidence(response_text, task_request)
            
            # Create response
            task_response = TaskResponse(
                task_type=task_request.task_type,
                response=response_text,
                confidence=confidence,
                metadata={
                    "model_used": model_name,
                    "prompt_length": len(prompt),
                    "response_length": len(response_text),
                    "context_provided": bool(task_request.context)
                }
            )
            
            # Store in history
            self.task_history.append(task_response)
            
            return task_response
            
        except Exception as e:
            print(f"Task execution failed: {e}")
            return TaskResponse(
                task_type=task_request.task_type,
                response=f"Error: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _prepare_prompt(self, task_request: TaskRequest) -> str:
        """Prepare prompt based on task type"""
        base_prompt = task_request.prompt
        
        if task_request.task_type == TaskType.MISSION_PLANNING:
            context_info = ""
            if task_request.context:
                context_info = f"\n\nContext: {json.dumps(task_request.context, indent=2)}"
            
            return f"""You are an expert SAR (Search and Rescue) mission planner. Please provide a detailed mission plan based on the following requirements:

{base_prompt}{context_info}

Please provide:
1. Mission objectives
2. Resource allocation
3. Risk assessment
4. Success criteria
5. Contingency plans

Respond in a structured, professional format."""
        
        elif task_request.task_type == TaskType.TEXT_ANALYSIS:
            return f"""Analyze the following text and provide insights:

{base_prompt}

Please provide:
1. Key points
2. Sentiment analysis
3. Important entities
4. Action items (if any)

Respond in a clear, structured format."""
        
        elif task_request.task_type == TaskType.CODE_GENERATION:
            return f"""Generate code based on the following requirements:

{base_prompt}

Please provide:
1. Clean, well-commented code
2. Brief explanation of the approach
3. Usage examples if applicable

Focus on readability and best practices."""
        
        elif task_request.task_type == TaskType.QUESTION_ANSWERING:
            return f"""Answer the following question based on your knowledge:

{base_prompt}

Please provide:
1. Direct answer
2. Supporting information
3. Additional context if relevant

Be accurate and helpful."""
        
        elif task_request.task_type == TaskType.SUMMARIZATION:
            return f"""Summarize the following content:

{base_prompt}

Please provide:
1. Key points summary
2. Main themes
3. Important details
4. Overall conclusion

Keep it concise but comprehensive."""
        
        else:
            return base_prompt
    
    async def _calculate_confidence(self, response: str, task_request: TaskRequest) -> float:
        """Calculate confidence score for the response"""
        try:
            # Simple confidence calculation based on response characteristics
            confidence = 0.5  # Base confidence
            
            # Adjust based on response length
            if len(response) > 100:
                confidence += 0.1
            if len(response) > 500:
                confidence += 0.1
            
            # Adjust based on task type
            if task_request.task_type == TaskType.MISSION_PLANNING:
                # Check for structured response
                if any(word in response.lower() for word in ["objective", "plan", "risk", "contingency"]):
                    confidence += 0.2
            
            elif task_request.task_type == TaskType.TEXT_ANALYSIS:
                # Check for analysis keywords
                if any(word in response.lower() for word in ["analysis", "key", "point", "summary"]):
                    confidence += 0.2
            
            elif task_request.task_type == TaskType.CODE_GENERATION:
                # Check for code structure
                if "def " in response or "class " in response or "import " in response:
                    confidence += 0.2
            
            # Adjust based on context provided
            if task_request.context:
                confidence += 0.1
            
            # Ensure confidence is between 0 and 1
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            print(f"Confidence calculation failed: {e}")
            return 0.5
    
    async def plan_mission(self, mission_requirements: str, context: Dict[str, Any] = None) -> TaskResponse:
        """Plan a SAR mission using AI"""
        task_request = TaskRequest(
            task_type=TaskType.MISSION_PLANNING,
            prompt=mission_requirements,
            context=context or {}
        )
        
        return await self.execute_task(task_request)
    
    async def analyze_text(self, text: str, context: Dict[str, Any] = None) -> TaskResponse:
        """Analyze text using AI"""
        task_request = TaskRequest(
            task_type=TaskType.TEXT_ANALYSIS,
            prompt=text,
            context=context or {}
        )
        
        return await self.execute_task(task_request)
    
    async def generate_code(self, requirements: str, context: Dict[str, Any] = None) -> TaskResponse:
        """Generate code using AI"""
        task_request = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            prompt=requirements,
            context=context or {}
        )
        
        return await self.execute_task(task_request)
    
    async def answer_question(self, question: str, context: Dict[str, Any] = None) -> TaskResponse:
        """Answer a question using AI"""
        task_request = TaskRequest(
            task_type=TaskType.QUESTION_ANSWERING,
            prompt=question,
            context=context or {}
        )
        
        return await self.execute_task(task_request)
    
    async def summarize_content(self, content: str, context: Dict[str, Any] = None) -> TaskResponse:
        """Summarize content using AI"""
        task_request = TaskRequest(
            task_type=TaskType.SUMMARIZATION,
            prompt=content,
            context=context or {}
        )
        
        return await self.execute_task(task_request)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models"""
        return self.available_models.copy()
    
    async def get_model_preferences(self) -> Dict[TaskType, str]:
        """Get current model preferences"""
        return self.model_preferences.copy()
    
    async def update_model_preference(self, task_type: TaskType, model_name: str):
        """Update model preference for a task type"""
        # Verify model exists
        model_exists = any(model.name == model_name for model in self.available_models)
        if model_exists:
            self.model_preferences[task_type] = model_name
        else:
            raise ValueError(f"Model {model_name} not found")
    
    async def get_task_history(self, limit: int = 50) -> List[TaskResponse]:
        """Get recent task history"""
        return self.task_history[-limit:]
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about executed tasks"""
        if not self.task_history:
            return {"total_tasks": 0}
        
        # Count tasks by type
        task_counts = {}
        confidence_scores = []
        
        for task in self.task_history:
            task_type = task.task_type.value
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
            confidence_scores.append(task.confidence)
        
        return {
            "total_tasks": len(self.task_history),
            "tasks_by_type": task_counts,
            "average_confidence": sum(confidence_scores) / len(confidence_scores),
            "available_models": len(self.available_models),
            "model_preferences": len(self.model_preferences)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Ollama intelligence engine"""
        ollama_health = await self.ollama_client.health_check()
        
        return {
            "status": "healthy" if self.is_initialized and ollama_health else "not_initialized",
            "initialized": self.is_initialized,
            "ollama_available": ollama_health,
            "available_models": len(self.available_models),
            "task_history_size": len(self.task_history),
            "model_preferences": len(self.model_preferences)
        }

# Global Ollama intelligence engine instance
ollama_intelligence_engine = OllamaIntelligenceEngine()