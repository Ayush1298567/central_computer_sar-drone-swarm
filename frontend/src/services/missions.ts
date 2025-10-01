import { apiClient } from './api';
import { Mission, ChatMessage } from '../types';

export const missionService = {
  // Create a new mission
  async create(missionData: Partial<Mission>): Promise<Mission> {
    const response = await apiClient.post<any>('/missions/create', missionData);
    return response.mission;
  },

  // Get all missions
  async list(): Promise<Mission[]> {
    const response = await apiClient.get<any>('/missions/list');
    return response.missions;
  },

  // Get mission by ID
  async get(missionId: number): Promise<Mission> {
    const response = await apiClient.get<any>(`/missions/${missionId}`);
    return response.mission;
  },

  // Update mission
  async update(missionId: number, updates: Partial<Mission>): Promise<Mission> {
    const response = await apiClient.put<any>(`/missions/${missionId}`, updates);
    return response.mission;
  },

  // Start mission
  async start(missionId: number): Promise<Mission> {
    const response = await apiClient.put<any>(`/missions/${missionId}/start`);
    return response.mission;
  },

  // Pause mission
  async pause(missionId: number): Promise<void> {
    await apiClient.put(`/missions/${missionId}/pause`);
  },

  // Complete mission
  async complete(missionId: number): Promise<Mission> {
    const response = await apiClient.put<any>(`/missions/${missionId}/complete`);
    return response.mission;
  },

  // Delete mission
  async delete(missionId: number): Promise<void> {
    await apiClient.delete(`/missions/${missionId}`);
  },

  // Get chat history
  async getChatHistory(missionId: number): Promise<ChatMessage[]> {
    const response = await apiClient.get<any>(`/missions/${missionId}/chat`);
    return response.messages;
  },
};
