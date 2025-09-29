// Core API Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// Mission Types
export interface Mission {
  id: string
  mission_id: string
  name: string
  description: string
  status: MissionStatus
  priority: MissionPriority
  center_lat: number
  center_lng: number
  search_area: SearchArea
  estimated_duration: number
  weather_conditions?: WeatherConditions
  created_at: string
  updated_at: string
  actual_start_time?: string
  actual_end_time?: string
}

export type MissionStatus =
  | 'planning'
  | 'ready'
  | 'active'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'failed'

export type MissionPriority = 'low' | 'medium' | 'high' | 'critical'

// Drone Types
export interface Drone {
  id: string
  drone_id: string
  name: string
  model: string
  status: DroneStatus
  battery_level: number
  position_lat: number | null
  position_lng: number | null
  position_alt: number | null
  heading: number
  speed: number
  last_seen: string
  capabilities: DroneCapabilities
  assigned_mission_id?: string
}

export type DroneStatus =
  | 'offline'
  | 'online'
  | 'flying'
  | 'returning'
  | 'charging'
  | 'maintenance'
  | 'emergency'

export interface DroneCapabilities {
  max_speed: number
  max_altitude: number
  max_payload: number
  battery_capacity: number
  camera_resolution: string
  sensors: string[]
  communication_range: number
}

// Discovery Types
export interface Discovery {
  id: string
  discovery_id: string
  mission_id: string
  latitude: number
  longitude: number
  discovery_type: DiscoveryType
  priority: DiscoveryPriority
  status: DiscoveryStatus
  description: string
  confidence_score: number
  detected_at: string
  investigated_by?: string
  investigation_notes?: string
}

export type DiscoveryType =
  | 'person'
  | 'vehicle'
  | 'structure'
  | 'debris'
  | 'signal'
  | 'thermal_anomaly'
  | 'other'

export type DiscoveryPriority = 'low' | 'medium' | 'high' | 'critical'

export type DiscoveryStatus =
  | 'detected'
  | 'investigating'
  | 'confirmed'
  | 'false_positive'
  | 'investigation_complete'

// Weather Types
export interface WeatherConditions {
  temperature: number
  humidity: number
  wind_speed: number
  wind_direction: number
  visibility: number
  conditions: string
  precipitation: number
  pressure: number
}

// Analytics Types
export interface AnalyticsData {
  total_missions: number
  active_missions: number
  completed_missions: number
  total_discoveries: number
  confirmed_discoveries: number
  average_mission_duration: number
  drone_utilization_rate: number
  system_uptime: number
  discoveries_by_type: Record<DiscoveryType, number>
  mission_success_rate: number
  response_time_metrics: ResponseTimeMetrics
}

export interface ResponseTimeMetrics {
  average_detection_time: number
  average_investigation_time: number
  average_mission_completion_time: number
}

// Search Area Types
export interface SearchArea {
  type: 'Polygon' | 'Circle'
  coordinates: number[][][] | [number, number, number] // GeoJSON format
  altitude?: number
  search_pattern?: SearchPattern
  priority_zones?: PriorityZone[]
}

export interface PriorityZone {
  coordinates: number[][][]
  priority: 'low' | 'medium' | 'high'
  reason: string
}

export type SearchPattern =
  | 'lawnmower'
  | 'spiral'
  | 'grid'
  | 'random'
  | 'adaptive'

// Chat Types
export interface ChatMessage {
  id: string
  mission_id: string
  user_id: string
  message: string
  message_type: ChatMessageType
  timestamp: string
  metadata?: Record<string, any>
}

export type ChatMessageType =
  | 'user_message'
  | 'system_message'
  | 'ai_response'
  | 'mission_update'
  | 'emergency_alert'

// WebSocket Types
export interface WebSocketMessage {
  type: WebSocketMessageType
  payload: any
  timestamp: string
  mission_id?: string
  drone_id?: string
}

export type WebSocketMessageType =
  | 'drone_update'
  | 'mission_update'
  | 'discovery_update'
  | 'weather_update'
  | 'emergency_alert'
  | 'coordination_command'
  | 'chat_message'
  | 'system_status'

// API Service Types
export interface ApiServiceConfig {
  baseURL: string
  timeout: number
  retries: number
  retryDelay: number
}

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: any
}

// File Upload Types
export interface FileUploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface FileUploadResult {
  id: string
  filename: string
  url: string
  size: number
  mime_type: string
  uploaded_at: string
}

// Video Stream Types
export interface VideoStream {
  id: string
  drone_id: string
  stream_url: string
  status: 'active' | 'inactive' | 'error'
  resolution: string
  fps: number
  bitrate: number
  started_at: string
}

// Authentication Types
export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  permissions: Permission[]
  last_login?: string
  created_at: string
}

export type UserRole = 'admin' | 'operator' | 'viewer' | 'guest'

export interface Permission {
  resource: string
  actions: string[]
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
  token_type: 'Bearer'
}

// Notification Types
export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  priority: NotificationPriority
  read: boolean
  created_at: string
  expires_at?: string
  actions?: NotificationAction[]
}

export type NotificationType =
  | 'mission_update'
  | 'discovery_alert'
  | 'system_alert'
  | 'weather_warning'
  | 'emergency'
  | 'maintenance_required'

export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical'

export interface NotificationAction {
  label: string
  action: string
  url?: string
}

// Map Types
export interface MapMarker {
  id: string
  position: [number, number]
  type: MapMarkerType
  title: string
  description?: string
  icon?: string
  color?: string
  data?: any
}

export type MapMarkerType =
  | 'drone'
  | 'discovery'
  | 'search_area'
  | 'waypoint'
  | 'base_station'
  | 'obstacle'
  | 'landing_zone'

// Form Types
export interface MissionFormData {
  name: string
  description: string
  priority: MissionPriority
  search_area: SearchArea
  estimated_duration: number
  assigned_drones: string[]
  weather_thresholds: WeatherThresholds
  communication_settings: CommunicationSettings
}

export interface WeatherThresholds {
  max_wind_speed: number
  min_visibility: number
  max_precipitation: number
  temperature_range: [number, number]
}

export interface CommunicationSettings {
  primary_frequency: number
  backup_frequency: number
  encryption_enabled: boolean
  heartbeat_interval: number
}

// Component Props Types
export interface ComponentProps {
  className?: string
  children?: React.ReactNode
  [key: string]: any
}

// Utility Types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type Required<T, K extends keyof T> = T & Pick<T, K>
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

// Constants
export const MISSION_PRIORITIES: MissionPriority[] = ['low', 'medium', 'high', 'critical']
export const DRONE_STATUSES: DroneStatus[] = ['offline', 'online', 'flying', 'returning', 'charging', 'maintenance', 'emergency']
export const DISCOVERY_TYPES: DiscoveryType[] = ['person', 'vehicle', 'structure', 'debris', 'signal', 'thermal_anomaly', 'other']
export const USER_ROLES: UserRole[] = ['admin', 'operator', 'viewer', 'guest']

// Re-export API types for convenience
export type {
  MissionListResponse,
  MissionDetailResponse,
  MissionCreateRequest,
  MissionUpdateRequest,
  MissionExecutionRequest,
  DroneListResponse,
  DroneDetailResponse,
  DroneUpdateRequest,
  DroneCommandRequest,
  DiscoveryListResponse,
  DiscoveryDetailResponse,
  DiscoveryUpdateRequest,
  AnalyticsResponse,
  WeatherResponse,
  ChatHistoryResponse,
  ChatSendRequest,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  FileUploadResponse,
  FileUploadRequest,
  VideoStreamListResponse,
  VideoStreamDetailResponse,
  VideoStreamCreateRequest,
  NotificationListResponse,
  NotificationDetailResponse,
  NotificationMarkReadRequest,
  NotificationActionRequest,
  WebSocketEvent,
  DronePositionUpdate,
  MissionStatusUpdate,
  DiscoveryUpdate,
  EmergencyAlert,
  CoordinationCommand,
  SystemStatus,
  ValidationError,
  ApiErrors,
  ListOptions,
  PaginatedResponse,
} from './api'