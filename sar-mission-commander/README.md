# Mission Commander SAR Drone System

A professional Search and Rescue drone control system designed for emergency response operations. This system provides conversational AI mission planning, real-time multi-drone coordination, and comprehensive monitoring capabilities.

## 🚁 System Overview

### Central Computer (Windows Desktop Application)
- **Conversational AI Mission Planning**: Natural language input ("Search the collapsed building")
- **Interactive Map Interface**: Draw areas, see coverage calculations  
- **Real-time Multi-drone Monitoring**: Live telemetry, video streams, progress tracking
- **Individual Drone Commands**: Direct control of specific drones
- **Learning System**: Performance optimization based on mission outcomes

### Raspberry Pi (Per Drone - Autonomous Intelligence)
- **Mission Interpretation**: JSON context processing for autonomous operation
- **Independent Navigation**: GPS-based autonomous flight and search execution
- **Real-time Object Detection**: AI-powered discovery identification
- **Individual Command Handling**: Response to direct operator commands
- **MAVLink Integration**: Flight controller communication

## 🏗️ Architecture

```
👤 User ↔ 🖥️ Central Computer ↔ 📡 JSON/WebSocket ↔ 🚁 Raspberry Pi ↔ 🎛️ Flight Controller
```

## 🛠️ Technology Stack

- **Backend**: FastAPI + Python + SQLAlchemy + PostgreSQL
- **Frontend**: React + TypeScript + Leaflet Maps + Tailwind CSS  
- **AI**: Ollama (local LLM) + YOLOv8 (object detection)
- **Communication**: WebSocket + JSON protocol
- **Drone AI**: Python + OpenCV + PyMAVLink + GPS

## 📋 Project Status

### ✅ Phase 1: Foundation Setup (COMPLETED)
- [x] Complete project structure created
- [x] Backend Python environment configured
- [x] Frontend React environment configured  
- [x] Docker development setup ready
- [x] Database models defined
- [x] Basic API structure established

### 🔄 Next Phases
- **Phase 2**: Conversational Mission Planning System
- **Phase 3**: AI Integration (Ollama client, decision engines)
- **Phase 4**: API Endpoints and Services
- **Phase 5**: React Frontend Components
- **Phase 6**: WebSocket Real-time Communication
- **Phase 7**: Raspberry Pi Drone System Architecture

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd sar-mission-commander
   ```

2. **Start with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Backend setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload
   ```

2. **Frontend setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📁 Project Structure

```
sar-mission-commander/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── core/              # Configuration, database, security
│   │   ├── api/               # API route handlers
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic services
│   │   ├── ai/                # AI components (Ollama, conversation)
│   │   ├── utils/             # Utility functions
│   │   └── tests/             # Test suite
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Docker configuration
│   └── .env.example          # Environment template
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Main pages
│   │   ├── services/         # API services
│   │   ├── hooks/            # Custom React hooks
│   │   ├── types/            # TypeScript definitions
│   │   └── utils/            # Utility functions
│   ├── package.json          # Node.js dependencies
│   └── vite.config.ts        # Vite configuration
├── docker-compose.yml         # Development environment
└── README.md                 # This file
```

## 🎯 Key Features (Planned)

### Mission Planning
- ✅ Natural language input processing
- ✅ Interactive map-based area selection
- ✅ Automatic coordinate generation
- ✅ Multi-drone coordination
- ✅ Safety validation and no-fly zones

### Real-time Operations  
- ✅ Live drone position tracking
- ✅ Multi-stream video monitoring
- ✅ Discovery detection and management
- ✅ Emergency override capabilities
- ✅ Real-time progress visualization

### AI Intelligence
- ✅ Autonomous decision making with explanations
- ✅ Adaptive search pattern optimization  
- ✅ Object detection and recognition
- ✅ Learning from mission outcomes
- ✅ Transparent decision explanations

## 🔒 Production Considerations

- **Security**: Authentication, authorization, encrypted communication
- **Reliability**: Failover systems, backup communication channels
- **Scalability**: Support for 50+ concurrent drones
- **Compliance**: Emergency services integration, evidence chain of custody
- **Performance**: Sub-second response times, real-time data processing

## 📖 Documentation

- [Build Plan](Build_plan.md) - Complete implementation guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Architecture Overview](docs/architecture.md) - System design details
- [Deployment Guide](docs/deployment.md) - Production deployment

## 🤝 Contributing

This is a critical emergency response system. All contributions must maintain the highest standards of reliability and safety.

## 📄 License

[License information to be added]

---

**⚠️ IMPORTANT**: This system is designed for professional emergency response operations. Proper training and certification are required before deployment in actual SAR missions.