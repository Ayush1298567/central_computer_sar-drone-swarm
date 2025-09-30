import { ApiResponse, Mission, ChatResponse, Drone, Discovery } from '../types/api'

// API client configuration
const API_BASE = '/api'

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE}${endpoint}`

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Mission API methods
  async getMissions(): Promise<ApiResponse<Mission[]>> {
    return this.request<Mission[]>('/missions')
  }

  async getMission(missionId: string): Promise<ApiResponse<Mission>> {
    return this.request<Mission>(`/missions/${missionId}`)
  }

  async createMission(missionData: Partial<Mission>): Promise<ApiResponse<Mission>> {
    return this.request<Mission>('/missions/create', {
      method: 'POST',
      body: JSON.stringify(missionData),
    })
  }

  async startMission(missionId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/missions/${missionId}/start`, {
      method: 'PUT',
    })
  }

  // Chat API methods
  async sendChatMessage(messageData: {
    message: string
    conversation_id: string
    mission_id?: string
  }): Promise<ApiResponse<ChatResponse>> {
    return this.request<ChatResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify(messageData),
    })
  }

  async getChatSession(conversationId: string): Promise<ApiResponse<any>> {
    return this.request(`/chat/sessions/${conversationId}`)
  }

  // Drone API methods
  async getDrones(): Promise<ApiResponse<Drone[]>> {
    return this.request<Drone[]>('/drones')
  }

  async getDrone(droneId: string): Promise<ApiResponse<Drone>> {
    return this.request<Drone>(`/drones/${droneId}`)
  }

  async createDrone(droneData: Partial<Drone>): Promise<ApiResponse<Drone>> {
    return this.request<Drone>('/drones', {
      method: 'POST',
      body: JSON.stringify(droneData),
    })
  }

  // Discovery API methods
  async getDiscoveries(missionId?: string): Promise<ApiResponse<Discovery[]>> {
    const endpoint = missionId ? `/discoveries?mission_id=${missionId}` : '/discoveries'
    return this.request<Discovery[]>(endpoint)
  }

  async createDiscovery(discoveryData: Partial<Discovery>): Promise<ApiResponse<Discovery>> {
    return this.request<Discovery>('/discoveries', {
      method: 'POST',
      body: JSON.stringify(discoveryData),
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()
export default apiClient