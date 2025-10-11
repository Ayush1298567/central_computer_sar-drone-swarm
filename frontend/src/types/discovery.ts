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