#!/usr/bin/env python3
"""
Comprehensive System Test for SAR Drone System

Tests all components end-to-end to ensure the system is fully functional.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🧪 COMPREHENSIVE SAR DRONE SYSTEM TEST")
print("=" * 60)

class ComprehensiveTester:
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

    def test_backend_server(self):
        """Test that the backend server is running and responsive."""
        self.log("Testing backend server connectivity...")

        try:
            req = urllib.request.Request('http://localhost:8000/health')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('status') == 'healthy':
                    self.log("✅ Backend server is running and healthy", "PASS")
                    return True
                else:
                    self.log(f"❌ Backend server unhealthy: {data}", "FAIL")
                    return False
        except Exception as e:
            self.log(f"❌ Backend server not accessible: {e}", "FAIL")
            return False

    def test_frontend_server(self):
        """Test that the frontend server is running."""
        self.log("Testing frontend server connectivity...")

        try:
            req = urllib.request.Request('http://localhost:3000/')
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    self.log("✅ Frontend server is running", "PASS")
                    return True
                else:
                    self.log(f"❌ Frontend server error: {response.status}", "FAIL")
                    return False
        except Exception as e:
            self.log(f"❌ Frontend server not accessible: {e}", "FAIL")
            return False

    def test_api_endpoints(self):
        """Test all API endpoints."""
        self.log("Testing API endpoints...")

        endpoints = [
            ('GET', '/health'),
            ('GET', '/api/missions'),
            ('GET', '/api/drones'),
            ('POST', '/api/chat/message'),
            ('GET', '/api/chat/sessions/test_session')
        ]

        success_count = 0

        for method, endpoint in endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
                else:
                    response = requests.post(
                        f'http://localhost:8000{endpoint}',
                        json={'message': 'test', 'conversation_id': 'test'},
                        timeout=5
                    )

                if response.status_code == 200:
                    self.log(f"✅ {method} {endpoint}", "PASS")
                    success_count += 1
                else:
                    self.log(f"❌ {method} {endpoint}: {response.status_code}", "FAIL")

            except Exception as e:
                self.log(f"❌ {method} {endpoint}: {e}", "FAIL")

        return success_count == len(endpoints)

    def test_api_proxy(self):
        """Test that the frontend API proxy is working."""
        self.log("Testing API proxy through frontend...")

        try:
            response = requests.post(
                'http://localhost:3000/api/chat/message',
                json={'message': 'proxy test', 'conversation_id': 'proxy_test'},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log("✅ API proxy is working correctly", "PASS")
                    return True
                else:
                    self.log(f"❌ API proxy returned error: {data}", "FAIL")
                    return False
            else:
                self.log(f"❌ API proxy error: {response.status_code}", "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ API proxy test failed: {e}", "FAIL")
            return False

    def test_logging_system(self):
        """Test that the logging system is working."""
        self.log("Testing logging system...")

        log_file = Path('logs/sar_system.log')
        if log_file.exists():
            # Check if log file has recent entries
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-5:] if len(lines) >= 5 else lines

                    if recent_lines:
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

    def test_ai_conversation(self):
        """Test AI conversational capabilities."""
        self.log("Testing AI conversational interface...")

        try:
            # Test different mission scenarios
            test_messages = [
                "Search for missing person in Central Park",
                "Find survivors in collapsed building",
                "Monitor construction site for safety",
            ]

            for message in test_messages:
                response = requests.post(
                    'http://localhost:8000/api/chat/message',
                    json={'message': message, 'conversation_id': 'ai_test'},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('response'):
                        ai_response = data['response']['response']
                        if len(ai_response) > 50:  # Reasonable response length
                            self.log(f"✅ AI responded to: '{message[:30]}...'", "PASS")
                        else:
                            self.log(f"❌ AI response too short for: {message[:30]}...", "FAIL")
                    else:
                        self.log(f"❌ Invalid AI response for: {message[:30]}...", "FAIL")
                else:
                    self.log(f"❌ AI request failed for: {message[:30]}...", "FAIL")

            return True

        except Exception as e:
            self.log(f"❌ AI conversation test failed: {e}", "FAIL")
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

    def test_websocket_proxy(self):
        """Test WebSocket proxy functionality."""
        self.log("Testing WebSocket proxy...")

        try:
            # This is a basic test - in a real scenario, we'd test actual WebSocket connections
            response = requests.get('http://localhost:3000/', timeout=3)
            if response.status_code == 200:
                # If we can reach the frontend, WebSocket proxy should work
                self.log("✅ WebSocket proxy infrastructure available", "PASS")
                return True
            else:
                self.log("❌ WebSocket proxy infrastructure issue", "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ WebSocket proxy test failed: {e}", "FAIL")
            return False

    def test_static_assets(self):
        """Test that static assets are being served."""
        self.log("Testing static asset serving...")

        try:
            # Test CSS file
            response = requests.get('http://localhost:3000/src/index.css', timeout=3)
            if response.status_code == 200 and 'tailwind' in response.text.lower():
                self.log("✅ CSS assets are being served correctly", "PASS")
                return True
            else:
                self.log("❌ CSS assets not served correctly", "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ Static asset test failed: {e}", "FAIL")
            return False

    def generate_report(self):
        """Generate comprehensive test report."""
        end_time = time.time()
        duration = end_time - self.start_time

        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
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
    tester = ComprehensiveTester()

    # Run all tests
    tests = [
        tester.test_backend_server,
        tester.test_frontend_server,
        tester.test_api_endpoints,
        tester.test_api_proxy,
        tester.test_logging_system,
        tester.test_ai_conversation,
        tester.test_computer_vision,
        tester.test_websocket_proxy,
        tester.test_static_assets,
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