# SAR Drone Swarm Central Computer

A comprehensive Search and Rescue (SAR) drone coordination system with multi-drone coordination, real-time monitoring, AI-powered mission planning, and professional command center interface.

## Features

### ✅ Core Capabilities
- **Multi-Drone Coordination**: Advanced coordination engine for optimal resource allocation
- **Real-time Mission Monitoring**: Live tracking, video feeds, and progress visualization
- **AI-Powered Mission Planning**: Natural language mission planning with conversational AI
- **Interactive Map Interface**: Professional mapping with area selection and drone tracking
- **Weather Integration**: Real-time weather data for safe operations
- **Discovery Management**: Automated object detection and investigation workflows
- **Emergency Response**: Immediate stop/return-to-home capabilities
- **Analytics & Reporting**: Mission performance analysis and insights

### 🏗️ Architecture
- **Backend**: FastAPI with SQLAlchemy, comprehensive API endpoints
- **Frontend**: React with TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: WebSocket for live updates
- **AI Integration**: Ollama for conversational mission planning
- **Containerization**: Docker with docker-compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sar-drone-swarm-central-computer
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database**
   ```bash
   docker-compose exec backend python init_db.py
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

1. **Backend Development**
   ```bash
   cd backend
   pip install -r requirements.txt
   python init_db.py
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API and WebSocket services
│   │   └── contexts/      # React contexts
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml      # Container orchestration
```

## API Endpoints

### Drones
- `GET /api/v1/drones` - List all drones
- `POST /api/v1/drones/{drone_id}/register` - Register new drone
- `PUT /api/v1/drones/{drone_id}/update` - Update drone state
- `GET /api/v1/drones/{drone_id}/telemetry` - Get drone telemetry

### Missions
- `GET /api/v1/missions` - List all missions
- `POST /api/v1/missions` - Create new mission
- `PUT /api/v1/missions/{mission_id}/start` - Start mission
- `GET /api/v1/missions/{mission_id}/status` - Get mission status

### Discoveries
- `GET /api/v1/discoveries` - List discoveries
- `POST /api/v1/discoveries` - Create discovery
- `POST /api/v1/discoveries/{discovery_id}/evidence` - Upload evidence

### Chat (AI Planning)
- `POST /api/v1/chat/sessions` - Create chat session
- `POST /api/v1/chat/sessions/{session_id}/messages` - Send message
- `POST /api/v1/chat/sessions/{session_id}/generate-mission` - Generate mission plan

### Analytics
- `GET /api/v1/analytics/system-overview` - System analytics
- `GET /api/v1/analytics/missions/{mission_id}` - Mission analytics
- `GET /api/v1/analytics/drones/{drone_id}` - Drone analytics

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./sar_missions.db

# Weather API (optional)
WEATHER_API_KEY=your_openweather_api_key

# Ollama AI (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Security
SECRET_KEY=your-secret-key-here
```

### Docker Configuration

The `docker-compose.yml` includes:
- Backend API server
- Frontend React application
- Ollama AI service (optional)
- Nginx reverse proxy

## Usage Guide

### Mission Planning
1. **Manual Planning**: Use the Mission Planning page to create missions with specific parameters
2. **AI Planning**: Use the conversational AI to describe your mission requirements in natural language

### Mission Execution
1. **Start Mission**: Begin mission execution with real-time monitoring
2. **Monitor Progress**: Track drone positions, battery levels, and discoveries
3. **Manage Discoveries**: Investigate detected objects and manage evidence

### Real-time Features
- Live drone position tracking
- Real-time video streaming (planned)
- Instant emergency response
- Weather-aware mission adjustments

## Development

### Backend Services
- **CoordinationEngine**: Multi-drone coordination and conflict resolution
- **MissionExecution**: Mission lifecycle management
- **AnalyticsEngine**: Performance analysis and insights
- **WeatherService**: Real-time weather integration
- **TaskManager**: Resource allocation and task coordination

### Frontend Components
- **Interactive Map**: Leaflet-based mapping with drone tracking
- **Real-time Dashboard**: Live mission monitoring and control
- **Mission Planning Interface**: Both manual and AI-powered planning
- **Discovery Management**: Evidence collection and investigation

## Deployment

### Production Deployment
1. Update environment variables for production
2. Use PostgreSQL instead of SQLite
3. Configure proper SSL certificates
4. Set up monitoring and logging
5. Configure backup strategies

### Scaling Considerations
- Horizontal scaling of backend services
- Redis for session management and caching
- CDN for static assets
- Load balancing for WebSocket connections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team

## Roadmap

- [ ] Video streaming integration
- [ ] Advanced AI object detection
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Integration with drone SDKs
- [ ] Offline mission planning
- [ ] Advanced weather modeling

---

**Built with ❤️ for Search and Rescue operations**