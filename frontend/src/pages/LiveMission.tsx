import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  MapPin,
  Plane,
  Activity,
  AlertTriangle,
  Play,
  Pause,
  Square,
  Clock,
  Battery,
  Signal,
  Eye,
  Camera
} from 'lucide-react';

const LiveMission: React.FC = () => {
  const { missionId } = useParams<{ missionId: string }>();
  const { subscribe, sendMessage } = useWebSocket();
  const [missionStatus, setMissionStatus] = useState<any>({});
  const [dronePositions, setDronePositions] = useState<any[]>([]);

  // Fetch mission details
  const { data: mission, isLoading: missionLoading } = useQuery(
    ['mission', missionId],
    () => apiService.missions.getById(missionId!),
    {
      enabled: !!missionId,
      refetchInterval: 5000,
    }
  );

  // Fetch mission status
  const { data: status, isLoading: statusLoading } = useQuery(
    ['mission-status', missionId],
    () => apiService.missions.getStatus(missionId!),
    {
      enabled: !!missionId,
      refetchInterval: 2000,
    }
  );

  useEffect(() => {
    if (missionId) {
      // Subscribe to real-time updates for this mission
      const unsubscribe = subscribe(`mission_${missionId}`, (data: any) => {
        if (data.type === 'drone_update') {
          setDronePositions(prev => {
            const existingIndex = prev.findIndex(d => d.drone_id === data.drone_id);
            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex] = { ...updated[existingIndex], ...data };
              return updated;
            } else {
              return [...prev, data];
            }
          });
        } else if (data.type === 'discovery') {
          setMissionStatus(prev => ({
            ...prev,
            discoveries: (prev.discoveries || 0) + 1
          }));
        }
      });

      return unsubscribe;
    }
  }, [missionId, subscribe]);

  const handleMissionControl = async (action: 'start' | 'pause' | 'resume' | 'complete') => {
    try {
      switch (action) {
        case 'start':
          await apiService.missions.start(missionId!);
          break;
        case 'pause':
          await apiService.missions.pause(missionId!);
          break;
        case 'resume':
          await apiService.missions.resume(missionId!);
          break;
        case 'complete':
          await apiService.missions.complete(missionId!, true);
          break;
      }

      // Refresh status
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error(`Error ${action}ing mission:`, error);
      alert(`Error ${action}ing mission`);
    }
  };

  if (missionLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!mission) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Mission Not Found</h2>
        <p className="text-gray-600">The requested mission could not be found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{mission.name}</h1>
          <p className="text-gray-600 mt-1">{mission.description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 text-sm rounded-full ${
            mission.status === 'active'
              ? 'bg-green-100 text-green-800'
              : mission.status === 'paused'
              ? 'bg-yellow-100 text-yellow-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {mission.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mission Control */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Mission Control</h2>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm text-gray-900">{mission.progress_percentage?.toFixed(1)}%</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Active Drones</span>
              <span className="text-sm text-gray-900">{mission.assigned_drones?.length || 0}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Discoveries</span>
              <span className="text-sm text-gray-900">{mission.discoveries_count || 0}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Area Covered</span>
              <span className="text-sm text-gray-900">{mission.area_covered?.toFixed(1)} m²</span>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            {mission.status === 'planning' || mission.status === 'ready' ? (
              <button
                onClick={() => handleMissionControl('start')}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center justify-center"
              >
                <Play className="h-4 w-4 mr-2" />
                Start Mission
              </button>
            ) : mission.status === 'active' ? (
              <>
                <button
                  onClick={() => handleMissionControl('pause')}
                  className="w-full bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 flex items-center justify-center"
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Pause Mission
                </button>
                <button
                  onClick={() => handleMissionControl('complete')}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 flex items-center justify-center"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Complete Mission
                </button>
              </>
            ) : mission.status === 'paused' ? (
              <button
                onClick={() => handleMissionControl('resume')}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center justify-center"
              >
                <Play className="h-4 w-4 mr-2" />
                Resume Mission
              </button>
            ) : null}
          </div>
        </div>

        {/* Live Map */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Live Mission View</h2>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">Interactive mission map will be displayed here</p>
              <p className="text-sm text-gray-400 mt-1">
                Center: {mission.center?.lat?.toFixed(4)}, {mission.center?.lng?.toFixed(4)}
              </p>
            </div>
          </div>

          {/* Drone Positions */}
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Active Drones</h3>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {dronePositions.map((drone, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center">
                    <Plane className="h-4 w-4 text-blue-500 mr-2" />
                    <span className="text-sm font-medium">{drone.drone_id}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-600">
                      {drone.position?.lat?.toFixed(4)}, {drone.position?.lng?.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {drone.battery_level?.toFixed(1)}% battery
                    </div>
                  </div>
                </div>
              ))}
              {dronePositions.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-2">No active drones</p>
              )}
            </div>
          </div>
        </div>

        {/* Mission Details */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Mission Details</h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Search Area</h3>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  Center: {mission.center?.lat?.toFixed(4)}, {mission.center?.lng?.toFixed(4)}
                </p>
                <p className="text-sm text-gray-600">
                  Altitude: {mission.search_altitude}m
                </p>
                <p className="text-sm text-gray-600">
                  Pattern: {mission.search_pattern}
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Assigned Drones</h3>
              <div className="space-y-2">
                {mission.assigned_drones?.map((drone: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium">{drone.drone_id}</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      drone.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {drone.status}
                    </span>
                  </div>
                )) || (
                  <p className="text-sm text-gray-500">No drones assigned</p>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Weather Conditions</h3>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Weather data will be displayed here</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Updates */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Real-time Updates</h2>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {status?.execution_status && (
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <Activity className="h-4 w-4 text-blue-500 mr-2" />
                <span className="text-sm font-medium">Mission Status</span>
              </div>
              <span className="text-sm text-blue-700 capitalize">
                {status.execution_status.status}
              </span>
            </div>
          )}

          {status?.coordination_status && (
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <Signal className="h-4 w-4 text-green-500 mr-2" />
                <span className="text-sm font-medium">Coordination</span>
              </div>
              <span className="text-sm text-green-700">
                {status.coordination_status.pending_commands} commands pending
              </span>
            </div>
          )}

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Camera className="h-4 w-4 text-gray-500 mr-2" />
              <span className="text-sm font-medium">Video Streams</span>
            </div>
            <span className="text-sm text-gray-700">Live feeds available</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;