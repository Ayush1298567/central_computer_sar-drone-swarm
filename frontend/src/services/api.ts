import axios, { AxiosInstance } from 'axios';
import { 
  Mission, 
  Drone, 
  ChatSession, 
  ChatMessage, 
  DroneTelemetry
} from '../types';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth tokens
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Mission API methods
  async getMissions(params?: { 
    status?: string; 
    limit?: number; 
    offset?: number; 
  }): Promise<Mission[]> {
    const response = await this.client.get('/missions/', { params });
    return response.data;
  }

  async getMission(id: string): Promise<Mission> {
    const response = await this.client.get(`/missions/${id}`);
    return response.data;
  }

  async createMission(mission: Partial<Mission>): Promise<Mission> {
    const response = await this.client.post('/missions/', mission);
    return response.data;
  }

  async updateMission(id: string, updates: Partial<Mission>): Promise<Mission> {
    const response = await this.client.patch(`/missions/${id}`, updates);
    return response.data;
  }

  async startMission(id: string): Promise<Mission> {
    const response = await this.client.post(`/missions/${id}/start`);
    return response.data;
  }

  async pauseMission(id: string): Promise<Mission> {
    const response = await this.client.post(`/missions/${id}/pause`);
    return response.data;
  }

  async resumeMission(id: string): Promise<Mission> {
    const response = await this.client.post(`/missions/${id}/resume`);
    return response.data;
  }

  async abortMission(id: string, reason: string): Promise<Mission> {
    const response = await this.client.post(`/missions/${id}/abort`, { reason });
    return response.data;
  }

  async deleteMission(id: string): Promise<void> {
    await this.client.delete(`/missions/${id}`);
  }

  // Drone API methods
  async discoverDrones(): Promise<Drone[]> {
    const response = await this.client.post('/drones/discover');
    return response.data;
  }

  async registerDrone(drone: Partial<Drone>): Promise<Drone> {
    const response = await this.client.post('/drones/register', drone);
    return response.data;
  }

  async getDrones(params?: { 
    status?: string; 
    limit?: number; 
    offset?: number; 
  }): Promise<Drone[]> {
    const response = await this.client.get('/drones/', { params });
    return response.data;
  }

  async getDrone(id: string): Promise<Drone> {
    const response = await this.client.get(`/drones/${id}`);
    return response.data;
  }

  async updateDrone(id: string, updates: Partial<Drone>): Promise<Drone> {
    const response = await this.client.patch(`/drones/${id}`, updates);
    return response.data;
  }

  async getDroneStatus(id: string): Promise<any> {
    const response = await this.client.get(`/drones/${id}/status`);
    return response.data;
  }

  async submitDroneTelemetry(id: string, telemetry: DroneTelemetry): Promise<void> {
    await this.client.post(`/drones/${id}/telemetry`, telemetry);
  }

  async getDroneTelemetry(id: string, params?: { 
    start_time?: string; 
    end_time?: string; 
    limit?: number; 
  }): Promise<DroneTelemetry[]> {
    const response = await this.client.get(`/drones/${id}/telemetry`, { params });
    return response.data;
  }

  async performDroneHealthCheck(id: string): Promise<any> {
    const response = await this.client.post(`/drones/${id}/health`);
    return response.data;
  }

  async sendDroneCommand(id: string, command: any): Promise<any> {
    const response = await this.client.post(`/drones/${id}/command`, command);
    return response.data;
  }

  async emergencyStopDrone(id: string): Promise<void> {
    await this.client.post(`/drones/${id}/emergency-stop`);
  }

  async getDroneDiagnostics(id: string): Promise<any> {
    const response = await this.client.get(`/drones/${id}/diagnostics`);
    return response.data;
  }

  async unregisterDrone(id: string): Promise<void> {
    await this.client.delete(`/drones/${id}`);
  }

  // Chat API methods
  async createChatSession(name: string): Promise<ChatSession> {
    const response = await this.client.post('/chat/sessions', { name });
    return response.data;
  }

  async getChatSessions(): Promise<ChatSession[]> {
    const response = await this.client.get('/chat/sessions');
    return response.data;
  }

  async getChatSession(id: string): Promise<ChatSession> {
    const response = await this.client.get(`/chat/sessions/${id}`);
    return response.data;
  }

  async sendChatMessage(sessionId: string, content: string, attachments?: File[]): Promise<ChatMessage> {
    const formData = new FormData();
    formData.append('content', content);
    
    if (attachments) {
      attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file);
      });
    }

    const response = await this.client.post(
      `/chat/sessions/${sessionId}/messages`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getChatProgress(sessionId: string): Promise<any> {
    const response = await this.client.get(`/chat/sessions/${sessionId}/progress`);
    return response.data;
  }

  async generateMissionFromChat(sessionId: string): Promise<Mission> {
    const response = await this.client.post(`/chat/sessions/${sessionId}/generate-mission`);
    return response.data;
  }

  async updateChatSessionStatus(sessionId: string, status: string): Promise<ChatSession> {
    const response = await this.client.patch(`/chat/sessions/${sessionId}/status`, { status });
    return response.data;
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    await this.client.delete(`/chat/sessions/${sessionId}`);
  }

  async exportChatSession(sessionId: string): Promise<Blob> {
    const response = await this.client.get(`/chat/sessions/${sessionId}/export`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // WebSocket connection info
  async getWebSocketConnections(): Promise<any> {
    const response = await this.client.get('/ws/connections');
    return response.data;
  }

  async broadcastWebSocketMessage(message: any): Promise<void> {
    await this.client.post('/ws/broadcast', message);
  }
}

export const apiService = new APIService();
export default apiService;