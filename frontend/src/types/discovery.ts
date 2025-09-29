/**
 * Discovery Types
 *
 * TypeScript definitions for discovery/detection data, matching backend model structure.
 */

export interface Discovery {
  id?: number;

  // Location fields matching backend naming convention
  lat: number;  // Discovery latitude
  lng: number;  // Discovery longitude
  altitude: number;  // Discovery altitude in meters

  // Detection details
  discovery_type: string;  // human, vehicle, debris, etc.
  confidence: number;  // Confidence score (0-100)
  description?: string;

  // Evidence and metadata
  evidence_data?: Record<string, any>;  // Additional evidence data
  image_url?: string;  // URL to evidence image
  video_url?: string;  // URL to evidence video

  // Classification
  classification?: 'confirmed' | 'potential' | 'false_positive';
  priority: 'low' | 'medium' | 'high' | 'critical';

  // Mission context
  mission_id: number;
  drone_id: number;

  // Verification status
  is_verified?: boolean;
  verified_by?: string;  // User ID who verified
  verification_notes?: string;

  // Environmental context
  weather_at_time?: string;
  lighting_conditions?: string;
  terrain_type?: string;

  // Metadata
  detected_at?: string;
  created_at?: string;
  updated_at?: string;
}

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