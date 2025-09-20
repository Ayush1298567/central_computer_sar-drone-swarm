// Drone Type Definitions
export interface Drone {
  id: string;
  name: string;
  model: string;
  type: DroneType;
  status: DroneStatus;
  capabilities: DroneCapabilities;
  current_mission_id?: string;
  location?: DroneLocation;
  battery_level: number;
  connection_status: ConnectionStatus;
  last_seen: string;
  telemetry?: TelemetryData;
  health: DroneHealth;
  configuration: DroneConfiguration;
}

export enum DroneType {
  QUADCOPTER = 'quadcopter',
  FIXED_WING = 'fixed_wing',
  HYBRID = 'hybrid',
  HELICOPTER = 'helicopter'
}

export enum DroneStatus {
  OFFLINE = 'offline',
  IDLE = 'idle',
  ACTIVE = 'active',
  RETURNING = 'returning',
  LANDING = 'landing',
  CHARGING = 'charging',
  MAINTENANCE = 'maintenance',
  ERROR = 'error',
  EMERGENCY = 'emergency'
}

export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  WEAK_SIGNAL = 'weak_signal',
  RECONNECTING = 'reconnecting'
}

export interface DroneCapabilities {
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
  weather_resistance: WeatherResistance;
  communication_range_km: number;
  gps_accuracy_m: number;
}

export enum WeatherResistance {
  NONE = 'none',
  LIGHT_RAIN = 'light_rain',
  MODERATE_RAIN = 'moderate_rain',
  HEAVY_RAIN = 'heavy_rain',
  WIND_RESISTANT = 'wind_resistant',
  ALL_WEATHER = 'all_weather'
}

export interface DroneLocation {
  latitude: number;
  longitude: number;
  altitude_m: number;
  heading: number;
  speed_kmh: number;
  timestamp: string;
}

export interface TelemetryData {
  timestamp: string;
  location: DroneLocation;
  battery: BatteryData;
  sensors: SensorData;
  flight_mode: FlightMode;
  system_status: SystemStatus;
  performance: PerformanceData;
}

export interface BatteryData {
  voltage: number;
  current: number;
  remaining_mah: number;
  percentage: number;
  temperature_c: number;
  time_remaining_minutes: number;
}

export interface SensorData {
  accelerometer: {
    x: number;
    y: number;
    z: number;
  };
  gyroscope: {
    x: number;
    y: number;
    z: number;
  };
  magnetometer: {
    x: number;
    y: number;
    z: number;
  };
  barometer: {
    pressure_hpa: number;
    altitude_m: number;
  };
  gps: {
    satellites: number;
    hdop: number;
    fix_type: GPSFixType;
  };
  camera: {
    temperature_c: number;
    recording: boolean;
    storage_remaining_gb: number;
  };
}

export enum GPSFixType {
  NO_FIX = 'no_fix',
  FIX_2D = '2d',
  FIX_3D = '3d',
  DGPS = 'dgps',
  RTK_FLOAT = 'rtk_float',
  RTK_FIXED = 'rtk_fixed'
}

export enum FlightMode {
  MANUAL = 'manual',
  STABILIZED = 'stabilized',
  ALTITUDE_HOLD = 'altitude_hold',
  POSITION_HOLD = 'position_hold',
  AUTO_MISSION = 'auto_mission',
  RETURN_TO_LAUNCH = 'return_to_launch',
  LAND = 'land',
  TAKEOFF = 'takeoff',
  FOLLOW_ME = 'follow_me',
  ORBIT = 'orbit'
}

export enum SystemStatus {
  BOOT = 'boot',
  CALIBRATING = 'calibrating',
  STANDBY = 'standby',
  ACTIVE = 'active',
  CRITICAL = 'critical',
  EMERGENCY = 'emergency',
  POWEROFF = 'poweroff',
  FLIGHT_TERMINATION = 'flight_termination'
}

export interface PerformanceData {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  storage_usage_percent: number;
  temperature_c: number;
  vibration_level: number;
  signal_strength_dbm: number;
  link_quality_percent: number;
}

export interface DroneHealth {
  overall_status: HealthStatus;
  battery_health: HealthStatus;
  motor_health: HealthStatus;
  sensor_health: HealthStatus;
  communication_health: HealthStatus;
  camera_health: HealthStatus;
  last_maintenance: string;
  flight_hours: number;
  issues: HealthIssue[];
}

export enum HealthStatus {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  FAIR = 'fair',
  POOR = 'poor',
  CRITICAL = 'critical',
  UNKNOWN = 'unknown'
}

export interface HealthIssue {
  severity: IssueSeverity;
  component: string;
  description: string;
  detected_at: string;
  resolved: boolean;
  resolution_notes?: string;
}

export enum IssueSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export interface DroneConfiguration {
  firmware_version: string;
  autopilot_type: string;
  communication_protocol: string;
  video_settings: VideoSettings;
  flight_parameters: FlightParameters;
  safety_settings: SafetySettings;
}

export interface VideoSettings {
  resolution: string;
  framerate: number;
  bitrate_kbps: number;
  codec: string;
  recording_enabled: boolean;
  streaming_enabled: boolean;
}

export interface FlightParameters {
  max_velocity_ms: number;
  max_acceleration_ms2: number;
  max_angular_velocity_rads: number;
  return_to_launch_altitude_m: number;
  failsafe_action: FailsafeAction;
}

export enum FailsafeAction {
  RETURN_TO_LAUNCH = 'return_to_launch',
  LAND = 'land',
  CONTINUE_MISSION = 'continue_mission',
  HOVER = 'hover'
}

export interface SafetySettings {
  geofence_enabled: boolean;
  geofence_boundaries?: number[][];
  max_altitude_m: number;
  max_distance_m: number;
  low_battery_action: FailsafeAction;
  low_battery_threshold_percent: number;
  emergency_landing_enabled: boolean;
}

export interface DroneCommand {
  id: string;
  drone_id: string;
  command_type: CommandType;
  parameters: Record<string, any>;
  timestamp: string;
  status: CommandStatus;
  response?: string;
  error?: string;
}

export enum CommandType {
  TAKEOFF = 'takeoff',
  LAND = 'land',
  GOTO = 'goto',
  ORBIT = 'orbit',
  RETURN_TO_LAUNCH = 'return_to_launch',
  START_MISSION = 'start_mission',
  PAUSE_MISSION = 'pause_mission',
  RESUME_MISSION = 'resume_mission',
  ABORT_MISSION = 'abort_mission',
  EMERGENCY_STOP = 'emergency_stop',
  SET_MODE = 'set_mode',
  CALIBRATE = 'calibrate',
  START_RECORDING = 'start_recording',
  STOP_RECORDING = 'stop_recording'
}

export enum CommandStatus {
  PENDING = 'pending',
  SENT = 'sent',
  ACKNOWLEDGED = 'acknowledged',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  TIMEOUT = 'timeout'
}