# SAR Mission Commander

A comprehensive Search and Rescue drone mission management system with AI-powered planning and real-time command capabilities.

## Features

### 🚁 Mission Planning
- **Conversational AI Planning**: Natural language mission planning with intelligent questioning
- **Interactive Map Interface**: Visual mission area selection and drone coverage calculation
- **Multi-Drone Coordination**: Automatic optimal area division and flight path generation
- **Safety Validation**: Weather integration and safety constraint checking

### 📡 Real-time Operations
- **Live Drone Tracking**: GPS coordinates, altitude, heading, and battery monitoring
- **Multi-Stream Video**: Real-time video feeds with AI-powered discovery detection
- **Emergency Override**: Immediate stop, return-to-home, and manual control capabilities
- **Progress Visualization**: Real-time mission progress and coverage tracking

### 🤖 AI Intelligence
- **Autonomous Decisions**: Smart routing and adaptive search patterns
- **Object Detection**: AI-powered discovery identification and classification
- **Learning System**: Performance optimization based on historical data
- **Transparent Explanations**: Clear reasoning for AI decisions and recommendations

### 🎛️ Command Center Interface
- **Multi-Monitor Support**: Professional emergency operations layout
- **Real-time Monitoring**: Live telemetry and video stream management
- **Discovery Management**: Investigation workflow and evidence handling
- **Analytics Dashboard**: Mission performance and fleet utilization metrics

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLAlchemy**: Database ORM with SQLite support
- **WebSockets**: Real-time bidirectional communication
- **Pydantic**: Data validation and serialization
- **Ollama**: Local AI model integration

### Frontend
- **React 18**: Modern user interface framework
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool and development server
- **React Query**: Server state management

### Infrastructure
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **SQLite**: Lightweight database for development

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sar-mission-commander
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

#### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload
```

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── ai/             # AI and conversational services
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Database and configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   ├── simulator/      # Drone simulation for testing
│   │   └── main.py         # Application entry point
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API integration services
│   │   ├── types/         # TypeScript type definitions
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Frontend container
└── docker-compose.yml     # Multi-service orchestration
```

## API Endpoints

### Missions
- `GET /api/v1/missions` - List all missions
- `POST /api/v1/missions` - Create new mission
- `GET /api/v1/missions/{id}` - Get mission details
- `PUT /api/v1/missions/{id}` - Update mission
- `DELETE /api/v1/missions/{id}` - Delete mission

### Drones
- `GET /api/v1/drones` - List all drones
- `POST /api/v1/drones` - Register new drone
- `GET /api/v1/drones/{id}/telemetry` - Get drone telemetry
- `POST /api/v1/drones/{id}/command` - Send drone command

### Discoveries
- `GET /api/v1/discoveries` - List discoveries
- `POST /api/v1/discoveries` - Report new discovery
- `PUT /api/v1/discoveries/{id}` - Update discovery
- `POST /api/v1/discoveries/{id}/investigate` - Start investigation

### Chat (AI Planning)
- `POST /api/v1/chat/converse` - Conversational mission planning
- `GET /api/v1/chat/messages` - Get chat history
- `POST /api/v1/chat/plan-mission` - Start new mission planning

## Mission Planning Workflow

1. **Initiate Planning**: User starts conversation with AI planner
2. **Location Input**: AI asks for search area coordinates or description
3. **Area Definition**: User specifies search area size and boundaries
4. **Altitude Setting**: AI recommends optimal flight altitude
5. **Priority Assessment**: System evaluates mission priority and urgency
6. **Plan Generation**: AI creates comprehensive mission plan
7. **User Approval**: Mission plan presented for final approval
8. **Execution**: Approved plan deployed to drone fleet

## Configuration

### Environment Variables
- `DATABASE_URL`: Database connection string (default: sqlite:///./sar_missions.db)
- `API_HOST`: Backend API host (default: 0.0.0.0)
- `API_PORT`: Backend API port (default: 8000)
- `OLLAMA_BASE_URL`: Ollama AI service URL (default: http://localhost:11434)

### Mission Parameters
- **Max Drones**: Maximum drones per mission (default: 10)
- **Search Altitude**: Default search altitude in meters (default: 50)
- **Max Duration**: Maximum mission duration in minutes (default: 120)

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

---

**Note**: This is a sophisticated system designed for professional SAR operations. Always ensure proper training and certification before using in real emergency situations.