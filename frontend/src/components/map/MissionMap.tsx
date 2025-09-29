import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default markers in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface MissionMapProps {
  center?: [number, number]
  zoom?: number
  drones?: Array<{
    id: string
    position: [number, number]
    status: string
    battery: number
  }>
  searchAreas?: Array<{
    id: string
    coordinates: number[][][]
    color?: string
  }>
  discoveries?: Array<{
    id: string
    position: [number, number]
    type: string
    priority: string
  }>
  className?: string
  height?: string
}

const MissionMap: React.FC<MissionMapProps> = ({
  center = [40.7128, -74.0060], // Default to NYC
  zoom = 13,
  drones = [],
  searchAreas = [],
  discoveries = [],
  className = '',
  height = '400px'
}) => {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const markersRef = useRef<L.Marker[]>([])
  const polygonsRef = useRef<L.Polygon[]>([])

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Initialize map
    const map = L.map(mapRef.current).setView(center, zoom)
    mapInstanceRef.current = map

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map)

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // Update markers when drones or discoveries change
  useEffect(() => {
    if (!mapInstanceRef.current) return

    const map = mapInstanceRef.current

    // Clear existing markers
    markersRef.current.forEach(marker => map.removeLayer(marker))
    markersRef.current = []

    // Add drone markers
    drones.forEach(drone => {
      const icon = L.divIcon({
        className: 'custom-drone-marker',
        html: `
          <div style="
            width: 20px;
            height: 20px;
            background: ${drone.status === 'flying' ? '#10B981' : '#F59E0B'};
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            font-weight: bold;
          ">
            ${drone.battery}%
          </div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      })

      const marker = L.marker(drone.position, { icon })
        .bindPopup(`
          <div>
            <h3>Drone ${drone.id}</h3>
            <p>Status: ${drone.status}</p>
            <p>Battery: ${drone.battery}%</p>
          </div>
        `)
        .addTo(map)

      markersRef.current.push(marker)
    })

    // Add discovery markers
    discoveries.forEach(discovery => {
      const color = discovery.priority === 'high' ? '#EF4444' : '#F59E0B'
      const icon = L.divIcon({
        className: 'custom-discovery-marker',
        html: `
          <div style="
            width: 16px;
            height: 16px;
            background: ${color};
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          "></div>
        `,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      })

      const marker = L.marker(discovery.position, { icon })
        .bindPopup(`
          <div>
            <h3>Discovery</h3>
            <p>Type: ${discovery.type}</p>
            <p>Priority: ${discovery.priority}</p>
          </div>
        `)
        .addTo(map)

      markersRef.current.push(marker)
    })
  }, [drones, discoveries])

  // Update polygons when search areas change
  useEffect(() => {
    if (!mapInstanceRef.current) return

    const map = mapInstanceRef.current

    // Clear existing polygons
    polygonsRef.current.forEach(polygon => map.removeLayer(polygon))
    polygonsRef.current = []

    // Add search area polygons
    searchAreas.forEach(area => {
      const polygon = L.polygon(area.coordinates[0], {
        color: area.color || '#3B82F6',
        fillColor: area.color || '#3B82F6',
        fillOpacity: 0.1,
        weight: 2,
      })
        .bindPopup(`Search Area ${area.id}`)
        .addTo(map)

      polygonsRef.current.push(polygon)
    })
  }, [searchAreas])

  return (
    <div className={className}>
      <div
        ref={mapRef}
        style={{ height, width: '100%' }}
        className="rounded-lg border"
      />
    </div>
  )
}

export default MissionMap