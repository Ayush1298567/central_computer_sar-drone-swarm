// Drone-related type definitions

import { Coordinate } from './mission';

export interface Drone {
  id: string;
  name: string;
  model?: string;
  serial_number?: string;
  status: 'offline' | 'online' | 'flying' | 'charging' | 'maintenance';
  connection_status: 'disconnected' | 'connected' | 'unstable';
  current_position?: Coordinate;
  home_position?: Coordinate;
  battery_level: number;
  battery_voltage?: number;
  charging_status: boolean;
  max_flight_time: number;
  cruise_speed: number;
  max_range: number;
  coverage_rate: number;
  signal_strength: number;
  last_heartbeat?: string;
  ip_address?: string;
  camera_specs?: Record<string, any>;
  sensor_specs?: Record<string, any>;
  flight_controller?: string;
  total_flight_hours: number;
  missions_completed: number;
  average_performance_score: number;
  last_maintenance?: string;
  next_maintenance_due?: string;
  maintenance_notes?: string;
  first_connected: string;
  last_seen: string;
}

export interface TelemetryData {
  id: string;
  drone_id: string;
  mission_id?: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading?: number;
  ground_speed?: number;
  vertical_speed?: number;
  battery_percentage?: number;
  battery_voltage?: number;
  power_consumption?: number;
  flight_mode?: string;
  armed_status?: boolean;
  gps_fix_type?: number;
  satellite_count?: number;
  temperature?: number;
  humidity?: number;
  pressure?: number;
  wind_speed?: number;
  wind_direction?: number;
  signal_strength?: number;
  data_rate?: number;
  timestamp: string;
}