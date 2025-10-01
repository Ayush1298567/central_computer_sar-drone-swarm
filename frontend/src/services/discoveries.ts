import { apiClient } from './api';
import { Discovery } from '../types';

export const discoveryService = {
  // Create a new discovery
  async create(discoveryData: Partial<Discovery>): Promise<Discovery> {
    const response = await apiClient.post<any>('/discoveries/create', discoveryData);
    return response.discovery;
  },

  // Get all discoveries
  async list(missionId?: number): Promise<Discovery[]> {
    const params = missionId ? { mission_id: missionId } : undefined;
    const response = await apiClient.get<any>('/discoveries/list', params);
    return response.discoveries;
  },

  // Get discovery by ID
  async get(discoveryId: number): Promise<Discovery> {
    const response = await apiClient.get<any>(`/discoveries/${discoveryId}`);
    return response.discovery;
  },

  // Update discovery
  async update(discoveryId: number, updates: Partial<Discovery>): Promise<Discovery> {
    const response = await apiClient.put<any>(`/discoveries/${discoveryId}`, updates);
    return response.discovery;
  },

  // Verify discovery
  async verify(discoveryId: number, verificationData: { operator_name: string; notes?: string }): Promise<Discovery> {
    const response = await apiClient.put<any>(`/discoveries/${discoveryId}/verify`, verificationData);
    return response.discovery;
  },

  // Delete discovery
  async delete(discoveryId: number): Promise<void> {
    await apiClient.delete(`/discoveries/${discoveryId}`);
  },
};
