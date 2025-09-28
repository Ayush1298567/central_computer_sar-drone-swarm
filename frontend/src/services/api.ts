import axios, { AxiosResponse } from 'axios';
import { ApiResponse, DroneStatus, Mission, Discovery } from '../types/api';

const API_BASE_URL = 'http://localhost:8000/api';

export class ApiService {
  private axios = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Drone API methods
  async getDrones(): Promise<DroneStatus[]> {
    try {
      const response: AxiosResponse<ApiResponse<DroneStatus[]>> = await this.axios.get('/drones');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching drones:', error);
      throw error;
    }
  }

  async getDrone(droneId: string): Promise<DroneStatus> {
    try {
      const response: AxiosResponse<ApiResponse<DroneStatus>> = await this.axios.get(`/drones/${droneId}`);
      return response.data.data;
    } catch (error) {
      console.error('Error fetching drone:', error);
      throw error;
    }
  }

  async commandDrone(droneId: string, command: string, parameters?: Record<string, any>): Promise<void> {
    try {
      await this.axios.post(`/drones/${droneId}/command`, {
        command,
        parameters,
      });
    } catch (error) {
      console.error('Error commanding drone:', error);
      throw error;
    }
  }

  // Mission API methods
  async getMissions(): Promise<Mission[]> {
    try {
      const response: AxiosResponse<ApiResponse<Mission[]>> = await this.axios.get('/missions');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching missions:', error);
      throw error;
    }
  }

  async getMission(missionId: string): Promise<Mission> {
    try {
      const response: AxiosResponse<ApiResponse<Mission>> = await this.axios.get(`/missions/${missionId}`);
      return response.data.data;
    } catch (error) {
      console.error('Error fetching mission:', error);
      throw error;
    }
  }

  async createMission(missionData: Partial<Mission>): Promise<Mission> {
    try {
      const response: AxiosResponse<ApiResponse<Mission>> = await this.axios.post('/missions', missionData);
      return response.data.data;
    } catch (error) {
      console.error('Error creating mission:', error);
      throw error;
    }
  }

  async updateMission(missionId: string, updates: Partial<Mission>): Promise<Mission> {
    try {
      const response: AxiosResponse<ApiResponse<Mission>> = await this.axios.put(`/missions/${missionId}`, updates);
      return response.data.data;
    } catch (error) {
      console.error('Error updating mission:', error);
      throw error;
    }
  }

  async cancelMission(missionId: string): Promise<void> {
    try {
      await this.axios.post(`/missions/${missionId}/cancel`);
    } catch (error) {
      console.error('Error cancelling mission:', error);
      throw error;
    }
  }

  // Discovery API methods
  async getDiscoveries(): Promise<Discovery[]> {
    try {
      const response: AxiosResponse<ApiResponse<Discovery[]>> = await this.axios.get('/discoveries');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching discoveries:', error);
      throw error;
    }
  }

  async getDiscovery(discoveryId: string): Promise<Discovery> {
    try {
      const response: AxiosResponse<ApiResponse<Discovery>> = await this.axios.get(`/discoveries/${discoveryId}`);
      return response.data.data;
    } catch (error) {
      console.error('Error fetching discovery:', error);
      throw error;
    }
  }

  async updateDiscoveryStatus(discoveryId: string, status: string, notes?: string): Promise<Discovery> {
    try {
      const response: AxiosResponse<ApiResponse<Discovery>> = await this.axios.put(`/discoveries/${discoveryId}/status`, {
        status,
        notes,
      });
      return response.data.data;
    } catch (error) {
      console.error('Error updating discovery status:', error);
      throw error;
    }
  }

  // System API methods
  async getSystemStatus(): Promise<any> {
    try {
      const response: AxiosResponse<ApiResponse<any>> = await this.axios.get('/system/status');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching system status:', error);
      throw error;
    }
  }

  async emergencyStop(reason: string): Promise<void> {
    try {
      await this.axios.post('/system/emergency-stop', { reason });
    } catch (error) {
      console.error('Error triggering emergency stop:', error);
      throw error;
    }
  }

  async returnToBase(droneIds?: string[]): Promise<void> {
    try {
      await this.axios.post('/system/return-to-base', { droneIds });
    } catch (error) {
      console.error('Error commanding return to base:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();