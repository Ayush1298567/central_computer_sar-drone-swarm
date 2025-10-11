import { apiClient } from './api';
import { Mission, ChatMessage } from '../types';

export const missionService = {
  // Create a new mission
  async create(missionData: Partial<Mission>): Promise<Mission> {
    const response = await apiClient.post<any>('/missions', missionData);
    return response;
  },

  // Get all missions
  async list(): Promise<Mission[]> {
    const response = await apiClient.get<any>('/missions');
    return response;
  },

  // Get mission by ID (using mission_id string)
  async get(missionId: string): Promise<Mission> {
    const response = await apiClient.get<any>(`/missions/${missionId}`);
    return response;
  },

  // Start mission
  async start(missionId: string): Promise<void> {
    await apiClient.put(`/missions/${missionId}/start`);
  },

  // Pause mission
  async pause(missionId: string): Promise<void> {
    await apiClient.put(`/missions/${missionId}/pause`);
  },

  // Resume mission
  async resume(missionId: string): Promise<void> {
    await apiClient.put(`/missions/${missionId}/resume`);
  },

  // Complete mission
  async complete(missionId: string, success: boolean = true): Promise<void> {
    await apiClient.put(`/missions/${missionId}/complete?success=${success}`);
  },

  // Get chat history
  async getChatHistory(missionId: number): Promise<ChatMessage[]> {
    const response = await apiClient.get<any>(`/missions/${missionId}/chat`);
    return response.messages;
  },
};
