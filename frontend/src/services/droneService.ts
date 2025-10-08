/**
 * Drone Service
 *
 * Service for managing drone operations with backend integration.
 */

import { apiService } from './api';
import { API_ENDPOINTS } from '../types';
import { Drone, CreateDroneRequest, UpdateDroneRequest } from '../types/drone';

export class DroneService {
  /**
   * Get all drones
   */
  static async getDrones(params?: { status?: string; mission_id?: number }) {
    return apiService.get<Drone[]>(API_ENDPOINTS.DRONES, params);
  }

  /**
   * Get drone by ID
   */
  static async getDrone(droneId: string) {
    return apiService.get<Drone>(`${API_ENDPOINTS.DRONES}/${droneId}`);
  }

  /**
   * Create new drone
   */
  static async createDrone(droneData: CreateDroneRequest) {
    return apiService.post<Drone>(API_ENDPOINTS.DRONES, droneData);
  }

  /**
   * Update existing drone
   */
  static async updateDrone(droneId: string, droneData: Partial<UpdateDroneRequest>) {
    return apiService.put<Drone>(`${API_ENDPOINTS.DRONES}/${droneId}`, droneData);
  }

  /**
   * Delete drone
   */
  static async deleteDrone(droneId: string) {
    return apiService.delete<void>(`${API_ENDPOINTS.DRONES}/${droneId}`);
  }

  /**
   * Get drone status
   */
  static async getDroneStatus(droneId: string) {
    return apiService.get<any>(`${API_ENDPOINTS.DRONES}/${droneId}/status`);
  }
}