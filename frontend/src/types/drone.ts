export interface Drone {
  id: string
  drone_id: string
  name: string
  status: 'online' | 'offline' | 'flying' | 'returning' | 'charging' | 'maintenance' | 'emergency'
  battery_level: number
  position_lat: number
  position_lng: number
  position_alt: number
  heading: number
  speed: number
  mission_id?: string
  last_seen: string
  created_at: string
  updated_at: string
  // Additional properties for UI
  current_position?: Coordinate
  model?: string
  max_flight_time?: number
  max_altitude?: number
  max_speed?: number
}

export interface DroneCreate {
  drone_id: string
  name: string
  battery_level: number
  position_lat: number
  position_lng: number
  position_alt: number
}

export interface DroneUpdate {
  name?: string
  status?: string
  battery_level?: number
  position_lat?: number
  position_lng?: number
  position_alt?: number
  heading?: number
  speed?: number
}

export interface DronePosition {
  lat: number
  lng: number
  alt: number
  heading: number
  speed: number
}

export interface Coordinate {
  lat: number
  lng: number
  alt: number
}

export interface DroneTelemetry {
  timestamp: string
  position: DronePosition
  battery_level: number
  status: string
  mission_id?: string
}

export interface TelemetryData {
  timestamp: string
  position: DronePosition
  battery_level: number
  status: string
  mission_id?: string
  altitude?: number
  speed?: number
  heading?: number
}