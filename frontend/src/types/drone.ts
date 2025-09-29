/**
 * Drone-related type definitions for the SAR Mission Commander frontend.
 */

export interface Drone {
  id: string;
  name: string;
  model?: string;
  serial_number?: string;
  status: DroneStatus;
  connection_status: ConnectionStatus;
  current_position?: DronePosition;
  home_position?: DronePosition;
  battery_level: number;
  battery_voltage?: number;
  charging_status: boolean;
  max_flight_time: number;
  cruise_speed: number;
  max_range: number;
  coverage_rate: number;
  signal_strength: number;
  last_heartbeat?: string;
  ip_address?: string;
  camera_specs?: CameraSpecs;
  sensor_specs?: SensorSpecs;
  flight_controller?: string;
  total_flight_hours: number;
  missions_completed: number;
  average_performance_score: number;
  last_maintenance?: string;
  next_maintenance_due?: string;
  maintenance_notes?: string;
  first_connected: string;
  last_seen: string;
}

export interface CreateDroneRequest {
  name: string;
  model?: string;
  serial_number?: string;
  home_position: DronePosition;
  camera_specs?: CameraSpecs;
  sensor_specs?: SensorSpecs;
}

export interface UpdateDroneRequest {
  name?: string;
  model?: string;
  serial_number?: string;
  home_position?: DronePosition;
  camera_specs?: CameraSpecs;
  sensor_specs?: SensorSpecs;
  maintenance_notes?: string;
}

export interface DroneTelemetry {
  id: string;
  drone_id: string;
  mission_id?: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading?: number;
  ground_speed?: number;
  vertical_speed?: number;
  battery_percentage?: number;
  battery_voltage?: number;
  power_consumption?: number;
  flight_mode?: string;
  armed_status?: boolean;
  gps_fix_type?: number;
  satellite_count?: number;
  temperature?: number;
  humidity?: number;
  pressure?: number;
  wind_speed?: number;
  wind_direction?: number;
  signal_strength?: number;
  data_rate?: number;
  timestamp: string;
}

export interface DroneCommand {
  drone_id: string;
  command_type: DroneCommandType;
  parameters: Record<string, any>;
  priority: CommandPriority;
  reason: string;
  timestamp: string;
}

export interface DronePosition {
  lat: number;
  lng: number;
  alt: number;
}

export interface CameraSpecs {
  resolution: string;
  fps: number;
  sensor_size: string;
  focal_length: number;
  has_thermal?: boolean;
  has_night_vision?: boolean;
  zoom_capability?: boolean;
  max_zoom?: number;
}

export interface SensorSpecs {
  lidar_range?: number;
  obstacle_detection?: boolean;
  precision_landing?: boolean;
  rtk_gps?: boolean;
  imu_accuracy?: string;
}

// Enums and Union Types
export type DroneStatus =
  | 'offline'
  | 'online'
  | 'flying'
  | 'returning'
  | 'charging'
  | 'maintenance'
  | 'emergency';

export type ConnectionStatus =
  | 'disconnected'
  | 'connected'
  | 'unstable'
  | 'poor_signal'
  | 'excellent';

export type DroneCommandType =
  | 'takeoff'
  | 'land'
  | 'return_to_home'
  | 'emergency_return'
  | 'navigate_to'
  | 'hover'
  | 'set_altitude'
  | 'set_speed'
  | 'start_recording'
  | 'stop_recording'
  | 'capture_image'
  | 'scan_area'
  | 'investigate_discovery'
  | 'enable_obstacle_avoidance'
  | 'disable_obstacle_avoidance'
  | 'adjust_camera_settings'
  | 'calibrate_sensors'
  | 'reboot_system';

export type CommandPriority =
  | 'low'
  | 'medium'
  | 'high'
  | 'critical'
  | 'emergency';

// API Response Types
export interface DroneResponse {
  success: boolean;
  drone?: Drone;
  message?: string;
}

export interface DronesResponse {
  success: boolean;
  drones?: Drone[];
  total?: number;
  message?: string;
}

export interface DroneTelemetryResponse {
  success: boolean;
  telemetry?: DroneTelemetry[];
  message?: string;
}

export interface DroneCommandResponse {
  success: boolean;
  command_id?: string;
  estimated_execution_time?: number;
  message?: string;
}

// Drone Management Types
export interface DroneFleet {
  drones: Drone[];
  total_count: number;
  active_count: number;
  available_count: number;
  maintenance_count: number;
  fleet_health_score: number;
}

export interface DronePerformanceMetrics {
  drone_id: string;
  flight_hours: number;
  missions_completed: number;
  average_mission_duration: number;
  success_rate: number;
  battery_efficiency: number;
  coverage_efficiency: number;
  reliability_score: number;
  maintenance_intervals: MaintenanceInterval[];
}

export interface MaintenanceInterval {
  component: string;
  last_maintenance: string;
  next_due: string;
  hours_remaining: number;
  condition: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
}

// Real-time Updates
export interface DroneUpdateEvent {
  drone_id: string;
  update_type: 'telemetry' | 'status' | 'command' | 'alert';
  data: Record<string, any>;
  timestamp: string;
}

export interface DroneAlert {
  drone_id: string;
  alert_type: DroneAlertType;
  severity: AlertSeverity;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  acknowledged: boolean;
}

export type DroneAlertType =
  | 'low_battery'
  | 'communication_loss'
  | 'sensor_failure'
  | 'propulsion_issue'
  | 'navigation_error'
  | 'obstacle_detected'
  | 'weather_hazard'
  | 'emergency_landing'
  | 'return_to_home'
  | 'maintenance_due';

export type AlertSeverity =
  | 'info'
  | 'warning'
  | 'error'
  | 'critical';

// Drone Control Types
export interface FlightPlan {
  drone_id: string;
  waypoints: Waypoint[];
  search_pattern: SearchPattern;
  altitude: number;
  speed: number;
  gimbal_settings?: GimbalSettings;
}

export interface Waypoint {
  id: string;
  position: DronePosition;
  altitude: number;
  speed?: number;
  heading?: number;
  actions?: WaypointAction[];
  estimated_arrival?: string;
}

export interface WaypointAction {
  action_type: 'hover' | 'capture_image' | 'start_recording' | 'scan' | 'investigate';
  parameters: Record<string, any>;
  duration?: number;
}

export type SearchPattern =
  | 'lawnmower'
  | 'spiral'
  | 'grid'
  | 'perimeter'
  | 'random_walk'
  | 'adaptive';

export interface GimbalSettings {
  pitch: number;
  yaw: number;
  roll: number;
  mode: 'manual' | 'auto_track' | 'stabilize';
}

// Mission Assignment Types
export interface DroneMissionAssignment {
  drone_id: string;
  mission_id: string;
  assigned_area: GeoJsonPolygon;
  priority: number;
  estimated_duration: number;
  waypoints: Waypoint[];
  search_parameters: SearchParameters;
}

export interface SearchParameters {
  altitude: number;
  speed: number;
  overlap_percentage: number;
  gimbal_pitch: number;
  detection_sensitivity: number;
  recording_mode: 'continuous' | 'event_triggered';
}

export interface GeoJsonPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}