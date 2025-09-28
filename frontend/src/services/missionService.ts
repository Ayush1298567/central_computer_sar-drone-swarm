/**
 * Mission API Service
 *
 * Handles all mission-related API calls including:
 * - Mission CRUD operations
 * - Mission control (start, pause, abort)
 * - Mission status monitoring
 * - React Query integration for caching and state management
 */

import {
  Mission,
  CreateMissionRequest,
  UpdateMissionRequest,
  MissionStatus,
  MissionPriority,
  ApiResponse,
  ApiError,
  PaginationParams,
  PaginatedResponse,
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = 10000; // 10 seconds

// Error handling utility
class MissionServiceError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'MissionServiceError';
  }
}

// Retry configuration
const RETRY_CONFIG = {
  maxAttempts: 3,
  delayMs: 1000,
  backoffMultiplier: 2,
};

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
      throw new MissionServiceError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code
      );
    }

    const data: ApiResponse<T> = await response.json();

    if (!data.success) {
      throw new MissionServiceError(data.error || 'API request failed');
    }

    return data.data as T;
  } catch (error) {
    if (error instanceof MissionServiceError) {
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
        throw new MissionServiceError('Request timeout');
      }
      throw new MissionServiceError(error.message);
    }

    throw new MissionServiceError('Unknown error occurred');
  }
}

// Mission API Service Class
export class MissionService {
  /**
   * Get all missions with optional filtering and pagination
   */
  static async getMissions(
    filters?: {
      status?: MissionStatus;
      priority?: MissionPriority;
      mission_type?: string;
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<Mission>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
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
    const endpoint = `/missions${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<Mission>>(endpoint);
  }

  /**
   * Get a single mission by ID
   */
  static async getMission(id: string): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}`);
  }

  /**
   * Create a new mission
   */
  static async createMission(missionData: CreateMissionRequest): Promise<Mission> {
    return apiRequest<Mission>('/missions', {
      method: 'POST',
      body: JSON.stringify(missionData),
    });
  }

  /**
   * Update an existing mission
   */
  static async updateMission(id: string, updates: UpdateMissionRequest): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete a mission
   */
  static async deleteMission(id: string): Promise<void> {
    return apiRequest<void>(`/missions/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Start a mission
   */
  static async startMission(id: string): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}/start`, {
      method: 'POST',
    });
  }

  /**
   * Pause a mission
   */
  static async pauseMission(id: string): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}/pause`, {
      method: 'POST',
    });
  }

  /**
   * Resume a paused mission
   */
  static async resumeMission(id: string): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}/resume`, {
      method: 'POST',
    });
  }

  /**
   * Abort a mission
   */
  static async abortMission(id: string, reason?: string): Promise<Mission> {
    return apiRequest<Mission>(`/missions/${id}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  /**
   * Get mission progress and status
   */
  static async getMissionProgress(id: string): Promise<{
    mission: Mission;
    progress: {
      completed_waypoints: number;
      total_waypoints: number;
      estimated_time_remaining: number;
      current_drone_positions: Array<{
        drone_id: string;
        position: [number, number, number]; // [lat, lng, alt]
        battery_level: number;
        status: string;
      }>;
    };
  }> {
    return apiRequest(`/missions/${id}/progress`);
  }

  /**
   * Get mission logs and events
   */
  static async getMissionLogs(
    id: string,
    filters?: {
      event_type?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<Array<{
    id: string;
    timestamp: string;
    event_type: string;
    message: string;
    drone_id?: string;
    severity: 'info' | 'warning' | 'error' | 'critical';
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
    const endpoint = `/missions/${id}/logs${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Get mission statistics
   */
  static async getMissionStats(filters?: {
    start_date?: string;
    end_date?: string;
    mission_type?: string;
  }): Promise<{
    total_missions: number;
    completed_missions: number;
    failed_missions: number;
    average_duration: number;
    missions_by_type: Record<string, number>;
    missions_by_status: Record<MissionStatus, number>;
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
    const endpoint = `/missions/stats${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }
}

// Export error class for consumers
export { MissionServiceError };