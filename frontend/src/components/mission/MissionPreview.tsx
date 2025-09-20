import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  MapPinIcon,
  CameraIcon,
  Battery100Icon as BatteryIcon,
  SignalIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  PauseIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { Mission, Drone, MissionStats, MissionStatus, PlanningProgress } from '../../types';
import { useWebSocket } from '../../hooks/useWebSocket';

interface MissionPreviewProps {
  mission?: Partial<Mission>;
  drones: Drone[];
  progress?: PlanningProgress;
  onApprove?: (mission: Mission) => void;
  onReject?: (reason: string) => void;
  onModify?: (changes: Partial<Mission>) => void;
  isLive?: boolean;
  className?: string;
}

const MissionPreview: React.FC<MissionPreviewProps> = ({
  mission,
  drones = [],
  progress,
  onApprove,
  onReject,
  onModify,
  isLive = false,
  className = ''
}) => {
  const [stats, setStats] = useState<MissionStats | null>(null);
  const [selectedDrones, setSelectedDrones] = useState<string[]>([]);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectionModal, setShowRejectionModal] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const webSocket = useWebSocket();

  // Calculate mission statistics
  const calculateStats = useCallback(async () => {
    if (!mission?.searchArea || !mission?.parameters) return;

    setIsCalculating(true);
    
    try {
      // Simulate calculation - in real app, this would call API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const area = mission.searchArea;
      let totalArea = 0;
      
      // Calculate area based on type
      if (area.type === 'circle' && area.radius) {
        totalArea = Math.PI * Math.pow(area.radius / 1000, 2); // km²
      } else if (area.type === 'polygon' && area.coordinates.length > 2) {
        // Simplified polygon area calculation
        totalArea = area.coordinates.length * 0.5; // Rough estimate
      } else if (area.type === 'rectangle' && area.coordinates.length >= 4) {
        // Calculate rectangle area
        const coords = area.coordinates;
        const width = Math.abs(coords[1].longitude - coords[0].longitude) * 111; // km
        const height = Math.abs(coords[2].latitude - coords[0].latitude) * 111; // km
        totalArea = width * height;
      }

      const assignedDroneCount = mission.assignedDrones?.length || selectedDrones.length;
      const estimatedSpeed = mission.parameters.speed || 10; // m/s
      const altitude = mission.parameters.searchAltitude || 100; // m
      
      // Calculate coverage and duration
      const coveragePerDrone = totalArea / Math.max(assignedDroneCount, 1);
      const estimatedDuration = (totalArea * 1000) / (estimatedSpeed * assignedDroneCount); // seconds
      const batteryUsage = Math.min((estimatedDuration / 3600) * 20, 90); // % per hour
      
      // Determine risk level
      let riskLevel: 'low' | 'medium' | 'high' = 'low';
      if (altitude > 200 || mission.parameters.weatherLimits?.maxWindSpeed > 15) {
        riskLevel = 'high';
      } else if (altitude > 100 || totalArea > 10) {
        riskLevel = 'medium';
      }

      const calculatedStats: MissionStats = {
        totalArea,
        estimatedCoverage: Math.min(coveragePerDrone * assignedDroneCount, 100),
        estimatedDuration: estimatedDuration / 60, // minutes
        droneCount: assignedDroneCount,
        batteryUsage,
        riskLevel
      };

      setStats(calculatedStats);
    } catch (error) {
      console.error('Failed to calculate mission stats:', error);
    } finally {
      setIsCalculating(false);
    }
  }, [mission, selectedDrones]);

  // Update selected drones when mission changes
  useEffect(() => {
    if (mission?.assignedDrones) {
      setSelectedDrones(mission.assignedDrones);
    }
  }, [mission?.assignedDrones]);

  // Recalculate stats when mission or drones change
  useEffect(() => {
    if (mission) {
      calculateStats();
    }
  }, [mission, calculateStats]);

  // WebSocket updates for live missions
  useEffect(() => {
    if (!isLive || !mission?.id) return;

    webSocket.subscribeMission(mission.id);

    webSocket.subscribe('mission_updated', (data) => {
      if (data.mission_id === mission.id) {
        // Update mission data
        if (onModify) {
          onModify(data.updates);
        }
      }
    });

    return () => {
      if (mission.id) {
        webSocket.unsubscribeMission(mission.id);
      }
      webSocket.unsubscribe('mission_updated');
    };
  }, [isLive, mission?.id, webSocket, onModify]);

  // Available drones for assignment
  const availableDrones = useMemo(() => {
    return drones.filter(drone => 
      drone.status === 'idle' || 
      drone.status === 'active' ||
      selectedDrones.includes(drone.id)
    );
  }, [drones, selectedDrones]);

  // Handle drone selection
  const toggleDroneSelection = useCallback((droneId: string) => {
    setSelectedDrones(prev => {
      const newSelection = prev.includes(droneId)
        ? prev.filter(id => id !== droneId)
        : [...prev, droneId];
      
      // Update mission with new drone assignment
      if (onModify) {
        onModify({ assignedDrones: newSelection });
      }
      
      return newSelection;
    });
  }, [onModify]);

  // Handle approval
  const handleApprove = useCallback(() => {
    if (mission && onApprove) {
      const completeMission: Mission = {
        ...mission,
        assignedDrones: selectedDrones,
        status: MissionStatus.PLANNED
      } as Mission;
      onApprove(completeMission);
    }
  }, [mission, selectedDrones, onApprove]);

  // Handle rejection
  const handleReject = useCallback(() => {
    if (onReject) {
      onReject(rejectionReason || 'Mission rejected by user');
    }
    setShowRejectionModal(false);
    setRejectionReason('');
  }, [onReject, rejectionReason]);

  // Render mission parameters
  const renderParameters = useCallback(() => {
    if (!mission?.parameters) return null;

    const params = mission.parameters;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Mission Parameters</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <MapPinIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Altitude</span>
            </div>
            <span className="text-lg font-semibold text-gray-900">
              {params.searchAltitude}m
            </span>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <ClockIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Speed</span>
            </div>
            <span className="text-lg font-semibold text-gray-900">
              {params.speed} m/s
            </span>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <CameraIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Resolution</span>
            </div>
            <span className="text-lg font-semibold text-gray-900">
              {params.cameraSettings.resolution}
            </span>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-1">
              <ExclamationTriangleIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Max Wind</span>
            </div>
            <span className="text-lg font-semibold text-gray-900">
              {params.weatherLimits.maxWindSpeed} m/s
            </span>
          </div>
        </div>

        {/* Time constraints */}
        {params.timeConstraints && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <h4 className="font-medium text-blue-900 mb-2">Time Constraints</h4>
            <div className="space-y-1 text-sm text-blue-800">
              {params.timeConstraints.startTime && (
                <p>Start: {new Date(params.timeConstraints.startTime).toLocaleString()}</p>
              )}
              {params.timeConstraints.endTime && (
                <p>End: {new Date(params.timeConstraints.endTime).toLocaleString()}</p>
              )}
              <p>Max Duration: {params.timeConstraints.maxDuration} minutes</p>
            </div>
          </div>
        )}
      </div>
    );
  }, [mission?.parameters]);

  // Render statistics
  const renderStats = useCallback(() => {
    if (!stats) {
      return (
        <div className="flex items-center justify-center py-8">
          {isCalculating ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          ) : (
            <p className="text-gray-500">No statistics available</p>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Mission Statistics</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="text-sm font-medium text-green-700 mb-1">Total Area</div>
            <div className="text-2xl font-bold text-green-900">
              {stats.totalArea.toFixed(1)} km²
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm font-medium text-blue-700 mb-1">Est. Duration</div>
            <div className="text-2xl font-bold text-blue-900">
              {Math.round(stats.estimatedDuration)} min
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="text-sm font-medium text-purple-700 mb-1">Coverage</div>
            <div className="text-2xl font-bold text-purple-900">
              {stats.estimatedCoverage.toFixed(1)}%
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="text-sm font-medium text-yellow-700 mb-1">Battery Usage</div>
            <div className="text-2xl font-bold text-yellow-900">
              {stats.batteryUsage.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Risk assessment */}
        <div className={`border rounded-lg p-3 ${
          stats.riskLevel === 'low' ? 'bg-green-50 border-green-200' :
          stats.riskLevel === 'medium' ? 'bg-yellow-50 border-yellow-200' :
          'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className={`w-5 h-5 ${
              stats.riskLevel === 'low' ? 'text-green-500' :
              stats.riskLevel === 'medium' ? 'text-yellow-500' :
              'text-red-500'
            }`} />
            <span className={`font-medium ${
              stats.riskLevel === 'low' ? 'text-green-900' :
              stats.riskLevel === 'medium' ? 'text-yellow-900' :
              'text-red-900'
            }`}>
              Risk Level: {stats.riskLevel.toUpperCase()}
            </span>
          </div>
        </div>
      </div>
    );
  }, [stats, isCalculating]);

  // Render drone assignments
  const renderDroneAssignments = useCallback(() => {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Drone Assignments ({selectedDrones.length} selected)
        </h3>
        
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {availableDrones.map(drone => {
            const isSelected = selectedDrones.includes(drone.id);
            const isAvailable = drone.status === 'idle';
            
            return (
              <div
                key={drone.id}
                className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                  isSelected 
                    ? 'border-blue-500 bg-blue-50' 
                    : isAvailable 
                      ? 'border-gray-200 hover:border-gray-300' 
                      : 'border-gray-100 bg-gray-50'
                }`}
                onClick={() => isAvailable && toggleDroneSelection(drone.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      isSelected ? 'bg-blue-500' : 
                      isAvailable ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                    
                    <div>
                      <div className="font-medium text-gray-900">{drone.name}</div>
                      <div className="text-sm text-gray-500">{drone.type}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <BatteryIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">{drone.battery}%</span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <SignalIcon className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600">{drone.signalStrength}%</span>
                    </div>
                    
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      drone.status === 'idle' ? 'bg-green-100 text-green-800' :
                      drone.status === 'active' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {drone.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }, [availableDrones, selectedDrones, toggleDroneSelection]);

  // Render progress indicator
  const renderProgress = useCallback(() => {
    if (!progress) return null;

    const progressPercentage = (progress.completedStages.length / 6) * 100;

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">Planning Progress</h3>
          <span className="text-sm text-gray-600">{Math.round(progressPercentage)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        <div className="mt-2 text-sm text-gray-600">
          Current stage: <span className="font-medium">{progress.stage}</span>
          {progress.confidence > 0 && (
            <span className="ml-2">
              (Confidence: {Math.round(progress.confidence * 100)}%)
            </span>
          )}
        </div>
      </div>
    );
  }, [progress]);

  if (!mission) {
    return (
      <div className={`flex items-center justify-center h-64 bg-gray-50 rounded-lg ${className}`}>
        <div className="text-center">
          <MapPinIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">No mission to preview</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {mission.name || 'Mission Preview'}
            </h2>
            <p className="text-gray-600 mt-1">
              {mission.description || 'Mission planning in progress...'}
            </p>
          </div>
          
          {mission.status && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              mission.status === 'planning' ? 'bg-yellow-100 text-yellow-800' :
              mission.status === 'planned' ? 'bg-blue-100 text-blue-800' :
              mission.status === 'active' ? 'bg-green-100 text-green-800' :
              mission.status === 'completed' ? 'bg-green-100 text-green-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {mission.status}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {renderProgress()}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            {renderParameters()}
            {renderStats()}
          </div>
          
          <div>
            {renderDroneAssignments()}
          </div>
        </div>
      </div>

      {/* Actions */}
      {progress?.stage === 'review' && (
        <div className="p-6 border-t bg-gray-50">
          <div className="flex items-center justify-end space-x-4">
            <button
              onClick={() => setShowRejectionModal(true)}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
            >
              <XCircleIcon className="w-4 h-4 inline mr-2" />
              Reject
            </button>
            
            <button
              onClick={handleApprove}
              disabled={selectedDrones.length === 0}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="w-4 h-4 inline mr-2" />
              Approve Mission
            </button>
          </div>
        </div>
      )}

      {/* Live mission controls */}
      {isLive && mission.status === 'active' && (
        <div className="p-6 border-t bg-blue-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-blue-800">
              Mission is currently active
            </div>
            
            <div className="flex space-x-2">
              <button className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600">
                <PauseIcon className="w-4 h-4 inline mr-1" />
                Pause
              </button>
              
              <button className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600">
                <StopIcon className="w-4 h-4 inline mr-1" />
                Abort
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rejection modal */}
      {showRejectionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Reject Mission
            </h3>
            
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Please provide a reason for rejection..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
              rows={3}
            />
            
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowRejectionModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              
              <button
                onClick={handleReject}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                Reject Mission
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MissionPreview;