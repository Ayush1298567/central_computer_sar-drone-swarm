export interface Drone {
  id: string;
  name: string;
  model: string;
  status: 'active' | 'idle' | 'charging' | 'maintenance' | 'error';
  battery_level: number;
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
}

export interface DroneCommand {
  drone_id: string;
  command: 'takeoff' | 'land' | 'return_to_base' | 'goto' | 'hover' | 'emergency_stop';
  parameters?: Record<string, any>;
}

export interface DroneTelemetry {
  drone_id: string;
  timestamp: number;
  position: {
    lat: number;
    lng: number;
    altitude: number;
  };
  orientation: {
    roll: number;
    pitch: number;
    yaw: number;
  };
  velocity: {
    vx: number;
    vy: number;
    vz: number;
  };
  battery: {
    level: number;
    voltage: number;
    current: number;
  };
  sensors: {
    temperature: number;
    humidity: number;
    pressure: number;
  };
}