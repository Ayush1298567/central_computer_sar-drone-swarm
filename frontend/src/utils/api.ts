/**
 * API utility functions for making HTTP requests to the backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Types
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
}

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const config: RequestInit = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<T> = await response.json();

      if (!data.success) {
        throw new Error(data.error || data.message || 'API request failed');
      }

      return data.data as T;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // GET request
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = params
      ? `${endpoint}?${new URLSearchParams(params).toString()}`
      : endpoint;

    return this.request<T>(url);
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // File upload
  async uploadFile<T>(endpoint: string, file: File, fieldName: string = 'file'): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const formData = new FormData();
    formData.append(fieldName, file);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse<T> = await response.json();

      if (!data.success) {
        throw new Error(data.error || data.message || 'File upload failed');
      }

      return data.data as T;
    } catch (error) {
      console.error(`File upload failed: ${endpoint}`, error);
      throw error;
    }
  }
}

// Create and export a default API client instance
export const apiClient = new ApiClient();

// Export the class for custom instances if needed
export { ApiClient };

// Export apiService as an alias for backward compatibility
export const apiService = apiClient;

// Convenience functions for common API endpoints
export const api = {
  // Missions
  missions: {
    getAll: (params?: { skip?: number; limit?: number; status?: string }) =>
      apiClient.get('/missions', params),

    getById: (id: number) =>
      apiClient.get(`/missions/${id}`),

    create: (missionData: any) =>
      apiClient.post('/missions', missionData),

    update: (id: number, missionData: any) =>
      apiClient.put(`/missions/${id}`, missionData),

    delete: (id: number) =>
      apiClient.delete(`/missions/${id}`),

    start: (id: number) =>
      apiClient.post(`/missions/${id}/start`),

    complete: (id: number) =>
      apiClient.post(`/missions/${id}/complete`),

    getDrones: (id: number) =>
      apiClient.get(`/missions/${id}/drones`),

    getDiscoveries: (id: number) =>
      apiClient.get(`/missions/${id}/discoveries`),
  },

  // Drones
  drones: {
    getAll: (params?: { skip?: number; limit?: number; status?: string }) =>
      apiClient.get('/drones', params),

    getById: (id: number) =>
      apiClient.get(`/drones/${id}`),

    create: (droneData: any) =>
      apiClient.post('/drones', droneData),

    update: (id: number, droneData: any) =>
      apiClient.put(`/drones/${id}`, droneData),

    delete: (id: number) =>
      apiClient.delete(`/drones/${id}`),

    connect: (id: number) =>
      apiClient.post(`/drones/${id}/connect`),

    disconnect: (id: number) =>
      apiClient.post(`/drones/${id}/disconnect`),

    getTelemetry: (id: number) =>
      apiClient.get(`/drones/${id}/telemetry`),

    sendCommand: (id: number, command: any) =>
      apiClient.post(`/drones/${id}/command`, command),
  },

  // Discoveries
  discoveries: {
    getAll: (params?: { skip?: number; limit?: number; mission_id?: number; status?: string }) =>
      apiClient.get('/discoveries', params),

    getById: (id: number) =>
      apiClient.get(`/discoveries/${id}`),

    create: (discoveryData: any) =>
      apiClient.post('/discoveries', discoveryData),

    update: (id: number, discoveryData: any) =>
      apiClient.put(`/discoveries/${id}`, discoveryData),

    delete: (id: number) =>
      apiClient.delete(`/discoveries/${id}`),

    investigate: (id: number) =>
      apiClient.post(`/discoveries/${id}/investigate`),

    resolve: (id: number, resolution: any) =>
      apiClient.post(`/discoveries/${id}/resolve`, resolution),

    uploadMedia: (id: number, mediaType: string, file: File) =>
      apiClient.uploadFile(`/discoveries/${id}/upload-media?media_type=${mediaType}`, file),

    getMedia: (id: number, mediaType: string) =>
      apiClient.get(`/discoveries/${id}/media/${mediaType}`),
  },

  // Chat
  chat: {
    getMessages: (params?: { mission_id?: number; skip?: number; limit?: number }) =>
      apiClient.get('/chat/messages', params),

    getMessage: (id: number) =>
      apiClient.get(`/chat/messages/${id}`),

    createMessage: (messageData: any) =>
      apiClient.post('/chat/messages', messageData),

    converse: (missionId: number, userMessage: string) =>
      apiClient.post('/chat/converse', { mission_id: missionId, user_message: userMessage }),

    startPlanning: () =>
      apiClient.post('/chat/plan-mission'),

    getPlanningProgress: (missionId: number) =>
      apiClient.get(`/chat/mission/${missionId}/planning-progress`),

    approvePlan: (missionId: number) =>
      apiClient.post(`/chat/mission/${missionId}/approve`),
  },

  // WebSocket connections
  websocket: {
    mission: (missionId: number) =>
      `ws://localhost:8000/api/v1/ws/mission/${missionId}`,

    drone: (droneId: number) =>
      `ws://localhost:8000/api/v1/ws/drone/${droneId}`,

    system: () =>
      `ws://localhost:8000/api/v1/ws/system`,
  },

  // Mission replay
  getMissionReplay: (missionId: string) =>
    apiClient.get(`/missions/${missionId}/replay`),

  // Report generation
  generateReport: (params: any) =>
    apiClient.post('/reports/generate', params),
};