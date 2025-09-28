export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  search_area: {
    center: { lat: number; lng: number };
    radius: number;
    bounds: { north: number; east: number; south: number; west: number };
  };
  assigned_drones: string[];
  waypoints: Waypoint[];
  discoveries: Discovery[];
  start_time?: number;
  end_time?: number;
  progress: number;
  estimated_completion?: number;
}

export interface Waypoint {
  id: string;
  position: { lat: number; lng: number; altitude: number };
  type: 'search' | 'hover' | 'transition';
  hold_time?: number;
  completed: boolean;
}

export interface MissionPlan {
  search_pattern: 'spiral' | 'grid' | 'perimeter' | 'custom';
  altitude: number;
  speed: number;
  overlap: number;
  camera_settings: {
    resolution: string;
    fps: number;
    zoom: number;
  };
}

export interface MissionProgress {
  mission_id: string;
  current_waypoint: number;
  total_waypoints: number;
  area_covered: number;
  total_area: number;
  discoveries_found: number;
  estimated_time_remaining: number;
}