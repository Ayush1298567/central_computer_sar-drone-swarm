/**
 * Live Mission Page for SAR Mission Commander.
 * Provides real-time monitoring, video streams, and emergency controls for active missions.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Play,
  Pause,
  Square,
  AlertTriangle,
  Wifi,
  WifiOff,
  Battery,
  MapPin,
  Clock,
  Users,
  Target,
  Activity,
  Settings,
  Download,
  Maximize,
  Minimize,
  Volume2,
  VolumeX,
  Camera,
  Monitor,
  Zap,
  Shield,
} from 'lucide-react';

// Import types
import {
  Mission,
  MissionProgress,
  Drone,
  DroneTelemetry,
  DroneAlert,
  Discovery,
  MissionEvent,
  Coordinate,
} from '../types';

// Import services
import { MissionService, websocketService, WebSocketSubscriptions } from '../services';

// Import components
import InteractiveMap from '../components/map/InteractiveMap';

interface LiveMissionProps {
  missionId: string;
  onBack?: () => void;
  className?: string;
}

interface LiveMissionState {
  mission: Mission | null;
  missionProgress: MissionProgress | null;
  drones: Drone[];
  discoveries: Discovery[];
  alerts: DroneAlert[];
  events: MissionEvent[];
  isLoading: boolean;
  error: string | null;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
  selectedDrone: string | null;
  showVideoStreams: boolean;
  showEmergencyPanel: boolean;
  autoCenterMap: boolean;
}

export const LiveMission: React.FC<LiveMissionProps> = ({
  missionId,
  onBack,
  className = '',
}) => {
  const [state, setState] = useState<LiveMissionState>({
    mission: null,
    missionProgress: null,
    drones: [],
    discoveries: [],
    alerts: [],
    events: [],
    isLoading: true,
    error: null,
    connectionStatus: 'disconnected',
    selectedDrone: null,
    showVideoStreams: true,
    showEmergencyPanel: false,
    autoCenterMap: true,
  });

  // Load initial mission data
  const loadMissionData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      // Load mission details
      const missionResponse = await MissionService.getMission(missionId);
      if (!missionResponse.success) {
        throw new Error(missionResponse.error || 'Failed to load mission');
      }

      const mission = missionResponse.data!;

      // Load initial mission progress
      const progressResponse = await MissionService.getMissionProgress(missionId);
      const missionProgress = progressResponse.success ? progressResponse.data! : null;

      // Load drones
      const dronesResponse = await MissionService.getDrones();
      const drones = dronesResponse.success ? dronesResponse.data || [] : [];

      setState(prev => ({
        ...prev,
        mission,
        missionProgress,
        drones,
        isLoading: false,
      }));

    } catch (error: any) {
      console.error('Error loading mission data:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load mission data',
        isLoading: false,
      }));
    }
  }, [missionId]);

  // Set up WebSocket subscriptions
  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect().catch(console.error);

    // Subscribe to mission updates
    const unsubscribeProgress = WebSocketSubscriptions.subscribeToMissionProgress(
      missionId,
      (progress: MissionProgress) => {
        setState(prev => ({ ...prev, missionProgress: progress }));
      }
    );

    const unsubscribeEvents = WebSocketSubscriptions.subscribeToMissionEvents(
      missionId,
      (event: MissionEvent) => {
        setState(prev => ({
          ...prev,
          events: [event, ...prev.events.slice(0, 99)], // Keep last 100 events
        }));
      }
    );

    const unsubscribeDiscoveries = WebSocketSubscriptions.subscribeToDiscoveries(
      missionId,
      (discovery: Discovery) => {
        setState(prev => ({
          ...prev,
          discoveries: [...prev.discoveries, discovery],
        }));
      }
    );

    // Connection status monitoring
    const unsubscribeConnection = websocketService.onConnectionChange((connected) => {
      setState(prev => ({
        ...prev,
        connectionStatus: connected ? 'connected' : 'disconnected',
      }));
    });

    return () => {
      unsubscribeProgress();
      unsubscribeEvents();
      unsubscribeDiscoveries();
      unsubscribeConnection();
      websocketService.disconnect();
    };
  }, [missionId]);

  // Load data on mount
  useEffect(() => {
    loadMissionData();
  }, [loadMissionData]);

  // Mission control functions
  const handleStartMission = async () => {
    try {
      const response = await MissionService.startMission(missionId);
      if (response.success) {
        // Reload mission data
        loadMissionData();
      }
    } catch (error) {
      console.error('Failed to start mission:', error);
    }
  };

  const handlePauseMission = async () => {
    try {
      const response = await MissionService.pauseMission(missionId, 'User requested pause');
      if (response.success) {
        loadMissionData();
      }
    } catch (error) {
      console.error('Failed to pause mission:', error);
    }
  };

  const handleResumeMission = async () => {
    try {
      const response = await MissionService.resumeMission(missionId);
      if (response.success) {
        loadMissionData();
      }
    } catch (error) {
      console.error('Failed to resume mission:', error);
    }
  };

  const handleAbortMission = async () => {
    if (window.confirm('Are you sure you want to abort this mission? This action cannot be undone.')) {
      try {
        const response = await MissionService.abortMission(missionId, 'Emergency abort by operator', true);
        if (response.success) {
          loadMissionData();
        }
      } catch (error) {
        console.error('Failed to abort mission:', error);
      }
    }
  };

  const handleEmergencyStop = async () => {
    try {
      await MissionService.emergencyStop(missionId);
      // This would trigger immediate drone stopping
    } catch (error) {
      console.error('Failed to execute emergency stop:', error);
    }
  };

  // Drone control functions
  const handleDroneCommand = async (droneId: string, command: string, parameters: any = {}) => {
    try {
      await MissionService.sendDroneCommand(droneId, command, parameters);
    } catch (error) {
      console.error(`Failed to send command to drone ${droneId}:`, error);
    }
  };

  // Calculate mission statistics
  const missionStats = React.useMemo(() => {
    if (!state.missionProgress) return null;

    const progress = state.missionProgress;
    const totalDrones = progress.total_drones;
    const activeDrones = progress.active_drones;
    const completedDrones = progress.drones_returned;

    return {
      progress: Math.round(progress.overall_progress * 100),
      coverage: Math.round(progress.coverage_percentage),
      discoveries: progress.discoveries_found,
      activeDrones,
      totalDrones,
      completedDrones,
      estimatedTimeRemaining: progress.estimated_completion
        ? Math.max(0, Math.round((new Date(progress.estimated_completion).getTime() - Date.now()) / 60000))
        : null,
    };
  }, [state.missionProgress]);

  // Connection status indicator
  const ConnectionStatusIndicator: React.FC = () => (
    <div className="flex items-center space-x-2">
      <div className={`w-3 h-3 rounded-full ${
        state.connectionStatus === 'connected' ? 'bg-green-500' :
        state.connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
        'bg-red-500'
      }`} />
      <span className="text-sm text-gray-600">
        {state.connectionStatus === 'connected' ? 'Live' :
         state.connectionStatus === 'connecting' ? 'Connecting...' :
         'Offline'}
      </span>
    </div>
  );

  // Mission header
  const MissionHeader: React.FC = () => (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="text-gray-500 hover:text-gray-700"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{state.mission?.name}</h1>
            <p className="text-gray-600">{state.mission?.description}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <ConnectionStatusIndicator />
          <div className="text-right text-sm">
            <div className="text-gray-600">Status</div>
            <div className={`font-medium ${
              state.mission?.status === 'active' ? 'text-green-600' :
              state.mission?.status === 'paused' ? 'text-yellow-600' :
              'text-gray-600'
            }`}>
              {state.mission?.status?.toUpperCase()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Mission statistics bar
  const MissionStatsBar: React.FC = () => {
    if (!missionStats) return null;

    return (
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{missionStats.progress}%</div>
            <div className="text-sm opacity-90">Progress</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{missionStats.coverage}%</div>
            <div className="text-sm opacity-90">Coverage</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{missionStats.discoveries}</div>
            <div className="text-sm opacity-90">Discoveries</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{missionStats.activeDrones}/{missionStats.totalDrones}</div>
            <div className="text-sm opacity-90">Active Drones</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {missionStats.estimatedTimeRemaining ? `${missionStats.estimatedTimeRemaining}m` : '--'}
            </div>
            <div className="text-sm opacity-90">Time Remaining</div>
          </div>
          <div className="text-center">
            <button
              onClick={() => setState(prev => ({ ...prev, showEmergencyPanel: !prev.showEmergencyPanel }))}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
            >
              Emergency
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Drone status cards
  const DroneStatusCards: React.FC = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {state.drones.map((drone) => (
        <div
          key={drone.id}
          className={`p-4 border rounded-lg cursor-pointer transition-colors ${
            state.selectedDrone === drone.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => setState(prev => ({ ...prev, selectedDrone: drone.id === prev.selectedDrone ? null : drone.id }))}
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-800">Drone {drone.name}</h3>
            <div className={`w-3 h-3 rounded-full ${
              drone.status === 'flying' ? 'bg-green-500' :
              drone.status === 'online' ? 'bg-blue-500' :
              'bg-gray-400'
            }`} />
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Battery:</span>
              <span className={`font-medium ${
                drone.battery_level < 25 ? 'text-red-600' : 'text-green-600'
              }`}>
                {drone.battery_level}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Signal:</span>
              <span className={`font-medium ${
                drone.signal_strength < 30 ? 'text-red-600' :
                drone.signal_strength < 70 ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {drone.signal_strength}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="font-medium">{drone.status}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  // Emergency control panel
  const EmergencyPanel: React.FC = () => (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-center mb-4">
        <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
        <h3 className="font-semibold text-red-800">Emergency Controls</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <button
          onClick={handleEmergencyStop}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center justify-center"
        >
          <Square className="w-4 h-4 mr-2" />
          Emergency Stop
        </button>
        <button
          onClick={() => handleAbortMission()}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center justify-center"
        >
          <Zap className="w-4 h-4 mr-2" />
          Abort Mission
        </button>
        <button
          onClick={() => handleDroneCommand('all', 'return_to_home')}
          className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded flex items-center justify-center"
        >
          <MapPin className="w-4 h-4 mr-2" />
          All Return Home
        </button>
        <button
          onClick={() => setState(prev => ({ ...prev, showEmergencyPanel: false }))}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded flex items-center justify-center"
        >
          Close
        </button>
      </div>
    </div>
  );

  // Mission control buttons
  const MissionControls: React.FC = () => (
    <div className="flex items-center space-x-3">
      {state.mission?.status === 'ready' && (
        <button
          onClick={handleStartMission}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center"
        >
          <Play className="w-4 h-4 mr-2" />
          Start Mission
        </button>
      )}

      {state.mission?.status === 'active' && (
        <button
          onClick={handlePauseMission}
          className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded flex items-center"
        >
          <Pause className="w-4 h-4 mr-2" />
          Pause Mission
        </button>
      )}

      {state.mission?.status === 'paused' && (
        <button
          onClick={handleResumeMission}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center"
        >
          <Play className="w-4 h-4 mr-2" />
          Resume Mission
        </button>
      )}

      <button
        onClick={() => setState(prev => ({ ...prev, showEmergencyPanel: !prev.showEmergencyPanel }))}
        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center"
      >
        <AlertTriangle className="w-4 h-4 mr-2" />
        Emergency
      </button>
    </div>
  );

  if (state.isLoading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading mission data...</p>
        </div>
      </div>
    );
  }

  if (state.error || !state.mission) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-8 text-center ${className}`}>
        <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Mission</h3>
        <p className="text-red-600 mb-4">{state.error || 'Mission not found'}</p>
        <button
          onClick={loadMissionData}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`h-screen flex flex-col bg-gray-100 ${className}`}>
      {/* Header */}
      <MissionHeader />

      {/* Stats Bar */}
      <MissionStatsBar />

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Panel - Mission Info & Controls */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Mission Controls */}
          <div className="p-4 border-b border-gray-200">
            <MissionControls />
          </div>

          {/* Emergency Panel */}
          {state.showEmergencyPanel && (
            <div className="p-4 border-b border-gray-200">
              <EmergencyPanel />
            </div>
          )}

          {/* Drone Status */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Drone Status ({state.drones.length})
            </h3>
            <DroneStatusCards />
          </div>

          {/* Recent Events */}
          <div className="p-4 border-t border-gray-200">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Recent Events
            </h3>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {state.events.slice(0, 5).map((event, index) => (
                <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                  <div className="font-medium">{event.event_type}</div>
                  <div className="text-gray-600 text-xs">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel - Map & Video */}
        <div className="flex-1 flex flex-col">
          {/* Map Controls */}
          <div className="bg-white border-b border-gray-200 p-2 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={state.autoCenterMap}
                  onChange={(e) => setState(prev => ({ ...prev, autoCenterMap: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm">Auto-center map</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={state.showVideoStreams}
                  onChange={(e) => setState(prev => ({ ...prev, showVideoStreams: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm">Show video streams</span>
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setState(prev => ({ ...prev, showVideoStreams: !prev.showVideoStreams }))}
                className="p-2 text-gray-500 hover:text-gray-700"
                title="Toggle video streams"
              >
                <Camera className="w-4 h-4" />
              </button>
              <button
                onClick={() => {/* Toggle fullscreen */}}
                className="p-2 text-gray-500 hover:text-gray-700"
                title="Toggle fullscreen"
              >
                <Maximize className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Map Area */}
          <div className="flex-1 relative">
            <InteractiveMap
              mission={state.mission}
              drones={state.drones}
              selectedDrone={state.selectedDrone}
              onDroneSelect={(drone) => setState(prev => ({ ...prev, selectedDrone: drone.id }))}
              height="100%"
            />

            {/* Video Streams Overlay */}
            {state.showVideoStreams && state.selectedDrone && (
              <div className="absolute top-4 right-4 w-64 bg-black rounded-lg overflow-hidden shadow-lg">
                <div className="bg-gray-800 text-white p-2 text-sm flex items-center justify-between">
                  <span>Drone {state.selectedDrone} Video</span>
                  <button
                    onClick={() => setState(prev => ({ ...prev, showVideoStreams: false }))}
                    className="text-gray-400 hover:text-white"
                  >
                    <VolumeX className="w-4 h-4" />
                  </button>
                </div>
                <div className="aspect-video bg-gray-900 flex items-center justify-center">
                  <Camera className="w-8 h-8 text-gray-600" />
                  <span className="text-gray-400 ml-2">Video Stream</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;