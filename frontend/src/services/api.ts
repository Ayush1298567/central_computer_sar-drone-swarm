import { Mission } from '../types/mission';
import { Drone, DroneCommand, DroneTelemetry } from '../types/drone';
import { ChatSession, ChatMessage, PlanningProgress } from '../types/chat';

const API_BASE = '/api/v1';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Mission API
  async getMissions(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ missions: Mission[]; total: number }> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/missions/?${query}`);
  }

  async getMission(id: string): Promise<Mission> {
    return this.request(`/missions/${id}`);
  }

  async createMission(mission: Partial<Mission>): Promise<Mission> {
    return this.request('/missions/', {
      method: 'POST',
      body: JSON.stringify(mission),
    });
  }

  async updateMission(id: string, updates: Partial<Mission>): Promise<Mission> {
    return this.request(`/missions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async startMission(id: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/missions/${id}/start`, { method: 'POST' });
  }

  async pauseMission(id: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/missions/${id}/pause`, { method: 'POST' });
  }

  async resumeMission(id: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/missions/${id}/resume`, { method: 'POST' });
  }

  async abortMission(id: string, reason?: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/missions/${id}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // Drone API
  async getDrones(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ drones: Drone[]; total: number }> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/drones/?${query}`);
  }

  async getDrone(id: string): Promise<Drone> {
    return this.request(`/drones/${id}`);
  }

  async discoverDrones(): Promise<{ discovered: Drone[]; message: string }> {
    return this.request('/drones/discover', { method: 'POST' });
  }

  async sendDroneCommand(droneId: string, command: Partial<DroneCommand>): Promise<DroneCommand> {
    return this.request(`/drones/${droneId}/command`, {
      method: 'POST',
      body: JSON.stringify(command),
    });
  }

  async getDroneTelemetry(droneId: string): Promise<DroneTelemetry[]> {
    return this.request(`/drones/${droneId}/telemetry`);
  }

  async emergencyStopDrone(droneId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/drones/${droneId}/emergency-stop`, { method: 'POST' });
  }

  // Chat API
  async getChatSessions(): Promise<{ sessions: ChatSession[]; total: number }> {
    return this.request('/chat/sessions');
  }

  async createChatSession(name: string): Promise<ChatSession> {
    return this.request('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getChatMessages(sessionId: string): Promise<{ messages: ChatMessage[]; total: number }> {
    return this.request(`/chat/sessions/${sessionId}`);
  }

  async sendChatMessage(
    sessionId: string,
    content: string,
    attachments?: File[]
  ): Promise<ChatMessage> {
    const formData = new FormData();
    formData.append('content', content);
    
    if (attachments) {
      attachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file);
      });
    }

    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getPlanningProgress(sessionId: string): Promise<PlanningProgress> {
    return this.request(`/chat/sessions/${sessionId}/progress`);
  }

  async generateMissionFromChat(sessionId: string): Promise<Mission> {
    return this.request(`/chat/sessions/${sessionId}/generate-mission`, {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();