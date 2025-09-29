import { apiService } from './api'
import {
  DroneUpdateRequest,
  DroneCommandRequest,
  ListOptions,
  ApiResponse,
} from '@/types'

class DroneService {
  private readonly endpoint = '/drones'

  /**
   * Get paginated list of drones
   */
  async getDrones(options: ListOptions = {}): Promise<{ data: any[]; pagination: any }> {
    const params = {
      page: options.page || 1,
      limit: options.limit || 20,
      sort_by: options.sort_by || 'name',
      sort_order: options.sort_order || 'asc',
      search: options.search,
      ...options.filters,
    }

    return apiService.get<{ data: any[]; pagination: any }>(this.endpoint, { params })
  }

  /**
   * Get single drone by ID
   */
  async getDroneById(droneId: string): Promise<any> {
    return apiService.get<any>(`${this.endpoint}/${droneId}`)
  }

  /**
   * Get drone by drone_id (not database ID)
   */
  async getDroneByDroneId(droneId: string): Promise<any> {
    return apiService.get<any>(`${this.endpoint}/by-id/${droneId}`)
  }

  /**
   * Update drone information
   */
  async updateDrone(droneId: string, updates: DroneUpdateRequest): Promise<any> {
    return apiService.put<any>(`${this.endpoint}/${droneId}`, updates)
  }

  /**
   * Update drone position
   */
  async updateDronePosition(droneId: string, position: { lat: number; lng: number; alt: number }): Promise<ApiResponse> {
    return apiService.patch<ApiResponse>(`${this.endpoint}/${droneId}/position`, position)
  }

  /**
   * Send command to drone
   */
  async sendDroneCommand(command: DroneCommandRequest): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/command`, command)
  }

  /**
   * Get drone telemetry data
   */
  async getDroneTelemetry(droneId: string, timeRange?: { start: string; end: string }): Promise<ApiResponse> {
    const params = timeRange ? { start: timeRange.start, end: timeRange.end } : {}
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/telemetry`, { params })
  }

  /**
   * Get available drones for mission assignment
   */
  async getAvailableDrones(): Promise<{ data: any[]; pagination: any }> {
    return apiService.get<{ data: any[]; pagination: any }>(`${this.endpoint}/available`)
  }

  /**
   * Get drones by status
   */
  async getDronesByStatus(status: string): Promise<{ data: any[]; pagination: any }> {
    return apiService.get<{ data: any[]; pagination: any }>(`${this.endpoint}/status/${status}`)
  }

  /**
   * Get drone capabilities
   */
  async getDroneCapabilities(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/capabilities`)
  }

  /**
   * Update drone capabilities
   */
  async updateDroneCapabilities(droneId: string, capabilities: any): Promise<ApiResponse> {
    return apiService.put<ApiResponse>(`${this.endpoint}/${droneId}/capabilities`, capabilities)
  }

  /**
   * Get drone maintenance history
   */
  async getMaintenanceHistory(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/maintenance`)
  }

  /**
   * Schedule drone maintenance
   */
  async scheduleMaintenance(droneId: string, maintenanceData: {
    type: string
    scheduled_date: string
    description: string
    estimated_duration: number
  }): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${droneId}/maintenance`, maintenanceData)
  }

  /**
   * Get drone mission history
   */
  async getMissionHistory(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/missions`)
  }

  /**
   * Get drone battery status
   */
  async getBatteryStatus(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/battery`)
  }

  /**
   * Get drone communication status
   */
  async getCommunicationStatus(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/communication`)
  }

  /**
   * Emergency stop drone
   */
  async emergencyStop(droneId: string, reason: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${droneId}/emergency-stop`, { reason })
  }

  /**
   * Return drone to home
   */
  async returnToHome(droneId: string): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${droneId}/return-home`)
  }

  /**
   * Get drone sensor data
   */
  async getSensorData(droneId: string, sensorType?: string): Promise<ApiResponse> {
    const params = sensorType ? { sensor_type: sensorType } : {}
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/sensors`, { params })
  }

  /**
   * Calibrate drone sensors
   */
  async calibrateSensors(droneId: string, sensorTypes: string[]): Promise<ApiResponse> {
    return apiService.post<ApiResponse>(`${this.endpoint}/${droneId}/calibrate`, { sensor_types: sensorTypes })
  }

  /**
   * Get drone firmware information
   */
  async getFirmwareInfo(droneId: string): Promise<ApiResponse> {
    return apiService.get<ApiResponse>(`${this.endpoint}/${droneId}/firmware`)
  }

  /**
   * Update drone firmware
   */
  async updateFirmware(droneId: string, firmwareData: {
    version: string
    firmware_file: File
  }): Promise<ApiResponse> {
    const formData = new FormData()
    formData.append('version', firmwareData.version)
    formData.append('firmware_file', firmwareData.firmware_file)

    return apiService.post<ApiResponse>(`${this.endpoint}/${droneId}/firmware`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }
}

// Export singleton instance
export const droneService = new DroneService()

// Export class for testing
export { DroneService }