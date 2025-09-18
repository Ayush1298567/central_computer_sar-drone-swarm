// Mission-related type definitions

export interface Coordinate {
  lat: number;
  lng: number;
}

export interface CoordinateWithAlt extends Coordinate {
  alt: number;
}

export interface Mission {
  id: string;
  name: string;
  description?: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted';
  search_area?: Coordinate[];
  launch_point?: Coordinate;
  search_altitude?: number;
  search_speed?: 'fast' | 'thorough';
  search_target?: string;
  recording_mode?: 'continuous' | 'event_triggered';
  assigned_drone_count: number;
  estimated_duration?: number;
  actual_duration?: number;
  coverage_percentage: number;
  ai_confidence?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface DroneAssignment {
  id: string;
  mission_id: string;
  drone_id: string;
  assigned_area?: Coordinate[];
  navigation_waypoints?: CoordinateWithAlt[];
  priority_level: number;
  estimated_coverage_time?: number;
  status: 'assigned' | 'navigating' | 'searching' | 'completed';
  progress_percentage: number;
  assigned_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ChatMessage {
  id: string;
  mission_id: string;
  sender: 'user' | 'ai';
  content: string;
  message_type: 'text' | 'question' | 'confirmation';
  ai_confidence?: number;
  processing_time?: number;
  attachments?: Record<string, any>;
  created_at: string;
}