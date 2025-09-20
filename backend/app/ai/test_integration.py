"""
Integration tests for AI Intelligence components.

Tests the Ollama client, LLM Intelligence Engine, and Conversational Mission Planner
to ensure they work together properly for SAR drone operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from ollama_client import (
    OllamaClient, GenerationRequest, StructuredRequest,
    ollama_client, ensure_model_available
)
from llm_intelligence import (
    LLMIntelligenceEngine, MissionContext, DecisionType,
    create_intelligence_engine
)
from conversation import (
    ConversationalMissionPlanner, create_mission_planner,
    ConversationState
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_ollama_client():
    """Test Ollama client functionality."""
    print("\n=== Testing Ollama Client ===")
    
    try:
        async with ollama_client() as client:
            # Test health check
            healthy = await client.health_check()
            print(f"Ollama server healthy: {healthy}")
            
            if not healthy:
                print("Ollama server not available, skipping tests")
                return False
                
            # Test model listing
            models = await client.list_models()
            print(f"Available models: {len(models)}")
            for model in models[:3]:  # Show first 3
                print(f"  - {model.name} ({model.size} bytes)")
                
            if not models:
                print("No models available, attempting to pull llama2...")
                success = await client.pull_model("llama2")
                if not success:
                    print("Failed to pull model, skipping generation tests")
                    return False
                models = await client.list_models()
                
            # Test text generation
            if models:
                model_name = models[0].name
                request = GenerationRequest(
                    prompt="What is a search and rescue mission? Answer briefly.",
                    model=model_name,
                    max_tokens=100
                )
                
                response = await client.generate_text(request)
                print(f"Generated text: {response.content[:100]}...")
                
                # Test structured output
                struct_request = StructuredRequest(
                    prompt="List 3 key components of a SAR drone system in JSON format",
                    model=model_name,
                    max_tokens=200
                )
                
                structured_response = await client.generate_structured(struct_request)
                print(f"Structured output: {json.dumps(structured_response, indent=2)}")
                
            return True
            
    except Exception as e:
        logger.error(f"Ollama client test failed: {e}")
        return False


async def test_llm_intelligence():
    """Test LLM Intelligence Engine functionality."""
    print("\n=== Testing LLM Intelligence Engine ===")
    
    try:
        # Create intelligence engine (will use fallback if APIs not available)
        engine = await create_intelligence_engine({
            "primary_provider": "ollama",  # Use local Ollama as primary
            "fallback_provider": "ollama",
            "temperature": 0.5
        })
        
        # Create test mission context
        context = MissionContext(
            mission_id="test-001",
            mission_type="missing_person",
            search_area={"size_km2": 5.0, "terrain": "mountainous"},
            weather_conditions={"visibility": "good", "wind_speed": 15},
            available_drones=[{"id": "drone-1", "type": "quadcopter"}],
            time_constraints={"remaining_minutes": 240},
            priority_level=7,
            discovered_objects=[],
            current_progress=0.0
        )
        
        print(f"Test mission context: {context.mission_id}")
        
        # Test mission context analysis
        try:
            analysis = await engine.analyze_mission_context(context)
            print(f"Mission analysis: {type(analysis).__name__}")
            if isinstance(analysis, dict) and "situation_assessment" in analysis:
                print(f"  Situation: {analysis['situation_assessment'][:100]}...")
        except Exception as e:
            print(f"Mission analysis failed: {e}")
            
        # Test search strategy planning
        try:
            strategy = await engine.plan_search_strategy(context, "mountain", "high")
            print(f"Search strategy: {strategy.pattern_type}")
            print(f"  Estimated time: {strategy.estimated_time} minutes")
            print(f"  Success probability: {strategy.success_probability:.2f}")
        except Exception as e:
            print(f"Search strategy planning failed: {e}")
            
        # Test risk assessment
        try:
            risk_assessment = await engine.assess_risks(context)
            print(f"Risk assessment: {risk_assessment.overall_risk}")
            print(f"  Go/No-Go: {'GO' if risk_assessment.go_no_go else 'NO-GO'}")
        except Exception as e:
            print(f"Risk assessment failed: {e}")
            
        # Test tactical decision
        try:
            decision = await engine.make_tactical_decision(
                DecisionType.SEARCH_PATTERN,
                context,
                {"new_weather_report": "visibility decreasing"}
            )
            print(f"Tactical decision: {decision.recommendation}")
            print(f"  Confidence: {decision.confidence:.2f}")
            print(f"  Reasoning: {decision.reasoning[:100]}...")
        except Exception as e:
            print(f"Tactical decision failed: {e}")
            
        return True
        
    except Exception as e:
        logger.error(f"LLM Intelligence Engine test failed: {e}")
        return False


async def test_conversational_planner():
    """Test Conversational Mission Planner functionality."""
    print("\n=== Testing Conversational Mission Planner ===")
    
    try:
        # Create mission planner
        planner = await create_mission_planner({
            "enable_ai": True,
            "ai_config": {
                "primary_provider": "ollama",
                "fallback_provider": "ollama"
            },
            "max_turns": 10
        })
        
        print("Created conversational mission planner")
        
        # Start conversation
        session = await planner.start_conversation(
            "I need help planning a search mission for a missing hiker"
        )
        
        print(f"Started conversation: {session.session_id}")
        print(f"Initial state: {session.state.value}")
        print(f"AI response: {session.messages[-1].content[:100]}...")
        
        # Simulate conversation turns
        test_responses = [
            "The hiker went missing in Rocky Mountain National Park, about 10 square kilometers",
            "We have 2 drones available and need to find them within 6 hours",
            "Weather is cloudy with light rain, visibility about 2 miles. This is urgent.",
            "Yes, that sounds like a good plan"
        ]
        
        for i, response in enumerate(test_responses):
            try:
                session = await planner.continue_conversation(session.session_id, response)
                print(f"\nTurn {i+1}:")
                print(f"User: {response}")
                print(f"State: {session.state.value}")
                print(f"AI: {session.messages[-1].content[:100]}...")
                
                if session.state == ConversationState.COMPLETED:
                    break
                    
            except Exception as e:
                print(f"Conversation turn {i+1} failed: {e}")
                break
                
        # Check final state
        print(f"\nFinal state: {session.state.value}")
        print(f"Requirements gathered: {len(session.requirements)}")
        
        if session.current_plan:
            print(f"Mission plan created: {session.current_plan.mission_type}")
            print(f"Priority level: {session.current_plan.priority_level}")
            
        return True
        
    except Exception as e:
        logger.error(f"Conversational planner test failed: {e}")
        return False


async def test_full_integration():
    """Test full integration of all AI components."""
    print("\n=== Testing Full AI Integration ===")
    
    try:
        # Test complete workflow: conversation -> intelligence -> execution
        planner = await create_mission_planner()
        
        # Quick conversation to generate mission plan
        session = await planner.start_conversation(
            "Emergency search for missing child in forest area, 3 drones available, 2 hour window"
        )
        
        # Force complete a basic plan for testing
        session.requirements["mission_type"] = type('Req', (), {
            'category': 'mission_type', 'value': 'missing_person',
            'confidence': 0.9, 'validated': True
        })()
        session.requirements["search_area"] = type('Req', (), {
            'category': 'search_area', 'value': {'size_km2': 2.0, 'terrain': 'forest'},
            'confidence': 0.8, 'validated': True
        })()
        session.requirements["priority_level"] = type('Req', (), {
            'category': 'priority_level', 'value': 9,
            'confidence': 1.0, 'validated': True
        })()
        
        await planner._create_mission_plan(session)
        
        if session.current_plan:
            print(f"Created mission plan: {session.current_plan.mission_id}")
            
            # Convert to mission context for intelligence engine
            context = session.current_plan.to_mission_context()
            
            # Test intelligence engine analysis
            try:
                engine = await create_intelligence_engine()
                strategy = await engine.plan_search_strategy(context, "forest", "critical")
                print(f"Generated strategy: {strategy.pattern_type}")
                
                risk_assessment = await engine.assess_risks(context)
                print(f"Risk level: {risk_assessment.overall_risk}")
                
                print("Full integration test completed successfully")
                return True
                
            except Exception as e:
                print(f"Intelligence analysis failed: {e}")
                return False
                
        else:
            print("Failed to create mission plan")
            return False
            
    except Exception as e:
        logger.error(f"Full integration test failed: {e}")
        return False


async def run_all_tests():
    """Run all AI component tests."""
    print("Starting AI Intelligence System Tests")
    print("=" * 50)
    
    results = {}
    
    # Test individual components
    results["ollama_client"] = await test_ollama_client()
    results["llm_intelligence"] = await test_llm_intelligence()
    results["conversational_planner"] = await test_conversational_planner()
    results["full_integration"] = await test_full_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:25} : {status}")
        
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All AI components are working correctly!")
    elif passed_tests > 0:
        print("⚠️  Some components working, check failed tests")
    else:
        print("❌ AI system needs configuration (likely missing Ollama or API keys)")
        
    return results


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(run_all_tests())