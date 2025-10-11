// Mission Types
export interface Mission {
  id?: number;
  mission_id?: string;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted';
  priority?: number;
  mission_type?: string;
  search_area: any;
  center_lat?: number;
  center_lng?: number;
  altitude?: number;
  radius?: number;
  search_altitude?: number;
  search_pattern?: string;
  overlap_percentage?: number;
  max_drones?: number;
  estimated_duration?: number;
  discoveries_count?: number;
  area_covered?: number;
  progress_percentage?: number;
  weather_conditions?: any;
  time_limit_minutes?: number;
  created_at?: string;
  updated_at?: string;
  start_time?: string;
  end_time?: string;
  planned_start_time?: string;
  planned_end_time?: string;
  actual_start_time?: string;
  actual_end_time?: string;
  created_by?: string;
}

// Drone Types
export interface Drone {
  id?: number;
  drone_id: string;
  name: string;
  model?: string;
  serial_number?: string;
  status: 'offline' | 'online' | 'flying' | 'charging' | 'maintenance' | 'error' | 'idle' | 'mission' | 'returning';
  connection_status: 'disconnected' | 'connected' | 'unstable';
  position_lat?: number;
  position_lng?: number;
  position_alt?: number;
  heading?: number;
  speed?: number;
  altitude?: number;
  current_position?: Coordinate;
  is_active?: boolean;
  battery_level: number;
  battery_voltage?: number;
  charging_status?: boolean;
  max_flight_time: number;
  max_altitude?: number;
  max_speed?: number;
  cruise_speed?: number;
  max_range?: number;
  coverage_rate?: number;
  capabilities?: any;
  signal_strength?: number;
  last_heartbeat?: string;
  ip_address?: string;
  flight_controller?: string;
  total_flight_hours?: number;
  missions_completed: number;
  average_performance_score?: number;
  last_maintenance?: string;
  next_maintenance_due?: string;
  maintenance_notes?: string;
  first_connected?: string;
  last_seen?: string;
}

// Discovery Types
export interface Discovery {
  id?: number;
  mission_id?: number;
  drone_id?: number;
  discovery_type: string;
  description?: string;
  confidence?: number;
  latitude: number;
  longitude: number;
  altitude?: number;
  verified?: boolean;
  false_positive?: boolean;
  priority?: number;
  image_url?: string;
  video_url?: string;
  ai_analysis?: string;
  discovered_at?: string;
  verified_at?: string;
  video_clip_url?: string;
}

// Chat Types
export interface ChatMessage {
  id: number;
  mission_id: number;
  sender: 'user' | 'ai';
  content: string;
  message_type: 'text' | 'question' | 'confirmation' | 'response';
  ai_confidence?: number;
  created_at: string;
}

// Telemetry Types
export interface TelemetryData {
  id: number;
  drone_id: number;
  mission_id?: number;
  latitude: number;
  longitude: number;
  altitude: number;
  battery_percentage: number;
  signal_strength: number;
  timestamp: string;
}

// Geographic Types
export type Coordinate = [number, number, number?]; // [lat, lng, alt?]

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

// API Response Types
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

// API Endpoints
export const API_ENDPOINTS = {
  MISSIONS: '/v1/missions',
  DRONES: '/v1/drones',
  DISCOVERIES: '/v1/discoveries',
  EMERGENCY: '/v1/emergency',
  ANALYTICS: '/v1/analytics',
  CHAT: '/v1/chat',
  WEBSOCKET: '/ws'
} as const;

// Drone Create/Update Types
export interface DroneCreate {
  drone_id: string;
  name: string;
  model?: string;
  status?: string;
  battery_level?: number;
  max_flight_time?: number;
  capabilities?: any;
}

export interface DroneUpdate {
  name?: string;
  status?: string;
  battery_level?: number;
  position_lat?: number;
  position_lng?: number;
  position_alt?: number;
  capabilities?: any;
}

// Discovery with status
export interface DiscoveryWithStatus extends Discovery {
  status: 'pending' | 'verified' | 'false_positive' | 'investigating';
  created_at: string;
}