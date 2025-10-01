import { apiClient } from './api';
import { Drone, TelemetryData } from '../types';

export const droneService = {
  // Register a new drone
  async register(droneData: Partial<Drone>): Promise<Drone> {
    const response = await apiClient.post<any>('/drones/register', droneData);
    return response.drone;
  },

  // Get all drones
  async list(): Promise<Drone[]> {
    const response = await apiClient.get<any>('/drones/list');
    return response.drones;
  },

  // Get drone by ID
  async get(droneId: number): Promise<Drone> {
    const response = await apiClient.get<any>(`/drones/${droneId}`);
    return response.drone;
  },

  // Update drone
  async update(droneId: number, updates: Partial<Drone>): Promise<Drone> {
    const response = await apiClient.put<any>(`/drones/${droneId}`, updates);
    return response.drone;
  },

  // Update telemetry
  async updateTelemetry(droneId: number, telemetry: Partial<TelemetryData>): Promise<void> {
    await apiClient.post(`/drones/${droneId}/telemetry`, telemetry);
  },

  // Get telemetry history
  async getTelemetry(droneId: number, limit: number = 100): Promise<TelemetryData[]> {
    const response = await apiClient.get<any>(`/drones/${droneId}/telemetry`, { limit });
    return response.telemetry;
  },

  // Delete drone
  async delete(droneId: number): Promise<void> {
    await apiClient.delete(`/drones/${droneId}`);
  },
};
