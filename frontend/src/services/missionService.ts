/**
 * Mission service for the SAR Mission Commander frontend.
 * Provides methods for creating, managing, and monitoring missions.
 */

import {
  apiService,
  cachedApiService,
  API_ENDPOINTS,
  ApiResponse,
  ApiError,
  RetryHandler,
} from './api';

import {
  Mission,
  CreateMissionRequest,
  UpdateMissionRequest,
  MissionProgress,
  MissionStatus,
  MissionResponse,
  MissionsResponse,
  MissionProgressResponse,
  MissionPlan,
  MissionAnalytics,
  MissionControlCommand,
  WeatherConditions,
  RiskAssessment,
} from '../types/mission';

export class MissionService {
  /**
   * Get all missions with optional filtering
   */
  static async getMissions(
    status?: MissionStatus,
    limit?: number,
    offset?: number
  ): Promise<ApiResponse<Mission[]>> {
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (limit) params.append('limit', limit.toString());
      if (offset) params.append('offset', offset.toString());

      const queryString = params.toString();
      const endpoint = queryString ? `${API_ENDPOINTS.MISSIONS}?${queryString}` : API_ENDPOINTS.MISSIONS;

      return await RetryHandler.withRetry(
        () => cachedApiService.get<Mission[]>(endpoint, 30000), // 30 second cache
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get a specific mission by ID
   */
  static async getMission(missionId: string): Promise<ApiResponse<Mission>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get<Mission>(API_ENDPOINTS.MISSION_BY_ID(missionId), 15000), // 15 second cache
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Create a new mission
   */
  static async createMission(missionData: CreateMissionRequest): Promise<ApiResponse<Mission>> {
    try {
      // Validate mission data
      this.validateMissionData(missionData);

      return await RetryHandler.withRetry(
        () => apiService.post<Mission>(API_ENDPOINTS.MISSIONS, missionData),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Update an existing mission
   */
  static async updateMission(
    missionId: string,
    updates: UpdateMissionRequest
  ): Promise<ApiResponse<Mission>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.put<Mission>(API_ENDPOINTS.MISSION_BY_ID(missionId), updates),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Start mission execution
   */
  static async startMission(missionId: string): Promise<ApiResponse<{ mission_id: string; started: boolean }>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.post(API_ENDPOINTS.MISSION_START(missionId)),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Pause a running mission
   */
  static async pauseMission(missionId: string, reason: string): Promise<ApiResponse<{ paused: boolean }>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.post(API_ENDPOINTS.MISSION_PAUSE(missionId), { reason }),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Resume a paused mission
   */
  static async resumeMission(missionId: string): Promise<ApiResponse<{ resumed: boolean }>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.post(API_ENDPOINTS.MISSION_RESUME(missionId)),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Abort a mission
   */
  static async abortMission(
    missionId: string,
    reason: string,
    emergency: boolean = false
  ): Promise<ApiResponse<{ aborted: boolean }>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.post(API_ENDPOINTS.MISSION_ABORT(missionId), { reason, emergency }),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get real-time mission progress
   */
  static async getMissionProgress(missionId: string): Promise<ApiResponse<MissionProgress>> {
    try {
      // Use shorter cache for progress data
      return await RetryHandler.withRetry(
        () => cachedApiService.get<MissionProgress>(
          `${API_ENDPOINTS.MISSIONS}/${missionId}/progress`,
          5000 // 5 second cache
        ),
        3,
        500
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get mission analytics and performance data
   */
  static async getMissionAnalytics(missionId: string): Promise<ApiResponse<MissionAnalytics>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get<MissionAnalytics>(API_ENDPOINTS.ANALYTICS_MISSION(missionId), 60000), // 1 minute cache
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Send a control command to a mission
   */
  static async sendMissionCommand(command: MissionControlCommand): Promise<ApiResponse<{ executed: boolean }>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.post(`${API_ENDPOINTS.MISSIONS}/${command.parameters.mission_id}/command`, command),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get weather conditions for mission planning
   */
  static async getWeatherConditions(
    latitude: number,
    longitude: number
  ): Promise<ApiResponse<WeatherConditions>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get<WeatherConditions>(
          `${API_ENDPOINTS.WEATHER}?lat=${latitude}&lng=${longitude}`,
          300000 // 5 minute cache
        ),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get weather forecast for mission timing
   */
  static async getWeatherForecast(
    latitude: number,
    longitude: number,
    hours: number = 24
  ): Promise<ApiResponse<any[]>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get<any[]>(
          `${API_ENDPOINTS.WEATHER_FORECAST}?lat=${latitude}&lng=${longitude}&hours=${hours}`,
          600000 // 10 minute cache
        ),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Generate a mission plan with AI assistance
   */
  static async generateMissionPlan(
    area: any,
    searchTarget: string,
    availableDrones: string[]
  ): Promise<ApiResponse<MissionPlan>> {
    try {
      const planRequest = {
        search_area: area,
        search_target: searchTarget,
        available_drones: availableDrones,
        include_weather: true,
        include_risk_assessment: true,
      };

      return await RetryHandler.withRetry(
        () => apiService.post<MissionPlan>(`${API_ENDPOINTS.MISSIONS}/plan`, planRequest),
        3,
        2000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Get mission execution history and events
   */
  static async getMissionHistory(
    missionId: string,
    limit: number = 100
  ): Promise<ApiResponse<any[]>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get<any[]>(
          `${API_ENDPOINTS.MISSIONS}/${missionId}/history?limit=${limit}`,
          60000 // 1 minute cache
        ),
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Export mission data for reporting
   */
  static async exportMissionData(
    missionId: string,
    format: 'json' | 'csv' | 'pdf' = 'json'
  ): Promise<ApiResponse<Blob>> {
    try {
      return await RetryHandler.withRetry(
        () => apiService.get(
          `${API_ENDPOINTS.MISSIONS}/${missionId}/export?format=${format}`,
          { timeout: 30000 } // Longer timeout for exports
        ),
        2,
        2000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Validate mission data before creation
   */
  private static validateMissionData(data: CreateMissionRequest): void {
    if (!data.name || data.name.trim().length === 0) {
      throw new Error('Mission name is required');
    }

    if (!data.search_area || !data.search_area.coordinates) {
      throw new Error('Search area is required');
    }

    if (!data.launch_point) {
      throw new Error('Launch point is required');
    }

    if (!data.search_target || data.search_target.trim().length === 0) {
      throw new Error('Search target is required');
    }

    if (!data.assigned_drones || data.assigned_drones.length === 0) {
      throw new Error('At least one drone must be assigned');
    }

    // Validate coordinates format
    const coords = data.search_area.coordinates;
    if (!Array.isArray(coords) || coords.length === 0 || !Array.isArray(coords[0])) {
      throw new Error('Invalid search area coordinates format');
    }

    // Validate launch point
    if (typeof data.launch_point.lat !== 'number' || typeof data.launch_point.lng !== 'number') {
      throw new Error('Invalid launch point coordinates');
    }
  }

  /**
   * Calculate estimated mission duration based on parameters
   */
  static calculateEstimatedDuration(
    areaKm2: number,
    droneCount: number,
    searchSpeed: string = 'thorough'
  ): number {
    // Base coverage rate in km² per minute per drone
    const baseRate = searchSpeed === 'fast' ? 0.8 : 0.5;

    if (droneCount > 0) {
      const totalRate = baseRate * droneCount;
      const estimatedMinutes = areaKm2 / totalRate;
      return Math.max(10, Math.min(180, estimatedMinutes)); // Between 10-180 minutes
    }

    return 30; // Default fallback
  }

  /**
   * Get mission status summary for dashboard
   */
  static async getMissionSummary(): Promise<ApiResponse<{
    total_missions: number;
    active_missions: number;
    completed_missions: number;
    failed_missions: number;
    average_completion_time: number;
  }>> {
    try {
      return await RetryHandler.withRetry(
        () => cachedApiService.get(API_ENDPOINTS.ANALYTICS_OVERVIEW, 60000), // 1 minute cache
        3,
        1000
      );
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Batch operations for multiple missions
   */
  static async batchOperation(
    operations: Array<{
      mission_id: string;
      operation: 'start' | 'pause' | 'resume' | 'abort';
      parameters?: any;
    }>
  ): Promise<ApiResponse<Array<{ mission_id: string; success: boolean; message?: string }>>> {
    try {
      const batchRequests = operations.map(op => ({
        endpoint: `${API_ENDPOINTS.MISSIONS}/${op.mission_id}/${op.operation}`,
        options: {
          method: 'POST',
          body: JSON.stringify(op.parameters || {}),
        },
      }));

      return await apiService.batch(batchRequests);
    } catch (error) {
      throw ApiErrorHandler.handleError(error);
    }
  }
}

// Error handling utilities specific to missions
export class MissionErrorHandler {
  static handleMissionError(error: any): { message: string; action: string } {
    const apiError = ApiErrorHandler.handleError(error);

    switch (apiError.status) {
      case 400:
        return {
          message: 'Invalid mission parameters',
          action: 'Please check your mission configuration and try again',
        };
      case 403:
        return {
          message: 'Access denied',
          action: 'You do not have permission to perform this action',
        };
      case 404:
        return {
          message: 'Mission not found',
          action: 'The specified mission does not exist',
        };
      case 409:
        return {
          message: 'Mission conflict',
          action: 'The mission is in a state that prevents this operation',
        };
      case 422:
        return {
          message: 'Invalid mission data',
          action: 'Please verify all required fields are filled correctly',
        };
      case 500:
        return {
          message: 'Server error',
          action: 'The server encountered an error. Please try again later',
        };
      case 503:
        return {
          message: 'Service unavailable',
          action: 'The mission service is temporarily unavailable',
        };
      default:
        return {
          message: apiError.message || 'Unknown error',
          action: 'Please try again or contact support if the problem persists',
        };
    }
  }
}

// Import the error handler
import { ApiErrorHandler } from './api';