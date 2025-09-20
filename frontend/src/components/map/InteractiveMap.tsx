import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  Polygon, 
  Circle,
  Rectangle,
  useMap,
  useMapEvents
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet-draw';
import { 
  Coordinates, 
  Drone, 
  Mission, 
  SearchArea, 
  MapViewport, 
} from '../../types';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom drone icon
const droneIcon = new L.DivIcon({
  className: 'drone-marker',
  html: `
    <div class="drone-icon">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L13.5 8.5L20 7L18.5 13.5L22 15L15.5 16.5L17 23L10.5 21.5L9 24L7.5 17.5L1 19L2.5 12.5L-1 11L5.5 9.5L4 3L10.5 4.5L12 2Z" fill="#3B82F6"/>
      </svg>
    </div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

interface InteractiveMapProps {
  drones: Drone[];
  missions: Mission[];
  selectedMission?: Mission | null;
  onAreaSelected?: (area: SearchArea) => void;
  onDroneClick?: (drone: Drone) => void;
  onMapClick?: (coordinates: Coordinates) => void;
  drawingEnabled?: boolean;
  drawingMode?: 'polygon' | 'rectangle' | 'circle' | 'marker';
  viewport?: MapViewport;
  onViewportChange?: (viewport: MapViewport) => void;
  className?: string;
}

// Drawing tools component
function DrawingToolsComponent({ 
  enabled, 
  mode, 
  onAreaSelected 
}: { 
  enabled: boolean; 
  mode: string; 
  onAreaSelected?: (area: SearchArea) => void; 
}) {
  const map = useMap();
  const drawnItemsRef = useRef<L.FeatureGroup>(new L.FeatureGroup());

  useEffect(() => {
    if (!enabled) return;

    const drawnItems = drawnItemsRef.current;
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      position: 'topright',
      draw: {
        polygon: mode === 'polygon' ? {
          allowIntersection: false,
          drawError: {
            color: '#e1e100',
            message: '<strong>Oh snap!</strong> you can\'t draw that!'
          },
          shapeOptions: {
            color: '#3B82F6',
            fillColor: '#3B82F6',
            fillOpacity: 0.2,
            weight: 2
          }
        } : false,
        rectangle: mode === 'rectangle' ? {
          shapeOptions: {
            color: '#3B82F6',
            fillColor: '#3B82F6',
            fillOpacity: 0.2,
            weight: 2
          }
        } : false,
        circle: mode === 'circle' ? {
          shapeOptions: {
            color: '#3B82F6',
            fillColor: '#3B82F6',
            fillOpacity: 0.2,
            weight: 2
          }
        } : false,
        marker: mode === 'marker' ? {} : false,
        polyline: false,
        circlemarker: false
      },
      edit: {
        featureGroup: drawnItems,
        remove: true
      }
    });

    map.addControl(drawControl);

    // Handle draw events
    const onDrawCreated = (e: any) => {
      const { layerType, layer } = e;
      drawnItems.addLayer(layer);

      if (onAreaSelected) {
        let area: SearchArea;

        if (layerType === 'polygon') {
          const latLngs = layer.getLatLngs()[0];
          area = {
            type: 'polygon',
            coordinates: latLngs.map((latLng: any) => ({
              latitude: latLng.lat,
              longitude: latLng.lng
            })),
            name: `Polygon Area ${Date.now()}`,
            description: 'Search area drawn on map'
          };
        } else if (layerType === 'rectangle') {
          const bounds = layer.getBounds();
          area = {
            type: 'rectangle',
            coordinates: [
              { latitude: bounds.getNorth(), longitude: bounds.getWest() },
              { latitude: bounds.getNorth(), longitude: bounds.getEast() },
              { latitude: bounds.getSouth(), longitude: bounds.getEast() },
              { latitude: bounds.getSouth(), longitude: bounds.getWest() }
            ],
            name: `Rectangle Area ${Date.now()}`,
            description: 'Rectangular search area'
          };
        } else if (layerType === 'circle') {
          const center = layer.getLatLng();
          const radius = layer.getRadius();
          area = {
            type: 'circle',
            coordinates: [],
            center: { latitude: center.lat, longitude: center.lng },
            radius: radius,
            name: `Circle Area ${Date.now()}`,
            description: 'Circular search area'
          };
        } else {
          return;
        }

        onAreaSelected(area);
      }
    };

    map.on(L.Draw.Event.CREATED, onDrawCreated);

    return () => {
      map.removeControl(drawControl);
      map.removeLayer(drawnItems);
      map.off(L.Draw.Event.CREATED, onDrawCreated);
    };
  }, [map, enabled, mode, onAreaSelected]);

  return null;
}

// Map click handler component
function MapClickHandler({ 
  onMapClick 
}: { 
  onMapClick?: (coordinates: Coordinates) => void 
}) {
  useMapEvents({
    click: (e) => {
      if (onMapClick) {
        onMapClick({
          latitude: e.latlng.lat,
          longitude: e.latlng.lng
        });
      }
    }
  });

  return null;
}

// Viewport controller component
function ViewportController({ 
  viewport, 
  onViewportChange 
}: { 
  viewport?: MapViewport; 
  onViewportChange?: (viewport: MapViewport) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (viewport) {
      map.setView(viewport.center, viewport.zoom);
      if (viewport.bounds) {
        map.fitBounds(viewport.bounds);
      }
    }
  }, [map, viewport]);

  useMapEvents({
    moveend: () => {
      if (onViewportChange) {
        const center = map.getCenter();
        const zoom = map.getZoom();
        const bounds = map.getBounds();
        
        onViewportChange({
          center: [center.lat, center.lng],
          zoom,
          bounds: [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]]
        });
      }
    },
    zoomend: () => {
      if (onViewportChange) {
        const center = map.getCenter();
        const zoom = map.getZoom();
        const bounds = map.getBounds();
        
        onViewportChange({
          center: [center.lat, center.lng],
          zoom,
          bounds: [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]]
        });
      }
    }
  });

  return null;
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({
  drones = [],
  missions = [],
  selectedMission,
  onAreaSelected,
  onDroneClick,
  onMapClick,
  drawingEnabled = false,
  drawingMode = 'polygon',
  viewport,
  onViewportChange,
  className = ''
}) => {
  // const [mapReady, setMapReady] = useState(false);

  const defaultCenter: [number, number] = [40.7128, -74.0060]; // New York City
  const defaultZoom = 10;

  // const handleMapReady = useCallback(() => {
  //   setMapReady(true);
  // }, []);

  // Render search areas for missions
  const renderSearchAreas = useCallback(() => {
    const areas: React.ReactNode[] = [];

    missions.forEach((mission) => {
      const area = mission.searchArea;
      const isSelected = selectedMission?.id === mission.id;
      const color = isSelected ? '#EF4444' : '#3B82F6';
      const fillOpacity = isSelected ? 0.3 : 0.2;

      if (area.type === 'polygon' && area.coordinates.length > 0) {
        const positions: [number, number][] = area.coordinates.map(coord => [
          coord.latitude,
          coord.longitude
        ]);

        areas.push(
          <Polygon
            key={`mission-${mission.id}`}
            positions={positions}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity,
              weight: 2
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-semibold">{mission.name}</h3>
                <p className="text-sm text-gray-600">{mission.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Status: {mission.status} | Priority: {mission.priority}
                </p>
              </div>
            </Popup>
          </Polygon>
        );
      } else if (area.type === 'circle' && area.center && area.radius) {
        areas.push(
          <Circle
            key={`mission-${mission.id}`}
            center={[area.center.latitude, area.center.longitude]}
            radius={area.radius}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity,
              weight: 2
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-semibold">{mission.name}</h3>
                <p className="text-sm text-gray-600">{mission.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Status: {mission.status} | Priority: {mission.priority}
                </p>
              </div>
            </Popup>
          </Circle>
        );
      } else if (area.type === 'rectangle' && area.coordinates.length >= 4) {
        const bounds: [[number, number], [number, number]] = [
          [area.coordinates[0].latitude, area.coordinates[0].longitude],
          [area.coordinates[2].latitude, area.coordinates[2].longitude]
        ];

        areas.push(
          <Rectangle
            key={`mission-${mission.id}`}
            bounds={bounds}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity,
              weight: 2
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-semibold">{mission.name}</h3>
                <p className="text-sm text-gray-600">{mission.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Status: {mission.status} | Priority: {mission.priority}
                </p>
              </div>
            </Popup>
          </Rectangle>
        );
      }
    });

    return areas;
  }, [missions, selectedMission]);

  // Render drone markers
  const renderDrones = useCallback(() => {
    return drones
      .filter(drone => drone.position)
      .map(drone => (
        <Marker
          key={drone.id}
          position={[drone.position!.latitude, drone.position!.longitude]}
          icon={droneIcon}
          eventHandlers={{
            click: () => onDroneClick?.(drone)
          }}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-semibold">{drone.name}</h3>
              <div className="text-sm space-y-1">
                <p>Status: <span className={`font-medium ${
                  drone.status === 'active' ? 'text-green-600' :
                  drone.status === 'offline' ? 'text-red-600' :
                  drone.status === 'emergency' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>{drone.status}</span></p>
                <p>Battery: {drone.battery}%</p>
                <p>Signal: {drone.signalStrength}%</p>
                {drone.position && (
                  <>
                    <p>Altitude: {drone.position.altitude || 0}m</p>
                    <p>Speed: {drone.position.speed}m/s</p>
                    <p>Heading: {drone.position.heading}°</p>
                  </>
                )}
                <p className="text-xs text-gray-500">
                  Last seen: {drone.lastSeen.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </Popup>
        </Marker>
      ));
  }, [drones, onDroneClick]);

  return (
    <div className={`relative w-full h-full ${className}`}>
      <MapContainer
        center={viewport?.center || defaultCenter}
        zoom={viewport?.zoom || defaultZoom}
        style={{ height: '100%', width: '100%' }}
        // whenReady={handleMapReady}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Viewport controller */}
        <ViewportController 
          viewport={viewport} 
          onViewportChange={onViewportChange} 
        />
        
        {/* Map click handler */}
        <MapClickHandler onMapClick={onMapClick} />
        
        {/* Drawing tools */}
        {drawingEnabled && (
          <DrawingToolsComponent
            enabled={drawingEnabled}
            mode={drawingMode}
            onAreaSelected={onAreaSelected}
          />
        )}
        
        {/* Render mission search areas */}
        {renderSearchAreas()}
        
        {/* Render drone markers */}
        {renderDrones()}
      </MapContainer>

      {/* Connection status indicator */}
      <div className="absolute top-4 right-4 z-[1000]">
        <div className="bg-white rounded-lg shadow-lg p-2">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600">Map Ready</span>
          </div>
        </div>
      </div>

      {/* Drawing mode indicator */}
      {drawingEnabled && (
        <div className="absolute top-4 left-4 z-[1000]">
          <div className="bg-blue-500 text-white rounded-lg shadow-lg p-2">
            <span className="text-xs font-medium">
              Drawing Mode: {drawingMode}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveMap;