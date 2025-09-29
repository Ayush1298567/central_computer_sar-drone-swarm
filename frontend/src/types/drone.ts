/**
 * Drone Types
 *
 * TypeScript definitions for drone data and status, matching backend model structure.
 */

export interface Drone {
  id?: number;
  name: string;
  model?: string;
  status: 'offline' | 'online' | 'active' | 'maintenance' | 'error';

  // Location fields matching backend naming convention
  current_lat: number;  // Current latitude
  current_lng: number;  // Current longitude
  altitude: number;  // Current altitude in meters

  // Performance fields
  battery_level: number;  // Battery percentage (0-100)
  max_speed: number;  // Maximum speed in m/s
  current_speed?: number;  // Current speed in m/s

  // Operational status
  is_connected: boolean;
  last_seen?: string;
  signal_strength?: number;  // Signal strength percentage

  // Mission assignment
  assigned_mission_id?: number;
  mission_status: 'idle' | 'assigned' | 'enroute' | 'searching' | 'returning';

  // Hardware status
  camera_status: 'operational' | 'malfunction' | 'offline';
  sensor_status: 'operational' | 'malfunction' | 'offline';

  // Metadata
  created_at?: string;
  updated_at?: string;
}

export interface CreateDroneRequest {
  name: string;
  model?: string;
  current_lat: number;
  current_lng: number;
  altitude: number;
  max_speed?: number;
}

export interface UpdateDroneRequest extends Partial<CreateDroneRequest> {
  id: number;
  status?: 'offline' | 'online' | 'active' | 'maintenance' | 'error';
  battery_level?: number;
  mission_status?: 'idle' | 'assigned' | 'enroute' | 'searching' | 'returning';
  camera_status?: 'operational' | 'malfunction' | 'offline';
  sensor_status?: 'operational' | 'malfunction' | 'offline';
}