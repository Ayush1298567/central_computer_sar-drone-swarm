# SAR Drone AI Intelligence System

This document describes the AI Intelligence components implemented for the SAR (Search and Rescue) drone command and control system.

## Overview

The AI Intelligence System consists of three main components:

1. **Ollama Client** - Local LLM integration for offline AI capabilities
2. **LLM Intelligence Engine** - Advanced decision making with OpenAI/Claude integration  
3. **Conversational Mission Planner** - Natural language mission planning interface

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SAR Drone AI Intelligence                │
├─────────────────────────────────────────────────────────────┤
│  Conversational Mission Planner                            │
│  ├─ Natural language processing                             │
│  ├─ Requirement extraction                                  │
│  ├─ Interactive planning workflow                           │
│  └─ Mission plan generation                                 │
├─────────────────────────────────────────────────────────────┤
│  LLM Intelligence Engine                                    │
│  ├─ Tactical decision making                                │
│  ├─ Search strategy planning                                │
│  ├─ Risk assessment                                         │
│  ├─ Mission context analysis                                │
│  └─ Multi-provider LLM integration                          │
├─────────────────────────────────────────────────────────────┤
│  Ollama Client                                              │
│  ├─ Local LLM communication                                 │
│  ├─ Model management                                        │
│  ├─ Health monitoring                                       │
│  └─ Structured output generation                            │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ollama Client (`app/ai/ollama_client.py`)

Provides async HTTP communication with local Ollama server for offline AI capabilities.

**Features:**
- Async HTTP client with retry logic and timeout management
- Health checks and server monitoring
- Model management (list, pull, ensure availability)
- Text generation with configurable parameters
- Structured JSON output generation
- Chat completion support
- Connection pooling and resource management

**Key Classes:**
- `OllamaClient` - Main client class
- `GenerationRequest` - Text generation parameters
- `StructuredRequest` - JSON output generation
- `OllamaResponse` - Response data structure
- `ModelInfo` - Model metadata

**Usage Example:**
```python
async with ollama_client() as client:
    # Health check
    healthy = await client.health_check()
    
    # Generate text
    request = GenerationRequest(
        prompt="Plan a search pattern for mountainous terrain",
        model="llama2",
        temperature=0.7
    )
    response = await client.generate_text(request)
    
    # Generate structured output
    struct_request = StructuredRequest(
        prompt="Create a mission plan with coordinates and timing",
        model="llama2"
    )
    json_response = await client.generate_structured(struct_request)
```

### 2. LLM Intelligence Engine (`app/ai/llm_intelligence.py`)

Advanced AI decision making engine with multi-provider LLM integration.

**Features:**
- Multi-provider support (OpenAI, Claude, Ollama)
- Automatic fallback between providers
- Tactical decision making for SAR operations
- Search strategy planning and optimization
- Risk assessment and mitigation recommendations
- Mission context analysis
- Adaptive parameter adjustment
- Decision explanation generation

**Key Classes:**
- `LLMIntelligenceEngine` - Main intelligence engine
- `MissionContext` - Mission state and parameters
- `TacticalDecision` - Decision results with reasoning
- `SearchStrategy` - Search pattern recommendations
- `RiskAssessment` - Risk analysis results

**Decision Types:**
- Search pattern optimization
- Resource allocation
- Risk assessment
- Mission adjustments
- Emergency response

**Usage Example:**
```python
# Create intelligence engine
engine = await create_intelligence_engine({
    "primary_provider": "openai",
    "fallback_provider": "ollama"
})

# Create mission context
context = MissionContext(
    mission_id="SAR-001",
    mission_type="missing_person",
    search_area={"size_km2": 10.0},
    weather_conditions={"visibility": "good"},
    available_drones=[{"id": "drone-1"}],
    time_constraints={"remaining_minutes": 120},
    priority_level=8,
    discovered_objects=[],
    current_progress=0.0
)

# Analyze mission
analysis = await engine.analyze_mission_context(context)

# Plan search strategy
strategy = await engine.plan_search_strategy(context, "forest", "high")

# Assess risks
risks = await engine.assess_risks(context)

# Make tactical decision
decision = await engine.make_tactical_decision(
    DecisionType.SEARCH_PATTERN,
    context,
    {"weather_change": "visibility decreasing"}
)
```

### 3. Conversational Mission Planner (`app/ai/conversation.py`)

Natural language interface for mission planning through AI-guided conversation.

**Features:**
- Natural language mission requirement gathering
- Intelligent question generation
- Requirement extraction and validation
- Iterative conversation workflow
- Mission plan generation
- Conversation state management
- Session persistence
- Multi-turn conversation support

**Key Classes:**
- `ConversationalMissionPlanner` - Main planner class
- `ConversationSession` - Session state management
- `ConversationMessage` - Individual messages
- `MissionPlan` - Complete mission specification
- `MissionRequirement` - Extracted requirements

**Conversation States:**
- `INITIALIZING` - Starting conversation
- `GATHERING_REQUIREMENTS` - Collecting mission parameters
- `CLARIFYING_DETAILS` - Refining requirements
- `VALIDATING_PLAN` - Confirming generated plan
- `FINALIZING` - Completing mission plan
- `COMPLETED` - Mission ready for execution

**Usage Example:**
```python
# Create mission planner
planner = await create_mission_planner({
    "enable_ai": True,
    "max_turns": 20
})

# Start conversation
session = await planner.start_conversation(
    "I need to plan a search mission for a missing hiker"
)

# Continue conversation
session = await planner.continue_conversation(
    session.session_id,
    "The hiker was last seen near Mount Wilson, about 5km area to search"
)

# Check conversation progress
print(f"State: {session.state.value}")
print(f"Requirements: {len(session.requirements)}")

# Finalize mission when ready
if session.state == ConversationState.VALIDATING_PLAN:
    final_plan = await planner.finalize_mission(session.session_id)
```

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Claude Configuration  
ANTHROPIC_API_KEY=your_claude_api_key

# Ollama Configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434
```

### AI Engine Configuration

```python
config = {
    # LLM Provider Settings
    "primary_provider": "openai",      # openai, claude, ollama
    "fallback_provider": "ollama",     # fallback when primary fails
    "temperature": 0.3,                # sampling temperature
    "max_tokens": 2000,                # maximum response length
    
    # Ollama Settings
    "ollama_url": "http://localhost:11434",
    "ollama_timeout": 120.0,
    "ollama_retries": 3,
    
    # Conversation Settings
    "max_turns": 20,                   # max conversation length
    "confidence_threshold": 0.7,       # requirement confidence
}
```

## Installation and Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install httpx pydantic openai anthropic
```

### 2. Setup Ollama (Optional)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model
ollama pull llama2
```

### 3. Configure API Keys

```bash
# Add to your environment
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-claude-key"
```

### 4. Run Tests

```bash
# Basic functionality test
python test_basic_ai.py

# Full integration test (requires Ollama/APIs)
python app/ai/test_integration.py
```

## Integration with SAR System

### Mission Planning Workflow

1. **Operator Input**: Natural language mission description
2. **AI Processing**: Requirement extraction and clarification
3. **Plan Generation**: Complete mission specification
4. **Intelligence Analysis**: Strategy optimization and risk assessment
5. **Execution**: Mission deployment with AI monitoring

### Real-time Operations

- **Adaptive Planning**: Adjust strategies based on discoveries
- **Risk Monitoring**: Continuous assessment of changing conditions
- **Decision Support**: AI recommendations for tactical choices
- **Performance Analysis**: Mission effectiveness evaluation

## Error Handling

The system implements comprehensive error handling:

- **Connection Failures**: Automatic retry with exponential backoff
- **API Timeouts**: Graceful degradation to fallback providers
- **Invalid Responses**: JSON parsing with error recovery
- **Rate Limiting**: Respect API limits with queuing
- **Model Unavailability**: Automatic model pulling and management

## Performance Considerations

- **Caching**: Response caching for repeated queries
- **Connection Pooling**: Efficient HTTP connection management
- **Async Operations**: Non-blocking AI operations
- **Resource Limits**: Memory and token usage monitoring
- **Fallback Strategies**: Multiple provider redundancy

## Security

- **API Key Management**: Secure environment variable storage
- **Input Validation**: Sanitization of user inputs
- **Output Filtering**: Response content validation
- **Access Control**: Session-based conversation isolation
- **Audit Logging**: Comprehensive operation logging

## Monitoring and Logging

All components include structured logging:

```python
import logging
logger = logging.getLogger(__name__)

# Log levels used:
# INFO - Normal operations
# WARNING - Fallback activations, retries
# ERROR - Operation failures
# DEBUG - Detailed execution traces
```

## Future Enhancements

1. **Multi-modal AI**: Image and sensor data analysis
2. **Reinforcement Learning**: Adaptive strategy optimization
3. **Federated Learning**: Multi-mission knowledge sharing
4. **Real-time Streaming**: Live data processing
5. **Edge Deployment**: Drone-mounted AI processing

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Ollama Connection Failed**
   ```bash
   # Check Ollama service
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

3. **API Key Issues**
   ```bash
   # Verify environment variables
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

4. **Model Not Found**
   ```bash
   # Pull required model
   ollama pull llama2
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs for specific issues
3. Verify all dependencies are installed
4. Ensure API keys are properly configured
5. Test with the provided test scripts

---

**Status**: ✅ **IMPLEMENTED AND TESTED**

All AI Intelligence components are fully implemented and tested. The system provides comprehensive AI capabilities for SAR drone operations with robust error handling and fallback mechanisms.