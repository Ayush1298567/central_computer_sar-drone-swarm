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
  static async getDrone(id: number) {
    return apiService.get<Drone>(`${API_ENDPOINTS.DRONES}/${id}`);
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
  static async updateDrone(id: number, droneData: Partial<UpdateDroneRequest>) {
    return apiService.put<Drone>(`${API_ENDPOINTS.DRONES}/${id}`, droneData);
  }

  /**
   * Delete drone
   */
  static async deleteDrone(id: number) {
    return apiService.delete<void>(`${API_ENDPOINTS.DRONES}/${id}`);
  }

  /**
   * Assign drone to mission
   */
  static async assignToMission(droneId: number, missionId: number) {
    return apiService.post<Drone>(`${API_ENDPOINTS.DRONES}/${droneId}/assign`, { mission_id: missionId });
  }

  /**
   * Return drone to base
   */
  static async returnToBase(id: number) {
    return apiService.post<Drone>(`${API_ENDPOINTS.DRONES}/${id}/return`, {});
  }

  /**
   * Get drone telemetry
   */
  static async getTelemetry(id: number) {
    return apiService.get<any>(`${API_ENDPOINTS.DRONES}/${id}/telemetry`);
  }

  /**
   * Send command to drone
   */
  static async sendCommand(id: number, command: string, params?: Record<string, any>) {
    return apiService.post<any>(`${API_ENDPOINTS.DRONES}/${id}/command`, { command, params });
  }

  /**
   * Get drone telemetry data
   */
  static async getDroneTelemetry(id: number) {
    return apiService.get<any>(`${API_ENDPOINTS.DRONES}/${id}/telemetry`);
  }

  /**
   * Get drone telemetry data by drone ID string
   */
  static async getDroneTelemetryByString(id: string) {
    return apiService.get<any>(`${API_ENDPOINTS.DRONES}/${id}/telemetry`);
  }

  /**
   * Update drone status and data
   */
  static async updateDrone(id: number, updates: Partial<UpdateDroneRequest>) {
    return apiService.put<Drone>(`${API_ENDPOINTS.DRONES}/${id}`, updates);
  }

  /**
   * Update drone status and data by string ID
   */
  static async updateDroneByString(id: string, updates: Partial<UpdateDroneRequest>) {
    return apiService.put<Drone>(`${API_ENDPOINTS.DRONES}/${id}`, updates);
  }
}