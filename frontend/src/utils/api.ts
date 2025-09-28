// API utility functions for the SAR Mission Commander system

export class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Emergency Controls API
  async emergencyStop(droneId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/emergency/stop/${droneId}`, {
      method: 'POST',
    });
  }

  async returnToHome(droneId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/emergency/rth/${droneId}`, {
      method: 'POST',
    });
  }

  async getEmergencySituations(): Promise<any[]> {
    return this.request('/api/emergency/situations');
  }

  async resolveEmergency(situationId: string, notes: string): Promise<{ success: boolean }> {
    return this.request(`/api/emergency/resolve/${situationId}`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  // Notification API
  async getNotifications(): Promise<any[]> {
    return this.request('/api/notifications');
  }

  async markNotificationRead(notificationId: string): Promise<{ success: boolean }> {
    return this.request(`/api/notifications/${notificationId}/read`, {
      method: 'POST',
    });
  }

  async updateNotificationPreferences(preferences: any): Promise<{ success: boolean }> {
    return this.request('/api/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Analytics API
  async getMissionAnalytics(missionId: string): Promise<any> {
    return this.request(`/api/analytics/mission/${missionId}`);
  }

  async getPerformanceMetrics(): Promise<any> {
    return this.request('/api/analytics/performance');
  }

  async generateReport(missionId: string, reportType: string): Promise<{ downloadUrl: string }> {
    return this.request(`/api/analytics/report/${missionId}`, {
      method: 'POST',
      body: JSON.stringify({ reportType }),
    });
  }

  async getMissionReplay(missionId: string): Promise<any> {
    return this.request(`/api/analytics/replay/${missionId}`);
  }

  // Settings API
  async getSystemSettings(): Promise<any> {
    return this.request('/api/settings/system');
  }

  async updateSystemSettings(settings: any): Promise<{ success: boolean }> {
    return this.request('/api/settings/system', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async getDroneSettings(droneId: string): Promise<any> {
    return this.request(`/api/settings/drone/${droneId}`);
  }

  async updateDroneSettings(droneId: string, settings: any): Promise<{ success: boolean }> {
    return this.request(`/api/settings/drone/${droneId}`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async getUserPreferences(): Promise<any> {
    return this.request('/api/settings/preferences');
  }

  async updateUserPreferences(preferences: any): Promise<{ success: boolean }> {
    return this.request('/api/settings/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  async getAIConfiguration(): Promise<any> {
    return this.request('/api/settings/ai');
  }

  async updateAIConfiguration(config: any): Promise<{ success: boolean }> {
    return this.request('/api/settings/ai', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }
}

// Singleton instance
export const apiService = new ApiService();