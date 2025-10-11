/**
 * Drone Connection Service
 * Integrates frontend with the drone connection hub for real drone control
 */

import { apiClient } from './api';

export interface DroneConnection {
  connection_id: string;
  drone_id: string;
  connection_type: 'wifi' | 'lora' | 'mavlink' | 'websocket';
  status: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'failed';
  host?: string;
  port?: number;
  protocol?: string;
  last_heartbeat?: string;
  metrics?: {
    messages_sent: number;
    messages_received: number;
    bytes_sent: number;
    bytes_received: number;
    connection_uptime: number;
    average_latency: number;
    connection_stability: number;
  };
}

export interface DroneCapabilities {
  max_flight_time: number;
  max_speed: number;
  max_altitude: number;
  payload_capacity: number;
  camera_resolution: string;
  has_thermal_camera: boolean;
  has_gimbal: boolean;
  has_rtk_gps: boolean;
  has_collision_avoidance: boolean;
  has_return_to_home: boolean;
  communication_range: number;
  battery_capacity: number;
  supported_commands: string[];
}

export interface DroneInfo {
  drone_id: string;
  name: string;
  model: string;
  manufacturer: string;
  firmware_version: string;
  serial_number: string;
  capabilities: DroneCapabilities;
  connection_type: string;
  connection_params: Record<string, any>;
  status: 'disconnected' | 'connecting' | 'connected' | 'idle' | 'flying' | 'returning' | 'landing' | 'charging' | 'maintenance' | 'emergency' | 'offline';
  last_seen: string;
  battery_level: number;
  position: {
    lat: number;
    lon: number;
    alt: number;
  };
  heading: number;
  speed: number;
  signal_strength: number;
  current_mission_id?: string;
  assigned_operator?: string;
  maintenance_due?: string;
}

export interface ConnectDroneRequest {
  drone_id: string;
  name: string;
  connection_type: 'wifi' | 'lora' | 'mavlink' | 'websocket';
  connection_params: Record<string, any>;
  model?: string;
  manufacturer?: string;
  firmware_version?: string;
  serial_number?: string;
  max_flight_time?: number;
  max_speed?: number;
  max_altitude?: number;
  payload_capacity?: number;
  camera_resolution?: string;
  has_thermal_camera?: boolean;
  has_gimbal?: boolean;
  has_rtk_gps?: boolean;
  has_collision_avoidance?: boolean;
  has_return_to_home?: boolean;
  communication_range?: number;
  battery_capacity?: number;
}

export interface DroneCommand {
  command_type: string;
  parameters?: Record<string, any>;
  priority?: number;
}

export interface DiscoveryStatus {
  discovery_active: boolean;
  total_drones: number;
  by_status: Record<string, number>;
  by_connection_type: Record<string, number>;
}

class DroneConnectionService {
  private baseUrl = '/api/v1/drone-connections';

  /**
   * Get all drone connections
   */
  async getConnections(): Promise<{
    connections: Record<string, DroneConnection>;
    statistics: Record<string, any>;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/connections`);
    return response.data;
  }

  /**
   * Get connection status for a specific drone
   */
  async getDroneConnection(droneId: string): Promise<DroneConnection> {
    const response = await apiClient.get(`${this.baseUrl}/connections/${droneId}`);
    return response.data.connection_status;
  }

  /**
   * Connect to a drone
   */
  async connectDrone(connectionRequest: ConnectDroneRequest): Promise<{
    success: boolean;
    message: string;
    drone_info: any;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/connect`, connectionRequest);
    return response.data;
  }

  /**
   * Disconnect from a drone
   */
  async disconnectDrone(droneId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/${droneId}/disconnect`);
    return response.data;
  }

  /**
   * Send command to a drone
   */
  async sendCommand(droneId: string, command: DroneCommand): Promise<{
    success: boolean;
    message: string;
    command: any;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/${droneId}/command`, command);
    return response.data;
  }

  /**
   * Request telemetry from a drone
   */
  async requestTelemetry(droneId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/${droneId}/telemetry`);
    return response.data;
  }

  /**
   * Get all registered drones
   */
  async getAllDrones(): Promise<{
    drones: {
      all: DroneInfo[];
      connected: DroneInfo[];
      available: DroneInfo[];
    };
    statistics: Record<string, any>;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/drones`);
    return response.data;
  }

  /**
   * Get information for a specific drone
   */
  async getDroneInfo(droneId: string): Promise<{
    drone: DroneInfo;
    connection_status: DroneConnection;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/drones/${droneId}`);
    return response.data;
  }

  /**
   * Get drone discovery status
   */
  async getDiscoveryStatus(): Promise<DiscoveryStatus> {
    const response = await apiClient.get(`${this.baseUrl}/discovery/status`);
    return response.data;
  }

  /**
   * Start drone discovery
   */
  async startDiscovery(): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/discovery/start`);
    return response.data;
  }

  /**
   * Stop drone discovery
   */
  async stopDiscovery(): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/discovery/stop`);
    return response.data;
  }

  /**
   * Flight control commands
   */
  async takeoff(droneId: string, altitude: number = 50): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'takeoff',
      parameters: { altitude },
      priority: 2
    });
    return result.success;
  }

  async land(droneId: string, location?: { lat: number; lon: number }): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'land',
      parameters: location ? { latitude: location.lat, longitude: location.lon } : {},
      priority: 2
    });
    return result.success;
  }

  async returnHome(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'return_home',
      parameters: {},
      priority: 2
    });
    return result.success;
  }

  async emergencyStop(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'emergency_stop',
      parameters: {},
      priority: 3  // Emergency priority
    });
    return result.success;
  }

  async setAltitude(droneId: string, altitude: number): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'set_altitude',
      parameters: { altitude },
      priority: 1
    });
    return result.success;
  }

  async setHeading(droneId: string, heading: number): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'set_heading',
      parameters: { heading },
      priority: 1
    });
    return result.success;
  }

  /**
   * Mission control commands
   */
  async startMission(droneId: string, missionData: any): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'start_mission',
      parameters: missionData,
      priority: 2
    });
    return result.success;
  }

  async pauseMission(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'pause_mission',
      parameters: {},
      priority: 2
    });
    return result.success;
  }

  async resumeMission(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'resume_mission',
      parameters: {},
      priority: 2
    });
    return result.success;
  }

  async abortMission(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'abort_mission',
      parameters: {},
      priority: 3
    });
    return result.success;
  }

  /**
   * System commands
   */
  async enableAutonomous(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'enable_autonomous',
      parameters: {},
      priority: 1
    });
    return result.success;
  }

  async disableAutonomous(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'disable_autonomous',
      parameters: {},
      priority: 1
    });
    return result.success;
  }

  async calibrateSensors(droneId: string): Promise<boolean> {
    const result = await this.sendCommand(droneId, {
      command_type: 'calibrate_sensors',
      parameters: {},
      priority: 1
    });
    return result.success;
  }

  /**
   * Utility methods for common drone operations
   */
  async getConnectedDrones(): Promise<DroneInfo[]> {
    const data = await this.getAllDrones();
    return data.drones.connected;
  }

  async getAvailableDrones(): Promise<DroneInfo[]> {
    const data = await this.getAllDrones();
    return data.drones.available;
  }

  async isDroneConnected(droneId: string): Promise<boolean> {
    try {
      const connection = await this.getDroneConnection(droneId);
      return connection.status === 'connected';
    } catch (error) {
      return false;
    }
  }

  async getDroneBatteryLevel(droneId: string): Promise<number> {
    try {
      const info = await this.getDroneInfo(droneId);
      return info.drone.battery_level;
    } catch (error) {
      return 0;
    }
  }

  async getDronePosition(droneId: string): Promise<{ lat: number; lon: number; alt: number }> {
    try {
      const info = await this.getDroneInfo(droneId);
      return info.drone.position;
    } catch (error) {
      return { lat: 0, lon: 0, alt: 0 };
    }
  }
}

export const droneConnectionService = new DroneConnectionService();
