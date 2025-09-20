import React, { useState, useEffect } from 'react';
import { 
  Battery, 
  Signal, 
  MapPin, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Thermometer,
  Gauge,
  Plane,
  Navigation
} from 'lucide-react';
import { Drone, DroneTelemetry } from '../../types/drone';
import { webSocketService } from '../../services/websocket';

interface DroneStatusProps {
  drone: Drone;
  showDetails?: boolean;
  onStatusClick?: (drone: Drone) => void;
  className?: string;
}

export const DroneStatus: React.FC<DroneStatusProps> = ({
  drone,
  showDetails = false,
  onStatusClick,
  className = '',
}) => {
  const [realTimeDrone, setRealTimeDrone] = useState<Drone>(drone);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Subscribe to real-time telemetry updates
  useEffect(() => {
    const handleTelemetryUpdate = (telemetry: DroneTelemetry) => {
      if (telemetry.timestamp && realTimeDrone.id === telemetry.timestamp.split('-')[0]) {
        setRealTimeDrone(prev => ({
          ...prev,
          position: telemetry.position,
          battery_level: telemetry.battery_level,
          signal_strength: telemetry.signal_strength,
          status: telemetry.status as any,
          telemetry,
        }));
        setLastUpdate(new Date());
      }
    };

    webSocketService.subscribe('drone_telemetry', handleTelemetryUpdate);
    webSocketService.subscribeDrone(drone.id);

    return () => {
      webSocketService.unsubscribe('drone_telemetry', handleTelemetryUpdate);
      webSocketService.unsubscribeDrone(drone.id);
    };
  }, [drone.id, realTimeDrone.id]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'idle': return 'text-blue-600 bg-blue-100';
      case 'charging': return 'text-yellow-600 bg-yellow-100';
      case 'maintenance': return 'text-orange-600 bg-orange-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'offline': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle size={16} className="text-green-600" />;
      case 'idle': return <Plane size={16} className="text-blue-600" />;
      case 'charging': return <Battery size={16} className="text-yellow-600" />;
      case 'maintenance': return <AlertTriangle size={16} className="text-orange-600" />;
      case 'error': return <XCircle size={16} className="text-red-600" />;
      case 'offline': return <XCircle size={16} className="text-gray-600" />;
      default: return <AlertTriangle size={16} className="text-gray-600" />;
    }
  };

  const getBatteryColor = (level: number) => {
    if (level > 60) return 'text-green-600 bg-green-100';
    if (level > 30) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getSignalColor = (strength: number) => {
    if (strength > 70) return 'text-green-600';
    if (strength > 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatTimeSince = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  const formatCoordinate = (value: number, isLongitude: boolean = false) => {
    const direction = isLongitude ? (value >= 0 ? 'E' : 'W') : (value >= 0 ? 'N' : 'S');
    return `${Math.abs(value).toFixed(6)}°${direction}`;
  };

  return (
    <div 
      className={`bg-white rounded-lg shadow-md border border-gray-200 transition-all duration-200 hover:shadow-lg ${
        onStatusClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={() => onStatusClick?.(realTimeDrone)}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full">
              <Plane size={20} className="text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{realTimeDrone.name}</h3>
              <p className="text-sm text-gray-600">{realTimeDrone.model}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {getStatusIcon(realTimeDrone.status)}
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(realTimeDrone.status)}`}>
              {realTimeDrone.status}
            </span>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="p-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* Battery */}
          <div className="text-center">
            <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full mb-1 ${getBatteryColor(realTimeDrone.battery_level)}`}>
              <Battery size={16} />
            </div>
            <div className="text-lg font-bold text-gray-900">{realTimeDrone.battery_level}%</div>
            <div className="text-xs text-gray-600">Battery</div>
          </div>

          {/* Signal */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 mb-1">
              <Signal size={16} className={getSignalColor(realTimeDrone.signal_strength)} />
            </div>
            <div className="text-lg font-bold text-gray-900">{realTimeDrone.signal_strength}%</div>
            <div className="text-xs text-gray-600">Signal</div>
          </div>

          {/* Altitude */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 mb-1">
              <Navigation size={16} className="text-gray-600" />
            </div>
            <div className="text-lg font-bold text-gray-900">{realTimeDrone.position.altitude}m</div>
            <div className="text-xs text-gray-600">Altitude</div>
          </div>
        </div>

        {/* Detailed Information */}
        {showDetails && (
          <div className="space-y-3 border-t border-gray-200 pt-4">
            {/* Position */}
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <MapPin size={14} className="text-gray-400" />
                <span className="text-gray-600">Position</span>
              </div>
              <div className="text-right text-gray-900 font-mono text-xs">
                <div>{formatCoordinate(realTimeDrone.position.latitude)}</div>
                <div>{formatCoordinate(realTimeDrone.position.longitude, true)}</div>
              </div>
            </div>

            {/* Telemetry Data */}
            {realTimeDrone.telemetry && (
              <>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Thermometer size={14} className="text-gray-400" />
                    <span className="text-gray-600">Temperature</span>
                  </div>
                  <span className="text-gray-900">{realTimeDrone.telemetry.temperature}°C</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Gauge size={14} className="text-gray-400" />
                    <span className="text-gray-600">Velocity</span>
                  </div>
                  <span className="text-gray-900 font-mono text-xs">
                    {Math.sqrt(
                      realTimeDrone.telemetry.velocity.x ** 2 + 
                      realTimeDrone.telemetry.velocity.y ** 2
                    ).toFixed(1)} m/s
                  </span>
                </div>

                {/* Errors */}
                {realTimeDrone.telemetry.errors && realTimeDrone.telemetry.errors.length > 0 && (
                  <div className="text-sm">
                    <div className="flex items-center space-x-2 mb-1">
                      <AlertTriangle size={14} className="text-red-500" />
                      <span className="text-red-600 font-medium">Errors</span>
                    </div>
                    <div className="text-xs text-red-600 ml-5">
                      {realTimeDrone.telemetry.errors.slice(0, 2).map((error, index) => (
                        <div key={index}>{error}</div>
                      ))}
                      {realTimeDrone.telemetry.errors.length > 2 && (
                        <div>+{realTimeDrone.telemetry.errors.length - 2} more</div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Last Update */}
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <Clock size={14} className="text-gray-400" />
                <span className="text-gray-600">Last Update</span>
              </div>
              <span className="text-gray-500 text-xs">{formatTimeSince(lastUpdate)}</span>
            </div>

            {/* Capabilities */}
            <div className="text-sm">
              <div className="text-gray-600 mb-1">Capabilities</div>
              <div className="flex flex-wrap gap-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {realTimeDrone.capabilities.max_flight_time}min flight
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  {realTimeDrone.capabilities.max_range}km range
                </span>
                {realTimeDrone.capabilities.thermal_camera && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                    Thermal
                  </span>
                )}
                {realTimeDrone.capabilities.night_vision && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                    Night Vision
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Status Indicator */}
      <div className="px-4 pb-4">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">
            ID: {realTimeDrone.id.slice(0, 8)}...
          </span>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${
              realTimeDrone.status === 'active' ? 'bg-green-500 animate-pulse' :
              realTimeDrone.status === 'idle' ? 'bg-blue-500' :
              realTimeDrone.status === 'offline' ? 'bg-gray-400' :
              'bg-red-500'
            }`}></div>
            <span className="text-gray-500">
              {realTimeDrone.status === 'offline' 
                ? formatTimeSince(new Date(realTimeDrone.last_seen))
                : 'Live'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};