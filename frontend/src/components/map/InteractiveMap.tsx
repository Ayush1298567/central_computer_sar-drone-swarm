import React, { useEffect, useRef } from 'react';
import { DroneStatus, Mission, Discovery } from '../../types/api';

interface InteractiveMapProps {
  drones: DroneStatus[];
  missions: Mission[];
  discoveries: Discovery[];
  onDroneSelect?: (drone: DroneStatus) => void;
  onDiscoverySelect?: (discovery: Discovery) => void;
  height?: string;
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  drones,
  missions,
  discoveries,
  onDroneSelect,
  onDiscoverySelect,
  height = '400px',
}) => {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize map (placeholder for actual map implementation)
    // In a real implementation, you would use Leaflet, Google Maps, or similar
    console.log('Map initialized with:', { drones: drones.length, missions: missions.length, discoveries: discoveries.length });
  }, [drones, missions, discoveries]);

  return (
    <div className="w-full h-full bg-gray-900 relative">
      <div
        ref={mapRef}
        className="w-full h-full bg-gray-800 rounded"
        style={{ height }}
      >
        {/* Placeholder map content */}
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <div className="text-4xl mb-2">🗺️</div>
            <p>Interactive Map</p>
            <p className="text-sm">Real-time drone tracking and mission visualization</p>
            <div className="mt-4 text-xs text-gray-600">
              Drones: {drones.length} | Missions: {missions.length} | Discoveries: {discoveries.length}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-90 p-3 rounded text-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Active Drones</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Discoveries</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Mission Areas</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveMap;