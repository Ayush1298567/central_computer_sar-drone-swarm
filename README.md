# SAR Drone Central Computer System

A complete search and rescue drone management system with AI-powered mission planning, real-time drone simulation, and comprehensive fleet management.

## 🚁 System Overview

This system provides a desktop application for operators to:
- Plan SAR missions through conversational AI
- Manage a fleet of drones (add, configure, monitor)
- Execute missions with simulated drones
- Monitor real-time progress on an interactive map
- Send commands and receive updates

## ✨ Key Features

### 🤖 AI-Powered Mission Planning
- **Conversational Interface**: Natural language mission planning with intelligent follow-up questions
- **35+ AI Agents**: Coordinated agents for planning, execution, intelligence, and safety
- **Local LLM Integration**: Uses Ollama with Mistral-7B for offline AI processing
- **Smart Question Generation**: Context-aware questions to gather mission details

### 🛸 Realistic Drone Simulation
- **Autonomous Behavior**: Drones fly assigned search patterns automatically
- **Real-time Telemetry**: Position, battery, status updates every 2 seconds
- **Intelligent Decision Making**: Autonomous return-to-base, collision avoidance
- **Discovery Simulation**: Realistic detection of survivors, hazards, obstacles

### 🗺️ Real-time Map Interface
- **Interactive Map**: Live drone positions with smooth movement
- **Coverage Visualization**: Real-time search area coverage tracking
- **Discovery Markers**: Visual indicators for found items/survivors
- **Command Interface**: Click-to-command drone operations

### 🔧 Fleet Management
- **Complete CRUD**: Add, edit, remove, and monitor drones
- **Status Tracking**: Real-time battery, position, and mission status
- **Capability Management**: Configure camera types, sensors, battery capacity
- **Health Monitoring**: Visual indicators for drone health and status

### ⚡ Real-time Communication
- **WebSocket Streaming**: Live updates for telemetry, discoveries, commands
- **Redis Pub/Sub**: High-performance agent coordination
- **Command Execution**: Natural language command processing
- **Progress Tracking**: Real-time mission progress and coverage

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Database ORM with SQLite
- **Redis**: Pub/sub messaging for agent coordination
- **Ollama**: Local LLM integration
- **35+ AI Agents**: Specialized agents for different functions

### Frontend (React)
- **React 18**: Modern UI framework
- **Material-UI**: Professional component library
- **React-Leaflet**: Interactive mapping
- **WebSocket Client**: Real-time communication

### AI Agent Clusters
- **Mission Planning**: Conversation orchestrator, NLP, question generator, plan synthesizer
- **Execution**: Task assignment, route optimization, progress monitoring, command dispatch
- **Intelligence**: Detection analysis, pattern recognition
- **Safety**: Battery monitoring, collision avoidance, emergency handling

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- Redis
- Ollama

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd sar-drone-system
chmod +x setup.sh
./setup.sh
```

2. **Start the system**:
```bash
chmod +x start.sh
./start.sh
```

3. **Open in browser**:
```
http://localhost:8000
```

### Manual Setup

1. **Install dependencies**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build
```

2. **Start services**:
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Ollama
ollama serve
ollama pull mistral:7b

# Terminal 3: Application
cd backend
python main.py
```

## 🧪 Testing

Run the comprehensive system test:
```bash
python test_system.py
```

This tests:
- System health and status
- Drone creation and management
- Mission planning conversation
- Command execution
- Agent coordination
- WebSocket communication

## 📖 Usage Guide

### 1. Mission Planning
1. Go to "Mission Planning" tab
2. Describe your mission: "Search the collapsed warehouse for survivors"
3. Answer AI questions about location, hazards, resources
4. Review and accept the generated mission plan

### 2. Drone Fleet Management
1. Go to "Drone Fleet" tab
2. Click "Add Drone" to create new drones
3. Configure capabilities (camera, sensors, battery)
4. Monitor real-time status and battery levels

### 3. Mission Control
1. Go to "Mission Control" tab
2. Start missions from the mission list
3. Watch drones on the interactive map
4. Send commands: "return to base", "investigate area"
5. Monitor discoveries and progress

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./sar_drone_system.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

### Agent Configuration
Agents can be configured in `backend/agents/`:
- Adjust safety parameters in safety agents
- Modify question templates in planning agents
- Configure detection thresholds in intelligence agents

## 🏥 System Health

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Agent Status
```bash
curl http://localhost:8000/api/agents
```

### System Status
```bash
curl http://localhost:8000/api/status
```

## 🐛 Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ollama pull mistral:7b
   ```

2. **Redis connection failed**:
   ```bash
   redis-server
   ```

3. **Port already in use**:
   - Change port in `backend/main.py`
   - Update frontend proxy in `frontend/package.json`

4. **WebSocket connection failed**:
   - Check firewall settings
   - Verify WebSocket endpoint is accessible

### Logs
- Application logs: `logs/`
- Database: `sar_drone_system.db`
- Test results: `test_results.json`

## 🔒 Security Notes

- This is a simulation system - no real hardware integration
- All data stored locally in SQLite
- No external API calls except for map tiles
- Ollama runs locally for AI processing

## 📊 Performance

- **Concurrent Drones**: Supports 50+ simulated drones
- **Real-time Updates**: 2-second telemetry intervals
- **Agent Response**: <100ms for most operations
- **Memory Usage**: ~500MB for full system
- **Database**: SQLite with automatic indexing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_system.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Run the system test: `python test_system.py`
3. Check logs in the `logs/` directory
4. Create an issue with test results

---

**Built with ❤️ for Search and Rescue Operations**