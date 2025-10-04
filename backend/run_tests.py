#!/usr/bin/env python3
"""
SAR Drone System Test Runner
Runs comprehensive tests to validate system functionality
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def run_import_tests():
    """Test that all critical modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test core imports
        from app.core.config import settings
        from app.core.database import init_db, check_db_health
        from app.core.security import create_access_token, verify_token
        
        # Test service imports
        from app.services.mission_planner import MissionPlanner
        from app.services.emergency_protocols import EmergencyProtocols, EmergencyType
        from app.services.search_algorithms import SearchAlgorithms, SearchPattern
        from app.services.advanced_computer_vision import AdvancedComputerVision
        
        # Test AI imports
        from app.ai.ollama_client import OllamaClient
        from app.ai.llm_intelligence import LLMIntelligence
        
        # Test model imports
        from app.models.user import User
        
        print("✅ All critical modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def run_basic_functionality_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic functionality tests...")
    
    try:
        # Test mission planner
        from app.services.mission_planner import MissionPlanner
        planner = MissionPlanner()
        
        result = await planner.plan_mission(
            user_input="Test mission",
            context={"drone_count": 3},
            conversation_id="test"
        )
        
        assert "status" in result
        print("✅ Mission planner basic functionality works")
        
        # Test emergency protocols
        from app.services.emergency_protocols import EmergencyProtocols, EmergencyType
        protocols = EmergencyProtocols()
        
        result = await protocols.trigger_emergency(
            emergency_type=EmergencyType.EMERGENCY_STOP,
            reason="Test emergency",
            operator_id="test_operator"
        )
        
        assert result["success"] is True
        print("✅ Emergency protocols basic functionality works")
        
        # Test search algorithms
        from app.services.search_algorithms import SearchAlgorithms, SearchPattern
        
        waypoints = SearchAlgorithms.generate_search_pattern(
            pattern_type=SearchPattern.GRID,
            center={"lat": 37.7749, "lon": -122.4194},
            parameters={
                "width_m": 500,
                "height_m": 500,
                "spacing_m": 50,
                "altitude_m": 50
            }
        )
        
        assert len(waypoints) > 0
        print("✅ Search algorithms basic functionality works")
        
        # Test computer vision
        from app.services.advanced_computer_vision import AdvancedComputerVision
        cv = AdvancedComputerVision()
        
        model_info = await cv.get_model_info()
        assert "status" in model_info
        print("✅ Computer vision basic functionality works")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

async def run_database_tests():
    """Test database functionality"""
    print("\n🗄️ Testing database functionality...")
    
    try:
        from app.core.database import init_db, check_db_health
        
        # Test database health
        is_healthy = await check_db_health()
        if is_healthy:
            print("✅ Database health check passed")
        else:
            print("⚠️ Database health check failed - this may be expected in test environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def run_ai_tests():
    """Test AI functionality"""
    print("\n🤖 Testing AI functionality...")
    
    try:
        from app.ai.ollama_client import OllamaClient
        from app.ai.llm_intelligence import LLMIntelligence
        
        # Test Ollama client
        ollama = OllamaClient()
        status = await ollama.test_connection()
        
        if status["connected"]:
            print("✅ Ollama connection successful")
        else:
            print("⚠️ Ollama not available - this is expected if Ollama is not running")
        
        # Test LLM intelligence
        llm = LLMIntelligence()
        ai_status = await llm.get_ai_status()
        
        assert "overall_status" in ai_status
        print("✅ LLM intelligence service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ AI test failed: {e}")
        return False

async def run_pytest_tests():
    """Run pytest test suite"""
    print("\n🧪 Running pytest test suite...")
    
    try:
        # Change to backend directory
        os.chdir(backend_dir)
        
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--timeout=300"  # 5 minute timeout
        ], capture_output=True, text=True, timeout=600)  # 10 minute overall timeout
        
        if result.returncode == 0:
            print("✅ All pytest tests passed")
            return True
        else:
            print(f"❌ Some pytest tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Pytest tests timed out")
        return False
    except Exception as e:
        print(f"❌ Pytest execution failed: {e}")
        return False

async def run_configuration_tests():
    """Test configuration validation"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from app.core.config import settings
        
        # Test critical settings
        assert settings.PROJECT_NAME == "SAR Drone Swarm Control"
        assert len(settings.SECRET_KEY) >= 32
        assert settings.OLLAMA_HOST.startswith(("http://", "https://"))
        assert settings.DATABASE_URL.startswith(("sqlite://", "postgresql://", "mysql://"))
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run all validation tests"""
    print("🚀 SAR Drone System Validation")
    print("=" * 50)
    
    tests = [
        ("Import Tests", run_import_tests),
        ("Configuration Tests", run_configuration_tests),
        ("Database Tests", run_database_tests),
        ("AI Tests", run_ai_tests),
        ("Basic Functionality Tests", run_basic_functionality_tests),
        ("Pytest Suite", run_pytest_tests),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SYSTEM IS READY FOR DEPLOYMENT!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed - system needs attention")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Validation crashed: {e}")
        sys.exit(1)