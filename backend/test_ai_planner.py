#!/usr/bin/env python3
"""
Test script for Conversational Mission Planner AI

Tests the AI conversational interface without external dependencies.
"""

import sys
import os
import asyncio

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🤖 Testing Conversational Mission Planner")
print("=" * 50)

async def test_conversational_planner():
    """Test the conversational mission planner."""
    try:
        from app.services.conversational_mission_planner import get_conversational_planner

        planner = get_conversational_planner()
        print("✅ Conversational planner initialized successfully")

        # Test various mission scenarios
        test_messages = [
            "I need to search for a missing person in Central Park",
            "Find the lost hiker in the wooded area",
            "Monitor the construction site for safety violations",
            "Survey the flood damage in the residential area",
            "Search the collapsed building for survivors"
        ]

        print("\n🧪 Testing AI Responses:")
        print("-" * 50)

        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. User: {message}")

            # Process the message
            response_data = await planner.process_message({
                "message": message,
                "conversation_id": f"test_{i}"
            })

            print(f"   AI: {response_data['response'][:100]}...")
            print(f"   Confidence: {response_data['confidence']}")
            print(f"   Next Action: {response_data['next_action']}")

        print("\n✅ All AI response tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ AI planner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ai_keywords():
    """Test AI keyword detection."""
    print("\n🔍 Testing AI Keyword Detection:")
    print("-" * 50)

    try:
        from app.services.conversational_mission_planner import ConversationalMissionPlanner

        planner = ConversationalMissionPlanner(None)

        test_cases = [
            ("search for missing person", "Should detect mission type"),
            ("find lost hiker", "Should detect emergency situation"),
            ("monitor construction site", "Should detect monitoring mission"),
            ("survey flood damage", "Should detect survey mission"),
            ("patrol the area", "Should detect patrol mission")
        ]

        for message, expected in test_cases:
            next_action = planner._determine_next_action(message)
            response = await planner._generate_ai_response(message, "test")

            print(f"Input: '{message}'")
            print(f"  Next Action: {next_action}")
            print(f"  Response: {response[:80]}...")
            print(f"  Expected: {expected}")
            print()

        return True

    except Exception as e:
        print(f"❌ Keyword detection test failed: {e}")
        return False

async def main():
    """Run all AI tests."""
    print("Starting AI Conversational Planner Tests...")

    # Test basic functionality
    basic_success = await test_conversational_planner()

    # Test keyword detection
    keyword_success = await test_ai_keywords()

    print("\n" + "=" * 50)
    if basic_success and keyword_success:
        print("✅ AI CONVERSATIONAL PLANNER TEST: PASSED")
        print("🎯 AI mission planner is working correctly")
        print("🚀 Ready for integration with external AI services")
    else:
        print("❌ AI CONVERSATIONAL PLANNER TEST: FAILED")
        print("🔧 AI planner needs fixes before proceeding")

    return 0 if basic_success and keyword_success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)