import { ApiResponse, Mission, Drone, Discovery, AnalyticsData, ChatMessage, WeatherConditions, User, Notification, FileUploadResult, VideoStream } from './index'

// Generic API response types
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    total_pages: number
  }
}

export interface ListOptions {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  search?: string
  filters?: Record<string, any>
}

// Mission API types
export interface MissionListResponse extends PaginatedResponse<Mission> {}
export interface MissionDetailResponse extends ApiResponse<Mission> {}
export interface MissionCreateRequest {
  name: string
  description: string
  priority: string
  center_lat: number
  center_lng: number
  search_area: any
  estimated_duration: number
  assigned_drones?: string[]
}
export interface MissionUpdateRequest extends Partial<MissionCreateRequest> {
  id: string
}
export interface MissionExecutionRequest {
  mission_id: string
  start_time?: string
  parameters?: Record<string, any>
}

// Drone API types
export interface DroneListResponse extends PaginatedResponse<Drone> {}
export interface DroneDetailResponse extends ApiResponse<Drone> {}
export interface DroneUpdateRequest {
  drone_id: string
  position_lat?: number
  position_lng?: number
  position_alt?: number
  heading?: number
  speed?: number
  status?: string
}
export interface DroneCommandRequest {
  drone_id: string
  command: string
  parameters?: Record<string, any>
}

// Discovery API types
export interface DiscoveryListResponse extends PaginatedResponse<Discovery> {}
export interface DiscoveryDetailResponse extends ApiResponse<Discovery> {}
export interface DiscoveryUpdateRequest {
  discovery_id: string
  status?: string
  investigation_notes?: string
  priority?: string
}

// Analytics API types
export interface AnalyticsResponse extends ApiResponse<AnalyticsData> {}
export interface AnalyticsTimeRangeRequest {
  start_date: string
  end_date: string
  metrics?: string[]
}

// Weather API types
export interface WeatherResponse extends ApiResponse<WeatherConditions> {}
export interface WeatherRequest {
  latitude: number
  longitude: number
}

// Chat API types
export interface ChatHistoryResponse extends PaginatedResponse<ChatMessage> {}
export interface ChatSendRequest {
  mission_id: string
  message: string
  message_type?: string
}

// Authentication API types
export interface LoginRequest {
  username: string
  password: string
}
export interface LoginResponse extends ApiResponse<{
  user: User
  tokens: {
    access_token: string
    refresh_token: string
    expires_in: number
  }
}> {}

export interface RefreshTokenRequest {
  refresh_token: string
}
export interface RefreshTokenResponse extends ApiResponse<{
  access_token: string
  expires_in: number
}> {}

export interface LogoutRequest {
  refresh_token?: string
}

// File Upload API types
export interface FileUploadResponse extends ApiResponse<FileUploadResult> {}
export interface FileUploadRequest {
  file: File
  mission_id?: string
  category?: string
  description?: string
}

// Video Stream API types
export interface VideoStreamListResponse extends PaginatedResponse<VideoStream> {}
export interface VideoStreamDetailResponse extends ApiResponse<VideoStream> {}
export interface VideoStreamCreateRequest {
  drone_id: string
  resolution?: string
  fps?: number
  bitrate?: number
}

// Notification API types
export interface NotificationListResponse extends PaginatedResponse<Notification> {}
export interface NotificationDetailResponse extends ApiResponse<Notification> {}
export interface NotificationMarkReadRequest {
  notification_ids: string[]
}
export interface NotificationActionRequest {
  notification_id: string
  action: string
}

// WebSocket event types
export interface WebSocketEvent<T = any> {
  type: string
  payload: T
  timestamp: string
  mission_id?: string
  drone_id?: string
}

// Real-time update types
export interface DronePositionUpdate {
  drone_id: string
  position: {
    lat: number
    lng: number
    alt: number
  }
  heading: number
  speed: number
  battery_level: number
  timestamp: string
}

export interface MissionStatusUpdate {
  mission_id: string
  status: string
  progress?: number
  estimated_completion?: string
  active_drones?: string[]
  timestamp: string
}

export interface DiscoveryUpdate {
  discovery_id: string
  status: string
  position?: {
    lat: number
    lng: number
  }
  investigation_notes?: string
  timestamp: string
}

// Emergency types
export interface EmergencyAlert {
  id: string
  type: 'communication_loss' | 'critical_battery' | 'weather_emergency' | 'system_failure' | 'obstacle_detected'
  severity: 'low' | 'medium' | 'high' | 'critical'
  drone_id?: string
  mission_id?: string
  description: string
  location?: {
    lat: number
    lng: number
  }
  timestamp: string
  resolved: boolean
  response_required: boolean
}

// System status types
export interface SystemStatus {
  status: 'operational' | 'degraded' | 'offline' | 'maintenance'
  uptime: number
  version: string
  active_components: string[]
  performance_metrics: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_latency: number
  }
  last_updated: string
}

// Coordination command types
export interface CoordinationCommand {
  drone_id: string
  command_type: string
  parameters: Record<string, any>
  priority: 'critical' | 'high' | 'medium' | 'low'
  reason: string
  timestamp: string
}

// Error types
export interface ApiError {
  message: string
  status: number
  code?: string
  details?: Record<string, any>
  timestamp: string
}

export interface ValidationError {
  field: string
  message: string
  code: string
}

export interface ApiErrors {
  message: string
  errors?: ValidationError[]
  status: number
}