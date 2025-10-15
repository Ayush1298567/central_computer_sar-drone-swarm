import React, { useEffect, useState } from 'react';
import { wsService } from '../services/websocket';
import RealTimeDroneMonitor from '../components/drone/RealTimeDroneMonitor';
import { droneConnectionService, DroneInfo } from '../services/droneConnections';

interface DroneStatus {
  id: string;
  status: string;
  battery: number;
  position: { lat: number; lon: number; alt: number };
  last_update: string;
}

interface Detection {
  class: string;
  confidence: number;
  bbox: number[];
  timestamp: string;
  drone_id: string;
}

interface MissionStatus {
  id: string;
  name: string;
  status: string;
  progress: number;
  drones_active: number;
}

const Dashboard: React.FC = () => {
  const [drones, setDrones] = useState<DroneStatus[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [missions, setMissions] = useState<MissionStatus[]>([]);
  const [aiDecisions, setAiDecisions] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  const [alerts, setAlerts] = useState<any[]>([]);
  const [realDrones, setRealDrones] = useState<DroneInfo[]>([]);
  const [selectedRealDrone, setSelectedRealDrone] = useState<DroneInfo | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect();
    
    // Load real drones
    loadRealDrones();
    
    // Update connection status
    const updateStatus = () => {
      setConnectionStatus(wsService.getConnectionStatus());
    };
    
    updateStatus();
    const statusInterval = setInterval(updateStatus, 1000);

    // Subscribe to telemetry updates
    const unsubTelemetry = wsService.on('telemetry', (data) => {
      setDrones(data.drones || []);
    });

    // Subscribe to detections
    const unsubDetections = wsService.on('detections', (data) => {
      setDetections(prev => [data, ...prev].slice(0, 20)); // Keep last 20 detections
    });

    // Subscribe to mission updates
    const unsubMissions = wsService.on('mission_updates', (data) => {
      setMissions(prev => {
        const updated = prev.filter(m => m.id !== data.id);
        return [data, ...updated];
      });
    });

    // Subscribe to AI decisions
    const unsubAIDecisions = wsService.on('ai_decisions', (data) => {
      setAiDecisions(prev => [data, ...prev].slice(0, 20));
    });

    // Subscribe to alerts
    const unsubAlerts = wsService.on('alerts', (data) => {
      setAlerts(prev => [data, ...prev].slice(0, 10)); // Keep last 10 alerts
    });

    // Request initial data
    wsService.requestTelemetry();

    return () => {
      unsubTelemetry();
      unsubDetections();
      unsubMissions();
      unsubAlerts();
      clearInterval(statusInterval);
      unsubAIDecisions();
    };
  }, []);

  // Load real drones from connection hub
  const loadRealDrones = async () => {
    try {
      const data = await droneConnectionService.getAllDrones();
      setRealDrones(data.drones.all);
    } catch (error) {
      console.error('Error loading real drones:', error);
    }
  };

  // Handle real drone selection
  const handleRealDroneSelect = (drone: DroneInfo) => {
    setSelectedRealDrone(drone);
  };

  const handleEmergencyStop = () => {
    if (window.confirm('Are you sure you want to trigger emergency stop for all drones?')) {
      wsService.triggerEmergencyStop('Manual emergency stop triggered from dashboard');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'flying':
        return 'text-green-600 bg-green-100';
      case 'landing':
      case 'returning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'emergency':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery < 20) return 'text-red-600';
    if (battery < 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">SAR Mission Control</h1>
              <p className="text-gray-600 mt-2">Real-time drone swarm monitoring and control</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                connectionStatus === 'connected' 
                  ? 'bg-green-100 text-green-800' 
                  : connectionStatus === 'connecting'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {connectionStatus === 'connected' ? '🟢 Connected' : 
                 connectionStatus === 'connecting' ? '🟡 Connecting' : '🔴 Disconnected'}
              </div>
              <button
                onClick={handleEmergencyStop}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                🚨 Emergency Stop
              </button>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-2xl">🚁</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Drones</p>
                <p className="text-2xl font-bold text-gray-900">{drones.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-2xl">👁️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Detections</p>
                <p className="text-2xl font-bold text-gray-900">{detections.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-2xl">📋</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Missions</p>
                <p className="text-2xl font-bold text-gray-900">{missions.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <span className="text-2xl">⚠️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{alerts.length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Real Drone Connection Hub */}
        <div className="mb-8">
          <RealTimeDroneMonitor 
            className="w-full"
            onDroneSelect={handleRealDroneSelect}
            selectedDroneId={selectedRealDrone?.drone_id}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Drone Status */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Drone Status</h2>
            </div>
            <div className="p-6">
              {drones.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No drone data available</p>
              ) : (
                <div className="space-y-4">
                  {drones.map((drone) => (
                    <div key={drone.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <div>
                          <p className="font-medium text-gray-900">{drone.id}</p>
                          <p className="text-sm text-gray-600">
                            {drone.position.lat.toFixed(4)}, {drone.position.lon.toFixed(4)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(drone.status)}`}>
                          {drone.status}
                        </span>
                        <span className={`text-sm font-medium ${getBatteryColor(drone.battery)}`}>
                          {drone.battery}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Detections */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Recent Detections</h2>
            </div>
            <div className="p-6">
              {detections.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No detections yet</p>
              ) : (
                <div className="space-y-3">
                  {detections.slice(0, 10).map((detection, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="font-medium text-gray-900">{detection.class}</p>
                          <p className="text-sm text-gray-600">Drone: {detection.drone_id}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {(detection.confidence * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(detection.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Active Missions */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Active Missions</h2>
            </div>
            <div className="p-6">
              {missions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No active missions</p>
              ) : (
                <div className="space-y-4">
                  {missions.map((mission) => (
                    <div key={mission.id} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900">{mission.name}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(mission.status)}`}>
                          {mission.status}
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>Progress</span>
                          <span>{mission.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${mission.progress}%` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>Drones Active</span>
                          <span>{mission.drones_active}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Alerts */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">System Alerts</h2>
            </div>
            <div className="p-6">
              {alerts.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No alerts</p>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert, index) => (
                    <div key={index} className={`p-3 border rounded-lg ${
                      alert.level === 'critical' ? 'border-red-200 bg-red-50' :
                      alert.level === 'warning' ? 'border-yellow-200 bg-yellow-50' :
                      'border-blue-200 bg-blue-50'
                    }`}>
                      <div className="flex items-start space-x-3">
                        <span className="text-lg">
                          {alert.level === 'critical' ? '🚨' : 
                           alert.level === 'warning' ? '⚠️' : 'ℹ️'}
                        </span>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{alert.message}</p>
                          <p className="text-sm text-gray-600 mt-1">
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* AI Decisions */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">AI Decisions</h2>
            </div>
            <div className="p-6">
              {aiDecisions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No AI decisions yet</p>
              ) : (
                <div className="space-y-3">
                  {aiDecisions.slice(0, 10).map((d, idx) => (
                    <div key={idx} className="p-3 border border-gray-200 rounded-lg">
                      <div className="flex justify-between">
                        <div className="font-medium text-gray-900">{d.type}</div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          d.severity === 'critical' ? 'bg-red-100 text-red-800' :
                          d.severity === 'high' ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {d.severity}
                        </span>
                      </div>
                      <div className="text-sm text-gray-700 mt-1">{d.reasoning}</div>
                      <div className="text-xs text-gray-500 mt-1">Confidence: {(d.confidence_score * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;