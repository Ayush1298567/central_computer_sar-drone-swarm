// Drone Types
export interface Drone {
  id: string;
  name: string;
  model: string;
  serial_number: string;
  status: DroneStatus;
  battery_level: number;
  position: DronePosition;
  altitude: number;
  heading: number;
  speed: number;
  armed: boolean;
  mode: DroneMode;
  mission_id?: string;
  home_location: DronePosition;
  capabilities: DroneCapability[];
  sensors: DroneSensor[];
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface DronePosition {
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;
}

export interface DroneTelemetry {
  drone_id: string;
  timestamp: string;
  position: DronePosition;
  altitude: number;
  heading: number;
  speed: number;
  battery_level: number;
  battery_voltage: number;
  battery_current: number;
  signal_strength: number;
  satellite_count: number;
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
}

export interface DroneCommand {
  drone_id: string;
  command: DroneCommandType;
  parameters?: Record<string, any>;
  priority?: CommandPriority;
}

export interface DroneCommandResponse {
  success: boolean;
  message: string;
  command_id?: string;
  estimated_execution_time?: number;
}

export interface RegisterDroneRequest {
  name: string;
  model: string;
  serial_number: string;
  capabilities: DroneCapability[];
  home_location: DronePosition;
}

export interface UpdateDroneRequest {
  name?: string;
  status?: DroneStatus;
  home_location?: DronePosition;
}

export interface DroneCapability {
  type: DroneCapabilityType;
  enabled: boolean;
  parameters?: Record<string, any>;
}

export interface DroneSensor {
  type: SensorType;
  enabled: boolean;
  reading?: SensorReading;
  last_updated?: string;
}

export interface SensorReading {
  value: number;
  unit: string;
  timestamp: string;
  quality?: 'poor' | 'fair' | 'good' | 'excellent';
}

export type DroneStatus =
  | 'offline'
  | 'connecting'
  | 'ready'
  | 'arming'
  | 'armed'
  | 'taking_off'
  | 'in_air'
  | 'landing'
  | 'error'
  | 'maintenance'
  | 'updating';

export type DroneMode =
  | 'manual'
  | 'auto'
  | 'guided'
  | 'rtl' // Return to Launch
  | 'land'
  | 'loiter'
  | 'mission'
  | 'follow'
  | 'sport';

export type DroneCommandType =
  | 'arm'
  | 'disarm'
  | 'takeoff'
  | 'land'
  | 'rtl'
  | 'goto'
  | 'orbit'
  | 'survey'
  | 'pause'
  | 'resume'
  | 'set_home'
  | 'reboot'
  | 'calibrate'
  | 'emergency_stop';

export type CommandPriority =
  | 'low'
  | 'normal'
  | 'high'
  | 'critical';

export type DroneCapabilityType =
  | 'camera'
  | 'thermal_camera'
  | 'gps'
  | 'rtk_gps'
  | 'lidar'
  | 'sonar'
  | 'radar'
  | 'payload_delivery'
  | 'sample_collection'
  | 'winch'
  | 'first_person_view'
  | 'night_vision'
  | 'obstacle_avoidance'
  | 'auto_return'
  | 'geofencing'
  | 'precision_landing'
  | 'swarm_coordination';

export type SensorType =
  | 'gps'
  | 'accelerometer'
  | 'gyroscope'
  | 'magnetometer'
  | 'barometer'
  | 'temperature'
  | 'humidity'
  | 'air_pressure'
  | 'wind_speed'
  | 'wind_direction'
  | 'battery_voltage'
  | 'battery_current'
  | 'signal_strength'
  | 'ultrasonic'
  | 'infrared'
  | 'camera'
  | 'thermal_camera';