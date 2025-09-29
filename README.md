# SAR Mission Commander

A comprehensive Search and Rescue (SAR) Mission Command and Control System built with modern web technologies.

## 🚀 Features

### Core Capabilities
- **Conversational Mission Planning**: AI-powered natural language mission planning with intelligent context awareness
- **Real-time Mission Tracking**: Live mission status updates and progress monitoring
- **Multi-Drone Coordination**: Support for coordinating multiple drone operations
- **Discovery Management**: AI-assisted object detection and discovery tracking
- **Chat Integration**: Real-time chat with AI mission coordinator
- **WebSocket Notifications**: Live updates for mission events and notifications

### Technical Features
- **FastAPI Backend**: High-performance Python API with async support
- **React Frontend**: Modern React application with TypeScript
- **PostgreSQL Database**: Robust data storage with proper relationships
- **Ollama AI Integration**: Local AI model integration for mission planning
- **WebSocket Support**: Real-time bidirectional communication
- **Docker Deployment**: Production-ready containerized deployment
- **Comprehensive Testing**: Unit, integration, and end-to-end tests

## 🏗️ Architecture

### Backend Structure
```
backend/
├── app/
│   ├── core/           # Database, config, utilities
│   ├── api/            # API endpoints and WebSocket handlers
│   ├── models/         # Database models
│   ├── services/       # Business logic services
│   ├── ai/             # AI integration (Ollama)
│   ├── simulator/      # Drone simulation for testing
│   └── utils/          # Utility functions
├── requirements.txt    # Python dependencies
└── Dockerfile          # Container configuration
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/     # React components
│   ├── services/       # API and WebSocket services
│   ├── pages/          # Application pages
│   ├── types/          # TypeScript type definitions
│   └── utils/          # Utility functions
├── package.json        # Node.js dependencies
└── Dockerfile          # Container configuration
```

## 🛠️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)
- Ollama (for AI features)

### Quick Start with Docker

1. **Clone and navigate to the repository**
   ```bash
   git clone <repository-url>
   cd sar-mission-commander
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**
   ```bash
   # Check backend
   curl http://localhost:8000/health

   # Check frontend
   curl http://localhost:3000

   # Check database
   docker-compose exec db pg_isready -U postgres

   # Check Ollama
   curl http://localhost:11434/api/tags
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

#### Backend Development
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app.core.database import create_tables; create_tables()"

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

### AI Setup (Ollama)

1. **Install Ollama**
   ```bash
   # On Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # On macOS
   brew install ollama

   # On Windows
   # Download from https://ollama.ai/download
   ```

2. **Pull required model**
   ```bash
   ollama pull phi3:mini
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

## 📊 API Endpoints

### Mission Management
- `GET /api/missions/` - List all missions
- `POST /api/missions/` - Create new mission
- `GET /api/missions/{id}` - Get mission details
- `PUT /api/missions/{id}` - Update mission
- `DELETE /api/missions/{id}` - Delete mission

### Chat Integration
- `GET /api/missions/{id}/chat` - Get mission chat history
- `POST /api/missions/{id}/chat` - Send chat message
- `POST /api/missions/{id}/start` - Start mission
- `POST /api/missions/{id}/complete` - Complete mission

### WebSocket
- `WS /ws/client/{client_id}` - WebSocket connection for real-time updates

### Health & Status
- `GET /health` - Health check
- `GET /api/v1/status` - API status with service information

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-32-char-minimum-secret-key
ALLOWED_ORIGINS=https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
```

#### Frontend (.env)
```bash
# API
REACT_APP_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws

# Maps
VITE_MAPBOX_TOKEN=your-mapbox-token

# Features
VITE_ENABLE_DEBUG_TOOLS=false
```

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_mission_planner.py
```

### Frontend Tests
```bash
cd frontend

# Run unit tests
npm test

# Run with UI
npm run test:ui

# Run e2e tests
npm run test:e2e
```

### Integration Tests
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest app/tests/test_integration.py
```

## 🚀 Deployment

### Production Deployment
```bash
# Build and start all services
docker-compose up -d

# Or build specific services
docker-compose build backend
docker-compose build frontend
```

### Environment Setup
1. Copy configuration files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. Update configuration for production:
   - Set secure `SECRET_KEY`
   - Configure database credentials
   - Set proper domain names
   - Configure SSL certificates

3. Set up reverse proxy (nginx example included)

### SSL Configuration
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# Update nginx configuration with your domain
# Edit nginx.conf and replace yourdomain.com
```

## 📈 Monitoring

### Health Checks
- Backend: `GET /health`
- Frontend: `GET /`
- Database: PostgreSQL health check
- Ollama: `GET /api/tags`

### Logs
- Application logs: `./backend/logs/`
- Docker logs: `docker-compose logs [service-name]`
- Database logs: Available via docker-compose

### Metrics (Optional)
- Prometheus metrics endpoint: `/metrics`
- Sentry error tracking
- Custom dashboards for mission analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `npm test && pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📝 Mission Planning Workflow

1. **Initiate Mission**: Use conversational interface to describe mission requirements
2. **AI Analysis**: System analyzes requirements and suggests optimal parameters
3. **Parameter Refinement**: Interactive chat to refine mission details
4. **Mission Creation**: System creates structured mission with optimal settings
5. **Execution**: Deploy drones and monitor progress in real-time
6. **Discovery Management**: AI-assisted identification and verification of discoveries
7. **Completion**: Mission wrap-up with analytics and reporting

## 🔒 Security Considerations

- All API endpoints require proper authentication headers
- Environment variables for sensitive configuration
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection in frontend
- CORS configuration for cross-origin requests
- Rate limiting for API endpoints
- Secure WebSocket connections (WSS in production)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, React, and modern web technologies
- AI integration powered by Ollama
- Database operations with SQLAlchemy
- Real-time updates via WebSockets
- Containerized with Docker

---

**Status**: ✅ Active Development | 📧 Contact: your-email@example.com
