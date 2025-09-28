// Drone API Service
// Handles all drone-related API calls with real-time data management

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

// TypeScript interfaces for drone requests/responses
export interface Drone {
  id: string;
  name: string;
  model: string;
  serial_number: string;
  status: 'offline' | 'online' | 'busy' | 'maintenance' | 'error';
  battery_level: number;
  location: {
    latitude: number;
    longitude: number;
    altitude: number;
    heading: number;
    speed: number;
  };
  capabilities: {
    max_altitude: number;
    max_speed: number;
    max_payload: number;
    camera_resolution: string;
    thermal_imaging: boolean;
    night_vision: boolean;
    autonomy_hours: number;
  };
  last_seen: string;
  mission_id?: string;
  connection_type: 'wifi' | 'cellular' | 'satellite' | 'mesh';
  signal_strength: number;
  firmware_version: string;
  hardware_health: {
    motors: 'good' | 'warning' | 'critical';
    sensors: 'good' | 'warning' | 'critical';
    battery: 'good' | 'warning' | 'critical';
    communication: 'good' | 'warning' | 'critical';
  };
}

export interface RegisterDroneRequest {
  name: string;
  model: string;
  serial_number: string;
  capabilities: {
    max_altitude: number;
    max_speed: number;
    max_payload: number;
    camera_resolution: string;
    thermal_imaging: boolean;
    night_vision: boolean;
    autonomy_hours: number;
  };
  connection_type: 'wifi' | 'cellular' | 'satellite' | 'mesh';
}

export interface UpdateDroneRequest {
  name?: string;
  status?: 'offline' | 'online' | 'busy' | 'maintenance' | 'error';
  location?: {
    latitude?: number;
    longitude?: number;
    altitude?: number;
    heading?: number;
    speed?: number;
  };
}

export interface DroneCommand {
  type: 'takeoff' | 'land' | 'return_home' | 'goto' | 'hover' | 'follow_path' | 'scan_area' | 'emergency_stop';
  parameters: Record<string, any>;
  priority: 'low' | 'normal' | 'high' | 'emergency';
}

export interface DroneTelemetry {
  timestamp: string;
  battery_voltage: number;
  battery_current: number;
  battery_temperature: number;
  cpu_usage: number;
  memory_usage: number;
  storage_usage: number;
  gps_satellites: number;
  signal_quality: number;
  wind_speed: number;
  wind_direction: number;
  temperature: number;
  humidity: number;
  pressure: number;
}

export interface DroneFleet {
  total_drones: number;
  online_drones: number;
  busy_drones: number;
  maintenance_drones: number;
  error_drones: number;
  average_battery: number;
  fleet_efficiency: number;
  utilization_rate: number;
}

// Real-time drone data management
class DroneDataManager {
  private listeners: Map<string, Set<(drone: Drone) => void>> = new Map();
  private telemetryListeners: Map<string, Set<(telemetry: DroneTelemetry) => void>> = new Map();
  private websocket: WebSocket | null = null;

  connectWebSocket() {
    if (this.websocket?.readyState === WebSocket.OPEN) return;

    this.websocket = new WebSocket(api.wsUrl + '/drones');

    this.websocket.onopen = () => {
      console.log('Drone WebSocket connected');
    };

    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'drone_update' && data.drone) {
          this.notifyDroneListeners(data.drone.id, data.drone);
        } else if (data.type === 'telemetry_update' && data.telemetry) {
          this.notifyTelemetryListeners(data.drone_id, data.telemetry);
        }
      } catch (error) {
        console.error('Error parsing drone WebSocket message:', error);
      }
    };

    this.websocket.onclose = () => {
      console.log('Drone WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connectWebSocket(), 5000);
    };

    this.websocket.onerror = (error) => {
      console.error('Drone WebSocket error:', error);
    };
  }

  subscribeToDrone(droneId: string, callback: (drone: Drone) => void) {
    if (!this.listeners.has(droneId)) {
      this.listeners.set(droneId, new Set());
    }
    this.listeners.get(droneId)!.add(callback);

    if (this.websocket?.readyState !== WebSocket.OPEN) {
      this.connectWebSocket();
    }

    return () => {
      this.listeners.get(droneId)?.delete(callback);
    };
  }

  subscribeToTelemetry(droneId: string, callback: (telemetry: DroneTelemetry) => void) {
    if (!this.telemetryListeners.has(droneId)) {
      this.telemetryListeners.set(droneId, new Set());
    }
    this.telemetryListeners.get(droneId)!.add(callback);

    if (this.websocket?.readyState !== WebSocket.OPEN) {
      this.connectWebSocket();
    }

    return () => {
      this.telemetryListeners.get(droneId)?.delete(callback);
    };
  }

  private notifyDroneListeners(droneId: string, drone: Drone) {
    this.listeners.get(droneId)?.forEach(callback => callback(drone));
  }

  private notifyTelemetryListeners(droneId: string, telemetry: DroneTelemetry) {
    this.telemetryListeners.get(droneId)?.forEach(callback => callback(telemetry));
  }
}

// API service class with error handling and retry logic
class DroneService {
  private queryClient: ReturnType<typeof useQueryClient>;
  private dataManager = new DroneDataManager();

  constructor() {
    // Query client will be injected when using hooks
  }

  setQueryClient(client: ReturnType<typeof useQueryClient>) {
    this.queryClient = client;
  }

  getDataManager() {
    return this.dataManager;
  }

  // Get all drones with optional filtering
  async getDrones(status?: string, mission_id?: string): Promise<Drone[]> {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (mission_id) params.append('mission_id', mission_id);

      const query = params.toString() ? `?${params.toString()}` : '';
      const response = await fetch(`${api.baseUrl}/drones${query}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch drones: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching drones:', error);
      throw error;
    }
  }

  // Get single drone by ID
  async getDrone(id: string): Promise<Drone> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch drone: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching drone:', error);
      throw error;
    }
  }

  // Register new drone
  async registerDrone(droneData: RegisterDroneRequest): Promise<Drone> {
    try {
      const response = await fetch(`${api.baseUrl}/drones`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(droneData),
      });

      if (!response.ok) {
        throw new Error(`Failed to register drone: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error registering drone:', error);
      throw error;
    }
  }

  // Update drone
  async updateDrone(id: string, updates: UpdateDroneRequest): Promise<Drone> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update drone: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating drone:', error);
      throw error;
    }
  }

  // Delete drone
  async deleteDrone(id: string): Promise<void> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete drone: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting drone:', error);
      throw error;
    }
  }

  // Send command to drone
  async sendCommand(droneId: string, command: DroneCommand): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/${droneId}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(command),
      });

      if (!response.ok) {
        throw new Error(`Failed to send command: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending command:', error);
      throw error;
    }
  }

  // Get drone telemetry
  async getDroneTelemetry(droneId: string, hours = 24): Promise<DroneTelemetry[]> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/${droneId}/telemetry?hours=${hours}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch telemetry: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching telemetry:', error);
      throw error;
    }
  }

  // Get drone fleet analytics
  async getDroneFleet(): Promise<DroneFleet> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/fleet`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch fleet data: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching fleet data:', error);
      throw error;
    }
  }

  // Emergency stop all drones
  async emergencyStopAll(reason?: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${api.baseUrl}/drones/emergency-stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        throw new Error(`Failed to emergency stop drones: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error emergency stopping drones:', error);
      throw error;
    }
  }
}

// Export singleton instances
export const droneService = new DroneService();

// React Query hooks
export const useDrones = (status?: string, mission_id?: string) => {
  return useQuery({
    queryKey: ['drones', status, mission_id],
    queryFn: () => droneService.getDrones(status, mission_id),
    staleTime: 10000, // 10 seconds
    retry: 3,
  });
};

export const useDrone = (id: string) => {
  return useQuery({
    queryKey: ['drone', id],
    queryFn: () => droneService.getDrone(id),
    enabled: !!id,
    staleTime: 5000, // 5 seconds
    retry: 3,
  });
};

export const useRegisterDrone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: droneService.registerDrone,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drones'] });
    },
    retry: 2,
  });
};

export const useUpdateDrone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: UpdateDroneRequest }) =>
      droneService.updateDrone(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['drones'] });
      queryClient.invalidateQueries({ queryKey: ['drone', data.id] });
    },
    retry: 2,
  });
};

export const useDeleteDrone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: droneService.deleteDrone,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drones'] });
    },
    retry: 2,
  });
};

export const useSendCommand = () => {
  return useMutation({
    mutationFn: ({ droneId, command }: { droneId: string; command: DroneCommand }) =>
      droneService.sendCommand(droneId, command),
    retry: 2,
  });
};

export const useDroneTelemetry = (droneId: string, hours = 24) => {
  return useQuery({
    queryKey: ['droneTelemetry', droneId, hours],
    queryFn: () => droneService.getDroneTelemetry(droneId, hours),
    enabled: !!droneId,
    staleTime: 30000, // 30 seconds
    retry: 3,
  });
};

export const useDroneFleet = () => {
  return useQuery({
    queryKey: ['droneFleet'],
    queryFn: droneService.getDroneFleet,
    staleTime: 15000, // 15 seconds
    retry: 3,
  });
};

export const useEmergencyStopAll = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reason }: { reason?: string }) =>
      droneService.emergencyStopAll(reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drones'] });
    },
    retry: 1, // Only retry once for emergency commands
  });
};

// Real-time subscription hooks
export const useDroneSubscription = (droneId: string) => {
  const queryClient = useQueryClient();

  return (callback: (drone: Drone) => void) => {
    return droneService.getDataManager().subscribeToDrone(droneId, (drone) => {
      // Update React Query cache
      queryClient.setQueryData(['drone', droneId], drone);
      callback(drone);
    });
  };
};

export const useTelemetrySubscription = (droneId: string) => {
  return (callback: (telemetry: DroneTelemetry) => void) => {
    return droneService.getDataManager().subscribeToTelemetry(droneId, callback);
  };
};