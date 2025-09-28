/**
 * Live Mission Dashboard
 * Real-time mission monitoring and control interface
 */

import React, { useState, useEffect, useCallback } from 'react';
import { websocketService, WebSocketMessage } from '../services/websocketService';
import {
  Drone,
  Mission,
  Discovery,
  VideoStream,
  MissionControlCommand,
  DashboardStats,
  MapViewport
} from '../types';

// Import components (will be created next)
import { VideoWall } from '../components/video/VideoWall';
import { DiscoveryAlert } from '../components/discovery/DiscoveryAlert';
import { DiscoveryList } from '../components/discovery/DiscoveryList';

interface LiveMissionProps {
  missionId?: string;
}

export const LiveMission: React.FC<LiveMissionProps> = ({ missionId }) => {
  // State management
  const [mission, setMission] = useState<Mission | null>(null);
  const [drones, setDrones] = useState<Drone[]>([]);
  const [discoveries, setDiscoveries] = useState<Discovery[]>([]);
  const [videoStreams, setVideoStreams] = useState<VideoStream[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalDrones: 0,
    activeDrones: 0,
    totalDiscoveries: 0,
    criticalDiscoveries: 0,
    missionProgress: 0,
    averageBattery: 100,
    connectionStatus: 'disconnected'
  });
  const [mapViewport, setMapViewport] = useState<MapViewport>({
    center: { lat: 40.7128, lng: -74.0060 }, // Default to NYC
    zoom: 10
  });
  const [selectedDrone, setSelectedDrone] = useState<string | null>(null);
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [newDiscoveries, setNewDiscoveries] = useState<Discovery[]>([]);

  // WebSocket message handlers
  useEffect(() => {
    const unsubscribeDroneUpdate = websocketService.subscribe('drone_update', (message: WebSocketMessage) => {
      const updatedDrone: Drone = message.payload;
      setDrones(prev => prev.map(drone =>
        drone.id === updatedDrone.id ? updatedDrone : drone
      ));

      // Update selected drone if it's the one being updated
      if (selectedDrone === updatedDrone.id) {
        setSelectedDrone(updatedDrone.id);
      }
    });

    const unsubscribeMissionUpdate = websocketService.subscribe('mission_update', (message: WebSocketMessage) => {
      const updatedMission: Mission = message.payload;
      setMission(updatedMission);
      updateStats(updatedMission, drones, discoveries);
    });

    const unsubscribeDiscoveryUpdate = websocketService.subscribe('discovery_update', (message: WebSocketMessage) => {
      const discovery: Discovery = message.payload;

      // Check if this is a new discovery
      const isNew = !discoveries.find(d => d.id === discovery.id);
      if (isNew) {
        setNewDiscoveries(prev => [discovery, ...prev.slice(0, 4)]); // Keep last 5 new discoveries

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
          setNewDiscoveries(prev => prev.filter(d => d.id !== discovery.id));
        }, 5000);
      }

      setDiscoveries(prev => {
        const existingIndex = prev.findIndex(d => d.id === discovery.id);
        if (existingIndex >= 0) {
          // Update existing discovery
          const updated = [...prev];
          updated[existingIndex] = discovery;
          return updated;
        } else {
          // Add new discovery
          return [discovery, ...prev];
        }
      });

      updateStats(mission, drones, [...discoveries, discovery]);
    });

    const unsubscribeVideoStream = websocketService.subscribe('video_stream_update', (message: WebSocketMessage) => {
      const stream: VideoStream = message.payload;
      setVideoStreams(prev => prev.map(s =>
        s.id === stream.id ? stream : s
      ));
    });

    const unsubscribeConnectionStatus = websocketService.subscribe('connection_status', (message: WebSocketMessage) => {
      const status = message.payload;
      setStats(prev => ({
        ...prev,
        connectionStatus: status.isConnected ? 'connected' : 'disconnected'
      }));
    });

    // Request initial data
    if (missionId) {
      websocketService.send({
        type: 'request_mission_data',
        payload: { missionId },
        timestamp: Date.now()
      });
    }

    // Cleanup subscriptions
    return () => {
      unsubscribeDroneUpdate();
      unsubscribeMissionUpdate();
      unsubscribeDiscoveryUpdate();
      unsubscribeVideoStream();
      unsubscribeConnectionStatus();
    };
  }, [missionId, selectedDrone, mission, drones, discoveries]);

  // Update dashboard statistics
  const updateStats = useCallback((currentMission: Mission | null, currentDrones: Drone[], currentDiscoveries: Discovery[]) => {
    if (!currentMission) return;

    const activeDrones = currentDrones.filter(d => d.status === 'active').length;
    const criticalDiscoveries = currentDiscoveries.filter(d => d.priority === 'critical').length;

    setStats({
      totalDrones: currentDrones.length,
      activeDrones,
      totalDiscoveries: currentDiscoveries.length,
      criticalDiscoveries,
      missionProgress: currentMission.progress,
      averageBattery: currentDrones.length > 0
        ? Math.round(currentDrones.reduce((sum, d) => sum + d.battery, 0) / currentDrones.length)
        : 100,
      connectionStatus: websocketService.getConnectionStatus().isConnected ? 'connected' : 'disconnected'
    });
  }, []);

  // Emergency control handlers
  const handleEmergencyStop = useCallback(() => {
    const command: MissionControlCommand = {
      type: 'emergency_stop',
      timestamp: new Date(),
      issuedBy: 'operator'
    };

    websocketService.send({
      type: 'mission_command',
      payload: command,
      timestamp: Date.now()
    });

    setEmergencyMode(true);
  }, []);

  const handleReturnToBase = useCallback(() => {
    const command: MissionControlCommand = {
      type: 'return_to_base',
      timestamp: new Date(),
      issuedBy: 'operator'
    };

    websocketService.send({
      type: 'mission_command',
      payload: command,
      timestamp: Date.now()
    });
  }, []);

  const handlePauseMission = useCallback(() => {
    if (!mission) return;

    const command: MissionControlCommand = {
      type: 'pause_mission',
      targetMissionId: mission.id,
      timestamp: new Date(),
      issuedBy: 'operator'
    };

    websocketService.send({
      type: 'mission_command',
      payload: command,
      timestamp: Date.now()
    });
  }, []);

  const handleResumeMission = useCallback(() => {
    if (!mission) return;

    const command: MissionControlCommand = {
      type: 'resume_mission',
      targetMissionId: mission.id,
      timestamp: new Date(),
      issuedBy: 'operator'
    };

    websocketService.send({
      type: 'mission_command',
      payload: command,
      timestamp: Date.now()
    });
  }, [mission]);

  // Map interaction handlers
  const handleMapViewportChange = useCallback((newViewport: MapViewport) => {
    setMapViewport(newViewport);
  }, []);

  const handleDroneSelect = useCallback((droneId: string) => {
    setSelectedDrone(droneId);
  }, []);

  if (!mission) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading mission data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{mission.name}</h1>
            <p className="text-gray-600">Mission ID: {mission.id}</p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
              stats.connectionStatus === 'connected'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                stats.connectionStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm font-medium capitalize">{stats.connectionStatus}</span>
            </div>

            {/* Emergency Controls */}
            <div className="flex space-x-2">
              <button
                onClick={handleEmergencyStop}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
              >
                Emergency Stop
              </button>
              <button
                onClick={handleReturnToBase}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 font-medium"
              >
                Return to Base
              </button>
              {mission.status === 'active' ? (
                <button
                  onClick={handlePauseMission}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium"
                >
                  Pause Mission
                </button>
              ) : (
                <button
                  onClick={handleResumeMission}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                >
                  Resume Mission
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-white border-b p-4">
        <div className="grid grid-cols-6 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.totalDrones}</div>
            <div className="text-sm text-gray-600">Total Drones</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.activeDrones}</div>
            <div className="text-sm text-gray-600">Active Drones</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{stats.totalDiscoveries}</div>
            <div className="text-sm text-gray-600">Discoveries</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.criticalDiscoveries}</div>
            <div className="text-sm text-gray-600">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{stats.missionProgress}%</div>
            <div className="text-sm text-gray-600">Progress</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">{stats.averageBattery}%</div>
            <div className="text-sm text-gray-600">Avg Battery</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Map Section */}
        <div className="flex-1 relative">
          <DroneMap
            drones={drones}
            mission={mission}
            discoveries={discoveries}
            viewport={mapViewport}
            onViewportChange={handleMapViewportChange}
            onDroneSelect={handleDroneSelect}
            selectedDrone={selectedDrone}
          />

          {/* Discovery Alerts Overlay */}
          <div className="absolute top-4 right-4 space-y-2">
            {newDiscoveries.map(discovery => (
              <DiscoveryAlert
                key={discovery.id}
                discovery={discovery}
                onDismiss={() => setNewDiscoveries(prev => prev.filter(d => d.id !== discovery.id))}
              />
            ))}
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-96 bg-white border-l flex flex-col">
          {/* Video Streams */}
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold mb-3">Live Video Feeds</h3>
            <VideoWall
              streams={videoStreams}
              maxStreams={4}
              onStreamSelect={(streamId) => console.log('Stream selected:', streamId)}
            />
          </div>

          {/* Discovery Management */}
          <div className="flex-1 p-4 overflow-hidden">
            <h3 className="text-lg font-semibold mb-3">Recent Discoveries</h3>
            <DiscoveryList
              discoveries={discoveries.slice(0, 10)}
              onDiscoverySelect={(discoveryId) => console.log('Discovery selected:', discoveryId)}
              compact={true}
            />
          </div>
        </div>
      </div>

      {/* Emergency Mode Overlay */}
      {emergencyMode && (
        <div className="absolute inset-0 bg-red-900 bg-opacity-90 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg text-center max-w-md">
            <div className="text-6xl text-red-600 mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-red-800 mb-4">Emergency Stop Activated</h2>
            <p className="text-gray-700 mb-6">
              All drones have been instructed to stop immediately and return to base.
            </p>
            <button
              onClick={() => setEmergencyMode(false)}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
            >
              Acknowledge
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Placeholder components (will be implemented next)
const DroneMap: React.FC<{
  drones: Drone[];
  mission: Mission;
  discoveries: Discovery[];
  viewport: MapViewport;
  onViewportChange: (viewport: MapViewport) => void;
  onDroneSelect: (droneId: string) => void;
  selectedDrone: string | null;
}> = ({ drones, mission, discoveries, viewport, onViewportChange, onDroneSelect, selectedDrone }) => {
  return (
    <div className="w-full h-full bg-gray-200 flex items-center justify-center">
      <div className="text-center text-gray-600">
        <div className="text-4xl mb-4">🗺️</div>
        <p>Interactive Map Component</p>
        <p className="text-sm mt-2">Real-time drone tracking and mission visualization</p>
        <div className="mt-4 text-xs">
          Drones: {drones.length} | Discoveries: {discoveries.length}
        </div>
      </div>
    </div>
  );
};