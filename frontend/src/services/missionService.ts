/**
 * Mission service for SAR Mission Commander
 */
import { api, handleApiError } from './api';

export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';
  mission_type: 'search' | 'rescue' | 'survey' | 'training';
  priority: 'low' | 'medium' | 'high' | 'critical';
  center_latitude?: number;
  center_longitude?: number;
  altitude?: number;
  radius?: number;
  search_area?: any;
  weather_conditions?: any;
  time_limit_minutes?: number;
  max_drones?: number;
  discoveries_found?: number;
  area_covered?: number;
  created_at: string;
  updated_at: string;
  start_time?: string;
  end_time?: string;
  chat_session_id?: string;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  content: string;
  message_type: 'text' | 'system' | 'ai_response' | 'user_input';
  timestamp: string;
  user_id?: string;
  ai_confidence?: number;
  ai_model_used?: string;
}

export interface ChatSession {
  session_id: string;
  messages: ChatMessage[];
  current_stage: string;
}

export interface CreateMissionData {
  name: string;
  description?: string;
  mission_type?: string;
  priority?: string;
  center_latitude?: number;
  center_longitude?: number;
  altitude?: number;
  radius?: number;
  search_area?: any;
  weather_conditions?: any;
  time_limit_minutes?: number;
  max_drones?: number;
}

export interface ChatMessageData {
  content: string;
  message_type?: string;
  user_id?: string;
}

/**
 * Mission API functions
 */
export const missionService = {
  /**
   * Get all missions
   */
  async getMissions(): Promise<Mission[]> {
    try {
      const response = await api.get('/missions/');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get a specific mission
   */
  async getMission(missionId: string): Promise<Mission> {
    try {
      const response = await api.get(`/missions/${missionId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Create a new mission
   */
  async createMission(missionData: CreateMissionData): Promise<Mission> {
    try {
      const response = await api.post('/missions/', missionData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Update a mission
   */
  async updateMission(missionId: string, missionData: Partial<CreateMissionData>): Promise<Mission> {
    try {
      const response = await api.put(`/missions/${missionId}`, missionData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Delete a mission
   */
  async deleteMission(missionId: string): Promise<void> {
    try {
      await api.delete(`/missions/${missionId}`);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Start a mission
   */
  async startMission(missionId: string): Promise<Mission> {
    try {
      const response = await api.post(`/missions/${missionId}/start`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Complete a mission
   */
  async completeMission(missionId: string): Promise<Mission> {
    try {
      const response = await api.post(`/missions/${missionId}/complete`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get chat messages for a mission
   */
  async getMissionChat(missionId: string): Promise<ChatSession> {
    try {
      const response = await api.get(`/missions/${missionId}/chat`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Send a chat message for a mission
   */
  async sendMissionChatMessage(missionId: string, messageData: ChatMessageData): Promise<any> {
    try {
      const response = await api.post(`/missions/${missionId}/chat`, messageData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
};

export default missionService;