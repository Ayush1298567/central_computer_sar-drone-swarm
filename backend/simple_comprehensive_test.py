#!/usr/bin/env python3
"""
Simple Comprehensive System Test for SAR Drone System

Tests all components end-to-end using only standard library.
"""

import sys
import os
import json
import time
import socket
import subprocess
from pathlib import Path

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🧪 SIMPLE COMPREHENSIVE SAR DRONE SYSTEM TEST")
print("=" * 60)

class SimpleTester:
    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def log(self, message, status="INFO"):
        """Log test results."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        self.results.append({
            'timestamp': timestamp,
            'status': status,
            'message': message
        })

    def test_port_open(self, host, port):
        """Test if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def test_backend_server(self):
        """Test that the backend server is running."""
        self.log("Testing backend server connectivity...")

        if self.test_port_open('localhost', 8000):
            self.log("✅ Backend server is running on port 8000", "PASS")
            return True
        else:
            self.log("❌ Backend server not accessible on port 8000", "FAIL")
            return False

    def test_frontend_server(self):
        """Test that the frontend server is running."""
        self.log("Testing frontend server connectivity...")

        if self.test_port_open('localhost', 3000):
            self.log("✅ Frontend server is running on port 3000", "PASS")
            return True
        else:
            self.log("❌ Frontend server not accessible on port 3000", "FAIL")
            return False

    def test_logging_system(self):
        """Test that the logging system is working."""
        self.log("Testing logging system...")

        log_file = Path('logs/sar_system.log')
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        self.log(f"✅ Logging system active - {len(lines)} entries", "PASS")
                        return True
                    else:
                        self.log("❌ Log file exists but no entries", "FAIL")
                        return False
            except Exception as e:
                self.log(f"❌ Could not read log file: {e}", "FAIL")
                return False
        else:
            self.log("❌ Log file does not exist", "FAIL")
            return False

    def test_ai_service(self):
        """Test AI conversational service."""
        self.log("Testing AI conversational service...")

        try:
            from app.services.conversational_mission_planner import get_conversational_planner

            planner = get_conversational_planner()

            # Test AI response generation (synchronous for testing)
            test_message = "Search for missing person in park"

            # For testing purposes, we'll test the synchronous methods
            next_action = planner._determine_next_action(test_message)
            if next_action:
                self.log(f"✅ AI service working - next action: {next_action}", "PASS")
                return True
            else:
                self.log("❌ AI service returned invalid next action", "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ AI service test failed: {e}", "FAIL")
            return False

    def test_computer_vision(self):
        """Test computer vision service."""
        self.log("Testing computer vision service...")

        try:
            from app.services.computer_vision_service import cv_service

            # Test model status
            model_status = cv_service.get_model_status()
            if model_status.get('service_status') == 'operational':
                self.log(f"✅ CV service operational with {model_status['total_models']} models", "PASS")
                return True
            else:
                self.log("❌ CV service not operational", "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ CV service test failed: {e}", "FAIL")
            return False

    def test_directory_structure(self):
        """Test that all required directories exist."""
        self.log("Testing directory structure...")

        required_dirs = [
            'backend/app',
            'backend/logs',
            'frontend/src',
            'frontend/public',
        ]

        all_exist = True
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                self.log(f"✅ Directory exists: {dir_path}", "PASS")
            else:
                self.log(f"❌ Directory missing: {dir_path}", "FAIL")
                all_exist = False

        return all_exist

    def test_file_structure(self):
        """Test that key files exist."""
        self.log("Testing file structure...")

        key_files = [
            'backend/start.py',
            'backend/mock_server.py',
            'frontend/package.json',
            'frontend/vite.config.ts',
            'frontend/src/App.tsx',
            'frontend/src/main.tsx',
        ]

        all_exist = True
        for file_path in key_files:
            if Path(file_path).exists():
                self.log(f"✅ File exists: {file_path}", "PASS")
            else:
                self.log(f"❌ File missing: {file_path}", "FAIL")
                all_exist = False

        return all_exist

    def generate_report(self):
        """Generate comprehensive test report."""
        end_time = time.time()
        duration = end_time - self.start_time

        print("\n" + "=" * 60)
        print("📊 SIMPLE COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        print(f"Test Duration: {duration:.2f} seconds")
        print(f"Total Tests: {len(self.results)}")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = len(self.results) - passed

        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {passed/len(self.results)*100:.1f}%")

        print("\n📋 Detailed Results:")
        print("-" * 60)

        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['message']}")

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ SAR Drone System is fully functional")
            print("🚀 Ready for production deployment")
        else:
            print(f"\n⚠️ {failed} tests failed")
            print("🔧 System needs fixes before production")

        return failed == 0

def main():
    """Run comprehensive system tests."""
    tester = SimpleTester()

    # Run all tests
    tests = [
        tester.test_backend_server,
        tester.test_frontend_server,
        tester.test_logging_system,
        tester.test_ai_service,
        tester.test_computer_vision,
        tester.test_directory_structure,
        tester.test_file_structure,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            tester.log(f"Test execution error: {e}", "ERROR")

    # Generate final report
    success = tester.generate_report()

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)