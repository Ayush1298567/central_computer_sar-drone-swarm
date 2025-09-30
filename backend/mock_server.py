#!/usr/bin/env python3
"""
Mock Backend Server for Frontend Testing

Simple HTTP server that mocks the SAR API endpoints for frontend testing.
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import re

PORT = 8000

class MockHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_json_response({
                'status': 'healthy',
                'version': '1.0.0',
                'database': {'status': 'healthy'},
                'ai_system': {'status': 'healthy', 'model': 'mock'}
            })
        elif self.path.startswith('/api/missions'):
            if self.path == '/api/missions':
                self.send_json_response({
                    'success': True,
                    'missions': []
                })
            elif match := re.match(r'/api/missions/([^/]+)$', self.path):
                mission_id = match.group(1)
                self.send_json_response({
                    'success': True,
                    'mission': {
                        'id': mission_id,
                        'name': f'Mission {mission_id}',
                        'status': 'active'
                    }
                })
        elif self.path.startswith('/api/drones'):
            if self.path == '/api/drones':
                self.send_json_response({
                    'success': True,
                    'drones': [
                        {
                            'id': 'drone_001',
                            'name': 'Search Drone 1',
                            'status': 'online',
                            'battery_level': 85
                        }
                    ]
                })
        elif self.path.startswith('/api/chat/sessions'):
            conversation_id = self.path.split('/')[-1]
            self.send_json_response({
                'success': True,
                'conversation_id': conversation_id,
                'messages': []
            })
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path == '/api/chat/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Mock AI response
            response = self.generate_mock_ai_response(data.get('message', ''))

            self.send_json_response({
                'success': True,
                'response': response
            })
        elif self.path.startswith('/api/missions'):
            if '/create' in self.path:
                self.send_json_response({
                    'success': True,
                    'mission': {
                        'id': 'new_mission_id',
                        'name': 'New Mission',
                        'status': 'planning'
                    }
                })
        else:
            self.send_error(404, 'Not Found')

    def generate_mock_ai_response(self, message):
        """Generate mock AI responses for testing."""
        message_lower = message.lower()

        if 'search' in message_lower and 'person' in message_lower:
            return {
                'response': "I understand you want to search for a missing person. I can help you plan an optimal search strategy with systematic coverage patterns. To create the best mission plan, I'll need to know the search area size and any specific constraints.",
                'confidence': 0.9,
                'conversation_id': 'test_session',
                'message_type': 'response',
                'next_action': 'area_selection'
            }
        elif 'collapsed' in message_lower and 'building' in message_lower:
            return {
                'response': "This appears to be a structural collapse emergency. I'll prioritize safety protocols and focus the search on the building area with emergency response coordination. I recommend using thermal imaging for survivor detection.",
                'confidence': 0.95,
                'conversation_id': 'test_session',
                'message_type': 'response',
                'next_action': 'emergency_protocols'
            }
        else:
            return {
                'response': f"I understand your mission requirements: '{message}'. Let me help you plan an effective search and rescue operation. I can assist with area selection, drone assignment, and mission optimization.",
                'confidence': 0.8,
                'conversation_id': 'test_session',
                'message_type': 'response',
                'next_action': 'mission_details'
            }

    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error(self, code, message):
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        error_data = {
            'success': False,
            'error': message,
            'status_code': code
        }
        self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    """Start the mock server."""
    print("🚀 Starting Mock SAR Backend Server")
    print(f"📍 Server running at http://localhost:{PORT}")
    print("📋 Available endpoints:")
    print("   GET  /health")
    print("   GET  /api/missions")
    print("   GET  /api/missions/{id}")
    print("   GET  /api/drones")
    print("   POST /api/missions/create")
    print("   POST /api/chat/message")
    print("   GET  /api/chat/sessions/{id}")
    print()

    with socketserver.TCPServer(("", PORT), MockHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Mock server stopped")

if __name__ == "__main__":
    main()