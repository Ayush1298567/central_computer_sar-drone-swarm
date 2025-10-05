import { apiClient } from './api';
import { Drone, TelemetryData } from '../types';

export const droneService = {
  // Create a new drone
  async create(droneData: Partial<Drone>): Promise<Drone> {
    const response = await apiClient.post<any>('/drones', droneData);
    return response;
  },

  // Get all drones
  async list(): Promise<Drone[]> {
    const response = await apiClient.get<any>('/drones');
    return response;
  },

  // Get drone by ID (using drone_id string)
  async get(droneId: string): Promise<Drone> {
    const response = await apiClient.get<any>(`/drones/${droneId}`);
    return response;
  },

  // Update drone
  async update(droneId: string, updates: Partial<Drone>): Promise<Drone> {
    const response = await apiClient.put<any>(`/drones/${droneId}`, updates);
    return response;
  },

  // Delete drone
  async delete(droneId: string): Promise<void> {
    await apiClient.delete(`/drones/${droneId}`);
  },
};
