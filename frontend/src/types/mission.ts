// Mission Types
export interface Mission {
  id: string;
  name: string;
  description?: string;
  status: MissionStatus;
  priority: MissionPriority;
  mission_type: MissionType;
  area: MissionArea;
  waypoints?: Waypoint[];
  assigned_drones: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_duration?: number;
  actual_duration?: number;
  weather_conditions?: WeatherData;
  risk_assessment?: RiskAssessment;
  emergency_contacts?: EmergencyContact[];
}

export interface CreateMissionRequest {
  name: string;
  description?: string;
  mission_type: MissionType;
  area: MissionArea;
  waypoints?: Waypoint[];
  priority?: MissionPriority;
  assigned_drones?: string[];
  estimated_duration?: number;
  emergency_contacts?: EmergencyContact[];
}

export interface UpdateMissionRequest {
  name?: string;
  description?: string;
  status?: MissionStatus;
  waypoints?: Waypoint[];
  assigned_drones?: string[];
  priority?: MissionPriority;
}

export interface MissionArea {
  type: 'polygon' | 'circle' | 'rectangle';
  coordinates: number[][]; // [lat, lng] pairs
  center?: [number, number]; // [lat, lng]
  radius?: number; // for circle
  width?: number; // for rectangle
  height?: number; // for rectangle
}

export interface Waypoint {
  id: string;
  latitude: number;
  longitude: number;
  altitude?: number;
  speed?: number;
  action?: WaypointAction;
  parameters?: Record<string, any>;
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  visibility: number;
  conditions: string;
  last_updated: string;
}

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  factors: RiskFactor[];
  mitigation_strategies: string[];
}

export interface RiskFactor {
  type: 'weather' | 'terrain' | 'technical' | 'operational';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

export interface EmergencyContact {
  name: string;
  role: string;
  phone: string;
  email?: string;
}

export type MissionStatus =
  | 'planning'
  | 'scheduled'
  | 'active'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type MissionPriority =
  | 'low'
  | 'medium'
  | 'high'
  | 'urgent'
  | 'critical';

export type MissionType =
  | 'search_and_rescue'
  | 'surveillance'
  | 'mapping'
  | 'delivery'
  | 'inspection'
  | 'training';

export type WaypointAction =
  | 'hover'
  | 'photo'
  | 'video'
  | 'thermal_scan'
  | 'payload_drop'
  | 'sample_collection';