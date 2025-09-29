/**
 * Mission Service
 *
 * Service for managing SAR missions with backend integration.
 */

import { apiService } from './api';
import { API_ENDPOINTS } from '../types';
import { Mission, CreateMissionRequest, UpdateMissionRequest } from '../types/mission';

export class MissionService {
  /**
   * Get all missions
   */
  static async getMissions(params?: { status?: string; page?: number; per_page?: number }) {
    return apiService.get<Mission[]>(API_ENDPOINTS.MISSIONS, params);
  }

  /**
   * Get mission by ID
   */
  static async getMission(id: number) {
    return apiService.get<Mission>(`${API_ENDPOINTS.MISSIONS}/${id}`);
  }

  /**
   * Create new mission
   */
  static async createMission(missionData: CreateMissionRequest) {
    return apiService.post<Mission>(API_ENDPOINTS.MISSIONS, missionData);
  }

  /**
   * Update existing mission
   */
  static async updateMission(id: number, missionData: Partial<UpdateMissionRequest>) {
    return apiService.put<Mission>(`${API_ENDPOINTS.MISSIONS}/${id}`, missionData);
  }

  /**
   * Delete mission
   */
  static async deleteMission(id: number) {
    return apiService.delete<void>(`${API_ENDPOINTS.MISSIONS}/${id}`);
  }

  /**
   * Start mission
   */
  static async startMission(id: number) {
    return apiService.post<Mission>(`${API_ENDPOINTS.MISSIONS}/${id}/start`, {});
  }

  /**
   * Stop mission
   */
  static async stopMission(id: number) {
    return apiService.post<Mission>(`${API_ENDPOINTS.MISSIONS}/${id}/stop`, {});
  }

  /**
   * Get mission statistics
   */
  static async getMissionStats(id: number) {
    return apiService.get<any>(`${API_ENDPOINTS.MISSIONS}/${id}/stats`);
  }
}