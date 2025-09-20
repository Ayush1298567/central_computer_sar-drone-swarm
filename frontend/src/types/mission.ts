export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'ready' | 'active' | 'paused' | 'completed' | 'aborted';
  priority: 'low' | 'medium' | 'high' | 'critical';
  search_area: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  assigned_drones: string[];
  created_at: string;
  started_at?: string;
  estimated_duration?: number;
  progress_percentage: number;
  weather_conditions?: {
    wind_speed: number;
    visibility: number;
    temperature: number;
  };
}

export interface MissionPlan {
  id: string;
  mission_id: string;
  waypoints: Waypoint[];
  coverage_paths: CoveragePath[];
  estimated_duration: number;
  total_distance: number;
  drone_assignments: DroneAssignment[];
}

export interface Waypoint {
  id: string;
  latitude: number;
  longitude: number;
  altitude: number;
  sequence: number;
  action: 'navigate' | 'search' | 'hover' | 'land' | 'takeoff';
}

export interface CoveragePath {
  id: string;
  drone_id: string;
  path_points: Array<{
    latitude: number;
    longitude: number;
    altitude: number;
  }>;
  estimated_time: number;
}

export interface DroneAssignment {
  drone_id: string;
  drone_name: string;
  assigned_area: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  estimated_flight_time: number;
  battery_required: number;
}