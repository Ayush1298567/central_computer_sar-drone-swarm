/**
 * Interactive Map Component for SAR Mission Commander.
 * Provides map display, area selection, drone tracking, and mission visualization.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  MapContainer,
  TileLayer,
  Polygon,
  Marker,
  Popup,
  useMapEvents,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';

// Import types
import {
  Mission,
  MissionProgress,
  Drone,
  Coordinate,
  GeoJsonPolygon,
} from '../../types';

// Import services
// import { websocketService, WebSocketSubscriptions } from '../../services';

// Custom marker icons
const createDroneIcon = (color: string = '#3B82F6') => {
  return L.divIcon({
    html: `
      <div style="
        width: 20px;
        height: 20px;
        background-color: ${color};
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
      ">
        <div style="
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 8px;
          height: 8px;
          background-color: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    className: 'custom-drone-marker',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

const createHomeIcon = () => {
  return L.divIcon({
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background-color: #10B981;
        border: 2px solid white;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background-color: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    className: 'custom-home-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

// Discovery icon creation function removed - not currently used

// Map drawing component
const MapDrawing: React.FC<{
  onAreaSelect: (area: GeoJsonPolygon) => void;
  selectedArea?: GeoJsonPolygon;
  isDrawing: boolean;
}> = ({ onAreaSelect, selectedArea, isDrawing }) => {
  const map = useMap();
  // const [drawnArea, setDrawnArea] = useState<GeoJsonPolygon | null>(null); // Not currently used

  useEffect(() => {
    if (!map || !isDrawing) return;

    // TODO: Re-implement drawing functionality with proper Leaflet Draw types
    // For now, drawing is disabled due to type issues
    console.log('Drawing mode enabled - functionality to be implemented');

    return () => {
      // Cleanup would go here
    };
  }, [map, isDrawing, onAreaSelect]);

  return (
    <>
      {selectedArea && (
        <Polygon
          positions={selectedArea.coordinates[0].map(coord => [coord[1], coord[0]])}
          pathOptions={{
            color: '#3B82F6',
            fillColor: '#3B82F6',
            fillOpacity: 0.3,
            weight: 2,
          }}
        />
      )}
    </>
  );
};

// Drone tracking component
const DroneTracker: React.FC<{
  drones: Drone[];
  selectedDrone?: string;
  onDroneSelect?: (drone: Drone) => void;
}> = ({ drones, selectedDrone, onDroneSelect }) => {
  const map = useMap();

  // Track drone positions
  useEffect(() => {
    const droneMarkers = new Map<string, L.Marker>();

    drones.forEach(drone => {
      if (drone.current_position) {
        const { lat, lng, alt } = drone.current_position;
        const color = selectedDrone === drone.id ? '#EF4444' : '#3B82F6';
        const icon = createDroneIcon(color);

        let marker = droneMarkers.get(drone.id);

        if (marker) {
          // Update existing marker position
          marker.setLatLng([lat, lng]);
        } else {
          // Create new marker
          marker = L.marker([lat, lng], { icon });
          marker.addTo(map);

          // Add popup with drone info
          marker.bindPopup(`
            <div>
              <h4>${drone.name}</h4>
              <p><strong>Status:</strong> ${drone.status}</p>
              <p><strong>Battery:</strong> ${drone.battery_level}%</p>
              <p><strong>Altitude:</strong> ${alt}m</p>
              <p><strong>Speed:</strong> ${drone.cruise_speed} m/s</p>
            </div>
          `);

          droneMarkers.set(drone.id, marker);
        }

        // Add click handler
        if (onDroneSelect) {
          marker.on('click', () => onDroneSelect(drone));
        }
      }
    });

    // Remove markers for drones no longer present
    droneMarkers.forEach((marker, droneId) => {
      if (!drones.find(d => d.id === droneId)) {
        map.removeLayer(marker);
        droneMarkers.delete(droneId);
      }
    });

    return () => {
      droneMarkers.forEach(marker => {
        map.removeLayer(marker);
      });
    };
  }, [drones, selectedDrone, onDroneSelect, map]);

  return null;
};

// Mission area visualization
const MissionAreas: React.FC<{
  mission: Mission;
}> = ({ mission }) => {
  if (!mission.search_area) return null;

  const positions = mission.search_area.coordinates[0].map(coord => [coord[1], coord[0]]);

  return (
    <Polygon
      positions={positions as [number, number][][]}
      pathOptions={{
        color: '#10B981',
        fillColor: '#10B981',
        fillOpacity: 0.2,
        weight: 3,
        dashArray: '10, 5',
      }}
    >
      <Popup>
        <div>
          <h4>Mission Area: {mission.name}</h4>
          <p><strong>Target:</strong> {mission.search_target}</p>
          <p><strong>Altitude:</strong> {mission.search_altitude}m</p>
          <p><strong>Status:</strong> {mission.status}</p>
        </div>
      </Popup>
    </Polygon>
  );
};

// Launch point marker
const LaunchPoint: React.FC<{
  mission: Mission;
}> = ({ mission }) => {
  if (!mission.launch_point) return null;

  const { lat, lng } = mission.launch_point;

  return (
    <Marker position={[lat, lng]} icon={createHomeIcon()}>
      <Popup>
        <div>
          <h4>Launch Point</h4>
          <p><strong>Mission:</strong> {mission.name}</p>
          <p><strong>Location:</strong> {lat.toFixed(6)}, {lng.toFixed(6)}</p>
        </div>
      </Popup>
    </Marker>
  );
};

// Main Interactive Map Component
interface InteractiveMapProps {
  mission?: Mission;
  drones?: Drone[];
  selectedDrone?: string;
  onDroneSelect?: (drone: Drone) => void;
  onAreaSelect?: (area: GeoJsonPolygon) => void;
  isDrawing?: boolean;
  center?: Coordinate;
  zoom?: number;
  height?: string;
  className?: string;
}

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  mission,
  drones = [],
  selectedDrone,
  onDroneSelect,
  onAreaSelect,
  isDrawing = false,
  center = { lat: 40.7128, lng: -74.0060 }, // Default to NYC
  zoom = 13,
  height = '400px',
  className = '',
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const [mapCenter, setMapCenter] = useState<Coordinate>(center);
  const [mapZoom, setMapZoom] = useState<number>(zoom);

  // Handle map events
  const MapEvents: React.FC = () => {
    useMapEvents({
      moveend: (e) => {
        const map = e.target;
        setMapCenter({ lat: map.getCenter().lat, lng: map.getCenter().lng });
        setMapZoom(map.getZoom());
      },
    });
    return null;
  };

  // WebSocket subscriptions for real-time updates
  useEffect(() => {
    if (!mission?.id) return;

    const unsubscribeProgress = WebSocketSubscriptions.subscribeToMissionProgress(
      mission.id,
      (progress: MissionProgress) => {
        // Update map center if needed
        if (progress.total_drones > 0) {
          // Could center on mission area centroid here
        }
      }
    );

    const unsubscribeEvents = WebSocketSubscriptions.subscribeToMissionEvents(
      mission.id,
      (event: any) => {
        // Handle mission events that affect the map
        if (event.event_type === 'area_updated' && mapRef.current) {
          // Could trigger map refresh or area redraw
        }
      }
    );

    return () => {
      unsubscribeProgress();
      unsubscribeEvents();
    };
  }, [mission?.id]);

  // Handle map creation
  const handleMapReady = useCallback((map: L.Map) => {
    mapRef.current = map;

    // Add custom controls or overlays if needed
    // This is where you could add weather overlays, no-fly zones, etc.
  }, []);

  return (
    <div className={`relative ${className}`} style={{ height }}>
      <MapContainer
        center={[mapCenter.lat, mapCenter.lng]}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        whenReady={() => handleMapReady(mapRef.current!)}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Map interaction components */}
        <MapEvents />
        <MapDrawing
          onAreaSelect={onAreaSelect || (() => {})}
          selectedArea={mission?.search_area}
          isDrawing={isDrawing}
        />

        {/* Mission visualization */}
        {mission && (
          <>
            <MissionAreas mission={mission} />
            <LaunchPoint mission={mission} />
          </>
        )}

        {/* Drone tracking */}
        <DroneTracker
          drones={drones}
          selectedDrone={selectedDrone}
          onDroneSelect={onDroneSelect}
        />

        {/* Map overlay for drawing mode */}
        {isDrawing && (
          <div className="absolute top-4 left-4 z-1000 bg-white p-2 rounded shadow">
            <p className="text-sm text-gray-600">
              Click and drag to draw search area
            </p>
          </div>
        )}

        {/* Map controls overlay */}
        <div className="absolute top-4 right-4 z-1000">
          <div className="bg-white rounded shadow p-2 space-y-1">
            <button
              className="block w-full text-left px-2 py-1 text-sm hover:bg-gray-100"
              onClick={() => mapRef.current?.setZoom(mapZoom + 1)}
            >
              Zoom In
            </button>
            <button
              className="block w-full text-left px-2 py-1 text-sm hover:bg-gray-100"
              onClick={() => mapRef.current?.setZoom(mapZoom - 1)}
            >
              Zoom Out
            </button>
            <button
              className="block w-full text-left px-2 py-1 text-sm hover:bg-gray-100"
              onClick={() => {
                if (mission?.search_area) {
                  const bounds = L.geoJSON(mission.search_area).getBounds();
                  mapRef.current?.fitBounds(bounds);
                }
              }}
            >
              Fit to Mission
            </button>
          </div>
        </div>
      </MapContainer>

      {/* Map info overlay */}
      <div className="absolute bottom-4 left-4 z-1000 bg-white p-2 rounded shadow text-xs">
        <div>Center: {mapCenter.lat.toFixed(6)}, {mapCenter.lng.toFixed(6)}</div>
        <div>Zoom: {mapZoom}</div>
        {mission && (
          <div>Mission: {mission.name} ({mission.status})</div>
        )}
        <div>Drones: {drones.length} active</div>
      </div>
    </div>
  );
};

// Map utilities
export class MapUtils {
  /**
   * Calculate the center point of a polygon
   */
  static calculatePolygonCenter(coordinates: number[][][]): Coordinate {
    if (!coordinates || coordinates.length === 0 || coordinates[0].length === 0) {
      return { lat: 0, lng: 0 };
    }

    const points = coordinates[0];
    const totalLat = points.reduce((sum, point) => sum + point[1], 0);
    const totalLng = points.reduce((sum, point) => sum + point[0], 0);

    return {
      lat: totalLat / points.length,
      lng: totalLng / points.length,
    };
  }

  /**
   * Calculate the area of a polygon in square kilometers
   */
  static calculatePolygonArea(coordinates: number[][][]): number {
    if (!coordinates || coordinates.length === 0 || coordinates[0].length < 3) {
      return 0;
    }

    const points = coordinates[0];
    let area = 0;

    for (let i = 0; i < points.length; i++) {
      const j = (i + 1) % points.length;
      area += points[i][0] * points[j][1];
      area -= points[j][0] * points[i][1];
    }

    area = Math.abs(area) / 2;

    // Convert to square kilometers (approximate)
    return area * 111 * 111; // Rough conversion for degrees to km²
  }

  /**
   * Convert GeoJSON coordinates to Leaflet positions
   */
  static geoJsonToLeafletPositions(coordinates: number[][][]): L.LatLngExpression[] {
    return coordinates[0].map(coord => [coord[1], coord[0]]);
  }

  /**
   * Convert Leaflet positions to GeoJSON coordinates
   */
  static leafletToGeoJsonPositions(positions: L.LatLngExpression[][]): number[][][] {
    return positions.map(ring =>
      ring.map(pos => {
        const [lat, lng] = Array.isArray(pos) ? pos : [pos.lat, pos.lng];
        return [lng, lat]; // GeoJSON is [lng, lat]
      })
    );
  }
}

export default InteractiveMap;