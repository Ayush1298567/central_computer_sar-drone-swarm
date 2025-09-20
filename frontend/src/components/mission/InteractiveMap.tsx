import React, { useState, useCallback } from 'react';
import { MapContainer, TileLayer, Polygon, Circle, Rectangle, useMapEvents } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { Square, Circle as CircleIcon, Trash2, Save } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import { SearchArea } from '../../types/mission';

interface InteractiveMapProps {
  onAreaSelected: (area: SearchArea) => void;
  initialArea?: SearchArea;
}

type DrawingMode = 'polygon' | 'circle' | 'rectangle' | null;

const InteractiveMap: React.FC<InteractiveMapProps> = ({ onAreaSelected, initialArea }) => {
  const [drawingMode, setDrawingMode] = useState<DrawingMode>(null);
  const [currentArea, setCurrentArea] = useState<SearchArea | null>(initialArea || null);
  const [polygonPoints, setPolygonPoints] = useState<LatLng[]>([]);
  const [circleCenter, setCircleCenter] = useState<LatLng | null>(null);
  const [circleRadius, setCircleRadius] = useState<number>(1000);
  const [rectangleBounds, setRectangleBounds] = useState<[LatLng, LatLng] | null>(null);

  // Default map center (can be configurable)
  const defaultCenter: [number, number] = [40.7128, -74.0060]; // New York City
  const defaultZoom = 10;

  const MapEventHandler = () => {
    useMapEvents({
      click: (e) => {
        if (!drawingMode) return;

        // const { lat, lng } = e.latlng;
        
        if (drawingMode === 'polygon') {
          setPolygonPoints(prev => [...prev, e.latlng]);
        } else if (drawingMode === 'circle') {
          setCircleCenter(e.latlng);
        } else if (drawingMode === 'rectangle') {
          if (!rectangleBounds) {
            setRectangleBounds([e.latlng, e.latlng]);
          } else {
            setRectangleBounds([rectangleBounds[0], e.latlng]);
            finishDrawing();
          }
        }
      }
    });
    return null;
  };

  const finishDrawing = useCallback(() => {
    let area: SearchArea | null = null;

    if (drawingMode === 'polygon' && polygonPoints.length >= 3) {
      const coordinates = polygonPoints.map(point => [point.lng, point.lat]);
      area = {
        id: `area_${Date.now()}`,
        name: `Search Area ${new Date().toLocaleTimeString()}`,
        type: 'polygon',
        coordinates: [coordinates],
        area_km2: calculatePolygonArea(coordinates),
        terrain_type: 'unknown',
        difficulty_level: 'medium'
      };
    } else if (drawingMode === 'circle' && circleCenter) {
      area = {
        id: `area_${Date.now()}`,
        name: `Search Area ${new Date().toLocaleTimeString()}`,
        type: 'circle',
        coordinates: [],
        center: [circleCenter.lat, circleCenter.lng],
        radius: circleRadius,
        area_km2: Math.PI * Math.pow(circleRadius / 1000, 2),
        terrain_type: 'unknown',
        difficulty_level: 'medium'
      };
    } else if (drawingMode === 'rectangle' && rectangleBounds) {
      const [sw, ne] = rectangleBounds;
      const coordinates = [
        [sw.lng, sw.lat],
        [ne.lng, sw.lat],
        [ne.lng, ne.lat],
        [sw.lng, ne.lat],
        [sw.lng, sw.lat]
      ];
      area = {
        id: `area_${Date.now()}`,
        name: `Search Area ${new Date().toLocaleTimeString()}`,
        type: 'rectangle',
        coordinates: [coordinates],
        area_km2: calculateRectangleArea(sw, ne),
        terrain_type: 'unknown',
        difficulty_level: 'medium'
      };
    }

    if (area) {
      setCurrentArea(area);
      onAreaSelected(area);
    }

    setDrawingMode(null);
  }, [drawingMode, polygonPoints, circleCenter, circleRadius, rectangleBounds, onAreaSelected]);

  const calculatePolygonArea = (coordinates: number[][]): number => {
    // Simplified area calculation (should use proper geodesic calculation)
    return Math.abs(coordinates.reduce((acc, curr, i, arr) => {
      const next = arr[(i + 1) % arr.length];
      return acc + (curr[0] * next[1] - next[0] * curr[1]);
    }, 0)) / 2 * 111 * 111 / 1000000; // Rough conversion to km²
  };

  const calculateRectangleArea = (sw: LatLng, ne: LatLng): number => {
    const width = Math.abs(ne.lng - sw.lng) * 111; // Rough km conversion
    const height = Math.abs(ne.lat - sw.lat) * 111;
    return width * height;
  };

  const clearArea = () => {
    setCurrentArea(null);
    setPolygonPoints([]);
    setCircleCenter(null);
    setRectangleBounds(null);
    setDrawingMode(null);
  };

  const saveArea = () => {
    if (currentArea) {
      onAreaSelected(currentArea);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Map Controls */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Drawing Tools:</span>
            <button
              onClick={() => {
                setDrawingMode('polygon');
                setPolygonPoints([]);
              }}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
                drawingMode === 'polygon'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Square className="w-4 h-4" />
              <span>Polygon</span>
            </button>
            <button
              onClick={() => {
                setDrawingMode('circle');
                setCircleCenter(null);
              }}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
                drawingMode === 'circle'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <CircleIcon className="w-4 h-4" />
              <span>Circle</span>
            </button>
            <button
              onClick={() => {
                setDrawingMode('rectangle');
                setRectangleBounds(null);
              }}
              className={`flex items-center space-x-1 px-3 py-1 rounded text-sm ${
                drawingMode === 'rectangle'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Square className="w-4 h-4" />
              <span>Rectangle</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            {drawingMode === 'circle' && circleCenter && (
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-600">Radius (m):</label>
                <input
                  type="number"
                  value={circleRadius}
                  onChange={(e) => setCircleRadius(Number(e.target.value))}
                  className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                  min="100"
                  max="50000"
                  step="100"
                />
                <button
                  onClick={finishDrawing}
                  className="btn-primary text-sm"
                >
                  Confirm Circle
                </button>
              </div>
            )}
            
            {drawingMode === 'polygon' && polygonPoints.length >= 3 && (
              <button
                onClick={finishDrawing}
                className="btn-primary text-sm"
              >
                Finish Polygon
              </button>
            )}

            {currentArea && (
              <>
                <button
                  onClick={clearArea}
                  className="flex items-center space-x-1 px-3 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded text-sm"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Clear</span>
                </button>
                <button
                  onClick={saveArea}
                  className="flex items-center space-x-1 btn-primary text-sm"
                >
                  <Save className="w-4 h-4" />
                  <span>Save Area</span>
                </button>
              </>
            )}
          </div>
        </div>

        {drawingMode && (
          <div className="mt-2 text-sm text-gray-600">
            {drawingMode === 'polygon' && (
              <span>Click on the map to add points. Need at least 3 points to complete polygon. ({polygonPoints.length} points)</span>
            )}
            {drawingMode === 'circle' && (
              <span>Click on the map to set circle center, then adjust radius and confirm.</span>
            )}
            {drawingMode === 'rectangle' && (
              <span>Click two opposite corners to create a rectangle.</span>
            )}
          </div>
        )}
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          <MapEventHandler />

          {/* Render current drawing */}
          {drawingMode === 'polygon' && polygonPoints.length > 0 && (
            <Polygon
              positions={polygonPoints}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.2,
                weight: 2
              }}
            />
          )}

          {drawingMode === 'circle' && circleCenter && (
            <Circle
              center={circleCenter}
              radius={circleRadius}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.2,
                weight: 2
              }}
            />
          )}

          {drawingMode === 'rectangle' && rectangleBounds && (
            <Rectangle
              bounds={rectangleBounds as any}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.2,
                weight: 2
              }}
            />
          )}

          {/* Render saved area */}
          {currentArea && !drawingMode && (
            <>
              {currentArea.type === 'polygon' && (
                <Polygon
                  positions={currentArea.coordinates[0].map((coord: any) => [coord[1], coord[0]])}
                  pathOptions={{
                    color: '#10b981',
                    fillColor: '#10b981',
                    fillOpacity: 0.3,
                    weight: 3
                  }}
                />
              )}
              {currentArea.type === 'circle' && currentArea.center && (
                <Circle
                  center={currentArea.center}
                  radius={currentArea.radius || 1000}
                  pathOptions={{
                    color: '#10b981',
                    fillColor: '#10b981',
                    fillOpacity: 0.3,
                    weight: 3
                  }}
                />
              )}
              {currentArea.type === 'rectangle' && (
                <Rectangle
                  bounds={[
                    [(currentArea.coordinates[0][0] as any)[1], (currentArea.coordinates[0][0] as any)[0]],
                    [(currentArea.coordinates[0][2] as any)[1], (currentArea.coordinates[0][2] as any)[0]]
                  ]}
                  pathOptions={{
                    color: '#10b981',
                    fillColor: '#10b981',
                    fillOpacity: 0.3,
                    weight: 3
                  }}
                />
              )}
            </>
          )}
        </MapContainer>

        {/* Area Info Panel */}
        {currentArea && (
          <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg border border-gray-200 min-w-64">
            <h4 className="font-semibold text-gray-900 mb-2">Search Area</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium capitalize">{currentArea.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Area:</span>
                <span className="font-medium">{currentArea.area_km2.toFixed(2)} km²</span>
              </div>
              {currentArea.center && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Center:</span>
                  <span className="font-medium">
                    {currentArea.center[0].toFixed(4)}, {currentArea.center[1].toFixed(4)}
                  </span>
                </div>
              )}
              {currentArea.radius && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Radius:</span>
                  <span className="font-medium">{(currentArea.radius / 1000).toFixed(1)} km</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractiveMap;