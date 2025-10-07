export interface Mission {
  id: string
  mission_id: string
  name: string
  description?: string
  status: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'critical'
  search_area: {
    coordinates: number[][][]
    altitude: number
    pattern: 'lawnmower' | 'spiral' | 'grid'
  }
  center_lat: number
  center_lng: number
  start_time?: string
  end_time?: string
  estimated_duration: number
  actual_start_time?: string
  actual_end_time?: string
  assigned_drone_count: number
  created_at: string
  updated_at: string
}

export interface MissionCreate {
  mission_id: string
  name: string
  description?: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  search_area: {
    coordinates: number[][][]
    altitude: number
    pattern: 'lawnmower' | 'spiral' | 'grid'
  }
  center_lat: number
  center_lng: number
  estimated_duration: number
}

export interface MissionUpdate {
  name?: string
  description?: string
  status?: string
  priority?: string
  search_area?: {
    coordinates: number[][][]
    altitude: number
    pattern: 'lawnmower' | 'spiral' | 'grid'
  }
  estimated_duration?: number
}

export interface MissionProgress {
  mission_id: string
  status: string
  progress_percentage: number
  covered_area: number
  remaining_area: number
  active_drones: number
  discoveries_found: number
  estimated_completion: string
}

export interface MissionDrone {
  mission_id: string
  drone_id: string
  assigned_area?: {
    coordinates: number[][][]
    waypoints: Array<{ lat: number; lng: number; alt: number }>
  }
  status: 'assigned' | 'active' | 'completed' | 'failed'
}