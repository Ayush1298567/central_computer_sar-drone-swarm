/**
 * Mission Types
 *
 * TypeScript definitions for SAR mission data, matching backend model structure.
 */

export interface Mission {
  id?: number;
  name: string;
  description?: string;

  // Location fields matching backend naming convention
  center_lat: number;  // Center latitude
  center_lng: number;  // Center longitude
  area_size_km2: number;  // Area size in square kilometers
  search_altitude: number;  // Search altitude in meters

  // Mission status
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';

  // Mission parameters
  weather_conditions?: string;
  start_time?: string;
  estimated_duration?: number;  // Duration in minutes
  max_drones?: number;

  // Mission results
  discoveries_count?: number;
  area_covered?: number;
  completion_percentage?: number;

  // Metadata
  created_at?: string;
  updated_at?: string;
}

export interface CreateMissionRequest {
  name: string;
  description?: string;
  center_lat: number;
  center_lng: number;
  area_size_km2: number;
  search_altitude: number;
  weather_conditions?: string;
  estimated_duration?: number;
  max_drones?: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface UpdateMissionRequest extends Partial<CreateMissionRequest> {
  id: number;
  status?: 'planning' | 'active' | 'completed' | 'cancelled';
}