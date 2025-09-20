#!/usr/bin/env python3
"""
Comprehensive test runner for SAR Drone System
"""
import sys
import os
import traceback
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_all_tests():
    """Run all test modules"""
    print("=" * 60)
    print("SAR DRONE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Geometry utilities
    print("\n1. TESTING GEOMETRY UTILITIES")
    print("-" * 40)
    try:
        from app.tests.test_geometry import TestGeometryCalculator
        test_calc = TestGeometryCalculator()
        
        test_calc.test_coordinate_creation()
        print("✓ Coordinate creation")
        
        test_calc.test_degrees_radians_conversion()
        print("✓ Degrees/radians conversion")
        
        test_calc.test_haversine_distance()
        print("✓ Distance calculation")
        
        test_calc.test_bearing_calculation()
        print("✓ Bearing calculation")
        
        test_calc.test_destination_calculation()
        print("✓ Destination calculation")
        
        test_calc.test_polygon_area_calculation()
        print("✓ Area calculation")
        
        test_calc.test_search_grid_generation()
        print("✓ Search grid generation")
        
        test_calc.test_waypoint_calculation()
        print("✓ Waypoint calculation")
        
        test_calc.test_drone_path_optimization()
        print("✓ Path optimization")
        
        test_calc.test_flight_time_calculation()
        print("✓ Flight time calculation")
        
        test_calc.test_no_fly_zone_check()
        print("✓ No-fly zone checking")
        
        test_results.append(("Geometry Utilities", "PASSED"))
        
    except Exception as e:
        print(f"✗ Geometry tests failed: {e}")
        traceback.print_exc()
        test_results.append(("Geometry Utilities", "FAILED"))
    
    # Test 2: Logging system
    print("\n2. TESTING LOGGING SYSTEM")
    print("-" * 40)
    try:
        from app.tests.test_logging import run_logging_tests
        run_logging_tests()
        test_results.append(("Logging System", "PASSED"))
        
    except Exception as e:
        print(f"✗ Logging tests failed: {e}")
        traceback.print_exc()
        test_results.append(("Logging System", "FAILED"))
    
    # Test 3: FastAPI application
    print("\n3. TESTING FASTAPI APPLICATION")
    print("-" * 40)
    try:
        from app.tests.test_main import run_fastapi_tests
        run_fastapi_tests()
        test_results.append(("FastAPI Application", "PASSED"))
        
    except Exception as e:
        print(f"✗ FastAPI tests failed: {e}")
        traceback.print_exc()
        test_results.append(("FastAPI Application", "FAILED"))
    
    # Test 4: Integration tests
    print("\n4. TESTING SYSTEM INTEGRATION")
    print("-" * 40)
    try:
        # Test that all modules can be imported together
        from app.main import app
        from app.utils.geometry import GeometryCalculator, Coordinate
        from app.utils.logging import MissionLogger
        from app.core.config import settings
        
        print("✓ All modules import successfully")
        
        # Test basic integration
        coord1 = Coordinate(40.7128, -74.0060)
        coord2 = Coordinate(40.7589, -73.9851)
        distance = GeometryCalculator.haversine_distance(coord1, coord2)
        print(f"✓ Calculated distance between coordinates: {distance:.2f} km")
        
        logger = MissionLogger("integration_test", "test_mission")
        logger.info("Integration test successful")
        print("✓ Mission logger integration")
        
        print(f"✓ Application configured: {settings.PROJECT_NAME}")
        
        test_results.append(("System Integration", "PASSED"))
        
    except Exception as e:
        print(f"✗ Integration tests failed: {e}")
        traceback.print_exc()
        test_results.append(("System Integration", "FAILED"))
    
    # Test 5: Configuration validation
    print("\n5. TESTING CONFIGURATION")
    print("-" * 40)
    try:
        from app.core.config import settings
        
        # Validate required settings
        assert settings.PROJECT_NAME
        print(f"✓ Project name: {settings.PROJECT_NAME}")
        
        assert settings.VERSION
        print(f"✓ Version: {settings.VERSION}")
        
        assert settings.API_V1_STR
        print(f"✓ API version: {settings.API_V1_STR}")
        
        assert settings.DATABASE_URL
        print(f"✓ Database URL configured")
        
        assert settings.LOG_LEVEL
        print(f"✓ Log level: {settings.LOG_LEVEL}")
        
        assert len(settings.BACKEND_CORS_ORIGINS) > 0
        print(f"✓ CORS origins configured: {len(settings.BACKEND_CORS_ORIGINS)} origins")
        
        test_results.append(("Configuration", "PASSED"))
        
    except Exception as e:
        print(f"✗ Configuration tests failed: {e}")
        traceback.print_exc()
        test_results.append(("Configuration", "FAILED"))
    
    # Print final results
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_count = 0
    failed_count = 0
    
    for test_name, result in test_results:
        status_symbol = "✓" if result == "PASSED" else "✗"
        print(f"{status_symbol} {test_name}: {result}")
        
        if result == "PASSED":
            passed_count += 1
        else:
            failed_count += 1
    
    print("-" * 60)
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    
    if failed_count == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {failed_count} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)