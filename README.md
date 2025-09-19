# SAR Drone Swarm Command Center

An advanced AI-powered Search and Rescue (SAR) drone coordination system with conversational mission planning, real-time monitoring, and intelligent decision-making capabilities.

## 🚁 System Overview

This system provides a comprehensive solution for managing SAR drone operations with the following key features:

### Core Capabilities
- **AI-Driven Mission Planning**: Conversational interface that asks clarifying questions until the user approves a complete mission plan
- **Real-time Operations**: Live tracking, video monitoring, discovery management, emergency override, and progress visualization  
- **AI Intelligence**: Autonomous decisions, adaptive patterns, object detection, learning, and decision explanation
- **Multi-drone Coordination**: Swarm operations with intelligent resource allocation
- **Safety Validation**: Comprehensive safety checks and emergency override systems

### Memory-Based Requirements
Based on previous conversations, this system implements:
- Mission parameters gathered through AI-driven clarifying questions in a conversational interface [[memory:9055678]]
- Absolute minimum requirements: Mission Planning, Real-time Operations, and AI Intelligence as core buildable components [[memory:9055438]]

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI** web framework with WebSocket support
- **SQLAlchemy** ORM with SQLite/PostgreSQL support
- **Ollama** integration for local AI model inference
- **Pydantic** for data validation and settings management
- **AsyncIO** for concurrent operations

### Frontend (React/TypeScript)
- **React 18** with TypeScript
- **Ant Design** component library
- **React Router** for navigation
- **Socket.IO** for real-time communication
- **Leaflet** maps for drone tracking
- **Recharts** for data visualization

### AI Components
- **Ollama** for local LLM inference (Llama2/CodeLlama)
- **Conversational Mission Planner** with state management
- **Learning System** for mission optimization
- **Real-time Decision Making** capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Automated Setup
```bash
# Clone the repository
git clone <repository-url>
cd central_computer_sar-drone-swarm

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup

#### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
cd backend
python -c "
import asyncio
from app.core.database import init_database
asyncio.run(init_database())
"
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
```

#### 3. AI Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama2
ollama pull codellama
```

## 🏃‍♂️ Running the System

### Start All Services

#### 1. Start Ollama (Terminal 1)
```bash
ollama serve
```

#### 2. Start Backend (Terminal 2)
```bash
source venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Start Frontend (Terminal 3)
```bash
cd frontend
npm start
```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket Endpoint**: ws://localhost:8000/ws/{client_id}

## 📋 Features

### 1. AI Mission Planner
- **Conversational Interface**: Natural language mission planning
- **Intelligent Questions**: AI asks clarifying questions to gather complete mission parameters
- **Progressive Planning**: Step-by-step mission parameter collection
- **Safety Validation**: Automatic safety checks and recommendations
- **Plan Review**: Final review and approval process

### 2. Real-time Monitoring
- **Live Drone Tracking**: Real-time position updates on interactive maps
- **Video Streaming**: Live video feeds from drone cameras
- **Telemetry Dashboard**: Comprehensive drone status monitoring
- **Discovery Management**: Real-time discovery notifications and review
- **Emergency Controls**: Immediate override capabilities

### 3. AI Intelligence
- **Autonomous Decisions**: AI makes real-time operational decisions
- **Learning System**: Learns from mission outcomes to improve future operations
- **Pattern Recognition**: Identifies successful mission patterns
- **Adaptive Recommendations**: Mission parameter suggestions based on conditions
- **Decision Explanation**: Clear reasoning for AI-made decisions

### 4. Fleet Management
- **Drone Registration**: Add and configure drone capabilities
- **Health Monitoring**: Continuous drone system health checks
- **Maintenance Scheduling**: Automated maintenance reminders
- **Performance Analytics**: Flight time, efficiency, and success metrics
- **Resource Optimization**: Intelligent drone assignment algorithms

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./sar_missions.db

# AI/Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Safety Limits
MAX_WIND_SPEED=15.0
MIN_BATTERY_LEVEL=25.0
EMERGENCY_RETURN_BATTERY=15.0

# Mission Defaults
DEFAULT_SEARCH_ALTITUDE=100.0
MAX_MISSION_DURATION=14400
```

### Mission Parameters
The system collects comprehensive mission parameters through conversation:
- Search area description and coordinates
- Target information and characteristics
- Environmental conditions (weather, terrain)
- Resource requirements (drones, equipment)
- Safety constraints and emergency procedures
- Operational timeline and constraints

## 🛠️ Development

### Project Structure
```
central_computer_sar-drone-swarm/
├── backend/
│   ├── app/
│   │   ├── ai/              # AI components (Ollama, conversation, learning)
│   │   ├── api/             # FastAPI routers
│   │   ├── core/            # Core utilities (database, config, websockets)
│   │   ├── models/          # Database models
│   │   └── services/        # Business logic services
│   └── main.py              # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts (WebSocket, etc.)
│   │   ├── pages/           # Main application pages
│   │   └── App.tsx          # Main React application
│   └── package.json
├── requirements.txt         # Python dependencies
├── setup.sh                # Automated setup script
└── README.md
```

### Adding New Features

#### 1. Backend API Endpoints
```python
# backend/app/api/new_feature.py
from fastapi import APIRouter, Depends
from ..services.new_service import NewService

router = APIRouter()
service = NewService()

@router.get("/endpoint")
async def get_data():
    return await service.get_data()
```

#### 2. Frontend Components
```tsx
// frontend/src/components/NewComponent.tsx
import React from 'react';
import { Card } from 'antd';

const NewComponent: React.FC = () => {
  return (
    <Card title="New Feature">
      <p>Implementation here</p>
    </Card>
  );
};

export default NewComponent;
```

### Testing

#### Backend Tests
```bash
cd backend
pytest tests/
```

#### Frontend Tests
```bash
cd frontend
npm test
```

## 🔒 Security Considerations

- **Input Validation**: All API inputs are validated using Pydantic models
- **CORS Protection**: Configured for specific origins
- **WebSocket Authentication**: Client ID-based session management
- **Emergency Overrides**: Secure emergency command validation
- **Data Sanitization**: SQL injection prevention through ORM

## 📊 Performance

### Scalability Features
- **Async Operations**: Non-blocking I/O for concurrent requests
- **WebSocket Connections**: Efficient real-time communication
- **Database Optimization**: Indexed queries and connection pooling
- **Caching**: In-memory caching for frequent operations
- **Background Tasks**: Asynchronous processing for heavy operations

### Resource Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **AI Models**: Additional 4GB RAM for Ollama models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the [Issues](../../issues) page
2. Review the API documentation at `/docs`
3. Check Ollama status: `ollama list`
4. Verify all services are running on correct ports

## 🔮 Roadmap

### Phase 1 (Current)
- ✅ AI conversational mission planning
- ✅ Real-time monitoring dashboard
- ✅ Basic drone fleet management
- ✅ WebSocket communication

### Phase 2 (Next)
- [ ] Advanced video processing and object detection
- [ ] Multi-mission coordination
- [ ] Enhanced AI learning algorithms
- [ ] Mobile application support

### Phase 3 (Future)
- [ ] Integration with actual drone hardware
- [ ] Advanced weather integration
- [ ] Regulatory compliance modules
- [ ] Multi-operator collaboration

---

**Built with ❤️ for Search and Rescue Operations**