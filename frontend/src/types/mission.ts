// Mission Type Definitions
export interface Mission {
  id: string;
  name: string;
  description: string;
  status: MissionStatus;
  priority: MissionPriority;
  search_area: SearchArea;
  weather_conditions?: WeatherConditions;
  time_constraints?: TimeConstraints;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  assigned_drones: DroneAssignment[];
  chat_session_id?: string;
  progress?: MissionProgress;
  discoveries?: Discovery[];
}

export enum MissionStatus {
  PLANNING = 'planning',
  READY = 'ready',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  ABORTED = 'aborted',
  FAILED = 'failed'
}

export enum MissionPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface SearchArea {
  id: string;
  name: string;
  type: 'polygon' | 'circle' | 'rectangle';
  coordinates: number[][][];
  center?: [number, number];
  radius?: number;
  area_km2: number;
  terrain_type?: string;
  difficulty_level?: 'easy' | 'medium' | 'hard' | 'extreme';
  hazards?: string[];
}

export interface WeatherConditions {
  temperature_c: number;
  wind_speed_kmh: number;
  wind_direction: number;
  precipitation_mm: number;
  visibility_km: number;
  cloud_cover_percent: number;
  conditions: string;
  is_suitable_for_flight: boolean;
}

export interface TimeConstraints {
  start_time?: string;
  end_time?: string;
  max_duration_hours: number;
  daylight_only: boolean;
}

export interface DroneAssignment {
  drone_id: string;
  role: DroneRole;
  assigned_area?: SearchArea;
  status: AssignmentStatus;
  estimated_flight_time_minutes?: number;
  actual_flight_time_minutes?: number;
}

export enum DroneRole {
  SEARCH = 'search',
  RECONNAISSANCE = 'reconnaissance',
  RESCUE = 'rescue',
  SUPPORT = 'support',
  BACKUP = 'backup'
}

export enum AssignmentStatus {
  ASSIGNED = 'assigned',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface MissionProgress {
  overall_percent: number;
  area_covered_km2: number;
  area_remaining_km2: number;
  estimated_completion_time: string;
  drones_active: number;
  drones_total: number;
  discoveries_count: number;
  flight_time_total_minutes: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  message_type?: 'question' | 'response' | 'clarification' | 'confirmation';
  metadata?: {
    planning_stage?: string;
    confidence_score?: number;
    suggestions?: string[];
  };
}

export interface ChatSession {
  id: string;
  mission_id?: string;
  status: 'active' | 'completed' | 'abandoned';
  planning_stage: PlanningStage;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  context: ChatContext;
}

export enum PlanningStage {
  INITIAL = 'initial',
  AREA_DEFINITION = 'area_definition',
  REQUIREMENTS_GATHERING = 'requirements_gathering',
  DRONE_SELECTION = 'drone_selection',
  WEATHER_CHECK = 'weather_check',
  SAFETY_VALIDATION = 'safety_validation',
  FINAL_REVIEW = 'final_review',
  COMPLETED = 'completed'
}

export interface ChatContext {
  search_area?: Partial<SearchArea>;
  weather_requirements?: Partial<WeatherConditions>;
  time_constraints?: Partial<TimeConstraints>;
  drone_preferences?: {
    count?: number;
    types?: string[];
    capabilities?: string[];
  };
  mission_parameters?: Partial<Mission>;
}

export interface Discovery {
  id: string;
  mission_id: string;
  drone_id: string;
  type: DiscoveryType;
  confidence: number;
  coordinates: [number, number];
  altitude_m: number;
  timestamp: string;
  description: string;
  image_url?: string;
  verified: boolean;
  priority: DiscoveryPriority;
  metadata?: Record<string, any>;
}

export enum DiscoveryType {
  PERSON = 'person',
  VEHICLE = 'vehicle',
  STRUCTURE = 'structure',
  DEBRIS = 'debris',
  SIGNAL = 'signal',
  ANOMALY = 'anomaly',
  LANDMARK = 'landmark',
  HAZARD = 'hazard',
  WILDLIFE = 'wildlife',
  EQUIPMENT = 'equipment'
}

export enum DiscoveryPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}