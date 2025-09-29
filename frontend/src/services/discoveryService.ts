/**
 * Discovery Service
 *
 * Service for managing discoveries and detections with backend integration.
 */

import { apiService } from './api';
import { API_ENDPOINTS } from '../types';
import { Discovery, CreateDiscoveryRequest, UpdateDiscoveryRequest } from '../types/discovery';

export class DiscoveryService {
  /**
   * Get all discoveries
   */
  static async getDiscoveries(params?: {
    mission_id?: number;
    drone_id?: number;
    discovery_type?: string;
    priority?: string;
    is_verified?: boolean;
  }) {
    return apiService.get<Discovery[]>(API_ENDPOINTS.DISCOVERIES, params);
  }

  /**
   * Get discovery by ID
   */
  static async getDiscovery(id: number) {
    return apiService.get<Discovery>(`${API_ENDPOINTS.DISCOVERIES}/${id}`);
  }

  /**
   * Create new discovery
   */
  static async createDiscovery(discoveryData: CreateDiscoveryRequest) {
    return apiService.post<Discovery>(API_ENDPOINTS.DISCOVERIES, discoveryData);
  }

  /**
   * Update existing discovery
   */
  static async updateDiscovery(id: number, discoveryData: Partial<UpdateDiscoveryRequest>) {
    return apiService.put<Discovery>(`${API_ENDPOINTS.DISCOVERIES}/${id}`, discoveryData);
  }

  /**
   * Delete discovery
   */
  static async deleteDiscovery(id: number) {
    return apiService.delete<void>(`${API_ENDPOINTS.DISCOVERIES}/${id}`);
  }

  /**
   * Verify discovery
   */
  static async verifyDiscovery(id: number, verifiedBy: string, notes?: string) {
    return apiService.post<Discovery>(`${API_ENDPOINTS.DISCOVERIES}/${id}/verify`, {
      verified_by: verifiedBy,
      verification_notes: notes,
    });
  }

  /**
   * Get discovery evidence
   */
  static async getEvidence(id: number) {
    return apiService.get<any>(`${API_ENDPOINTS.DISCOVERIES}/${id}/evidence`);
  }

  /**
   * Get discoveries by mission
   */
  static async getByMission(missionId: number) {
    return apiService.get<Discovery[]>(API_ENDPOINTS.DISCOVERIES, { mission_id: missionId });
  }

  /**
   * Get discoveries by drone
   */
  static async getByDrone(droneId: number) {
    return apiService.get<Discovery[]>(API_ENDPOINTS.DISCOVERIES, { drone_id: droneId });
  }
}