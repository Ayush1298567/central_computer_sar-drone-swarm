import { apiService } from './api'
import {
  MissionCreateRequest,
  MissionUpdateRequest,
  MissionExecutionRequest,
  ListOptions,
  ApiResponse,
} from '@/types'

class MissionService {
  private readonly endpoint = '/missions'

  /**
   * Get paginated list of missions
   */
  async getMissions(options: ListOptions = {}): Promise<{ data: any[]; pagination: any }> {
    const params = {
      page: options.page || 1,
      limit: options.limit || 20,
      sort_by: options.sort_by || 'created_at',
      sort_order: options.sort_order || 'desc',
      search: options.search,
      ...options.filters,
    }

    return apiService.get<{ data: any[]; pagination: any }>(this.endpoint, { params })
  }

  /**
   * Get single mission by ID
   */
  async getMissionById(missionId: string): Promise<any> {
    return apiService.get<any>(`${this.endpoint}/${missionId}`)
  }

  /**
   * Create new mission
   */
  async createMission(missionData: MissionCreateRequest): Promise<any> {
    return apiService.post<any>(this.endpoint, missionData)
  }

  /**
   * Update existing mission
   */
  async updateMission(missionId: string, updates: MissionUpdateRequest): Promise<any> {
    return apiService.put<any>(`${this.endpoint}/${missionId}`, updates)
  }

  /**
   * Delete mission
   */
  async deleteMission(missionId: string): Promise<ApiResponse> {
    return apiService.delete<ApiResponse>(`${this.endpoint}/${missionId}`)
  }

  /**
   * Start mission execution
   */
  async startMission(request: MissionExecutionRequest): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${request.mission_id}/start`, request)
  }

  /**
   * Pause mission
   */
  async pauseMission(missionId: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${missionId}/pause`)
  }

  /**
   * Resume mission
   */
  async resumeMission(missionId: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${missionId}/resume`)
  }

  /**
   * Cancel mission
   */
  async cancelMission(missionId: string, reason?: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${missionId}/cancel`, { reason })
  }

  /**
   * Get mission statistics
   */
  async getMissionStats(missionId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${missionId}/stats`)
  }

  /**
   * Get active missions
   */
  async getActiveMissions(): Promise<{ data: any[]; pagination: any }> {
    return apiService.get<{ data: any[]; pagination: any }>(`${this.endpoint}/active`)
  }

  /**
   * Get missions by status
   */
  async getMissionsByStatus(status: string): Promise<{ data: any[]; pagination: any }> {
    return apiService.get<{ data: any[]; pagination: any }>(`${this.endpoint}/status/${status}`)
  }

  /**
   * Update mission search area
   */
  async updateSearchArea(missionId: string, searchArea: any): Promise<ApiResponse> {
    return apiService.put<ApiResponse>(`${this.endpoint}/${missionId}/search-area`, { search_area: searchArea })
  }

  /**
   * Assign drones to mission
   */
  async assignDrones(missionId: string, droneIds: string[]): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${missionId}/drones`, { drone_ids: droneIds })
  }

  /**
   * Remove drones from mission
   */
  async removeDrones(missionId: string, droneIds: string[]): Promise<ApiResponse> {
    return apiService.delete<ApiResponse>(`${this.endpoint}/${missionId}/drones`, {
      data: { drone_ids: droneIds }
    })
  }

  /**
   * Get mission timeline
   */
  async getMissionTimeline(missionId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${missionId}/timeline`)
  }

  /**
   * Export mission data
   */
  async exportMissionData(missionId: string, format: 'json' | 'geojson' | 'kml' = 'json'): Promise<Blob> {
    const response = await apiService.get(`${this.endpoint}/${missionId}/export`, {
      params: { format },
      responseType: 'blob',
    })
    return response as any
  }
}

// Export singleton instance
export const missionService = new MissionService()

// Export class for testing
export { MissionService }