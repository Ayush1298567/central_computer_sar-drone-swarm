import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  Users, 
  Target, 
  AlertTriangle,
  Plane,
  Route,
  Calendar,
  Thermometer,
  Wind,
  Eye
} from 'lucide-react';
import { Mission, MissionPlan } from '../../types/mission';
import { Drone } from '../../types/drone';
// import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';

interface MissionPreviewProps {
  mission: Mission;
  missionPlan?: MissionPlan;
  assignedDrones: Drone[];
  onApprove?: () => void;
  onReject?: (reason: string) => void;
  onModify?: () => void;
  isReadOnly?: boolean;
  className?: string;
}

interface MissionStats {
  totalDistance: number;
  estimatedDuration: number;
  coverageArea: number;
  droneCount: number;
  averageBatteryRequired: number;
  weatherRisk: 'low' | 'medium' | 'high';
}

export const MissionPreview: React.FC<MissionPreviewProps> = ({
  mission,
  missionPlan,
  assignedDrones,
  onApprove,
  onReject,
  onModify,
  isReadOnly = false,
  className = '',
}) => {
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [realTimeMission, setRealTimeMission] = useState<Mission>(mission);
  const [isLoading, setIsLoading] = useState(false);

  // Subscribe to real-time mission updates
  useEffect(() => {
    const handleMissionUpdate = (data: any) => {
      if (data.mission_id === mission.id) {
        setRealTimeMission(prev => ({ ...prev, ...data }));
      }
    };

    webSocketService.subscribe('mission_update', handleMissionUpdate);
    webSocketService.subscribeMission(mission.id);

    return () => {
      webSocketService.unsubscribe('mission_update', handleMissionUpdate);
      webSocketService.unsubscribeMission(mission.id);
    };
  }, [mission.id]);

  // Calculate mission statistics
  const missionStats: MissionStats = useMemo(() => {
    const stats: MissionStats = {
      totalDistance: missionPlan?.total_distance || 0,
      estimatedDuration: missionPlan?.estimated_duration || realTimeMission.estimated_duration || 0,
      coverageArea: calculatePolygonArea(realTimeMission.search_area.coordinates[0]),
      droneCount: assignedDrones.length,
      averageBatteryRequired: 0,
      weatherRisk: 'low',
    };

    // Calculate average battery required
    if (missionPlan?.drone_assignments) {
      const totalBattery = missionPlan.drone_assignments.reduce(
        (sum, assignment) => sum + assignment.battery_required, 0
      );
      stats.averageBatteryRequired = totalBattery / missionPlan.drone_assignments.length;
    }

    // Assess weather risk
    if (realTimeMission.weather_conditions) {
      const { wind_speed, visibility } = realTimeMission.weather_conditions;
      if (wind_speed > 15 || visibility < 5) {
        stats.weatherRisk = 'high';
      } else if (wind_speed > 10 || visibility < 10) {
        stats.weatherRisk = 'medium';
      }
    }

    return stats;
  }, [realTimeMission, missionPlan, assignedDrones]);

  // Calculate polygon area (simplified)
  function calculatePolygonArea(coordinates: number[][]): number {
    // Simplified area calculation for display purposes
    // In a real application, you'd use proper geospatial calculations
    if (coordinates.length < 3) return 0;
    
    let area = 0;
    for (let i = 0; i < coordinates.length; i++) {
      const j = (i + 1) % coordinates.length;
      area += coordinates[i][0] * coordinates[j][1];
      area -= coordinates[j][0] * coordinates[i][1];
    }
    return Math.abs(area / 2) * 111320 * 111320 / 1000000; // Rough conversion to km²
  }

  const handleApprove = async () => {
    if (!onApprove) return;
    
    setIsLoading(true);
    try {
      onApprove();
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    if (!onReject || !rejectReason.trim()) return;
    
    setIsLoading(true);
    try {
      onReject(rejectReason);
      setShowRejectModal(false);
      setRejectReason('');
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'completed': return 'text-blue-600 bg-blue-100';
      case 'aborted': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {realTimeMission.name}
            </h2>
            <p className="text-gray-600 mb-4">{realTimeMission.description}</p>
            
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(realTimeMission.priority)}`}>
                {realTimeMission.priority} priority
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(realTimeMission.status)}`}>
                {realTimeMission.status}
              </span>
              <div className="flex items-center text-sm text-gray-500">
                <Calendar size={14} className="mr-1" />
                {new Date(realTimeMission.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          {!isReadOnly && realTimeMission.status === 'planning' && (
            <div className="flex space-x-2">
              <button
                onClick={onModify}
                className="btn btn-secondary text-sm"
                disabled={isLoading}
              >
                Modify
              </button>
              <button
                onClick={() => setShowRejectModal(true)}
                className="btn btn-danger text-sm"
                disabled={isLoading}
              >
                Reject
              </button>
              <button
                onClick={handleApprove}
                className="btn btn-success text-sm"
                disabled={isLoading}
              >
                {isLoading ? 'Approving...' : 'Approve'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mission Statistics */}
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Mission Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
              <Target size={24} className="text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {missionStats.coverageArea.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">km² coverage</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
              <Clock size={24} className="text-green-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {formatDuration(missionStats.estimatedDuration)}
            </div>
            <div className="text-sm text-gray-600">estimated time</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-2">
              <Users size={24} className="text-purple-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {missionStats.droneCount}
            </div>
            <div className="text-sm text-gray-600">drones assigned</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-lg mx-auto mb-2">
              <Route size={24} className="text-yellow-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {missionStats.totalDistance.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">km total distance</div>
          </div>
        </div>
      </div>

      {/* Drone Assignments */}
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Drone Assignments</h3>
        <div className="space-y-3">
          {assignedDrones.map((drone) => {
            const assignment = missionPlan?.drone_assignments.find(a => a.drone_id === drone.id);
            return (
              <div key={drone.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                    <Plane size={16} className="text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{drone.name}</div>
                    <div className="text-sm text-gray-600">{drone.model}</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-6 text-sm">
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {assignment ? formatDuration(assignment.estimated_flight_time) : 'N/A'}
                    </div>
                    <div className="text-gray-600">flight time</div>
                  </div>
                  
                  <div className="text-center">
                    <div className={`font-medium ${
                      drone.battery_level > 60 ? 'text-green-600' :
                      drone.battery_level > 30 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {drone.battery_level}%
                    </div>
                    <div className="text-gray-600">battery</div>
                  </div>
                  
                  <div className="text-center">
                    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      drone.status === 'idle' ? 'bg-green-100 text-green-800' :
                      drone.status === 'active' ? 'bg-blue-100 text-blue-800' :
                      drone.status === 'charging' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {drone.status}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Weather & Conditions */}
      {realTimeMission.weather_conditions && (
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Weather Conditions</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <Wind size={20} className="text-gray-400" />
              <div>
                <div className="font-medium text-gray-900">
                  {realTimeMission.weather_conditions.wind_speed} m/s
                </div>
                <div className="text-sm text-gray-600">wind speed</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Eye size={20} className="text-gray-400" />
              <div>
                <div className="font-medium text-gray-900">
                  {realTimeMission.weather_conditions.visibility} km
                </div>
                <div className="text-sm text-gray-600">visibility</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Thermometer size={20} className="text-gray-400" />
              <div>
                <div className="font-medium text-gray-900">
                  {realTimeMission.weather_conditions.temperature}°C
                </div>
                <div className="text-sm text-gray-600">temperature</div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 flex items-center space-x-2">
            <AlertTriangle size={16} className={getRiskColor(missionStats.weatherRisk)} />
            <span className={`text-sm font-medium ${getRiskColor(missionStats.weatherRisk)}`}>
              {missionStats.weatherRisk.toUpperCase()} weather risk
            </span>
          </div>
        </div>
      )}

      {/* Progress Bar (for active missions) */}
      {realTimeMission.status === 'active' && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold">Mission Progress</h3>
            <span className="text-sm font-medium text-gray-600">
              {realTimeMission.progress_percentage}%
            </span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill bg-blue-600"
              style={{ width: `${realTimeMission.progress_percentage}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Started: {realTimeMission.started_at ? new Date(realTimeMission.started_at).toLocaleTimeString() : 'N/A'}</span>
            <span>ETA: {missionStats.estimatedDuration - (realTimeMission.progress_percentage * missionStats.estimatedDuration / 100)} min remaining</span>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Reject Mission</h3>
            <p className="text-gray-600 mb-4">
              Please provide a reason for rejecting this mission plan:
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-3 mb-4 resize-none"
              rows={3}
              placeholder="Enter rejection reason..."
            />
            <div className="flex space-x-2 justify-end">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                }}
                className="btn btn-secondary text-sm"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                className="btn btn-danger text-sm"
                disabled={!rejectReason.trim() || isLoading}
              >
                {isLoading ? 'Rejecting...' : 'Reject Mission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};