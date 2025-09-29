/**
 * Mission-related type definitions for the SAR Mission Commander frontend.
 */

export interface Mission {
  id: string;
  name: string;
  description?: string;
  status: MissionStatus;
  search_area?: GeoJsonPolygon;
  launch_point?: Coordinate;
  search_altitude?: number;
  search_speed?: SearchSpeed;
  search_target?: string;
  recording_mode?: RecordingMode;
  assigned_drone_count: number;
  estimated_duration?: number;
  actual_duration?: number;
  coverage_percentage?: number;
  ai_confidence?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface CreateMissionRequest {
  name: string;
  description?: string;
  search_area: GeoJsonPolygon;
  launch_point: Coordinate;
  search_target: string;
  search_altitude?: number;
  search_speed?: SearchSpeed;
  recording_mode?: RecordingMode;
  assigned_drones: string[];
}

export interface UpdateMissionRequest {
  name?: string;
  description?: string;
  search_area?: GeoJsonPolygon;
  launch_point?: Coordinate;
  search_target?: string;
  search_altitude?: number;
  search_speed?: SearchSpeed;
  recording_mode?: RecordingMode;
}

export interface MissionProgress {
  mission_id: string;
  overall_progress: number;
  phase: ExecutionPhase;
  start_time?: string;
  estimated_completion?: string;
  actual_completion?: string;
  total_area_km2: number;
  covered_area_km2: number;
  coverage_percentage: number;
  discoveries_found: number;
  discoveries_investigated: number;
  discoveries_verified: number;
  active_drones: number;
  total_drones: number;
  drones_returned: number;
  average_speed_ms: number;
  total_distance_km: number;
  battery_consumed: number;
  events: MissionEvent[];
}

export interface MissionEvent {
  timestamp: string;
  event_type: string;
  data: Record<string, any>;
}

export interface DroneAssignment {
  id: string;
  mission_id: string;
  drone_id: string;
  assigned_area: GeoJsonPolygon;
  navigation_waypoints: Coordinate[];
  priority_level: number;
  estimated_coverage_time: number;
  status: AssignmentStatus;
  progress_percentage: number;
  assigned_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ChatMessage {
  id: string;
  mission_id: string;
  sender: MessageSender;
  content: string;
  message_type: MessageType;
  ai_confidence?: number;
  processing_time?: number;
  attachments?: MessageAttachment[];
  conversation_context?: ConversationContext;
  created_at: string;
}

export interface MessageAttachment {
  type: 'map' | 'image' | 'video' | 'document';
  url: string;
  title?: string;
  description?: string;
}

export interface ConversationContext {
  current_phase: ConversationPhase;
  mission_parameters: Partial<CreateMissionRequest>;
  pending_questions: string[];
  user_preferences: Record<string, any>;
}

// Enums and Union Types
export type MissionStatus =
  | 'planning'
  | 'ready'
  | 'active'
  | 'paused'
  | 'completed'
  | 'aborted'
  | 'failed';

export type ExecutionPhase =
  | 'initializing'
  | 'launching'
  | 'searching'
  | 'discovery_investigation'
  | 'completing'
  | 'returning';

export type SearchSpeed = 'fast' | 'thorough' | 'custom';

export type RecordingMode = 'continuous' | 'event_triggered' | 'manual';

export type AssignmentStatus =
  | 'assigned'
  | 'navigating'
  | 'searching'
  | 'investigating'
  | 'returning'
  | 'completed'
  | 'failed';

export type MessageSender = 'user' | 'ai' | 'system';

export type MessageType =
  | 'text'
  | 'question'
  | 'confirmation'
  | 'suggestion'
  | 'warning'
  | 'error';

export type ConversationPhase =
  | 'initial_request'
  | 'area_selection'
  | 'parameter_gathering'
  | 'plan_review'
  | 'mission_approval'
  | 'execution_monitoring';

// GeoJSON Types
export interface GeoJsonPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // [[[lng, lat], [lng, lat], ...]]
}

export interface Coordinate {
  lat: number;
  lng: number;
}

// API Response Types
export interface MissionResponse {
  success: boolean;
  mission?: Mission;
  message?: string;
}

export interface MissionsResponse {
  success: boolean;
  missions?: Mission[];
  total?: number;
  message?: string;
}

export interface MissionProgressResponse {
  success: boolean;
  progress?: MissionProgress;
  message?: string;
}

// Mission Planning Types
export interface MissionPlan {
  mission: Partial<CreateMissionRequest>;
  drone_assignments: DroneAssignment[];
  estimated_duration: number;
  estimated_coverage: number;
  weather_impact?: WeatherImpact;
  risk_assessment: RiskAssessment;
}

export interface WeatherImpact {
  conditions: WeatherConditions;
  flight_restrictions: string[];
  recommended_adjustments: string[];
  safety_score: number;
}

export interface WeatherConditions {
  temperature: number;
  wind_speed: number;
  wind_direction: number;
  visibility: number;
  humidity: number;
  condition: string;
}

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: RiskFactor[];
  mitigation_strategies: string[];
}

export interface RiskFactor {
  type: 'weather' | 'terrain' | 'technical' | 'operational';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  probability: number;
}

// Mission Control Types
export interface MissionControlCommand {
  command: MissionControlCommandType;
  parameters: Record<string, any>;
  reason: string;
  priority: number;
}

export type MissionControlCommandType =
  | 'start_mission'
  | 'pause_mission'
  | 'resume_mission'
  | 'abort_mission'
  | 'emergency_stop'
  | 'adjust_parameters'
  | 'reassign_drones';

// Mission Analytics Types
export interface MissionAnalytics {
  mission_id: string;
  duration_minutes: number;
  coverage_efficiency: number;
  discovery_rate: number;
  success_metrics: SuccessMetrics;
  performance_insights: PerformanceInsight[];
  recommendations: string[];
}

export interface SuccessMetrics {
  coverage_percentage: number;
  discoveries_found: number;
  discoveries_verified: number;
  average_investigation_time: number;
  drone_utilization_rate: number;
}

export interface PerformanceInsight {
  category: 'efficiency' | 'safety' | 'effectiveness' | 'optimization';
  metric: string;
  value: number;
  benchmark: number;
  trend: 'improving' | 'stable' | 'declining';
  impact: 'positive' | 'neutral' | 'negative';
}

// Real-time update types for WebSocket
export interface DroneUpdateEvent {
  drone_id: string;
  update_type: 'telemetry' | 'status' | 'command' | 'alert';
  data: Record<string, any>;
  timestamp: string;
}

export interface DroneAlert {
  drone_id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  acknowledged: boolean;
}