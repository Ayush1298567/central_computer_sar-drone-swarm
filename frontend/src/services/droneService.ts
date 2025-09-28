/**
 * Drone API Service
 *
 * Handles all drone-related API calls including:
 * - Drone registration and discovery
 * - Drone status and telemetry monitoring
 * - Drone command execution
 * - Real-time drone data management
 */

import {
  Drone,
  DroneTelemetry,
  DroneCommand,
  DroneCommandResponse,
  RegisterDroneRequest,
  UpdateDroneRequest,
  DroneStatus,
  DroneMode,
  DroneCommandType,
  ApiResponse,
  PaginationParams,
  PaginatedResponse,
  DronePosition,
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = 10000; // 10 seconds
const TELEMETRY_UPDATE_INTERVAL = 1000; // 1 second

// Error handling utility
class DroneServiceError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'DroneServiceError';
  }
}

// Retry configuration
const RETRY_CONFIG = {
  maxAttempts: 3,
  delayMs: 1000,
  backoffMultiplier: 2,
};

// Real-time telemetry management
class DroneTelemetryManager {
  private static instance: DroneTelemetryManager;
  private telemetryCallbacks: Map<string, (telemetry: DroneTelemetry) => void> = new Map();
  private isPolling: boolean = false;
  private pollingInterval?: NodeJS.Timeout;

  static getInstance(): DroneTelemetryManager {
    if (!DroneTelemetryManager.instance) {
      DroneTelemetryManager.instance = new DroneTelemetryManager();
    }
    return DroneTelemetryManager.instance;
  }

  // Subscribe to telemetry updates for a specific drone
  subscribe(droneId: string, callback: (telemetry: DroneTelemetry) => void): void {
    this.telemetryCallbacks.set(droneId, callback);
    this.startPolling();
  }

  // Unsubscribe from telemetry updates
  unsubscribe(droneId: string): void {
    this.telemetryCallbacks.delete(droneId);
    if (this.telemetryCallbacks.size === 0) {
      this.stopPolling();
    }
  }

  private startPolling(): void {
    if (this.isPolling) return;

    this.isPolling = true;
    this.pollingInterval = setInterval(async () => {
      for (const droneId of this.telemetryCallbacks.keys()) {
        try {
          const telemetry = await DroneService.getDroneTelemetry(droneId);
          const callback = this.telemetryCallbacks.get(droneId);
          if (callback) {
            callback(telemetry);
          }
        } catch (error) {
          console.error(`Failed to get telemetry for drone ${droneId}:`, error);
        }
      }
    }, TELEMETRY_UPDATE_INTERVAL);
  }

  private stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = undefined;
    }
    this.isPolling = false;
  }
}

// Generic API request wrapper with error handling and retry logic
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(url, {
      ...config,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new DroneServiceError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code
      );
    }

    const data: ApiResponse<T> = await response.json();

    if (!data.success) {
      throw new DroneServiceError(data.error || 'API request failed');
    }

    return data.data as T;
  } catch (error) {
    if (error instanceof DroneServiceError) {
      throw error;
    }

    // Handle network errors and retries
    if (retryCount < RETRY_CONFIG.maxAttempts) {
      const delay = RETRY_CONFIG.delayMs * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount);
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiRequest<T>(endpoint, options, retryCount + 1);
    }

    // Final error after all retries
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new DroneServiceError('Request timeout');
      }
      throw new DroneServiceError(error.message);
    }

    throw new DroneServiceError('Unknown error occurred');
  }
}

// Drone API Service Class
export class DroneService {
  private static telemetryManager = DroneTelemetryManager.getInstance();

  /**
   * Get all drones with optional filtering and pagination
   */
  static async getDrones(
    filters?: {
      status?: DroneStatus;
      model?: string;
      capabilities?: string[];
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<Drone>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(`${key}[]`, v.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/drones${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<Drone>>(endpoint);
  }

  /**
   * Get a single drone by ID
   */
  static async getDrone(id: string): Promise<Drone> {
    return apiRequest<Drone>(`/drones/${id}`);
  }

  /**
   * Register a new drone
   */
  static async registerDrone(droneData: RegisterDroneRequest): Promise<Drone> {
    return apiRequest<Drone>('/drones', {
      method: 'POST',
      body: JSON.stringify(droneData),
    });
  }

  /**
   * Update an existing drone
   */
  static async updateDrone(id: string, updates: UpdateDroneRequest): Promise<Drone> {
    return apiRequest<Drone>(`/drones/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete a drone
   */
  static async deleteDrone(id: string): Promise<void> {
    return apiRequest<void>(`/drones/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Get drone telemetry data
   */
  static async getDroneTelemetry(droneId: string): Promise<DroneTelemetry> {
    return apiRequest<DroneTelemetry>(`/drones/${droneId}/telemetry`);
  }

  /**
   * Subscribe to real-time telemetry updates for a drone
   */
  static subscribeToTelemetry(
    droneId: string,
    callback: (telemetry: DroneTelemetry) => void
  ): void {
    this.telemetryManager.subscribe(droneId, callback);
  }

  /**
   * Unsubscribe from telemetry updates
   */
  static unsubscribeFromTelemetry(droneId: string): void {
    this.telemetryManager.unsubscribe(droneId);
  }

  /**
   * Send a command to a drone
   */
  static async sendCommand(command: DroneCommand): Promise<DroneCommandResponse> {
    return apiRequest<DroneCommandResponse>('/drones/commands', {
      method: 'POST',
      body: JSON.stringify(command),
    });
  }

  /**
   * Send multiple commands to multiple drones
   */
  static async sendBulkCommands(commands: DroneCommand[]): Promise<DroneCommandResponse[]> {
    return apiRequest<DroneCommandResponse[]>('/drones/commands/bulk', {
      method: 'POST',
      body: JSON.stringify({ commands }),
    });
  }

  /**
   * Get drone command history
   */
  static async getCommandHistory(
    droneId: string,
    filters?: {
      command_type?: DroneCommandType;
      start_date?: string;
      end_date?: string;
      status?: 'pending' | 'executing' | 'completed' | 'failed';
    }
  ): Promise<Array<{
    id: string;
    drone_id: string;
    command: DroneCommandType;
    parameters: Record<string, any>;
    status: 'pending' | 'executing' | 'completed' | 'failed';
    created_at: string;
    executed_at?: string;
    completed_at?: string;
    error_message?: string;
  }>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/drones/${droneId}/commands${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Update drone position (for simulation/testing)
   */
  static async updateDronePosition(
    droneId: string,
    position: DronePosition
  ): Promise<Drone> {
    return apiRequest<Drone>(`/drones/${droneId}/position`, {
      method: 'PUT',
      body: JSON.stringify({ position }),
    });
  }

  /**
   * Get drone capabilities
   */
  static async getDroneCapabilities(droneId: string): Promise<{
    drone_id: string;
    capabilities: Array<{
      type: string;
      enabled: boolean;
      parameters: Record<string, any>;
    }>;
  }> {
    return apiRequest(`/drones/${droneId}/capabilities`);
  }

  /**
   * Update drone capabilities
   */
  static async updateDroneCapabilities(
    droneId: string,
    capabilities: Array<{
      type: string;
      enabled: boolean;
      parameters?: Record<string, any>;
    }>
  ): Promise<Drone> {
    return apiRequest<Drone>(`/drones/${droneId}/capabilities`, {
      method: 'PUT',
      body: JSON.stringify({ capabilities }),
    });
  }

  /**
   * Get drone sensor data
   */
  static async getDroneSensors(droneId: string): Promise<{
    drone_id: string;
    sensors: Array<{
      type: string;
      enabled: boolean;
      reading?: {
        value: number;
        unit: string;
        timestamp: string;
        quality: string;
      };
      last_updated?: string;
    }>;
  }> {
    return apiRequest(`/drones/${droneId}/sensors`);
  }

  /**
   * Get drone statistics
   */
  static async getDroneStats(filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{
    total_drones: number;
    active_drones: number;
    drones_by_status: Record<DroneStatus, number>;
    average_battery_level: number;
    total_flight_time: number;
    missions_completed: number;
  }> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/drones/stats${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Emergency stop all drones
   */
  static async emergencyStop(reason?: string): Promise<{
    success: boolean;
    message: string;
    affected_drones: string[];
  }> {
    return apiRequest('/drones/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }
}

// Export error class and telemetry manager for consumers
export { DroneServiceError, DroneTelemetryManager };