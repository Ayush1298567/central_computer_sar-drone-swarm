# 🚁 Drone Connection System Documentation

## Overview

The SAR Drone Swarm System now includes a comprehensive **Drone Connection Hub** that supports multiple wireless communication protocols for connecting to real drones. This system provides a unified interface for managing drone connections, sending commands, and receiving telemetry data.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Drone Connection Hub                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   WiFi      │  │    LoRa     │  │   MAVLink   │  │WebSocket│ │
│  │ Connection  │  │ Connection  │  │ Connection  │  │Connect. │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Drone Registry                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • Drone Discovery                                           │ │
│  │ • Connection Management                                     │ │
│  │ • Status Tracking                                           │ │
│  │ • Capabilities Registry                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    REST API Endpoints                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • /drone-connections/*                                      │ │
│  │ • Connection Management                                     │ │
│  │ • Command Sending                                           │ │
│  │ • Telemetry Streaming                                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔌 Supported Communication Protocols

### 1. WiFi Connection (TCP/UDP)
- **Use Case**: Short to medium range connections (up to 1km)
- **Protocols**: TCP and UDP
- **Features**: 
  - Reliable data transmission
  - Low latency
  - Standard networking
- **Configuration**:
  ```json
  {
    "connection_type": "wifi",
    "connection_params": {
      "host": "192.168.1.100",
      "port": 8080,
      "protocol": "tcp",
      "timeout": 10.0
    }
  }
  ```

### 2. LoRa Connection
- **Use Case**: Long-range connections (up to 10km+)
- **Protocol**: LoRa radio communication
- **Features**:
  - Very long range
  - Low power consumption
  - Good penetration through obstacles
- **Configuration**:
  ```json
  {
    "connection_type": "lora",
    "connection_params": {
      "frequency": 868.1,
      "spreading_factor": 7,
      "bandwidth": 125000,
      "device_path": "/dev/ttyUSB0"
    }
  }
  ```

### 3. MAVLink Connection
- **Use Case**: Professional drone communication (ArduPilot/PX4)
- **Protocol**: MAVLink protocol
- **Features**:
  - Industry standard
  - Rich telemetry data
  - Flight control commands
- **Configuration**:
  ```json
  {
    "connection_type": "mavlink",
    "connection_params": {
      "connection_type": "serial",
      "device": "/dev/ttyUSB0",
      "baudrate": 57600
    }
  }
  ```

### 4. WebSocket Connection
- **Use Case**: Web-based drone interfaces
- **Protocol**: WebSocket over HTTP/HTTPS
- **Features**:
  - Real-time bidirectional communication
  - Web browser compatibility
  - JSON message format
- **Configuration**:
  ```json
  {
    "connection_type": "websocket",
    "connection_params": {
      "host": "localhost",
      "port": 8080,
      "protocol": "ws",
      "path": "/ws"
    }
  }
  ```

## 🚀 Quick Start

### 1. Start the System
```bash
python start_system.py
```

### 2. Connect to a Drone
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
    },
    "max_flight_time": 30,
    "max_speed": 15.0,
    "max_altitude": 120.0
  }'
```

### 3. Send Commands
```bash
curl -X POST "http://localhost:8000/api/v1/drone-connections/drone_001/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "takeoff",
    "parameters": {
      "altitude": 50.0
    },
    "priority": 1
  }'
```

### 4. Request Telemetry
```bash
curl -X POST "http://localhost:8000/api/v1/drone-connections/drone_001/telemetry"
```

## 📡 API Endpoints

### Connection Management
- `GET /api/v1/drone-connections/connections` - Get all connections
- `GET /api/v1/drone-connections/connections/{drone_id}` - Get specific connection
- `POST /api/v1/drone-connections/connect` - Connect to a drone
- `POST /api/v1/drone-connections/{drone_id}/disconnect` - Disconnect drone

### Drone Control
- `POST /api/v1/drone-connections/{drone_id}/command` - Send command
- `POST /api/v1/drone-connections/{drone_id}/telemetry` - Request telemetry

### Drone Information
- `GET /api/v1/drone-connections/drones` - Get all drones
- `GET /api/v1/drone-connections/drones/{drone_id}` - Get drone info

### Discovery
- `GET /api/v1/drone-connections/discovery/status` - Get discovery status
- `POST /api/v1/drone-connections/discovery/start` - Start discovery
- `POST /api/v1/drone-connections/discovery/stop` - Stop discovery

## 🎛️ Supported Commands

### Flight Commands
- `takeoff` - Take off to specified altitude
- `land` - Land at current or specified location
- `return_home` - Return to launch point
- `set_altitude` - Change flight altitude
- `set_heading` - Change flight direction
- `emergency_stop` - Immediate emergency stop

### Mission Commands
- `start_mission` - Begin assigned mission
- `pause_mission` - Pause current mission
- `resume_mission` - Resume paused mission
- `abort_mission` - Abort current mission

### System Commands
- `enable_autonomous` - Enable autonomous flight
- `disable_autonomous` - Disable autonomous flight
- `calibrate_sensors` - Calibrate drone sensors
- `update_firmware` - Update drone firmware

## 📊 Telemetry Data

The system receives and processes the following telemetry data:

### Position Data
- `position.lat` - Latitude
- `position.lon` - Longitude  
- `position.alt` - Altitude

### Flight Data
- `battery_level` - Battery percentage (0-100)
- `speed` - Ground speed (m/s)
- `heading` - Flight direction (degrees)
- `signal_strength` - Communication signal strength

### Environmental Data
- `temperature` - Ambient temperature (°C)
- `humidity` - Humidity percentage
- `wind_speed` - Wind speed (m/s)
- `gps_accuracy` - GPS accuracy (meters)

## 🔧 Configuration

### Environment Variables
```bash
# Drone Connection Settings
DRONE_CONNECTION_TIMEOUT=10.0
DRONE_HEARTBEAT_INTERVAL=5.0
DRONE_DISCOVERY_INTERVAL=10.0
DRONE_MAX_RECONNECT_ATTEMPTS=3
```

### Connection Pool Settings
```python
# Maximum concurrent connections
MAX_CONCURRENT_CONNECTIONS = 50

# Connection timeout settings
CONNECTION_TIMEOUT = 10.0
HEARTBEAT_TIMEOUT = 15.0
RECONNECT_DELAY = 5.0
```

## 🛠️ Hardware Requirements

### For WiFi Connections
- Standard WiFi adapter
- Network connectivity
- No additional hardware required

### For LoRa Connections
- LoRa radio module (e.g., SX1276, SX1278)
- Antenna (frequency-specific)
- Serial connection to computer

### For MAVLink Connections
- Serial port or network connection
- Compatible flight controller (Pixhawk, etc.)
- MAVLink-enabled autopilot

### For WebSocket Connections
- Standard network interface
- WebSocket-compatible drone firmware
- No additional hardware required

## 🔒 Security Features

### Connection Security
- Encrypted communication channels
- Authentication tokens
- Connection validation
- Command authorization

### Data Protection
- Message integrity checks
- Secure parameter validation
- Rate limiting
- Access control

## 📈 Monitoring and Diagnostics

### Connection Metrics
- Messages sent/received
- Connection uptime
- Average latency
- Connection stability score

### Health Monitoring
- Heartbeat monitoring
- Connection status tracking
- Automatic reconnection
- Error logging and reporting

## 🚨 Troubleshooting

### Common Issues

#### Connection Failed
1. Check network connectivity
2. Verify drone is powered on
3. Confirm connection parameters
4. Check firewall settings

#### Telemetry Not Received
1. Verify drone is sending telemetry
2. Check connection status
3. Monitor signal strength
4. Review error logs

#### Commands Not Executed
1. Check command format
2. Verify drone capabilities
3. Confirm connection status
4. Review command queue

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python start_system.py
```

## 🔮 Future Enhancements

### Planned Features
- Bluetooth Low Energy (BLE) support
- 4G/5G cellular connections
- Mesh networking capabilities
- Advanced encryption protocols
- Machine learning for connection optimization

### Integration Roadmap
- Integration with existing mission planner
- Real-time video streaming support
- Advanced telemetry analytics
- Automated drone fleet management

## 📚 Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [System Architecture Guide](Build_plan.md)
- [Mission Planning Documentation](README.md)
- [Emergency Procedures](docs/OPERATIONAL_RUNBOOKS.md)

---

**🚁 Ready to Connect Drones and Save Lives! 🆘**
