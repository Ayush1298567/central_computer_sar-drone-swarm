import React, { useState, useCallback } from 'react';
import { Drone } from '../../types';
import { droneService, emergencyService } from '../../services';

interface DroneGridProps {
  drones: Drone[];
  selectedDrone?: string | null;
  onDroneSelect?: (drone: Drone) => void;
  compactView?: boolean;
  showControls?: boolean;
  className?: string;
}

const DroneGrid: React.FC<DroneGridProps> = ({
  drones,
  selectedDrone,
  onDroneSelect,
  compactView = false,
  showControls = true,
  className = ''
}) => {
  const [loadingCommands, setLoadingCommands] = useState<Set<string>>(new Set());

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flying': return 'bg-green-500';
      case 'online': return 'bg-blue-500';
      case 'idle': return 'bg-yellow-500';
      case 'charging': return 'bg-purple-500';
      case 'maintenance': return 'bg-orange-500';
      case 'error': return 'bg-red-500';
      case 'offline': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'text-green-400';
    if (battery > 30) return 'text-yellow-400';
    return 'text-red-400';
  };

  const handleDroneClick = useCallback((drone: Drone) => {
    if (onDroneSelect) {
      onDroneSelect(drone);
    }
  }, [onDroneSelect]);

  const handleCommand = useCallback(async (droneId: string, command: string) => {
    setLoadingCommands(prev => new Set(prev).add(droneId));
    
    try {
      switch (command) {
        case 'takeoff':
          await droneService.updateDroneByString(droneId, { status: 'flying' });
          break;
        case 'land':
          await droneService.updateDroneByString(droneId, { status: 'idle' });
          break;
        case 'return_home':
          await emergencyService.emergencyReturnToHome(droneId, 'Manual return to home', 'operator');
          break;
        case 'emergency_stop':
          await emergencyService.emergencyStopAll('Manual emergency stop', 'operator');
          break;
        default:
          console.log(`Command ${command} not implemented`);
      }
    } catch (error) {
      console.error(`Failed to execute ${command} on drone ${droneId}:`, error);
    } finally {
      setLoadingCommands(prev => {
        const newSet = new Set(prev);
        newSet.delete(droneId);
        return newSet;
      });
    }
  }, []);

  const getDroneIcon = (status: string) => {
    switch (status) {
      case 'flying': return '🚁';
      case 'online': return '🟢';
      case 'idle': return '⏸️';
      case 'charging': return '🔋';
      case 'maintenance': return '🔧';
      case 'error': return '❌';
      case 'offline': return '⚫';
      default: return '🚁';
    }
  };

  if (drones.length === 0) {
    return (
      <div className={`text-center text-gray-500 py-8 ${className}`}>
        <div className="text-4xl mb-2">🚁</div>
        <p className="text-lg">No drones available</p>
        <p className="text-sm">Add drones to start monitoring</p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {drones.map((drone) => {
        const isSelected = selectedDrone === drone.drone_id;
        const isLoading = loadingCommands.has(drone.drone_id);
        const isFlying = drone.status === 'flying';
        const isOnline = drone.status === 'online' || drone.status === 'flying';

        return (
          <div
            key={drone.drone_id}
            className={`
              bg-white rounded-lg border-2 p-4 transition-all duration-200 cursor-pointer
              ${isSelected 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
              }
              ${isLoading ? 'opacity-50 pointer-events-none' : ''}
            `}
            onClick={() => handleDroneClick(drone)}
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{getDroneIcon(drone.status)}</div>
                <div>
                  <h4 className="font-semibold text-gray-900">{drone.name}</h4>
                  <p className="text-sm text-gray-500">ID: {drone.drone_id.slice(-8)}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(drone.status)}`} />
                <span className="text-sm font-medium capitalize text-gray-700">
                  {drone.status}
                </span>
              </div>
            </div>

            {/* Status Grid */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500 mb-1">Battery</div>
                <div className={`text-lg font-semibold ${getBatteryColor(drone.battery_level)}`}>
                  {drone.battery_level}%
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                  <div
                    className={`h-1 rounded-full transition-all duration-300 ${
                      drone.battery_level > 60 ? 'bg-green-500' :
                      drone.battery_level > 30 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${drone.battery_level}%` }}
                  />
                </div>
              </div>

              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500 mb-1">Altitude</div>
                <div className="text-lg font-semibold text-gray-900">
                  {drone.current_position?.altitude?.toFixed(1) || '0.0'}m
                </div>
                <div className="text-xs text-gray-500">
                  Max: {drone.max_altitude}m
                </div>
              </div>

              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500 mb-1">Speed</div>
                <div className="text-lg font-semibold text-gray-900">
                  {drone.cruise_speed || 0} m/s
                </div>
                <div className="text-xs text-gray-500">
                  Max: {drone.max_speed} m/s
                </div>
              </div>

              <div className="bg-gray-50 rounded p-2">
                <div className="text-xs text-gray-500 mb-1">Flight Time</div>
                <div className="text-lg font-semibold text-gray-900">
                  {drone.max_flight_time || 0}m
                </div>
                <div className="text-xs text-gray-500">
                  Remaining
                </div>
              </div>
            </div>

            {/* Position Info */}
            {drone.current_position && (
              <div className="bg-gray-50 rounded p-2 mb-3">
                <div className="text-xs text-gray-500 mb-1">Position</div>
                <div className="text-sm text-gray-700">
                  {drone.current_position.lat.toFixed(6)}, {drone.current_position.lng.toFixed(6)}
                </div>
              </div>
            )}

            {/* Controls */}
            {showControls && !compactView && (
              <div className="flex gap-2">
                {isOnline && !isFlying && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCommand(drone.drone_id, 'takeoff');
                    }}
                    disabled={isLoading}
                    className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded text-sm font-medium"
                  >
                    {isLoading ? '...' : 'Takeoff'}
                  </button>
                )}

                {isFlying && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCommand(drone.drone_id, 'land');
                    }}
                    disabled={isLoading}
                    className="flex-1 px-3 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white rounded text-sm font-medium"
                  >
                    {isLoading ? '...' : 'Land'}
                  </button>
                )}

                {isOnline && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCommand(drone.drone_id, 'return_home');
                    }}
                    disabled={isLoading}
                    className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded text-sm font-medium"
                  >
                    {isLoading ? '...' : 'RTH'}
                  </button>
                )}

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCommand(drone.drone_id, 'emergency_stop');
                  }}
                  disabled={isLoading}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded text-sm font-medium"
                >
                  {isLoading ? '...' : 'Emergency'}
                </button>
              </div>
            )}

            {/* Selection Indicator */}
            {isSelected && (
              <div className="absolute inset-0 border-2 border-blue-500 rounded-lg pointer-events-none" />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default DroneGrid;