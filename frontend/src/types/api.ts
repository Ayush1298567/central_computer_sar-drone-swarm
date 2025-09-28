export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}

export interface DroneStatus {
  id: string;
  name: string;
  position: {
    lat: number;
    lng: number;
    altitude: number;
  };
  battery: number;
  status: 'active' | 'idle' | 'charging' | 'maintenance' | 'error';
  mission_id?: string;
  last_seen: number;
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  area: {
    center: { lat: number; lng: number };
    radius: number;
    bounds: { north: number; east: number; south: number; west: number };
  };
  assigned_drones: string[];
  progress: number;
  start_time?: number;
  end_time?: number;
  discoveries: Discovery[];
}

export interface Discovery {
  id: string;
  type: 'person' | 'vehicle' | 'structure' | 'signal' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
  location: { lat: number; lng: number };
  description: string;
  evidence: Evidence[];
  status: 'new' | 'investigating' | 'confirmed' | 'false_positive';
  timestamp: number;
  assigned_drone?: string;
}

export interface Evidence {
  id: string;
  type: 'image' | 'video' | 'audio' | 'sensor';
  url: string;
  timestamp: number;
  metadata?: Record<string, any>;
}