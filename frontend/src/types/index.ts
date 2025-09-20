// Core types for SAR Drone System

export interface Coordinates {
  latitude: number;
  longitude: number;
  altitude?: number;
}

export interface DronePosition extends Coordinates {
  heading: number;
  speed: number;
  timestamp: Date;
}

export interface Drone {
  id: string;
  name: string;
  type: string;
  status: DroneStatus;
  position?: DronePosition;
  battery: number;
  signalStrength: number;
  isConnected: boolean;
  capabilities: DroneCapability[];
  telemetry?: DroneTelemetry;
  lastSeen: Date;
}

export enum DroneStatus {
  IDLE = 'idle',
  ACTIVE = 'active',
  RETURNING = 'returning',
  CHARGING = 'charging',
  MAINTENANCE = 'maintenance',
  OFFLINE = 'offline',
  EMERGENCY = 'emergency'
}

export interface DroneCapability {
  type: string;
  enabled: boolean;
  parameters?: Record<string, any>;
}

export interface DroneTelemetry {
  battery: number;
  signalStrength: number;
  position: DronePosition;
  sensors: {
    temperature: number;
    humidity: number;
    pressure: number;
  };
  camera: {
    isRecording: boolean;
    quality: string;
    zoom: number;
  };
  flightMetrics: {
    flightTime: number;
    distance: number;
    maxAltitude: number;
    averageSpeed: number;
  };
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  status: MissionStatus;
  type: MissionType;
  priority: MissionPriority;
  searchArea: SearchArea;
  assignedDrones: string[];
  parameters: MissionParameters;
  timeline: MissionTimeline;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
}

export enum MissionStatus {
  PLANNING = 'planning',
  PLANNED = 'planned',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  ABORTED = 'aborted'
}

export enum MissionType {
  SEARCH_AND_RESCUE = 'search_and_rescue',
  SURVEILLANCE = 'surveillance',
  MAPPING = 'mapping',
  EMERGENCY_RESPONSE = 'emergency_response'
}

export enum MissionPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface SearchArea {
  type: 'polygon' | 'circle' | 'rectangle';
  coordinates: Coordinates[];
  center?: Coordinates;
  radius?: number;
  name: string;
  description?: string;
}

export interface MissionParameters {
  searchAltitude: number;
  speed: number;
  overlapPercentage: number;
  cameraSettings: {
    resolution: string;
    frameRate: number;
    recordVideo: boolean;
  };
  weatherLimits: {
    maxWindSpeed: number;
    minVisibility: number;
    maxPrecipitation: number;
  };
  timeConstraints: {
    startTime?: Date;
    endTime?: Date;
    maxDuration: number;
  };
  notifications: {
    email: boolean;
    sms: boolean;
    webhook?: string;
  };
}

export interface MissionTimeline {
  estimatedDuration: number;
  startTime?: Date;
  endTime?: Date;
  milestones: MissionMilestone[];
}

export interface MissionMilestone {
  id: string;
  name: string;
  description: string;
  estimatedTime: Date;
  completed: boolean;
  completedTime?: Date;
}

export interface ChatSession {
  id: string;
  name: string;
  status: ChatStatus;
  messages: ChatMessage[];
  missionDraft?: Partial<Mission>;
  progress: PlanningProgress;
  createdAt: Date;
  updatedAt: Date;
}

export enum ChatStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived'
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: ChatAttachment[];
  metadata?: Record<string, any>;
}

export interface ChatAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

export interface PlanningProgress {
  stage: PlanningStage;
  completedStages: PlanningStage[];
  currentQuestions: string[];
  confidence: number;
  estimatedCompletion: number;
}

export enum PlanningStage {
  INITIAL = 'initial',
  AREA_DEFINITION = 'area_definition',
  PARAMETERS = 'parameters',
  DRONE_SELECTION = 'drone_selection',
  TIMELINE = 'timeline',
  REVIEW = 'review',
  APPROVED = 'approved'
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
  source: string;
}

export interface VideoFeedConfig {
  droneId: string;
  quality: 'low' | 'medium' | 'high';
  fps: number;
  recordingEnabled: boolean;
}

export interface MapViewport {
  center: [number, number];
  zoom: number;
  bounds?: [[number, number], [number, number]];
}

export interface DrawingTools {
  enabled: boolean;
  mode: 'polygon' | 'rectangle' | 'circle' | 'marker';
  activeDrawing?: any;
}

export interface MissionStats {
  totalArea: number;
  estimatedCoverage: number;
  estimatedDuration: number;
  droneCount: number;
  batteryUsage: number;
  riskLevel: 'low' | 'medium' | 'high';
}