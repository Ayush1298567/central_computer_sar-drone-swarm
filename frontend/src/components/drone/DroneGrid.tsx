import React from 'react';
import { DroneStatus } from '../../types/api';

interface DroneGridProps {
  drones: DroneStatus[];
  onDroneCommand?: (droneId: string, command: string) => void;
  compactView?: boolean;
}

const DroneGrid: React.FC<DroneGridProps> = ({
  drones,
  onDroneCommand,
  compactView = false,
}) => {
  const getStatusColor = (status: DroneStatus['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'idle': return 'bg-yellow-500';
      case 'charging': return 'bg-blue-500';
      case 'maintenance': return 'bg-orange-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'text-green-400';
    if (battery > 30) return 'text-yellow-400';
    return 'text-red-400';
  };

  const handleCommand = (droneId: string, command: string) => {
    onDroneCommand?.(droneId, command);
  };

  if (drones.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        <div className="text-2xl mb-2">🚁</div>
        <p>No drones connected</p>
      </div>
    );
  }

  return (
    <div className={`grid gap-2 ${compactView ? 'grid-cols-2' : 'grid-cols-1'}`}>
      {drones.map((drone) => (
        <div
          key={drone.id}
          className="bg-gray-700 rounded p-3 hover:bg-gray-600 transition-colors"
        >
          <div className="flex justify-between items-start mb-2">
            <div>
              <div className="font-medium">{drone.name}</div>
              <div className="text-xs text-gray-400">ID: {drone.id.slice(-8)}</div>
            </div>
            <div className={`w-2 h-2 rounded-full ${getStatusColor(drone.status)}`} />
          </div>

          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span>Battery:</span>
              <span className={getBatteryColor(drone.battery)}>
                {drone.battery}%
              </span>
            </div>

            <div className="flex justify-between">
              <span>Altitude:</span>
              <span>{drone.position.altitude.toFixed(1)}m</span>
            </div>

            <div className="flex justify-between">
              <span>Status:</span>
              <span className="capitalize">{drone.status}</span>
            </div>

            {drone.mission_id && (
              <div className="flex justify-between">
                <span>Mission:</span>
                <span className="text-blue-400">{drone.mission_id.slice(-8)}</span>
              </div>
            )}
          </div>

          {!compactView && (
            <div className="flex gap-1 mt-3">
              <button
                onClick={() => handleCommand(drone.id, 'status')}
                className="flex-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs"
              >
                Status
              </button>
              <button
                onClick={() => handleCommand(drone.id, 'return_home')}
                className="flex-1 px-2 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-xs"
              >
                RTH
              </button>
              <button
                onClick={() => handleCommand(drone.id, 'land')}
                className="flex-1 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs"
              >
                Land
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default DroneGrid;