#!/usr/bin/env python3
"""
Basic test script for AI Intelligence components.
Tests import and basic functionality without external dependencies.
"""

import sys
import asyncio
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all AI modules can be imported."""
    print("Testing imports...")
    
    try:
        from ai.ollama_client import OllamaClient, GenerationRequest, OllamaError
        print("✓ Ollama client imported successfully")
    except ImportError as e:
        print(f"✗ Ollama client import failed: {e}")
        return False
        
    try:
        from ai.llm_intelligence import (
            LLMIntelligenceEngine, MissionContext, DecisionType,
            create_intelligence_engine
        )
        print("✓ LLM Intelligence Engine imported successfully")
    except ImportError as e:
        print(f"✗ LLM Intelligence Engine import failed: {e}")
        return False
        
    try:
        from ai.conversation import (
            ConversationalMissionPlanner, ConversationState,
            create_mission_planner
        )
        print("✓ Conversational Mission Planner imported successfully")
    except ImportError as e:
        print(f"✗ Conversational Mission Planner import failed: {e}")
        return False
        
    return True


def test_data_structures():
    """Test that data structures can be created."""
    print("\nTesting data structures...")
    
    try:
        from ai.ollama_client import GenerationRequest
        request = GenerationRequest(
            prompt="Test prompt",
            model="test-model",
            temperature=0.7
        )
        print(f"✓ GenerationRequest created: {request.model}")
    except Exception as e:
        print(f"✗ GenerationRequest creation failed: {e}")
        return False
        
    try:
        from ai.llm_intelligence import MissionContext
        context = MissionContext(
            mission_id="test-001",
            mission_type="test_mission",
            search_area={"size": 10},
            weather_conditions={"temp": 20},
            available_drones=[],
            time_constraints={},
            priority_level=5,
            discovered_objects=[],
            current_progress=0.0
        )
        print(f"✓ MissionContext created: {context.mission_id}")
    except Exception as e:
        print(f"✗ MissionContext creation failed: {e}")
        return False
        
    try:
        from ai.conversation import ConversationMessage, MessageRole
        message = ConversationMessage(
            role=MessageRole.USER,
            content="Test message"
        )
        print(f"✓ ConversationMessage created: {message.role.value}")
    except Exception as e:
        print(f"✗ ConversationMessage creation failed: {e}")
        return False
        
    return True


async def test_basic_functionality():
    """Test basic functionality without external services."""
    print("\nTesting basic functionality...")
    
    try:
        from ai.ollama_client import OllamaClient
        
        # Test client creation (won't connect)
        client = OllamaClient(base_url="http://localhost:11434")
        print("✓ OllamaClient created successfully")
        
        # Test request creation
        from ai.ollama_client import GenerationRequest
        request = GenerationRequest(
            prompt="What is SAR?",
            model="test-model",
            temperature=0.5
        )
        print("✓ GenerationRequest configured successfully")
        
    except Exception as e:
        print(f"✗ Ollama client functionality failed: {e}")
        return False
        
    try:
        from ai.llm_intelligence import create_intelligence_engine
        
        # Test engine creation without API keys (will use fallback)
        engine = await create_intelligence_engine({
            "primary_provider": "ollama",
            "fallback_provider": "ollama",
            "temperature": 0.3
        })
        print("✓ LLM Intelligence Engine created successfully")
        
    except Exception as e:
        print(f"✗ LLM Intelligence Engine functionality failed: {e}")
        return False
        
    try:
        from ai.conversation import create_mission_planner
        
        # Test planner creation without AI (fallback mode)
        planner = await create_mission_planner({
            "enable_ai": False,  # Disable AI for basic test
            "max_turns": 10
        })
        print("✓ Conversational Mission Planner created successfully")
        
        # Test conversation start
        session = await planner.start_conversation(
            "Test mission planning request"
        )
        print(f"✓ Conversation session started: {session.session_id}")
        
    except Exception as e:
        print(f"✗ Conversational Mission Planner functionality failed: {e}")
        return False
        
    return True


def test_configuration():
    """Test configuration and parameter handling."""
    print("\nTesting configuration...")
    
    try:
        from ai.llm_intelligence import LLMProvider, DecisionType
        
        # Test enums
        provider = LLMProvider.OLLAMA
        decision = DecisionType.SEARCH_PATTERN
        print(f"✓ Enums work: {provider.value}, {decision.value}")
        
        # Test data validation
        from ai.llm_intelligence import SearchStrategy
        strategy = SearchStrategy(
            pattern_type="grid",
            coverage_priority="balanced",
            drone_assignments=[],
            waypoint_density="medium",
            estimated_time=60,
            success_probability=0.75
        )
        print(f"✓ SearchStrategy validation: {strategy.pattern_type}")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False
        
    return True


async def run_basic_tests():
    """Run all basic tests."""
    print("=" * 60)
    print("SAR DRONE AI INTELLIGENCE - BASIC TESTS")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test data structures
    results.append(("Data Structures", test_data_structures()))
    
    # Test basic functionality
    results.append(("Basic Functionality", await test_basic_functionality()))
    
    # Test configuration
    results.append(("Configuration", test_configuration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
            
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All basic tests passed! AI components are properly installed.")
        print("\nNOTE: This test only verifies imports and basic functionality.")
        print("For full testing, you would need:")
        print("- Ollama server running locally")
        print("- OpenAI API key for external LLM testing")
        print("- Claude API key for external LLM testing")
    elif passed > 0:
        print(f"\n⚠️  {passed} tests passed, {len(results)-passed} failed.")
        print("Check the failed tests above.")
    else:
        print("\n❌ All tests failed. Check your Python environment and dependencies.")
        
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_basic_tests())
    sys.exit(0 if success else 1)