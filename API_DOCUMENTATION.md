# API Documentation

## Mission Commander SAR Drone System API

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Missions

#### Create Mission
```http
POST /api/missions/create
Content-Type: application/json

{
  "name": "Emergency SAR Mission",
  "description": "Search for missing person in park area",
  "search_area": [
    [40.7829, -73.9654],
    [40.7829, -73.9494],
    [40.7739, -73.9494],
    [40.7739, -73.9654]
  ],
  "launch_point": [40.7829, -73.9654],
  "search_target": "person",
  "search_altitude": 25.0,
  "search_speed": "thorough",
  "recording_mode": "continuous"
}
```

**Response:**
```json
{
  "success": true,
  "mission": {
    "id": "mission_123",
    "name": "Emergency SAR Mission",
    "status": "planning",
    "search_area": [...],
    "launch_point": [40.7829, -73.9654],
    "search_target": "person",
    "search_altitude": 25.0,
    "created_at": "2024-01-15T10:00:00Z"
  },
  "message": "Mission created successfully"
}
```

#### Get Mission
```http
GET /api/missions/{mission_id}
```

**Response:**
```json
{
  "success": true,
  "mission": {
    "id": "mission_123",
    "name": "Emergency SAR Mission",
    "description": "Search for missing person in park area",
    "status": "active",
    "search_area": [...],
    "launch_point": [40.7829, -73.9654],
    "search_target": "person",
    "search_altitude": 25.0,
    "coverage_percentage": 45.0,
    "estimated_duration": 60,
    "created_at": "2024-01-15T10:00:00Z",
    "started_at": "2024-01-15T10:30:00Z",
    "drone_assignments": [
      {
        "drone_id": "drone_001",
        "assigned_area": [...],
        "navigation_waypoints": [...],
        "status": "searching",
        "progress_percentage": 35.0
      }
    ]
  }
}
```

#### Start Mission
```http
PUT /api/missions/{mission_id}/start
```

**Response:**
```json
{
  "success": true,
  "message": "Mission started successfully"
}
```

#### Complete Mission
```http
PUT /api/missions/{mission_id}/complete
Content-Type: application/json

{
  "coverage_percentage": 95.0,
  "discoveries": 2,
  "duration": 45
}
```

### Drones

#### Register Drone
```http
POST /api/drones/create
Content-Type: application/json

{
  "id": "drone_001",
  "name": "Alpha Drone",
  "model": "TestModel-X1",
  "status": "online",
  "battery_level": 90.0,
  "current_position": [40.7128, -74.0060, 10.0],
  "home_position": [40.7128, -74.0060, 0.0]
}
```

#### Get Drone Status
```http
GET /api/drones/{drone_id}
```

**Response:**
```json
{
  "success": true,
  "drone": {
    "id": "drone_001",
    "name": "Alpha Drone",
    "status": "flying",
    "battery_level": 78.0,
    "signal_strength": 95,
    "current_position": [40.7150, -74.0030, 25.0],
    "flight_mode": "AUTO",
    "missions_completed": 15,
    "total_flight_hours": 45.2
  }
}
```

#### Update Drone Status
```http
PUT /api/drones/{drone_id}/status
Content-Type: application/json

{
  "status": "flying",
  "battery_level": 75.0,
  "current_position": [40.7150, -74.0030, 25.0]
}
```

#### Submit Telemetry
```http
POST /api/drones/{drone_id}/telemetry
Content-Type: application/json

{
  "latitude": 40.7150,
  "longitude": -74.0030,
  "altitude": 25.0,
  "battery_percentage": 85.0,
  "flight_mode": "AUTO",
  "signal_strength": 95,
  "ground_speed": 5.2,
  "heading": 45.0
}
```

### Chat/AI Integration

#### Send Chat Message
```http
POST /api/chat/message
Content-Type: application/json

{
  "mission_id": "mission_123",
  "sender": "user",
  "content": "Search the collapsed building for survivors",
  "message_type": "text"
}
```

**Response:**
```json
{
  "success": true,
  "response": "I understand you want to search for survivors in the collapsed building. Let me help you plan this mission. What is the exact location and size of the area you want to search?",
  "confidence": 0.92,
  "message_type": "question",
  "next_action": "area_selection"
}
```

#### Get Chat History
```http
GET /api/chat/history/{mission_id}
```

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_001",
      "sender": "user",
      "content": "Search the collapsed building for survivors",
      "message_type": "text",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": "msg_002",
      "sender": "ai",
      "content": "I understand you want to search for survivors...",
      "message_type": "text",
      "confidence": 0.92,
      "created_at": "2024-01-15T10:00:05Z"
    }
  ]
}
```

#### Request AI Analysis
```http
POST /api/ai/analyze/{mission_id}
Content-Type: application/json

{
  "analysis_type": "search_pattern_optimization",
  "mission_context": {
    "search_area": [...],
    "search_target": "person",
    "environmental_conditions": {
      "wind_speed": 5.0,
      "visibility": 10000
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis_type": "search_pattern_optimization",
  "recommendations": [
    "Use lawnmower pattern for systematic coverage",
    "Adjust altitude to 25m for better detection",
    "Deploy 3 drones for optimal coverage"
  ],
  "confidence": 0.88,
  "estimated_improvement": 15.0
}
```

### Discoveries

#### Report Discovery
```http
POST /api/missions/{mission_id}/discoveries
Content-Type: application/json

{
  "object_type": "person",
  "confidence_score": 0.92,
  "latitude": 40.7150,
  "longitude": -74.0030,
  "altitude": 25.0,
  "detection_method": "visual",
  "environmental_conditions": {
    "lighting": "good",
    "weather": "clear"
  },
  "sensor_data": {
    "image_url": "https://example.com/detection_001.jpg",
    "thermal_signature": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "discovery": {
    "id": "discovery_001",
    "mission_id": "mission_123",
    "drone_id": "drone_001",
    "object_type": "person",
    "confidence_score": 0.92,
    "latitude": 40.7150,
    "longitude": -74.0030,
    "altitude": 25.0,
    "investigation_status": "pending",
    "priority_level": 4,
    "discovered_at": "2024-01-15T10:30:00Z"
  },
  "message": "Discovery reported successfully"
}
```

#### Update Discovery Status
```http
PUT /api/missions/{mission_id}/discoveries/{discovery_id}
Content-Type: application/json

{
  "investigation_status": "investigating",
  "human_verified": true,
  "verification_notes": "Confirmed person requiring rescue",
  "action_required": "rescue_team_dispatch"
}
```

### WebSocket Endpoints

#### Real-time Updates

**Telemetry Updates:**
```javascript
// Connect to telemetry WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

// Listen for telemetry updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event_type === 'telemetry_update') {
    console.log('Drone position:', data.data);
  }
};
```

**Discovery Notifications:**
```javascript
// Connect to discovery WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/discoveries');

// Listen for discovery alerts
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event_type === 'discovery_alert') {
    alert(`🚨 DISCOVERY: ${data.data.object_type} detected!`);
  }
};
```

**Mission Updates:**
```javascript
// Connect to mission WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/mission');

// Listen for mission status changes
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.event_type === 'mission_update') {
    console.log('Mission status:', data.data.status);
  }
};
```

## Error Handling

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (invalid data)
- **401**: Unauthorized (missing/invalid token)
- **404**: Not Found (resource doesn't exist)
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error

### Error Response Format

```json
{
  "error": true,
  "message": "Detailed error message",
  "status_code": 400,
  "timestamp": "2024-01-15T10:00:00Z",
  "path": "/api/missions/create",
  "details": {
    "field_name": ["Error description"]
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Chat endpoints**: 30 requests per minute
- **File upload endpoints**: 10 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhook Support

Configure webhooks for real-time notifications:

```http
POST /api/webhooks/register
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["discovery_alert", "mission_complete", "emergency_stop"],
  "secret": "your-webhook-secret"
}
```

## SDK Examples

### Python SDK

```python
from mission_commander import MissionCommander

# Initialize client
client = MissionCommander(api_key="your-api-key")

# Create mission
mission = client.create_mission({
    "name": "SAR Mission",
    "search_area": [...],
    "search_target": "person"
})

# Start conversational planning
response = client.chat(mission.id, "Search the building")
print(response.message)

# Monitor mission
status = client.get_mission_status(mission.id)
print(f"Coverage: {status.coverage_percentage}%")
```

### JavaScript SDK

```javascript
import { MissionCommander } from 'mission-commander-js';

const client = new MissionCommander({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:8000'
});

// Create mission
const mission = await client.missions.create({
  name: 'SAR Mission',
  searchArea: [...],
  searchTarget: 'person'
});

// Start chat
const response = await client.chat.sendMessage(mission.id, {
  content: 'Search the collapsed building'
});

console.log(response.response);
```

## Testing the API

### Using cURL

```bash
# Create a mission
curl -X POST "http://localhost:8000/api/missions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Mission",
    "search_area": [[40.7128, -74.0060], [40.7589, -74.0060], [40.7589, -73.9352], [40.7128, -73.9352]],
    "launch_point": [40.7128, -74.0060],
    "search_target": "person"
  }'

# Send chat message
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "mission_123",
    "sender": "user",
    "content": "Test message"
  }'
```

### Using Postman

1. Import the API collection
2. Set environment variables (base URL, auth token)
3. Use the pre-built requests for testing

## Versioning

API versions are specified in the URL:
- Current: `/api/v1/`
- Future versions will use `/api/v2/`, etc.

Breaking changes will be introduced in new major versions.