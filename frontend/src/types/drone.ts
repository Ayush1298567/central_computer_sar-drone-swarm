export interface Drone {
  id: string;
  name: string;
  model: string;
  status: 'offline' | 'idle' | 'active' | 'charging' | 'maintenance' | 'error';
  battery_level: number;
  signal_strength: number;
  position: {
    latitude: number;
    longitude: number;
    altitude: number;
  };
  last_seen: string;
  capabilities: DroneCapabilities;
  telemetry: DroneTelemetry;
}

export interface DroneCapabilities {
  max_flight_time: number;
  max_range: number;
  camera_resolution: string;
  thermal_camera: boolean;
  night_vision: boolean;
  max_speed: number;
  payload_capacity: number;
}

export interface DroneTelemetry {
  timestamp: string;
  position: {
    latitude: number;
    longitude: number;
    altitude: number;
  };
  velocity: {
    x: number;
    y: number;
    z: number;
  };
  battery_level: number;
  signal_strength: number;
  temperature: number;
  status: string;
  errors: string[];
}

export interface DroneCommand {
  id: string;
  drone_id: string;
  command_type: 'takeoff' | 'land' | 'goto' | 'hover' | 'return_home' | 'emergency_stop';
  parameters: Record<string, any>;
  priority: 'low' | 'medium' | 'high' | 'emergency';
  status: 'pending' | 'executing' | 'completed' | 'failed';
  created_at: string;
  executed_at?: string;
}

export interface VideoFeedData {
  drone_id: string;
  stream_url: string;
  quality: 'low' | 'medium' | 'high';
  is_recording: boolean;
  timestamp: string;
}