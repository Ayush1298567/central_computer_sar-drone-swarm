/**
 * Discovery Types
 *
 * TypeScript definitions for discovery/detection data, matching backend model structure.
 */

export interface Discovery {
  id: number;
  mission_id: number;
  drone_id: number;
  discovery_type: string;
  confidence: number;
  location_lat: number;
  location_lng: number;
  description?: string;
  image_url?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'investigating' | 'resolved' | 'false_positive';
  investigation_notes?: string;
  created_at: string;
  updated_at: string;
  // Additional properties for UI
  type?: string;
  timestamp?: string;
  location?: {
    lat: number;
    lng: number;
  };
  evidence?: Evidence[];
  tags?: string[];
}

export interface DiscoveryCreate {
  mission_id: number;
  drone_id: number;
  discovery_type: string;
  confidence: number;
  location_lat: number;
  location_lng: number;
  description?: string;
  image_url?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface DiscoveryUpdate {
  discovery_type?: string;
  confidence?: number;
  location_lat?: number;
  location_lng?: number;
  description?: string;
  image_url?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  status?: 'pending' | 'investigating' | 'resolved' | 'false_positive';
  investigation_notes?: string;
}

// Legacy interfaces for backward compatibility
export interface CreateDiscoveryRequest {
  lat: number;
  lng: number;
  altitude: number;
  discovery_type: string;
  confidence: number;
  description?: string;
  evidence_data?: Record<string, any>;
  image_url?: string;
  video_url?: string;
  mission_id: number;
  drone_id: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface UpdateDiscoveryRequest extends Partial<CreateDiscoveryRequest> {
  id: number;
  classification?: 'confirmed' | 'potential' | 'false_positive';
  is_verified?: boolean;
  verified_by?: string;
  verification_notes?: string;
}

// Additional discovery-related types
export interface DiscoveryAlert {
  id: string;
  type: 'new_discovery' | 'high_priority' | 'investigation_complete' | 'false_positive';
  discovery_id: number;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  created_at: string;
  acknowledged: boolean;
}

export interface Investigation {
  id: number;
  discovery_id: number;
  investigator_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  findings?: string;
  conclusion?: 'confirmed' | 'false_positive' | 'inconclusive';
  created_at: string;
  updated_at: string;
  // Additional properties for UI
  notes?: string;
  assigned_investigator?: string;
  start_time?: string;
  end_time?: string;
  actions?: InvestigationAction[];
}

export interface InvestigationAction {
  id: number;
  investigation_id: number;
  action_type: 'note' | 'photo' | 'video' | 'measurement' | 'sample';
  type?: string;
  description: string;
  data?: Record<string, any>;
  created_at: string;
}

export interface Evidence {
  id: number;
  discovery_id: number;
  evidence_type: 'image' | 'video' | 'audio' | 'sensor_data';
  file_url: string;
  url?: string;
  thumbnail_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
  timestamp?: string;
  type?: string;
}