/**
 * API response and request types for the SAR Mission Commander frontend.
 */

// Base API response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Mission types
export interface Mission {
  id: number;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  center_lat: number;
  center_lng: number;
  area_size_km2: number;
  search_altitude: number;
  priority: 'low' | 'normal' | 'high' | 'critical';
  weather_conditions?: any;
  estimated_duration?: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  user_approved: boolean;
  ai_plan?: any;
}

export interface CreateMissionRequest {
  name: string;
  description?: string;
  center_lat: number;
  center_lng: number;
  area_size_km2: number;
  search_altitude?: number;
  priority?: 'low' | 'normal' | 'high' | 'critical';
  weather_conditions?: any;
}

// Drone types
export interface Drone {
  id: number;
  name: string;
  model: string;
  serial_number?: string;
  status: 'available' | 'assigned' | 'active' | 'maintenance' | 'offline';
  is_connected: boolean;
  current_lat?: number;
  current_lng?: number;
  altitude: number;
  heading: number;
  battery_level: number;
  speed: number;
  max_speed: number;
  max_altitude: number;
  max_flight_time: number;
  camera_resolution: string;
  has_thermal: boolean;
  has_night_vision: boolean;
  weight?: number;
  dimensions?: any;
  current_mission_id?: number;
  last_maintenance?: string;
  flight_hours: number;
  notes?: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface DroneTelemetry {
  drone_id: number;
  name: string;
  position: {
    lat?: number;
    lng?: number;
    altitude: number;
  };
  attitude: {
    heading: number;
    speed: number;
  };
  battery: {
    level: number;
    remaining: number;
  };
  status: string;
  is_connected: boolean;
  last_seen: string;
  flight_hours: number;
}

// Discovery types
export interface Discovery {
  id: number;
  mission_id: number;
  drone_id?: number;
  lat: number;
  lng: number;
  altitude: number;
  discovery_type: string;
  confidence: number;
  description?: string;
  category: string;
  subcategory?: string;
  status: 'new' | 'investigating' | 'confirmed' | 'false_positive' | 'resolved';
  priority: 'low' | 'normal' | 'high' | 'critical';
  urgency: 'low' | 'medium' | 'high' | 'immediate';
  image_path?: string;
  video_path?: string;
  audio_path?: string;
  media_metadata?: any;
  investigation_notes?: string;
  response_required: boolean;
  response_type?: string;
  response_status: 'pending' | 'dispatched' | 'on_scene' | 'resolved';
  weather_conditions?: any;
  lighting_conditions?: string;
  visibility: 'poor' | 'fair' | 'good' | 'excellent';
  ai_analysis?: any;
  suggested_actions?: any[];
  discovered_at: string;
  investigated_at?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

// Chat types
export interface ChatMessage {
  id: number;
  mission_id: number;
  sender: 'user' | 'ai' | 'system';
  message: string;
  message_type: 'text' | 'image' | 'file';
  ai_context?: any;
  suggested_actions?: any[];
  mission_updates?: any;
  timestamp: string;
  edited: boolean;
  edited_at?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  mission_id?: number;
  drone_id?: number;
  data?: any;
  timestamp: string;
}

// Real-time update types
export interface MissionUpdate {
  type: 'mission_state' | 'drone_update' | 'discovery_alert' | 'chat_message';
  mission_id: number;
  timestamp: string;
  data: any;
}

export interface DroneUpdate {
  type: 'drone_update';
  mission_id: number;
  drone_id: number;
  position: {
    lat: number;
    lng: number;
    altitude: number;
  };
  status: string;
  timestamp: string;
}

export interface DiscoveryAlert {
  type: 'discovery_alert';
  mission_id: number;
  discovery: Discovery;
  alert_level: 'normal' | 'warning' | 'critical';
  timestamp: string;
}

// Analytics types
export interface MissionAnalytics {
  mission_id: number;
  total_discoveries: number;
  discoveries_by_type: Record<string, number>;
  discoveries_by_priority: Record<string, number>;
  average_confidence: number;
  search_coverage: number;
  drone_utilization: Record<number, number>;
  timeline_data: any[];
}

// Notification types
export interface NotificationData {
  id: string;
  type: 'mission_update' | 'drone_alert' | 'discovery_alert' | 'system_alert' | 'emergency';
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  data?: any;
  timestamp: string;
  read: boolean;
}