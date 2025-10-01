// Mission Types
export interface Mission {
  id: number;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted';
  search_area: GeoJSONPolygon | null;
  launch_point: Coordinate | null;
  search_altitude: number | null;
  search_speed: 'fast' | 'thorough';
  search_target: string | null;
  recording_mode: 'continuous' | 'event_triggered';
  assigned_drone_count: number;
  estimated_duration: number | null;
  actual_duration: number | null;
  coverage_percentage: number;
  ai_confidence: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

// Drone Types
export interface Drone {
  id: number;
  name: string;
  model?: string;
  serial_number?: string;
  status: 'offline' | 'online' | 'flying' | 'charging' | 'maintenance';
  connection_status: 'disconnected' | 'connected' | 'unstable';
  current_position: Coordinate | null;
  home_position: Coordinate | null;
  battery_level: number;
  signal_strength: number;
  max_flight_time: number;
  coverage_rate: number;
  missions_completed: number;
  last_seen: string | null;
}

// Discovery Types
export interface Discovery {
  id: number;
  mission_id: number;
  drone_id: number;
  object_type: string;
  confidence_score: number;
  latitude: number;
  longitude: number;
  altitude: number | null;
  investigation_status: 'pending' | 'investigating' | 'verified' | 'false_positive';
  priority_level: 1 | 2 | 3 | 4;
  human_verified: boolean;
  discovered_at: string;
  primary_image_url?: string;
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
