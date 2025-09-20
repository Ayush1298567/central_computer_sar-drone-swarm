// API Request/Response Type Definitions
import { MissionStatus, MissionPriority } from './mission';
import { DroneStatus, TelemetryData } from './drone';
// import { Discovery } from './discovery';

// Base API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: ApiError[];
}

export interface ApiError {
  field?: string;
  code: string;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Mission API Types
export interface CreateMissionRequest {
  name: string;
  description: string;
  priority: MissionPriority;
  search_area: {
    name: string;
    type: 'polygon' | 'circle' | 'rectangle';
    coordinates: number[][][];
    center?: [number, number];
    radius?: number;
  };
  weather_requirements?: {
    max_wind_speed_kmh?: number;
    min_visibility_km?: number;
    no_precipitation?: boolean;
  };
  time_constraints?: {
    start_time?: string;
    end_time?: string;
    max_duration_hours: number;
    daylight_only: boolean;
  };
  drone_requirements?: {
    min_count: number;
    preferred_types?: string[];
    required_capabilities?: string[];
  };
}

export interface UpdateMissionRequest {
  name?: string;
  description?: string;
  priority?: MissionPriority;
  search_area?: Partial<CreateMissionRequest['search_area']>;
  weather_requirements?: Partial<CreateMissionRequest['weather_requirements']>;
  time_constraints?: Partial<CreateMissionRequest['time_constraints']>;
}

export interface MissionListRequest {
  page?: number;
  per_page?: number;
  status?: MissionStatus;
  priority?: MissionPriority;
  search?: string;
  sort_by?: 'created_at' | 'updated_at' | 'priority' | 'name';
  sort_order?: 'asc' | 'desc';
}

export interface MissionActionRequest {
  reason?: string;
  force?: boolean;
}

// Drone API Types
export interface RegisterDroneRequest {
  name: string;
  model: string;
  type: string;
  capabilities: {
    max_flight_time_minutes: number;
    max_range_km: number;
    max_altitude_m: number;
    max_speed_kmh: number;
    payload_capacity_kg: number;
    camera_resolution: string;
    has_thermal_camera: boolean;
    has_night_vision: boolean;
    has_zoom: boolean;
    has_gimbal: boolean;
    weather_resistance: string;
    communication_range_km: number;
    gps_accuracy_m: number;
  };
  configuration?: {
    firmware_version: string;
    autopilot_type: string;
    communication_protocol: string;
  };
}

export interface UpdateDroneRequest {
  name?: string;
  capabilities?: Partial<RegisterDroneRequest['capabilities']>;
  configuration?: Partial<RegisterDroneRequest['configuration']>;
}

export interface DroneListRequest {
  page?: number;
  per_page?: number;
  status?: DroneStatus;
  type?: string;
  available_only?: boolean;
  mission_id?: string;
  search?: string;
  sort_by?: 'name' | 'status' | 'battery_level' | 'last_seen';
  sort_order?: 'asc' | 'desc';
}

export interface SubmitTelemetryRequest {
  telemetry_data: TelemetryData;
}

export interface DroneCommandRequest {
  command_type: string;
  parameters: Record<string, any>;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  timeout_seconds?: number;
}

export interface DroneDiscoveryRequest {
  network_range?: string;
  timeout_seconds?: number;
  discovery_method?: 'broadcast' | 'scan' | 'manual';
}

export interface DroneDiscoveryResponse {
  discovered_drones: {
    ip_address: string;
    mac_address: string;
    device_name: string;
    device_type: string;
    signal_strength: number;
    capabilities?: Partial<RegisterDroneRequest['capabilities']>;
  }[];
  scan_duration_seconds: number;
  total_found: number;
}

// Chat API Types
export interface CreateChatSessionRequest {
  mission_context?: {
    mission_type: 'search_and_rescue' | 'reconnaissance' | 'surveillance';
    urgency_level: 'low' | 'medium' | 'high' | 'critical';
    initial_requirements?: string;
  };
}

export interface SendMessageRequest {
  content: string;
  message_type?: 'question' | 'response' | 'clarification' | 'confirmation';
  context?: Record<string, any>;
}

export interface ChatSessionListRequest {
  page?: number;
  per_page?: number;
  status?: 'active' | 'completed' | 'abandoned';
  mission_id?: string;
  sort_by?: 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
}

export interface GenerateMissionRequest {
  validate_requirements?: boolean;
  auto_assign_drones?: boolean;
  weather_check?: boolean;
}

export interface UpdateSessionStatusRequest {
  status: 'active' | 'completed' | 'abandoned';
  completion_reason?: string;
}

// WebSocket API Types
export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
  sender_id?: string;
  mission_id?: string;
  drone_id?: string;
}

export enum WebSocketMessageType {
  // Mission Updates
  MISSION_STATUS_UPDATE = 'mission_status_update',
  MISSION_PROGRESS_UPDATE = 'mission_progress_update',
  MISSION_CREATED = 'mission_created',
  MISSION_COMPLETED = 'mission_completed',
  
  // Drone Updates
  DRONE_STATUS_UPDATE = 'drone_status_update',
  DRONE_TELEMETRY_UPDATE = 'drone_telemetry_update',
  DRONE_CONNECTED = 'drone_connected',
  DRONE_DISCONNECTED = 'drone_disconnected',
  DRONE_HEALTH_ALERT = 'drone_health_alert',
  
  // Discovery Updates
  NEW_DISCOVERY = 'new_discovery',
  DISCOVERY_VERIFIED = 'discovery_verified',
  DISCOVERY_UPDATED = 'discovery_updated',
  
  // Chat Updates
  NEW_CHAT_MESSAGE = 'new_chat_message',
  CHAT_SESSION_UPDATED = 'chat_session_updated',
  PLANNING_PROGRESS_UPDATE = 'planning_progress_update',
  
  // System Updates
  SYSTEM_ALERT = 'system_alert',
  WEATHER_UPDATE = 'weather_update',
  EMERGENCY_ALERT = 'emergency_alert',
  
  // Client Commands
  SUBSCRIBE_MISSION = 'subscribe_mission',
  UNSUBSCRIBE_MISSION = 'unsubscribe_mission',
  SUBSCRIBE_DRONE = 'subscribe_drone',
  UNSUBSCRIBE_DRONE = 'unsubscribe_drone',
  HEARTBEAT = 'heartbeat',
  HEARTBEAT_RESPONSE = 'heartbeat_response'
}

export interface WebSocketConnectionInfo {
  client_connections: number;
  drone_connections: number;
  admin_connections: number;
  active_subscriptions: {
    missions: string[];
    drones: string[];
  };
}

export interface BroadcastMessageRequest {
  message_type: WebSocketMessageType;
  data: any;
  target_audience?: 'all' | 'clients' | 'drones' | 'admins';
  mission_id?: string;
  drone_id?: string;
}

// File Upload Types
export interface FileUploadRequest {
  file: File;
  file_type: 'mission_plan' | 'map' | 'image' | 'video' | 'document';
  mission_id?: string;
  description?: string;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_url: string;
  file_size_bytes: number;
  mime_type: string;
  uploaded_at: string;
}

// System Status Types
export interface SystemStatus {
  api_status: 'healthy' | 'degraded' | 'down';
  database_status: 'healthy' | 'degraded' | 'down';
  websocket_status: 'healthy' | 'degraded' | 'down';
  ai_service_status: 'healthy' | 'degraded' | 'down';
  active_missions: number;
  connected_drones: number;
  system_uptime_seconds: number;
  version: string;
  last_updated: string;
}

// Error Types
export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    validation_errors?: ValidationError[];
  };
  timestamp: string;
  request_id: string;
}