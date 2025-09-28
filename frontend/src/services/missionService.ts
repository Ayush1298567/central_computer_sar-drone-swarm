// Mission API Service
// Handles all mission-related API calls with React Query integration

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

// TypeScript interfaces for mission requests/responses
export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted';
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  updated_at: string;
  created_by: string;
  assigned_drones: string[];
  area_of_interest: {
    coordinates: [number, number][];
    center: [number, number];
    radius: number;
  };
  search_pattern: 'spiral' | 'grid' | 'parallel' | 'custom';
  parameters: {
    altitude: number;
    speed: number;
    camera_angle: number;
    overlap_percentage: number;
  };
  estimated_duration: number;
  actual_duration?: number;
  weather_conditions: {
    wind_speed: number;
    temperature: number;
    visibility: number;
    precipitation: number;
  };
  results?: {
    areas_covered: number;
    objects_detected: number;
    false_positives: number;
    search_efficiency: number;
  };
}

export interface CreateMissionRequest {
  name: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  area_of_interest: {
    coordinates: [number, number][];
    center: [number, number];
    radius: number;
  };
  search_pattern: 'spiral' | 'grid' | 'parallel' | 'custom';
  parameters: {
    altitude: number;
    speed: number;
    camera_angle: number;
    overlap_percentage: number;
  };
  assigned_drones: string[];
}

export interface UpdateMissionRequest {
  name?: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  parameters?: {
    altitude?: number;
    speed?: number;
    camera_angle?: number;
    overlap_percentage?: number;
  };
  assigned_drones?: string[];
}

export interface MissionAnalytics {
  total_missions: number;
  active_missions: number;
  completed_missions: number;
  success_rate: number;
  average_duration: number;
  total_area_covered: number;
  efficiency_trends: {
    date: string;
    efficiency: number;
  }[];
}

// API service class with retry logic and error handling
class MissionService {
  private queryClient: ReturnType<typeof useQueryClient>;

  constructor() {
    // We'll inject the query client when using hooks
  }

  // Set query client for cache management
  setQueryClient(client: ReturnType<typeof useQueryClient>) {
    this.queryClient = client;
  }

  // Get all missions with pagination
  async getMissions(page = 1, limit = 20, status?: string): Promise<{ missions: Mission[], total: number }> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(status && { status })
      });

      const response = await fetch(`${api.baseUrl}/missions?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch missions: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        missions: data.missions,
        total: data.total
      };
    } catch (error) {
      console.error('Error fetching missions:', error);
      throw error;
    }
  }

  // Get single mission by ID
  async getMission(id: string): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching mission:', error);
      throw error;
    }
  }

  // Create new mission
  async createMission(missionData: CreateMissionRequest): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(missionData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating mission:', error);
      throw error;
    }
  }

  // Update mission
  async updateMission(id: string, updates: UpdateMissionRequest): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating mission:', error);
      throw error;
    }
  }

  // Delete mission
  async deleteMission(id: string): Promise<void> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete mission: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting mission:', error);
      throw error;
    }
  }

  // Start mission
  async startMission(id: string): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to start mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error starting mission:', error);
      throw error;
    }
  }

  // Pause mission
  async pauseMission(id: string): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}/pause`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to pause mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error pausing mission:', error);
      throw error;
    }
  }

  // Abort mission
  async abortMission(id: string, reason?: string): Promise<Mission> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}/abort`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        throw new Error(`Failed to abort mission: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error aborting mission:', error);
      throw error;
    }
  }

  // Get mission analytics
  async getMissionAnalytics(timeRange?: string): Promise<MissionAnalytics> {
    try {
      const params = timeRange ? `?timeRange=${timeRange}` : '';
      const response = await fetch(`${api.baseUrl}/missions/analytics${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching mission analytics:', error);
      throw error;
    }
  }

  // Get mission progress
  async getMissionProgress(id: string): Promise<{
    percentage: number;
    current_phase: string;
    estimated_completion: string;
    areas_covered: number;
    total_areas: number;
  }> {
    try {
      const response = await fetch(`${api.baseUrl}/missions/${id}/progress`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch mission progress: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching mission progress:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const missionService = new MissionService();

// React Query hooks
export const useMissions = (page = 1, limit = 20, status?: string) => {
  return useQuery({
    queryKey: ['missions', page, limit, status],
    queryFn: () => missionService.getMissions(page, limit, status),
    staleTime: 30000, // 30 seconds
    retry: 3,
  });
};

export const useMission = (id: string) => {
  return useQuery({
    queryKey: ['mission', id],
    queryFn: () => missionService.getMission(id),
    enabled: !!id,
    staleTime: 15000, // 15 seconds
    retry: 3,
  });
};

export const useCreateMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: missionService.createMission,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
    },
    retry: 2,
  });
};

export const useUpdateMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: UpdateMissionRequest }) =>
      missionService.updateMission(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      queryClient.invalidateQueries({ queryKey: ['mission', data.id] });
    },
    retry: 2,
  });
};

export const useDeleteMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: missionService.deleteMission,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
    },
    retry: 2,
  });
};

export const useStartMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: missionService.startMission,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      queryClient.invalidateQueries({ queryKey: ['mission', data.id] });
    },
    retry: 2,
  });
};

export const usePauseMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: missionService.pauseMission,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      queryClient.invalidateQueries({ queryKey: ['mission', data.id] });
    },
    retry: 2,
  });
};

export const useAbortMission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      missionService.abortMission(id, reason),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      queryClient.invalidateQueries({ queryKey: ['mission', data.id] });
    },
    retry: 2,
  });
};

export const useMissionAnalytics = (timeRange?: string) => {
  return useQuery({
    queryKey: ['missionAnalytics', timeRange],
    queryFn: () => missionService.getMissionAnalytics(timeRange),
    staleTime: 60000, // 1 minute
    retry: 3,
  });
};

export const useMissionProgress = (id: string) => {
  return useQuery({
    queryKey: ['missionProgress', id],
    queryFn: () => missionService.getMissionProgress(id),
    enabled: !!id,
    refetchInterval: 5000, // Poll every 5 seconds for active missions
    retry: 3,
  });
};