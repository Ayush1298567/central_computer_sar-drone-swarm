# 🚁 SAR Drone Swarm System

Advanced Search and Rescue drone coordination system with AI-powered mission planning, real-time computer vision, and multi-drone coordination.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama AI service (optional - will start automatically)

### Single Command Startup
```bash
python start_system.py
```

### Windows Users
```cmd
# Production system
start_system.bat
```

### What It Does
- ✅ Starts Ollama AI service automatically
- ✅ Initializes database
- ✅ Starts backend server (port 8000)
- ✅ Starts frontend server (port 3000)
- ✅ Monitors all services
- ✅ Clean shutdown with Ctrl+C

## 🎯 System Access

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Features

- **AI-Powered Mission Planning**: Conversational mission creation
- **Multi-Drone Coordination**: Up to 10 drones simultaneously
- **Real-Time Computer Vision**: YOLO object detection
- **Emergency Protocols**: Comprehensive safety systems
- **WebSocket Communication**: Real-time updates
- **Performance Analytics**: Mission optimization

## 🚨 Emergency Procedures

- **Emergency Stop**: Immediate drone halt
- **Battery Monitoring**: Automatic low-battery protocols
- **Weather Integration**: Flight condition monitoring
- **Collision Avoidance**: Multi-drone coordination

## 🧪 Development Features

The system includes:

- **Mock Data Generation**: Realistic SAR scenarios with 4 terrain types
- **Interactive Maps**: Folium and Plotly visualizations
- **Real-time Dashboards**: Battery, signal, and discovery monitoring
- **Export Capabilities**: JSON, CSV, GeoJSON formats
- **API Documentation**: Full interactive docs at `/docs`
- **Test Scenarios**: Mountain, Forest, Urban, Water rescue missions

## 📊 System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB for models and data
- **Network**: Stable internet for AI services

## 🔧 Configuration

Environment variables in `backend/.env`:
```
DATABASE_URL=sqlite:///./sar_drone.db
SECRET_KEY=your-secure-secret-key
OLLAMA_HOST=http://localhost:11434
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## 🎓 Training

Complete operator training program available with:
- System overview and architecture
- Mission planning and execution
- Emergency procedures
- Troubleshooting guides
- Certification requirements

## 🆘 Support

For technical support or emergency issues:
- Check system health: http://localhost:8000/health
- Review logs: `backend/logs/`
- Emergency stop: Use dashboard or API

---

**🚁 Ready to Save Lives! 🆘**
