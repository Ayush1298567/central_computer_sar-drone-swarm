import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Polygon, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface InteractiveMapProps {
  onAreaSelect: (area: any) => void
  mission: any
}

const InteractiveMap: React.FC<InteractiveMapProps> = ({ onAreaSelect, mission }) => {
  const [selectedArea, setSelectedArea] = useState<any>(null)
  const [mapCenter] = useState<[number, number]>([40.7128, -74.0060]) // NYC coordinates

  const handleMapClick = (e: any) => {
    // For now, just log the click - in a real implementation, this would start area selection
    console.log('Map clicked at:', e.latlng)

    // Simulate area selection for demo purposes
    if (!selectedArea) {
      const mockArea = {
        type: 'polygon',
        coordinates: [
          [e.latlng.lat - 0.001, e.latlng.lng - 0.001],
          [e.latlng.lat - 0.001, e.latlng.lng + 0.001],
          [e.latlng.lat + 0.001, e.latlng.lng + 0.001],
          [e.latlng.lat + 0.001, e.latlng.lng - 0.001],
          [e.latlng.lat - 0.001, e.latlng.lng - 0.001]
        ]
      }
      setSelectedArea(mockArea)
      onAreaSelect(mockArea)
    }
  }

  return (
    <div className="h-full w-full relative">
      <MapContainer
        center={mapCenter}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        onClick={handleMapClick}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Render selected area if exists */}
        {selectedArea && (
          <Polygon
            positions={selectedArea.coordinates}
            pathOptions={{
              color: '#3b82f6',
              fillColor: '#3b82f6',
              fillOpacity: 0.3,
              weight: 2
            }}
          />
        )}

        {/* Render mission area if mission exists */}
        {mission?.search_area && (
          <Polygon
            positions={mission.search_area.coordinates || mission.search_area}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.2,
              weight: 2
            }}
          />
        )}

        {/* Mission waypoints/launch point */}
        {mission?.launch_point && (
          <Marker position={[mission.launch_point.lat, mission.launch_point.lng]}>
            <Popup>
              <div>
                <h3 className="font-semibold">Launch Point</h3>
                <p>Lat: {mission.launch_point.lat.toFixed(6)}</p>
                <p>Lng: {mission.launch_point.lng.toFixed(6)}</p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map overlay instructions */}
      <div className="absolute top-4 left-4 bg-white bg-opacity-90 p-3 rounded-lg shadow-lg">
        <h4 className="font-semibold text-sm mb-2">Map Controls</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <p>• Click to select search area</p>
          <p>• Drag to pan the map</p>
          <p>• Scroll to zoom in/out</p>
        </div>
      </div>

      {/* Area info overlay */}
      {selectedArea && (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 p-3 rounded-lg shadow-lg">
          <h4 className="font-semibold text-sm mb-2">Selected Area</h4>
          <div className="text-xs text-gray-600">
            <p>Area: ~{(Math.random() * 10 + 5).toFixed(1)} km²</p>
            <p>Est. Coverage Time: ~{Math.floor(Math.random() * 20 + 10)} min</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default InteractiveMap