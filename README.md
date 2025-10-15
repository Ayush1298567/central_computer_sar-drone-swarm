# 🚁 SAR Drone Swarm Control System

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/Ayush1298567/central_computer_sar-drone-swarm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)

> **🎯 PRODUCTION-READY SAR SYSTEM FOR REAL-WORLD LIFE-SAVING OPERATIONS**

A comprehensive Search and Rescue (SAR) drone swarm control system capable of connecting to real drones, executing coordinated search missions, and saving lives in disaster scenarios.

## 🏆 **System Status: FULLY FUNCTIONAL**

✅ **All systems operational and ready for real SAR deployments**

---

## 🚀 **What This System Can Do**

### **Real-World Capabilities**
- 🔌 **Connect to Real Drones**: WiFi, LoRa, MAVLink, WebSocket protocols
- 🚁 **Execute Search Missions**: Multi-drone coordinated searches
- 🤖 **AI-Powered Detection**: Advanced computer vision for survivor detection
- 📡 **Live Video Streaming**: Real-time video feeds from drone cameras
- 🚨 **Emergency Response**: Immediate emergency protocols and failover
- 🎛️ **Mission Control**: Complete mission planning and execution
- 📊 **Real-Time Monitoring**: Live telemetry and status tracking

### **Mission Types Supported**
- ✅ Grid Search (Systematic area coverage)
- ✅ Spiral Search (Concentric pattern search)
- ✅ Sector Search (Radial pattern search)
- ✅ Lawnmower Search (Parallel line search)
- ✅ Adaptive Search (AI-optimized patterns)

---

## 🏗️ **System Architecture**

### **Multi-Protocol Communication Hub**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Drone Connection Hub                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   WiFi      │  │    LoRa     │  │   MAVLink   │  │WebSocket│ │
│  │ Connection  │  │ Connection  │  │ Connection  │  │Connect. │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Real Mission Execution                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • Multi-Drone Coordination                                 │ │
│  │ • Mission Phase Management                                  │ │
│  │ • Emergency Response Protocols                             │ │
│  │ • Real-Time Progress Tracking                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Communication Flow**
```
👤 User ↔ 🖥️ Central Computer ↔ 📡 Multi-Protocol Hub ↔ 🚁 Real Drones
```

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Git

### **Installation & Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ayush1298567/central_computer_sar-drone-swarm.git
   cd central_computer_sar-drone-swarm
   ```

2. **Start the complete system**
```bash
python start_system.py
```

3. **Access the dashboard**
   - Open your browser to `http://localhost:3000`
   - The system automatically starts all services

### **Connect to Real Drones**

1. **Via WiFi**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/drone-connections/connect" \
     -H "Content-Type: application/json" \
     -d '{
       "drone_id": "drone_001",
       "name": "Search Drone Alpha",
       "connection_type": "wifi",
       "connection_params": {
         "host": "192.168.1.100",
         "port": 8080,
         "protocol": "tcp"
       }
     }'
   ```

2. **Via MAVLink (ArduPilot/PX4)**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/drone-connections/connect" \
     -H "Content-Type: application/json" \
     -d '{
       "drone_id": "drone_002",
       "connection_type": "mavlink",
       "connection_params": {
         "connection_type": "serial",
         "device": "/dev/ttyUSB0",
         "baudrate": 57600
       }
     }'
   ```

3. **Via LoRa (Long Range)**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/drone-connections/connect" \
     -H "Content-Type: application/json" \
     -d '{
       "drone_id": "drone_003",
       "connection_type": "lora",
       "connection_params": {
         "frequency": 868.1,
         "spreading_factor": 7,
         "device_path": "/dev/ttyUSB0"
       }
     }'
   ```

---

## 🎛️ **System Features**

### **🔌 Drone Connection Hub**
- **Multi-Protocol Support**: WiFi, LoRa, MAVLink, WebSocket
- **Real-Time Communication**: Bidirectional messaging with live telemetry
- **Connection Management**: Automatic discovery, health monitoring, failover
- **Command Interface**: Complete flight and mission control commands
- **Security**: Encrypted communication and authentication

### **🚁 Real Mission Execution**
- **Mission Phases**: Takeoff → Navigation → Search → Return
- **Multi-Drone Coordination**: Simultaneous operation of multiple drones
- **Real-Time Monitoring**: Live progress tracking and status updates
- **Emergency Protocols**: Immediate abort and return-to-home capabilities
- **Error Handling**: Comprehensive error recovery and logging

### **🤖 AI Intelligence**
- **Computer Vision**: YOLOv8-based object detection for survivors
- **Mission Planning**: Conversational AI for mission creation
- **Adaptive Search**: AI-optimized search patterns
- **Decision Loop (Phase 10)**: Real-time AIMonitor detects conditions (low_battery, stale_heartbeat, lost_drone, off_route) and broadcasts decisions over `ai_decisions` WebSocket topic with fields `decision_id`, `type`, `reasoning`, `confidence_score`, `severity`, and optional `recommended_action`. Operators can apply via `POST /api/v1/ai/decisions/{decision_id}/apply`, which routes to the mission engine to execute: pause/resume/abort/replan and emergency RTL/Land. All actions are persisted to `MissionLog` and `AIDecisionLog`, and per-drone telemetry snapshots are written each second to `DroneStateHistory`.
- **Learning System**: Improves performance from mission outcomes

### **📊 Real-Time Monitoring**
- **Live Telemetry**: Position, battery, speed, heading, signal strength
- **Video Streaming**: Real-time video feeds from drone cameras
- **Mission Progress**: Live mission status and completion tracking
- **Discovery Alerts**: Immediate notifications for survivor detection
- **Emergency Status**: Real-time emergency monitoring and response

---

## 🧠 AI Decision Loop (End-to-End)

The Intelligence Core continuously monitors telemetry and mission context, proposes decisions, and executes actions safely.

- Context aggregation: `ContextAggregator` snapshots mission and drone state for decisions.
- Monitoring: `AIMonitor` detects conditions like `low_battery`, `stale_heartbeat`, `lost_drone`, and `off_route` in real time.
- Broadcast: Each decision is published via WebSocket topic `ai_decisions` with `decision_id`, `type`, `reasoning`, `confidence_score`, `severity`, and optional `recommended_action`.
- Human-in-the-loop or autonomous: Operators can apply decisions via `POST /api/v1/ai/decisions/{decision_id}/apply`. When `autonomous_execute` is enabled, the monitor can trigger safe actions (e.g., RTL/Land) automatically.
- Mission Engine: `real_mission_execution` applies actions (`pause/resume/abort/replan`, emergency RTL/Land) with guards for paused missions and continuous per-second persistence to `DroneStateHistory`.
- Auditing: All decisions and outcomes are written to `MissionLog` and `AIDecisionLog` for traceability.


## 📡 **API Endpoints**

### **Drone Connections**
- `GET /api/v1/drone-connections/connections` - All connections
- `POST /api/v1/drone-connections/connect` - Connect to drone
- `POST /api/v1/drone-connections/{drone_id}/disconnect` - Disconnect
- `POST /api/v1/drone-connections/{drone_id}/command` - Send command
- `POST /api/v1/drone-connections/{drone_id}/telemetry` - Request telemetry

### **Mission Execution**
- `POST /api/v1/real-mission-execution/execute` - Execute mission
- `POST /api/v1/real-mission-execution/{mission_id}/pause` - Pause mission
- `POST /api/v1/real-mission-execution/{mission_id}/resume` - Resume mission
- `POST /api/v1/real-mission-execution/{mission_id}/abort` - Abort mission
- `GET /api/v1/real-mission-execution/{mission_id}/status` - Mission status

### **Computer Vision**
- `POST /api/v1/computer-vision/detect-objects` - Object detection
- `POST /api/v1/computer-vision/detect-sar-targets` - SAR target detection
- `POST /api/v1/computer-vision/analyze-image-quality` - Image quality analysis

---

## 🎯 **Supported Commands**

### **Flight Commands**
- `takeoff` - Take off to specified altitude
- `land` - Land at current or specified location
- `return_home` - Return to launch point
- `set_altitude` - Change flight altitude
- `set_heading` - Change flight direction
- `emergency_stop` - Immediate emergency stop

### **Mission Commands**
- `start_mission` - Begin assigned mission
- `pause_mission` - Pause current mission
- `resume_mission` - Resume paused mission
- `abort_mission` - Abort current mission

### **System Commands**
- `enable_autonomous` - Enable autonomous flight
- `disable_autonomous` - Disable autonomous flight
- `calibrate_sensors` - Calibrate drone sensors

---

## 🛠️ **Technology Stack**

### **Backend**
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with PostgreSQL/SQLite support
- **WebSockets**: Real-time bidirectional communication
- **Ollama**: Local LLM integration for AI intelligence
- **OpenCV**: Computer vision processing
- **PyMAVLink**: MAVLink protocol support
- **PySerial**: Serial communication for LoRa and MAVLink

### **Frontend**
- **React 18**: Modern UI framework with TypeScript
- **Tailwind CSS**: Utility-first styling
- **Leaflet**: Interactive mapping and real-time tracking
- **Socket.io**: Real-time WebSocket communication
- **React Query**: Data fetching and caching

### **Infrastructure**
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Kubernetes**: Production deployment (optional)
- **PostgreSQL**: Production database
- **Redis**: Caching and session storage
- **Grafana**: Monitoring and analytics

---

## 📁 **Project Structure**

```
central_computer_sar-drone-swarm/
├── 🚁 backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                  # REST API endpoints
│   │   ├── ai/                   # AI and ML components
│   │   ├── communication/        # 🆕 Drone connection hub
│   │   ├── core/                 # Core configuration
│   │   ├── models/               # Database models
│   │   ├── services/             # Business logic
│   │   └── simulator/            # Drone simulation
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile               # Container configuration
├── 🎨 frontend/                  # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── drone/          # 🆕 Real-time drone monitoring
│   │   │   ├── mission/        # Mission planning and control
│   │   │   ├── video/          # Video streaming
│   │   │   └── ui/             # UI components
│   │   ├── services/           # API services
│   │   └── types/              # TypeScript types
│   ├── package.json            # Node.js dependencies
│   └── Dockerfile             # Container configuration
├── 🚀 deployment/               # Production deployment
├── 📊 monitoring/              # Grafana and Prometheus
├── 📚 docs/                   # Documentation
├── 🧪 isef_materials/         # ISEF competition materials
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
└── start_system.py           # System startup script
```

---

## 🔧 **Configuration**

### **Environment Variables**

**Backend (.env)**
```bash
DATABASE_URL=postgresql://user:pass@localhost/sar_drone
OLLAMA_HOST=http://localhost:11434
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Frontend (.env)**
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_MAP_API_KEY=your-map-api-key
```

---

## 🚨 **Emergency Procedures**

The system includes comprehensive emergency protocols:

1. **🚨 Emergency Stop**: Immediately halt all drone operations
2. **🏠 Return to Home**: Automatic return to launch point
3. **🔌 Connection Loss**: Automatic failover and reconnection
4. **🔋 Battery Low**: Automatic return when battery is critical
5. **🌪️ Weather Alert**: Automatic landing in adverse conditions
6. **⚠️ System Failure**: Automatic mission abort and safety protocols

---

## 📊 **Monitoring & Analytics**

- **Real-time Dashboard**: Live drone status and telemetry
- **Mission Analytics**: Performance tracking and reporting
- **Discovery Management**: Evidence logging and investigation
- **System Health**: Comprehensive monitoring and alerting
- **Performance Metrics**: Connection stability and mission success rates

---

## 🏆 **System Achievements**

✅ **Complete Hardware Integration**: Connect to real drones via multiple protocols  
✅ **Real Mission Execution**: Execute actual search and rescue missions  
✅ **Live Monitoring**: Real-time telemetry and video streaming  
✅ **Emergency Response**: Comprehensive emergency protocols  
✅ **AI Intelligence**: Advanced object detection and mission optimization  
✅ **Multi-Drone Coordination**: Simultaneous operation of drone swarms  
✅ **Production Ready**: All systems tested and functional  

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

For support and questions:
- Create an issue in this repository
- Check the documentation in the `docs/` directory
- Review the operational runbooks for detailed procedures

---

## 🎯 **Repository Information**

- **GitHub**: [https://github.com/Ayush1298567/central_computer_sar-drone-swarm](https://github.com/Ayush1298567/central_computer_sar-drone-swarm)
- **Status**: Production Ready
- **Last Updated**: October 2024
- **Version**: 1.0.0

---

**⚠️ IMPORTANT**: This system is designed for life-saving operations. Always follow proper safety protocols and ensure adequate training before deployment in real SAR scenarios.

**🚁 Ready to save lives with drone technology! 🆘🏆**