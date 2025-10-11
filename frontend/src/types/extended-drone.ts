// Extended drone types for interactive components
import { Drone, DroneTelemetry } from './drone';

export interface ExtendedDrone {
  id: string;
  name: string;
  model: string;
  status: 'offline' | 'idle' | 'active' | 'charging' | 'maintenance' | 'error';
  battery_level: number;
  signal_strength: number;
  position: {
    lat: number;
    lng: number;
    altitude: number;
  };
  heading: number;
  speed: number;
  mission_id?: string;
  capabilities: string[];
  last_communication: number;
  last_seen?: number;
  capabilities_extended: DroneCapabilities;
  telemetry?: ExtendedTelemetry;
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

export interface ExtendedTelemetry extends DroneTelemetry {
  velocity: {
    vx: number;
    vy: number;
    vz: number;
  };
  status: string;
  errors: string[];
  temperature?: number;
  ground_speed?: number;
  // Additional properties to match DroneTelemetry
  latitude?: number;
  longitude?: number;
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

// Utility function to convert base Drone to ExtendedDrone
export function toExtendedDrone(drone: Drone): ExtendedDrone {
  return {
    id: drone.id,
    name: drone.name,
    model: drone.model,
    status: mapDroneStatus(drone.status),
    battery_level: drone.battery_level,
    signal_strength: 85, // Default value
    position: {
      lat: drone.position.lat,
      lng: drone.position.lng,
      altitude: drone.position.altitude,
    },
    heading: drone.heading,
    speed: drone.speed,
    mission_id: drone.mission_id,
    capabilities: drone.capabilities,
    last_communication: drone.last_communication,
    last_seen: drone.last_communication,
    capabilities_extended: {
      max_flight_time: 30, // Default value in minutes
      max_range: 5000, // Default value in meters
      camera_resolution: '1080p',
      thermal_camera: false,
      night_vision: false,
      max_speed: 15, // Default value in m/s
      payload_capacity: 2.0, // Default value in kg
    },
  };
}

function mapDroneStatus(status: string): ExtendedDrone['status'] {
  switch (status) {
    case 'online': return 'idle';
    case 'flying': return 'active';
    case 'offline': return 'offline';
    case 'charging': return 'charging';
    case 'maintenance': return 'maintenance';
    default: return 'error';
  }
}
