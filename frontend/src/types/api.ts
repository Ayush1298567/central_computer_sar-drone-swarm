// API response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// Mission types
export interface Mission {
  id: string
  name: string
  description: string
  status: 'planning' | 'active' | 'paused' | 'completed' | 'aborted'
  search_area?: {
    type: string
    coordinates: [number, number][][]
  }
  launch_point?: {
    lat: number
    lng: number
  }
  search_altitude?: number
  search_speed?: string
  assigned_drone_count?: number
  estimated_duration?: number
  coverage_percentage?: number
  created_at: string
  started_at?: string
  completed_at?: string
}

// Chat types
export interface ChatMessage {
  id: string
  sender: 'user' | 'ai'
  content: string
  timestamp: string
  confidence?: number
  message_type?: string
}

export interface ChatResponse {
  response: string
  confidence: number
  conversation_id: string
  message_type: string
  next_action?: string
}

// Drone types
export interface Drone {
  id: string
  name: string
  status: 'offline' | 'online' | 'flying' | 'charging' | 'maintenance'
  connection_status: 'disconnected' | 'connected' | 'unstable'
  current_position?: {
    lat: number
    lng: number
    alt: number
  }
  battery_level: number
  signal_strength: number
  max_flight_time: number
  missions_completed: number
  last_seen?: string
}

// Discovery types
export interface Discovery {
  id: string
  mission_id: string
  drone_id: string
  object_type: string
  confidence_score: number
  latitude: number
  longitude: number
  altitude?: number
  investigation_status: 'pending' | 'investigating' | 'verified' | 'false_positive'
  priority_level: number
  discovered_at: string
  primary_image_url?: string
  video_clip_url?: string
}