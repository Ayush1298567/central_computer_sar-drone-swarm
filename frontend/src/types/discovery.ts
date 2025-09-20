// Discovery Type Definitions
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
  video_url?: string;
  verified: boolean;
  priority: DiscoveryPriority;
  metadata: DiscoveryMetadata;
  analysis: DiscoveryAnalysis;
  follow_up_actions?: FollowUpAction[];
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

export interface DiscoveryMetadata {
  weather_conditions?: {
    temperature_c: number;
    wind_speed_kmh: number;
    visibility_km: number;
  };
  lighting_conditions: LightingConditions;
  camera_settings: {
    zoom_level: number;
    exposure: string;
    iso: number;
    focus_distance_m?: number;
  };
  detection_method: DetectionMethod;
  ai_model_version?: string;
  human_operator_id?: string;
  tags: string[];
  notes?: string;
}

export enum LightingConditions {
  DAYLIGHT = 'daylight',
  TWILIGHT = 'twilight',
  NIGHT = 'night',
  ARTIFICIAL_LIGHT = 'artificial_light',
  INFRARED = 'infrared',
  THERMAL = 'thermal'
}

export enum DetectionMethod {
  VISUAL_AI = 'visual_ai',
  THERMAL_AI = 'thermal_ai',
  HUMAN_OPERATOR = 'human_operator',
  MOTION_DETECTION = 'motion_detection',
  SIGNAL_DETECTION = 'signal_detection',
  HYBRID = 'hybrid'
}

export interface DiscoveryAnalysis {
  object_detection: ObjectDetection;
  classification_confidence: number;
  alternative_classifications?: AlternativeClassification[];
  size_estimation?: SizeEstimation;
  movement_analysis?: MovementAnalysis;
  context_analysis: ContextAnalysis;
}

export interface ObjectDetection {
  bounding_box: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  mask?: number[][];
  keypoints?: KeyPoint[];
  features: DetectedFeature[];
}

export interface KeyPoint {
  name: string;
  x: number;
  y: number;
  confidence: number;
  visible: boolean;
}

export interface DetectedFeature {
  name: string;
  confidence: number;
  description: string;
  importance: FeatureImportance;
}

export enum FeatureImportance {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface AlternativeClassification {
  type: DiscoveryType;
  confidence: number;
  reasoning: string;
}

export interface SizeEstimation {
  length_m?: number;
  width_m?: number;
  height_m?: number;
  area_m2?: number;
  volume_m3?: number;
  estimation_method: SizeEstimationMethod;
  confidence: number;
}

export enum SizeEstimationMethod {
  REFERENCE_OBJECT = 'reference_object',
  ALTITUDE_CALCULATION = 'altitude_calculation',
  STEREO_VISION = 'stereo_vision',
  LIDAR = 'lidar',
  MANUAL_MEASUREMENT = 'manual_measurement'
}

export interface MovementAnalysis {
  is_moving: boolean;
  direction_degrees?: number;
  speed_estimate_kmh?: number;
  movement_pattern: MovementPattern;
  tracking_confidence: number;
}

export enum MovementPattern {
  STATIONARY = 'stationary',
  LINEAR = 'linear',
  CIRCULAR = 'circular',
  ERRATIC = 'erratic',
  PERIODIC = 'periodic',
  UNKNOWN = 'unknown'
}

export interface ContextAnalysis {
  terrain_type: TerrainType;
  accessibility: AccessibilityLevel;
  nearby_landmarks: NearbyLandmark[];
  environmental_hazards: EnvironmentalHazard[];
  rescue_difficulty: RescueDifficulty;
}

export enum TerrainType {
  FLAT = 'flat',
  HILLY = 'hilly',
  MOUNTAINOUS = 'mountainous',
  FOREST = 'forest',
  DESERT = 'desert',
  WATER = 'water',
  URBAN = 'urban',
  AGRICULTURAL = 'agricultural',
  INDUSTRIAL = 'industrial'
}

export enum AccessibilityLevel {
  EASILY_ACCESSIBLE = 'easily_accessible',
  MODERATELY_ACCESSIBLE = 'moderately_accessible',
  DIFFICULT_ACCESS = 'difficult_access',
  EXTREMELY_DIFFICULT = 'extremely_difficult',
  INACCESSIBLE = 'inaccessible'
}

export interface NearbyLandmark {
  name: string;
  type: LandmarkType;
  distance_m: number;
  bearing_degrees: number;
  coordinates: [number, number];
}

export enum LandmarkType {
  BUILDING = 'building',
  ROAD = 'road',
  RIVER = 'river',
  MOUNTAIN = 'mountain',
  TOWER = 'tower',
  BRIDGE = 'bridge',
  NATURAL_FEATURE = 'natural_feature'
}

export interface EnvironmentalHazard {
  type: HazardType;
  severity: HazardSeverity;
  distance_m: number;
  description: string;
}

export enum HazardType {
  UNSTABLE_TERRAIN = 'unstable_terrain',
  WATER_HAZARD = 'water_hazard',
  FIRE = 'fire',
  TOXIC_AREA = 'toxic_area',
  HIGH_VOLTAGE = 'high_voltage',
  AVALANCHE_RISK = 'avalanche_risk',
  ROCKFALL_RISK = 'rockfall_risk',
  WEATHER_HAZARD = 'weather_hazard'
}

export enum HazardSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  EXTREME = 'extreme'
}

export enum RescueDifficulty {
  EASY = 'easy',
  MODERATE = 'moderate',
  DIFFICULT = 'difficult',
  EXTREME = 'extreme',
  IMPOSSIBLE = 'impossible'
}

export interface FollowUpAction {
  id: string;
  type: ActionType;
  priority: ActionPriority;
  assigned_to?: string;
  status: ActionStatus;
  description: string;
  estimated_duration_minutes?: number;
  required_resources?: string[];
  created_at: string;
  due_at?: string;
  completed_at?: string;
  notes?: string;
}

export enum ActionType {
  INVESTIGATE_CLOSER = 'investigate_closer',
  DEPLOY_RESCUE_TEAM = 'deploy_rescue_team',
  NOTIFY_AUTHORITIES = 'notify_authorities',
  MARK_FOR_LATER = 'mark_for_later',
  REQUEST_HUMAN_VERIFICATION = 'request_human_verification',
  COORDINATE_WITH_GROUND_TEAM = 'coordinate_with_ground_team',
  DOCUMENT_EVIDENCE = 'document_evidence',
  ESTABLISH_COMMUNICATION = 'establish_communication'
}

export enum ActionPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum ActionStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  FAILED = 'failed'
}