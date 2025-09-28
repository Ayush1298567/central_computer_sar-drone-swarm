import React, { useState, useEffect, useCallback } from 'react';
import { DroneStatus, Mission, Discovery, WebSocketMessage } from '../types/api';
import { WebSocketService } from '../services/websocketService';
import InteractiveMap from '../components/map/InteractiveMap';
import DroneGrid from '../components/drone/DroneGrid';
import MissionPreview from '../components/mission/MissionPreview';
import VideoWall from '../components/video/VideoWall';
import DiscoveryAlert from '../components/discovery/DiscoveryAlert';
import DiscoveryList from '../components/discovery/DiscoveryList';

const LiveMission: React.FC = () => {
  // State management
  const [drones, setDrones] = useState<DroneStatus[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [discoveries, setDiscoveries] = useState<Discovery[]>([]);
  const [activeMission, setActiveMission] = useState<Mission | null>(null);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [emergencyMode, setEmergencyMode] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = new WebSocketService();

    ws.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    ws.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    ws.on('drone_update', (data: DroneStatus) => {
      setDrones(prev => {
        const existingIndex = prev.findIndex(d => d.id === data.id);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = data;
          return updated;
        }
        return [...prev, data];
      });
    });

    ws.on('mission_update', (data: Mission) => {
      setMissions(prev => {
        const existingIndex = prev.findIndex(m => m.id === data.id);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = data;
          return updated;
        }
        return [...prev, data];
      });

      // Update active mission if it's the one being updated
      if (activeMission?.id === data.id) {
        setActiveMission(data);
      }
    });

    ws.on('discovery_update', (data: Discovery) => {
      setDiscoveries(prev => {
        const existingIndex = prev.findIndex(d => d.id === data.id);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = data;
          return updated;
        }
        return [...prev, data];
      });
    });

    ws.on('emergency_alert', (data: any) => {
      setEmergencyMode(true);
      // Handle emergency alert
      console.error('Emergency alert received:', data);
    });

    setWsService(ws);

    return () => {
      ws.disconnect();
    };
  }, []);

  // Emergency controls
  const handleEmergencyStop = useCallback(() => {
    if (wsService && isConnected) {
      wsService.emit('emergency_stop', {
        reason: 'Manual emergency stop from dashboard',
        timestamp: Date.now()
      });
      setEmergencyMode(true);
    }
  }, [wsService, isConnected]);

  const handleReturnToBase = useCallback(() => {
    if (wsService && isConnected) {
      wsService.emit('return_to_base', {
        drone_ids: drones.filter(d => d.status === 'active').map(d => d.id),
        timestamp: Date.now()
      });
    }
  }, [wsService, isConnected, drones]);

  const handleResolveEmergency = useCallback(() => {
    setEmergencyMode(false);
    if (wsService && isConnected) {
      wsService.emit('emergency_resolved', {
        timestamp: Date.now()
      });
    }
  }, [wsService, isConnected]);

  // Filter active mission discoveries
  const activeMissionDiscoveries = discoveries.filter(d =>
    activeMission?.discoveries.some(ad => ad.id === d.id)
  );

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 p-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Live Mission Dashboard</h1>
          <div className="flex items-center gap-4 mt-2">
            <span className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            {emergencyMode && (
              <span className="bg-red-600 px-2 py-1 rounded text-sm font-semibold">
                EMERGENCY MODE
              </span>
            )}
          </div>
        </div>

        {/* Emergency Controls */}
        <div className="flex gap-2">
          <button
            onClick={handleReturnToBase}
            disabled={!isConnected || emergencyMode}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 rounded"
          >
            Return to Base
          </button>
          <button
            onClick={handleEmergencyStop}
            disabled={!isConnected || emergencyMode}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded"
          >
            Emergency Stop
          </button>
          {emergencyMode && (
            <button
              onClick={handleResolveEmergency}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded"
            >
              Resolve Emergency
            </button>
          )}
        </div>
      </header>

      <div className="flex-1 flex">
        {/* Left Panel - Mission Info & Discoveries */}
        <div className="w-80 bg-gray-800 flex flex-col">
          {/* Mission Selection */}
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold mb-2">Active Missions</h2>
            <select
              value={activeMission?.id || ''}
              onChange={(e) => {
                const mission = missions.find(m => m.id === e.target.value);
                setActiveMission(mission || null);
              }}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded"
            >
              <option value="">Select Mission</option>
              {missions.map(mission => (
                <option key={mission.id} value={mission.id}>
                  {mission.name} ({mission.status})
                </option>
              ))}
            </select>
          </div>

          {/* Mission Progress */}
          {activeMission && (
            <div className="p-4 border-b border-gray-700">
              <h3 className="font-semibold mb-2">{activeMission.name}</h3>
              <MissionPreview mission={activeMission} />
            </div>
          )}

          {/* Discovery Alerts */}
          <div className="flex-1 p-4">
            <h3 className="font-semibold mb-2">Discovery Alerts</h3>
            <DiscoveryList
              discoveries={activeMissionDiscoveries}
              onDiscoverySelect={(discovery) => {
                // Handle discovery selection
                console.log('Selected discovery:', discovery);
              }}
            />
          </div>
        </div>

        {/* Center Panel - Map */}
        <div className="flex-1 bg-gray-900">
          <InteractiveMap
            drones={drones}
            missions={missions.filter(m => m.id === activeMission?.id)}
            discoveries={activeMissionDiscoveries}
            onDroneSelect={(drone) => {
              console.log('Selected drone:', drone);
            }}
            onDiscoverySelect={(discovery) => {
              console.log('Selected discovery:', discovery);
            }}
          />
        </div>

        {/* Right Panel - Drones & Video */}
        <div className="w-80 bg-gray-800 flex flex-col">
          {/* Drone Status Grid */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="font-semibold mb-2">Drone Status</h3>
            <DroneGrid
              drones={drones}
              onDroneCommand={(droneId, command) => {
                if (wsService && isConnected) {
                  wsService.emit('drone_command', { droneId, command });
                }
              }}
            />
          </div>

          {/* Video Streams */}
          <div className="flex-1 p-4">
            <h3 className="font-semibold mb-2">Live Video Feeds</h3>
            <VideoWall
              droneIds={drones.filter(d => d.status === 'active').map(d => d.id)}
              onStreamSelect={(droneId) => {
                console.log('Selected video stream:', droneId);
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;