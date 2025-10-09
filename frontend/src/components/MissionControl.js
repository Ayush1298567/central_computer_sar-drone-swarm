import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup, Polygon, CircleMarker } from 'react-leaflet';
import { Send, PlayArrow, Pause, Stop, Refresh } from '@mui/icons-material';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useWebSocket } from '../services/WebSocketService';
import { missionApi, commandApi } from '../services/ApiService';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const MissionControl = () => {
  const [missions, setMissions] = useState([]);
  const [selectedMission, setSelectedMission] = useState(null);
  const [drones, setDrones] = useState([]);
  const [discoveries, setDiscoveries] = useState([]);
  const [command, setCommand] = useState('');
  const [missionProgress, setMissionProgress] = useState(null);
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);
  const [mapZoom, setMapZoom] = useState(13);
  const [showCommandDialog, setShowCommandDialog] = useState(false);
  const [selectedDrone, setSelectedDrone] = useState(null);
  const { messages, sendMessage } = useWebSocket();
  const mapRef = useRef();

  useEffect(() => {
    loadMissions();
    loadDrones();
  }, []);

  useEffect(() => {
    // Process WebSocket messages
    messages.forEach(message => {
      if (message.type === 'telemetry') {
        updateDronePosition(message.data);
      } else if (message.type === 'discovery') {
        addDiscovery(message.data);
      } else if (message.type === 'mission_progress') {
        setMissionProgress(message.data);
      }
    });
  }, [messages]);

  const loadMissions = async () => {
    try {
      const response = await missionApi.getAll();
      setMissions(response.data);
    } catch (error) {
      console.error('Error loading missions:', error);
    }
  };

  const loadDrones = async () => {
    try {
      // In a real implementation, this would come from the API
      // For now, we'll simulate drone data
      setDrones([
        {
          id: 1,
          name: 'Drone Alpha',
          lat: 37.7749,
          lng: -122.4194,
          alt: 50,
          status: 'active',
          battery_percent: 85,
          heading: 0,
          speed: 8
        },
        {
          id: 2,
          name: 'Drone Beta',
          lat: 37.7759,
          lng: -122.4204,
          alt: 50,
          status: 'active',
          battery_percent: 72,
          heading: 90,
          speed: 6
        },
        {
          id: 3,
          name: 'Drone Gamma',
          lat: 37.7739,
          lng: -122.4184,
          alt: 50,
          status: 'returning_to_base',
          battery_percent: 25,
          heading: 180,
          speed: 12
        }
      ]);
    } catch (error) {
      console.error('Error loading drones:', error);
    }
  };

  const updateDronePosition = (telemetry) => {
    setDrones(prev => prev.map(drone => 
      drone.id === telemetry.drone_id 
        ? {
            ...drone,
            lat: telemetry.lat,
            lng: telemetry.lng,
            alt: telemetry.alt,
            battery_percent: telemetry.battery_percent,
            status: telemetry.status,
            heading: telemetry.heading,
            speed: telemetry.speed
          }
        : drone
    ));
  };

  const addDiscovery = (discovery) => {
    setDiscoveries(prev => [...prev, {
      id: Date.now(),
      lat: discovery.discovery.position.lat,
      lng: discovery.discovery.position.lng,
      type: discovery.discovery.type,
      confidence: discovery.discovery.confidence,
      description: discovery.discovery.description,
      drone_id: discovery.drone_id,
      timestamp: new Date()
    }]);
  };

  const startMission = async (missionId) => {
    try {
      await missionApi.start(missionId);
      setSelectedMission(missionId);
      loadMissions();
    } catch (error) {
      console.error('Error starting mission:', error);
    }
  };

  const pauseMission = async (missionId) => {
    try {
      await missionApi.pause(missionId);
      loadMissions();
    } catch (error) {
      console.error('Error pausing mission:', error);
    }
  };

  const resumeMission = async (missionId) => {
    try {
      await missionApi.resume(missionId);
      loadMissions();
    } catch (error) {
      console.error('Error resuming mission:', error);
    }
  };

  const sendCommand = async () => {
    if (!command.trim()) return;

    try {
      if (selectedDrone) {
        await commandApi.send(command, selectedDrone, `session_${Date.now()}`);
      } else {
        await commandApi.send(command, null, `session_${Date.now()}`);
      }
      setCommand('');
      setShowCommandDialog(false);
    } catch (error) {
      console.error('Error sending command:', error);
    }
  };

  const getDroneIcon = (drone) => {
    const color = drone.status === 'active' ? 'blue' : 
                  drone.status === 'returning_to_base' ? 'orange' : 
                  drone.status === 'emergency' ? 'red' : 'gray';
    
    return L.divIcon({
      className: 'drone-marker',
      html: `<div style="background: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">${drone.id}</div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
  };

  const getDiscoveryIcon = (discovery) => {
    const color = discovery.type === 'survivor' ? 'green' : 
                  discovery.type === 'hazard' ? 'red' : 'orange';
    
    return L.divIcon({
      className: 'discovery-marker',
      html: `<div style="background: ${color}; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 10px;">!</div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });
  };

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Mission Control Panel */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Mission Control</Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => { loadMissions(); loadDrones(); }}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Send />}
              onClick={() => setShowCommandDialog(true)}
            >
              Send Command
            </Button>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>Active Missions</Typography>
            <List dense>
              {missions.filter(m => m.status === 'active').map(mission => (
                <ListItem key={mission.id}>
                  <ListItemText
                    primary={mission.name}
                    secondary={`Status: ${mission.status}`}
                  />
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => pauseMission(mission.id)}
                    >
                      <Pause />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => resumeMission(mission.id)}
                    >
                      <PlayArrow />
                    </IconButton>
                  </Box>
                </ListItem>
              ))}
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>Mission Progress</Typography>
            {missionProgress ? (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Coverage: {missionProgress.coverage_percentage?.toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={missionProgress.coverage_percentage || 0}
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" gutterBottom>
                  Drones Active: {missionProgress.drones_active}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Completed Waypoints: {missionProgress.completed_waypoints} / {missionProgress.total_waypoints}
                </Typography>
              </Box>
            ) : (
              <Typography color="text.secondary">No active mission</Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Map and Drone Status */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2 }}>
        {/* Map */}
        <Paper sx={{ flex: 1 }}>
          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            style={{ height: '100%', width: '100%' }}
            ref={mapRef}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {/* Drone Markers */}
            {drones.map(drone => (
              <Marker
                key={drone.id}
                position={[drone.lat, drone.lng]}
                icon={getDroneIcon(drone)}
              >
                <Popup>
                  <Box>
                    <Typography variant="subtitle2">{drone.name}</Typography>
                    <Typography variant="body2">Status: {drone.status}</Typography>
                    <Typography variant="body2">Battery: {drone.battery_percent}%</Typography>
                    <Typography variant="body2">Speed: {drone.speed} m/s</Typography>
                    <Typography variant="body2">Heading: {drone.heading}°</Typography>
                  </Box>
                </Popup>
              </Marker>
            ))}
            
            {/* Discovery Markers */}
            {discoveries.map(discovery => (
              <Marker
                key={discovery.id}
                position={[discovery.lat, discovery.lng]}
                icon={getDiscoveryIcon(discovery)}
              >
                <Popup>
                  <Box>
                    <Typography variant="subtitle2">
                      {discovery.type.charAt(0).toUpperCase() + discovery.type.slice(1)} Detection
                    </Typography>
                    <Typography variant="body2">Confidence: {discovery.confidence}%</Typography>
                    <Typography variant="body2">{discovery.description}</Typography>
                    <Typography variant="body2">
                      Drone: {discovery.drone_id} • {discovery.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Box>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </Paper>

        {/* Drone Status Panel */}
        <Paper sx={{ width: 300, p: 2 }}>
          <Typography variant="h6" gutterBottom>Drone Status</Typography>
          
          {drones.map(drone => (
            <Card key={drone.id} sx={{ mb: 1 }}>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">{drone.name}</Typography>
                  <Chip
                    label={drone.status}
                    size="small"
                    color={drone.status === 'active' ? 'primary' : 
                           drone.status === 'returning_to_base' ? 'warning' : 'default'}
                  />
                </Box>
                
                <Typography variant="body2" gutterBottom>
                  Battery: {drone.battery_percent}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={drone.battery_percent}
                  color={drone.battery_percent > 50 ? 'success' : 
                         drone.battery_percent > 20 ? 'warning' : 'error'}
                  sx={{ mb: 1 }}
                />
                
                <Typography variant="body2" gutterBottom>
                  Position: {drone.lat.toFixed(4)}, {drone.lng.toFixed(4)}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Altitude: {drone.alt}m
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Speed: {drone.speed} m/s
                </Typography>
                
                <Button
                  size="small"
                  onClick={() => {
                    setSelectedDrone(drone.id);
                    setShowCommandDialog(true);
                  }}
                >
                  Send Command
                </Button>
              </CardContent>
            </Card>
          ))}
        </Paper>
      </Box>

      {/* Command Dialog */}
      <Dialog open={showCommandDialog} onClose={() => setShowCommandDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Send Command {selectedDrone ? `to Drone ${selectedDrone}` : 'to All Drones'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Command"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="e.g., return to base, investigate area, pause mission"
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCommandDialog(false)}>Cancel</Button>
          <Button onClick={sendCommand} variant="contained" disabled={!command.trim()}>
            Send Command
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MissionControl;