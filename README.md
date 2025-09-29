# SAR Drone Swarm Management System

A comprehensive Search and Rescue (SAR) drone swarm management system with real-time coordination, AI-powered mission planning, and advanced analytics.

## Features

- **Multi-Drone Coordination**: Advanced coordination engine for managing multiple drones simultaneously
- **Real-Time Mission Management**: Live tracking, monitoring, and control of SAR missions
- **AI-Powered Intelligence**: Autonomous decision-making, adaptive search patterns, and intelligent discovery management
- **Interactive Dashboard**: Modern React-based interface with real-time updates
- **Weather Integration**: Real-time weather monitoring and mission adjustments
- **Emergency Response**: Automated emergency protocols and safety systems

## Architecture

### Backend (FastAPI + Python)
- **API Layer**: RESTful APIs with automatic OpenAPI documentation
- **Coordination Engine**: Real-time multi-drone coordination with conflict resolution
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **WebSocket Support**: Real-time bidirectional communication
- **AI Integration**: Ollama integration for intelligent decision-making

### Frontend (React + TypeScript)
- **Modern UI**: React 18 with TypeScript and Tailwind CSS
- **Real-Time Updates**: WebSocket integration for live data
- **Interactive Maps**: Leaflet integration for mission visualization
- **State Management**: React Query for server state management
- **Component Library**: Reusable UI components with accessibility

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.9+ (for development)

### Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd sar-drone-swarm
   ```

2. **Start with Docker (Recommended):**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Backend API on http://localhost:8000
   - Frontend on http://localhost:3000
   - Ollama AI server on http://localhost:11434
   - PostgreSQL database on localhost:5432

3. **Manual Setup (Alternative):**

   **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Project Structure

```
sar-drone-swarm/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── ai/             # AI and Ollama integration
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── main.py         # FastAPI application
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   ├── simulator/      # Drone simulation
│   │   └── utils/          # Utility functions
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API and WebSocket services
│   │   ├── types/         # TypeScript definitions
│   │   └── utils/         # Utility functions
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Development environment
└── README.md
```

## Key Components

### Coordination Engine
- **Multi-drone coordination** with collision avoidance
- **Dynamic mission optimization** based on real-time conditions
- **Battery management** and automatic return-to-home
- **Weather-aware** mission adjustments
- **Emergency response** protocols

### AI Intelligence
- **Conversational mission planning** with natural language processing
- **Autonomous decision-making** for search pattern optimization
- **Object detection** and discovery classification
- **Predictive analytics** for mission success probability

### Real-Time Features
- **Live drone tracking** with position updates
- **Real-time video streaming** from drone cameras
- **Instant discovery notifications** with priority levels
- **Emergency alerts** and automated responses

## Development Workflow

1. **Mission Planning**: Use the conversational AI interface to plan missions
2. **Drone Assignment**: Automatically assign optimal drones to search areas
3. **Live Monitoring**: Track mission progress with real-time updates
4. **Discovery Management**: Handle discoveries with AI-powered prioritization
5. **Analytics**: Review mission performance and optimize future operations

## Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite:///./sar_missions.db
SECRET_KEY=your-secret-key
OLLAMA_BASE_URL=http://localhost:11434
WEATHER_API_KEY=your-weather-api-key
```

### Docker Configuration
The `docker-compose.yml` file includes:
- **Backend service** with auto-reload
- **Frontend development** server with hot reload
- **Ollama AI service** for intelligent features
- **PostgreSQL database** for production use

## Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Deployment

### Production Build
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup
1. Configure production database
2. Set up reverse proxy (nginx)
3. Configure SSL certificates
4. Set environment variables
5. Run database migrations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation

---

**Status**: ✅ 100% Functional for Development