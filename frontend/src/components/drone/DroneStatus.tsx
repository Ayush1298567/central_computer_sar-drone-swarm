import React, { useState, useEffect, useCallback } from 'react';
import {
  Battery100Icon as BatteryIcon,
  SignalIcon,
  MapPinIcon,
  ClockIcon,
  CameraIcon,
  CheckCircleIcon,
  PlayIcon,
  PauseIcon,
  HomeIcon
} from '@heroicons/react/24/outline';
import { Drone, DroneStatus as DroneStatusEnum, DroneTelemetry } from '../../types';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useDrones } from '../../hooks/useDrones';

interface DroneStatusProps {
  drone: Drone;
  showDetails?: boolean;
  onStatusClick?: (drone: Drone) => void;
  onCommandSend?: (droneId: string, command: any) => void;
  className?: string;
}

const DroneStatus: React.FC<DroneStatusProps> = ({
  drone,
  showDetails = false,
  onStatusClick,
  onCommandSend,
  className = ''
}) => {
  const [telemetry, setTelemetry] = useState<DroneTelemetry | null>(drone.telemetry || null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(drone.lastSeen);
  const webSocket = useWebSocket();
  const { subscribeToDrone, unsubscribeFromDrone } = useDrones();

  // Subscribe to drone updates
  useEffect(() => {
    subscribeToDrone(drone.id);

    webSocket.subscribe('drone_telemetry', (data) => {
      if (data.drone_id === drone.id) {
        setTelemetry(data.telemetry);
        setLastUpdate(new Date());
      }
    });

    webSocket.subscribe('drone_status_update', (data) => {
      if (data.drone_id === drone.id) {
        setLastUpdate(new Date());
      }
    });

    return () => {
      unsubscribeFromDrone(drone.id);
      webSocket.unsubscribe('drone_telemetry');
      webSocket.unsubscribe('drone_status_update');
    };
  }, [drone.id, webSocket, subscribeToDrone, unsubscribeFromDrone]);

  // Get status color
  const getStatusColor = useCallback((status: DroneStatusEnum) => {
    switch (status) {
      case DroneStatusEnum.ACTIVE:
        return 'text-green-600 bg-green-100';
      case DroneStatusEnum.IDLE:
        return 'text-blue-600 bg-blue-100';
      case DroneStatusEnum.RETURNING:
        return 'text-yellow-600 bg-yellow-100';
      case DroneStatusEnum.CHARGING:
        return 'text-purple-600 bg-purple-100';
      case DroneStatusEnum.MAINTENANCE:
        return 'text-orange-600 bg-orange-100';
      case DroneStatusEnum.OFFLINE:
        return 'text-gray-600 bg-gray-100';
      case DroneStatusEnum.EMERGENCY:
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  }, []);

  // Get battery color
  const getBatteryColor = useCallback((level: number) => {
    if (level > 50) return 'text-green-600';
    if (level > 20) return 'text-yellow-600';
    return 'text-red-600';
  }, []);

  // Get signal color
  const getSignalColor = useCallback((strength: number) => {
    if (strength > 70) return 'text-green-600';
    if (strength > 40) return 'text-yellow-600';
    return 'text-red-600';
  }, []);

  // Handle command sending
  const sendCommand = useCallback((command: any) => {
    if (onCommandSend) {
      onCommandSend(drone.id, command);
    }
  }, [drone.id, onCommandSend]);

  // Format time since last update
  const getTimeSinceUpdate = useCallback(() => {
    const now = new Date();
    const diff = now.getTime() - lastUpdate.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  }, [lastUpdate]);

  // Render basic status
  const renderBasicStatus = () => (
    <div 
      className={`bg-white rounded-lg border shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow ${className}`}
      onClick={() => {
        if (onStatusClick) {
          onStatusClick(drone);
        } else {
          setIsExpanded(!isExpanded);
        }
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* Status indicator */}
          <div className={`w-3 h-3 rounded-full ${
            drone.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          
          {/* Drone info */}
          <div>
            <h3 className="font-semibold text-gray-900">{drone.name}</h3>
            <p className="text-sm text-gray-500">{drone.type}</p>
          </div>
        </div>
        
        {/* Status badge */}
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(drone.status)}`}>
          {drone.status}
        </span>
      </div>
      
      {/* Quick stats */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <BatteryIcon className={`w-4 h-4 ${getBatteryColor(drone.battery)}`} />
            <span className="text-sm text-gray-600">{drone.battery}%</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <SignalIcon className={`w-4 h-4 ${getSignalColor(drone.signalStrength)}`} />
            <span className="text-sm text-gray-600">{drone.signalStrength}%</span>
          </div>
          
          {drone.position && (
            <div className="flex items-center space-x-1">
              <MapPinIcon className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">
                {drone.position.altitude || 0}m
              </span>
            </div>
          )}
        </div>
        
        <div className="text-xs text-gray-400">
          {getTimeSinceUpdate()}
        </div>
      </div>
    </div>
  );

  // Render detailed status
  const renderDetailedStatus = () => (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-4 h-4 rounded-full ${
              drone.isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{drone.name}</h3>
              <p className="text-sm text-gray-500">{drone.type} • ID: {drone.id}</p>
            </div>
          </div>
          
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(drone.status)}`}>
            {drone.status}
          </span>
        </div>
      </div>
      
      {/* Telemetry */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Battery */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <BatteryIcon className={`w-5 h-5 ${getBatteryColor(drone.battery)}`} />
              <span className="text-sm font-medium text-gray-700">Battery</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{drone.battery}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div 
                className={`h-2 rounded-full ${
                  drone.battery > 50 ? 'bg-green-500' :
                  drone.battery > 20 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${drone.battery}%` }}
              />
            </div>
          </div>

          {/* Signal Strength */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <SignalIcon className={`w-5 h-5 ${getSignalColor(drone.signalStrength)}`} />
              <span className="text-sm font-medium text-gray-700">Signal</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{drone.signalStrength}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div 
                className={`h-2 rounded-full ${
                  drone.signalStrength > 70 ? 'bg-green-500' :
                  drone.signalStrength > 40 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${drone.signalStrength}%` }}
              />
            </div>
          </div>
        </div>

        {/* Position */}
        {drone.position && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <MapPinIcon className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Position</span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Lat:</span> {drone.position.latitude.toFixed(6)}
              </div>
              <div>
                <span className="text-blue-700">Lng:</span> {drone.position.longitude.toFixed(6)}
              </div>
              <div>
                <span className="text-blue-700">Alt:</span> {drone.position.altitude || 0}m
              </div>
              <div>
                <span className="text-blue-700">Speed:</span> {drone.position.speed.toFixed(1)} m/s
              </div>
              <div>
                <span className="text-blue-700">Heading:</span> {drone.position.heading}°
              </div>
            </div>
          </div>
        )}

        {/* Advanced telemetry */}
        {telemetry && (
          <div className="space-y-4">
            {/* Sensors */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-sm font-medium text-green-900 mb-2">Sensors</div>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-green-700">Temp:</span> {telemetry.sensors.temperature}°C
                </div>
                <div>
                  <span className="text-green-700">Humidity:</span> {telemetry.sensors.humidity}%
                </div>
                <div>
                  <span className="text-green-700">Pressure:</span> {telemetry.sensors.pressure} hPa
                </div>
              </div>
            </div>

            {/* Camera */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <CameraIcon className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Camera</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-purple-700">Recording:</span> {telemetry.camera.isRecording ? 'Yes' : 'No'}
                </div>
                <div>
                  <span className="text-purple-700">Quality:</span> {telemetry.camera.quality}
                </div>
                <div>
                  <span className="text-purple-700">Zoom:</span> {telemetry.camera.zoom}x
                </div>
              </div>
            </div>

            {/* Flight metrics */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <ClockIcon className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Flight Metrics</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-yellow-700">Flight Time:</span> {Math.round(telemetry.flightMetrics.flightTime / 60)}min
                </div>
                <div>
                  <span className="text-yellow-700">Distance:</span> {(telemetry.flightMetrics.distance / 1000).toFixed(1)}km
                </div>
                <div>
                  <span className="text-yellow-700">Max Alt:</span> {telemetry.flightMetrics.maxAltitude}m
                </div>
                <div>
                  <span className="text-yellow-700">Avg Speed:</span> {telemetry.flightMetrics.averageSpeed.toFixed(1)} m/s
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Last update */}
        <div className="mt-4 text-xs text-gray-500 text-center">
          Last updated: {getTimeSinceUpdate()}
        </div>
      </div>

      {/* Controls */}
      {drone.status !== DroneStatusEnum.OFFLINE && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex justify-center space-x-2">
            {drone.status === DroneStatusEnum.IDLE && (
              <button
                onClick={() => sendCommand({ action: 'start_mission' })}
                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
              >
                <PlayIcon className="w-4 h-4 inline mr-1" />
                Start
              </button>
            )}
            
            {drone.status === DroneStatusEnum.ACTIVE && (
              <>
                <button
                  onClick={() => sendCommand({ action: 'pause' })}
                  className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm"
                >
                  <PauseIcon className="w-4 h-4 inline mr-1" />
                  Pause
                </button>
                
                <button
                  onClick={() => sendCommand({ action: 'return_home' })}
                  className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                >
                  <HomeIcon className="w-4 h-4 inline mr-1" />
                  Return
                </button>
              </>
            )}
            
            {drone.status === DroneStatusEnum.EMERGENCY && (
              <button
                onClick={() => sendCommand({ action: 'emergency_reset' })}
                className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
              >
                <CheckCircleIcon className="w-4 h-4 inline mr-1" />
                Reset
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return showDetails || isExpanded ? renderDetailedStatus() : renderBasicStatus();
};

export default DroneStatus;