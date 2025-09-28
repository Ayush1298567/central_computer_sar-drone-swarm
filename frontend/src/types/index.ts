/**
 * Type definitions for SAR Drone System
 */

export interface Drone {
  id: string;
  name: string;
  position: {
    lat: number;
    lng: number;
    altitude: number;
  };
  status: 'active' | 'inactive' | 'error' | 'returning' | 'charging';
  battery: number;
  speed: number;
  heading: number;
  lastUpdate: Date;
  missionId?: string;
  capabilities: string[];
}

export interface Mission {
  id: string;
  name: string;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
  progress: number;
  searchArea: {
    center: { lat: number; lng: number };
    radius: number;
    bounds: [[number, number], [number, number]];
  };
  assignedDrones: string[];
  discoveries: Discovery[];
  weather?: {
    temperature: number;
    windSpeed: number;
    windDirection: number;
    visibility: number;
  };
}

export interface Discovery {
  id: string;
  type: 'person' | 'vehicle' | 'structure' | 'debris' | 'other';
  priority: 'critical' | 'high' | 'medium' | 'low';
  position: {
    lat: number;
    lng: number;
  };
  confidence: number;
  timestamp: Date;
  status: 'new' | 'investigating' | 'confirmed' | 'false_positive';
  evidence: Evidence[];
  assignedDrone?: string;
  description?: string;
}

export interface Evidence {
  id: string;
  type: 'image' | 'video' | 'thermal' | 'audio';
  url: string;
  thumbnail?: string;
  timestamp: Date;
  metadata?: {
    cameraAngle?: number;
    altitude?: number;
    fileSize?: number;
    duration?: number; // for video
  };
}

export interface VideoStream {
  id: string;
  droneId: string;
  url: string;
  isLive: boolean;
  quality: 'low' | 'medium' | 'high';
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  lastUpdate: Date;
}

export interface MissionControlCommand {
  type: 'emergency_stop' | 'return_to_base' | 'pause_mission' | 'resume_mission' | 'update_search_area' | 'reassign_drone';
  targetDroneId?: string;
  targetMissionId?: string;
  payload?: any;
  timestamp: Date;
  issuedBy: string;
}

export interface MapViewport {
  center: { lat: number; lng: number };
  zoom: number;
  bounds?: [[number, number], [number, number]];
}

export interface DashboardStats {
  totalDrones: number;
  activeDrones: number;
  totalDiscoveries: number;
  criticalDiscoveries: number;
  missionProgress: number;
  averageBattery: number;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}