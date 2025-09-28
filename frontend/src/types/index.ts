// Core type definitions for the SAR Mission Commander system

export interface Coordinate {
  lat: number;
  lng: number;
  alt?: number;
}

export interface Drone {
  id: string;
  name: string;
  status: 'offline' | 'online' | 'flying' | 'charging' | 'maintenance';
  connection_status: 'disconnected' | 'connected' | 'unstable';
  current_position: Coordinate;
  battery_level: number;
  signal_strength: number;
  max_flight_time: number;
  coverage_rate: number;
  missions_completed: number;
  last_seen?: string;
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted';
  search_area: Coordinate[];
  launch_point: Coordinate;
  search_target: string;
  search_altitude: number;
  search_speed: 'fast' | 'thorough';
  assigned_drone_count: number;
  estimated_duration: number;
  coverage_percentage: number;
  ai_confidence: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Discovery {
  id: string;
  mission_id: string;
  drone_id: string;
  object_type: string;
  confidence_score: number;
  latitude: number;
  longitude: number;
  altitude?: number;
  investigation_status: 'pending' | 'investigating' | 'verified' | 'false_positive';
  priority_level: 1 | 2 | 3 | 4;
  human_verified: boolean;
  discovered_at: string;
  primary_image_url?: string;
  video_clip_url?: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  data?: any;
}

export interface EmergencySituation {
  id: string;
  type: 'communication_loss' | 'battery_critical' | 'weather_threat' | 'system_failure' | 'discovery_critical';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_drones: string[];
  description: string;
  timestamp: string;
  status: 'active' | 'resolved' | 'false_alarm';
  actions_taken: string[];
  resolution_notes?: string;
}

export interface SystemSettings {
  api_url: string;
  websocket_url: string;
  max_concurrent_missions: number;
  default_search_altitude: number;
  min_battery_level: number;
  max_wind_speed: number;
  enable_audio_alerts: boolean;
  enable_notifications: boolean;
  notification_volume: number;
  auto_save_interval: number;
}

export interface DroneSettings {
  id: string;
  name: string;
  model: string;
  max_flight_time: number;
  cruise_speed: number;
  max_range: number;
  coverage_rate: number;
  camera_specs: any;
  sensor_specs: any;
  maintenance_schedule: any;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  date_format: string;
  notifications: {
    mission_updates: boolean;
    discovery_alerts: boolean;
    system_status: boolean;
    emergency_alerts: boolean;
  };
  dashboard: {
    default_view: string;
    auto_refresh: boolean;
    refresh_interval: number;
  };
}

export interface AIConfiguration {
  provider: 'ollama' | 'openai' | 'anthropic';
  model: string;
  api_key?: string;
  base_url?: string;
  timeout: number;
  temperature: number;
  max_tokens: number;
}