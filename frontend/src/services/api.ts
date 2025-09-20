// API Service Layer
import { 
  ApiResponse, 
  PaginatedResponse,
  CreateMissionRequest,
  UpdateMissionRequest,
  MissionListRequest,
  RegisterDroneRequest,
  DroneListRequest,
  CreateChatSessionRequest,
  SendMessageRequest,
  SystemStatus
} from '../types/api';
import { Mission } from '../types/mission';
import { Drone } from '../types/drone';
import { Discovery } from '../types/discovery';

const API_BASE_URL = '/api/v1';

class ApiService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
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

  // Mission API Methods
  async createMission(data: CreateMissionRequest): Promise<ApiResponse<Mission>> {
    return this.request<Mission>('/missions/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMissions(params?: MissionListRequest): Promise<ApiResponse<PaginatedResponse<Mission>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return this.request<PaginatedResponse<Mission>>(`/missions/${query ? `?${query}` : ''}`);
  }

  async getMission(id: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}`);
  }

  async updateMission(id: string, data: UpdateMissionRequest): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async startMission(id: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}/start`, {
      method: 'POST',
    });
  }

  async pauseMission(id: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}/pause`, {
      method: 'POST',
    });
  }

  async resumeMission(id: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}/resume`, {
      method: 'POST',
    });
  }

  async abortMission(id: string, reason?: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${id}/abort`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async deleteMission(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/missions/${id}`, {
      method: 'DELETE',
    });
  }

  // Drone API Methods
  async registerDrone(data: RegisterDroneRequest): Promise<ApiResponse<Drone>> {
    return this.request<Drone>('/drones/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getDrones(params?: DroneListRequest): Promise<ApiResponse<PaginatedResponse<Drone>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return this.request<PaginatedResponse<Drone>>(`/drones/${query ? `?${query}` : ''}`);
  }

  async getDrone(id: string): Promise<ApiResponse<Drone>> {
    return this.request<Drone>(`/drones/${id}`);
  }

  async discoverDrones(): Promise<ApiResponse<any>> {
    return this.request<any>('/drones/discover', {
      method: 'POST',
    });
  }

  // Chat API Methods
  async createChatSession(data: CreateChatSessionRequest): Promise<ApiResponse<any>> {
    return this.request<any>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async sendMessage(sessionId: string, data: SendMessageRequest): Promise<ApiResponse<any>> {
    return this.request<any>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getChatSession(sessionId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/chat/sessions/${sessionId}`);
  }

  async generateMissionFromChat(sessionId: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/chat/sessions/${sessionId}/generate-mission`, {
      method: 'POST',
    });
  }

  // Discovery API Methods
  async getDiscoveries(missionId?: string): Promise<ApiResponse<Discovery[]>> {
    const endpoint = missionId 
      ? `/missions/${missionId}/discoveries` 
      : '/discoveries/';
    return this.request<Discovery[]>(endpoint);
  }

  // System API Methods
  async getSystemStatus(): Promise<ApiResponse<SystemStatus>> {
    return this.request<SystemStatus>('/system/status');
  }
}

export const apiService = new ApiService();
export default apiService;