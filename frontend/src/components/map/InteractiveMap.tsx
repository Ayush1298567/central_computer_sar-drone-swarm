import React, { useEffect, useRef, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Drone } from '../../types/drone';
import { Mission } from '../../types/mission';
import { webSocketService } from '../../services/websocket';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface InteractiveMapProps {
  drones: Drone[];
  missions: Mission[];
  selectedMission?: Mission;
  onAreaSelected?: (area: number[][][]) => void;
  onDroneClick?: (drone: Drone) => void;
  onMissionClick?: (mission: Mission) => void;
  drawingMode?: boolean;
  className?: string;
}

// Custom icons for different drone statuses
const createDroneIcon = (status: string, batteryLevel: number) => {
  const getColor = () => {
    switch (status) {
      case 'active': return '#10B981'; // green
      case 'idle': return '#3B82F6'; // blue
      case 'charging': return '#F59E0B'; // yellow
      case 'error': return '#EF4444'; // red
      default: return '#6B7280'; // gray
    }
  };

  const getBatteryColor = () => {
    if (batteryLevel > 60) return '#10B981';
    if (batteryLevel > 30) return '#F59E0B';
    return '#EF4444';
  };

  return L.divIcon({
    html: `
      <div class="relative">
        <div class="w-8 h-8 rounded-full border-2 border-white shadow-lg flex items-center justify-center" 
             style="background-color: ${getColor()}">
          <div class="w-3 h-3 bg-white rounded-full"></div>
        </div>
        <div class="absolute -bottom-1 -right-1 w-4 h-2 rounded-sm border border-white shadow-sm" 
             style="background-color: ${getBatteryColor()}">
          <div class="text-xs text-white text-center leading-none">${Math.round(batteryLevel)}</div>
        </div>
      </div>
    `,
    className: 'drone-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

// Drawing tool component
const DrawingTool: React.FC<{
  isDrawing: boolean;
  onAreaComplete: (coordinates: number[][][]) => void;
}> = ({ isDrawing, onAreaComplete }) => {
  const map = useMap();
  const [drawingPoints, setDrawingPoints] = useState<L.LatLng[]>([]);
  const [currentPolygon, setCurrentPolygon] = useState<L.Polygon | null>(null);

  useMapEvents({
    click: (e) => {
      if (!isDrawing) return;

      const newPoints = [...drawingPoints, e.latlng];
      setDrawingPoints(newPoints);

      // Remove existing polygon
      if (currentPolygon) {
        map.removeLayer(currentPolygon);
      }

      // Create new polygon if we have at least 3 points
      if (newPoints.length >= 3) {
        const polygon = L.polygon(newPoints, {
          color: '#3B82F6',
          fillColor: '#3B82F6',
          fillOpacity: 0.2,
          weight: 2,
        }).addTo(map);

        setCurrentPolygon(polygon);
      }
    },

    dblclick: () => {
      if (!isDrawing || drawingPoints.length < 3) return;

      // Complete the polygon
      const coordinates = [drawingPoints.map(point => [point.lng, point.lat])];
      onAreaComplete(coordinates);
      
      // Reset drawing state
      setDrawingPoints([]);
      if (currentPolygon) {
        map.removeLayer(currentPolygon);
        setCurrentPolygon(null);
      }
    },
  });

  // Cleanup on unmount or when drawing stops
  useEffect(() => {
    if (!isDrawing && currentPolygon) {
      map.removeLayer(currentPolygon);
      setCurrentPolygon(null);
      setDrawingPoints([]);
    }
  }, [isDrawing, currentPolygon, map]);

  return null;
};

// Mission overlay component
const MissionOverlay: React.FC<{
  mission: Mission;
  onClick: (mission: Mission) => void;
}> = ({ mission, onClick }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#10B981';
      case 'paused': return '#F59E0B';
      case 'completed': return '#6B7280';
      case 'aborted': return '#EF4444';
      default: return '#3B82F6';
    }
  };

  const coordinates = mission.search_area.coordinates[0].map(
    coord => [coord[1], coord[0]] as [number, number]
  );

  return (
    <Polygon
      positions={coordinates}
      pathOptions={{
        color: getStatusColor(mission.status),
        fillColor: getStatusColor(mission.status),
        fillOpacity: 0.2,
        weight: 2,
      }}
      eventHandlers={{
        click: () => onClick(mission),
      }}
    >
      <Popup>
        <div className="p-2">
          <h3 className="font-semibold">{mission.name}</h3>
          <p className="text-sm text-gray-600">{mission.description}</p>
          <div className="mt-2 flex items-center space-x-2">
            <span className={`status-indicator status-${mission.status}`}>
              {mission.status}
            </span>
            <span className="text-xs text-gray-500">
              {mission.progress_percentage}% complete
            </span>
          </div>
          <div className="mt-1 text-xs text-gray-500">
            Drones: {mission.assigned_drones.length}
          </div>
        </div>
      </Popup>
    </Polygon>
  );
};

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  drones,
  missions,
  onAreaSelected,
  onDroneClick,
  onMissionClick,
  drawingMode = false,
  className = '',
}) => {
  const [realTimeDrones, setRealTimeDrones] = useState<Drone[]>(drones);
  const mapRef = useRef<L.Map>(null);

  // Update drones when props change
  useEffect(() => {
    setRealTimeDrones(drones);
  }, [drones]);

  // Subscribe to real-time drone updates
  useEffect(() => {
    const handleDroneTelemetry = (data: any) => {
      setRealTimeDrones(prevDrones => 
        prevDrones.map(drone => 
          drone.id === data.drone_id 
            ? { 
                ...drone, 
                position: data.position,
                battery_level: data.battery_level,
                status: data.status,
                signal_strength: data.signal_strength,
                telemetry: data
              }
            : drone
        )
      );
    };

    webSocketService.subscribe('drone_telemetry', handleDroneTelemetry);

    // Subscribe to all drones
    drones.forEach(drone => {
      webSocketService.subscribeDrone(drone.id);
    });

    return () => {
      webSocketService.unsubscribe('drone_telemetry', handleDroneTelemetry);
      drones.forEach(drone => {
        webSocketService.unsubscribeDrone(drone.id);
      });
    };
  }, [drones]);

  const handleAreaComplete = useCallback((coordinates: number[][][]) => {
    if (onAreaSelected) {
      onAreaSelected(coordinates);
    }
  }, [onAreaSelected]);

  const handleDroneMarkerClick = useCallback((drone: Drone) => {
    if (onDroneClick) {
      onDroneClick(drone);
    }
  }, [onDroneClick]);

  const handleMissionPolygonClick = useCallback((mission: Mission) => {
    if (onMissionClick) {
      onMissionClick(mission);
    }
  }, [onMissionClick]);

  return (
    <div className={`relative ${className}`}>
      <MapContainer
        ref={mapRef}
        center={[37.7749, -122.4194]} // San Francisco default
        zoom={10}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Drawing tool */}
        <DrawingTool
          isDrawing={drawingMode}
          onAreaComplete={handleAreaComplete}
        />

        {/* Mission overlays */}
        {missions.map(mission => (
          <MissionOverlay
            key={mission.id}
            mission={mission}
            onClick={handleMissionPolygonClick}
          />
        ))}

        {/* Drone markers */}
        {realTimeDrones.map(drone => (
          <Marker
            key={drone.id}
            position={[drone.position.latitude, drone.position.longitude]}
            icon={createDroneIcon(drone.status, drone.battery_level)}
            eventHandlers={{
              click: () => handleDroneMarkerClick(drone),
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-semibold">{drone.name}</h3>
                <p className="text-sm text-gray-600">{drone.model}</p>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Status:</span>
                    <span className={`status-indicator status-${drone.status}`}>
                      {drone.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Battery:</span>
                    <span className={`font-medium ${
                      drone.battery_level > 60 ? 'text-green-600' :
                      drone.battery_level > 30 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {drone.battery_level}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Signal:</span>
                    <span className={`font-medium ${
                      drone.signal_strength > 70 ? 'text-green-600' :
                      drone.signal_strength > 40 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {drone.signal_strength}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Altitude:</span>
                    <span>{drone.position.altitude}m</span>
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Drawing mode indicator */}
      {drawingMode && (
        <div className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-md text-sm font-medium shadow-lg z-[1000]">
          Click to draw search area • Double-click to complete
        </div>
      )}

      {/* Map legend */}
      <div className="absolute bottom-4 right-4 bg-white p-3 rounded-lg shadow-lg z-[1000]">
        <h4 className="font-medium mb-2 text-sm">Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Active Drone</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Idle Drone</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Charging</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Error/Offline</span>
          </div>
        </div>
      </div>
    </div>
  );
};