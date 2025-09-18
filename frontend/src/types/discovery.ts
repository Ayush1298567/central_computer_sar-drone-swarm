// Discovery-related type definitions

export interface Discovery {
  id: string;
  mission_id: string;
  drone_id: string;
  object_type: string;
  confidence_score: number;
  detection_method?: string;
  latitude: number;
  longitude: number;
  altitude?: number;
  location_accuracy?: number;
  primary_image_url?: string;
  video_clip_url?: string;
  thermal_image_url?: string;
  environmental_conditions?: Record<string, any>;
  detection_context?: Record<string, any>;
  sensor_data?: Record<string, any>;
  investigation_status: 'pending' | 'investigating' | 'verified' | 'false_positive';
  priority_level: number;
  human_verified: boolean;
  verification_notes?: string;
  action_required?: string;
  ground_team_notified: boolean;
  emergency_services_contacted: boolean;
  discovered_by_operator?: string;
  verified_by_operator?: string;
  evidence_secured: boolean;
  legal_chain_maintained: boolean;
  discovered_at: string;
  investigated_at?: string;
  verified_at?: string;
  closed_at?: string;
}