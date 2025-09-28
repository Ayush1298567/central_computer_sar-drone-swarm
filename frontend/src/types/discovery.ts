export interface Discovery {
  id: string;
  type: 'person' | 'vehicle' | 'structure' | 'signal' | 'animal' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
  location: {
    lat: number;
    lng: number;
    altitude?: number;
    accuracy?: number;
  };
  description: string;
  confidence: number;
  evidence: Evidence[];
  status: 'new' | 'investigating' | 'confirmed' | 'false_positive' | 'resolved';
  timestamp: number;
  assigned_drone?: string;
  investigation_notes?: string;
  tags: string[];
}

export interface Evidence {
  id: string;
  discovery_id: string;
  type: 'image' | 'video' | 'thermal' | 'audio' | 'sensor';
  url: string;
  thumbnail_url?: string;
  timestamp: number;
  metadata: {
    size: number;
    duration?: number;
    resolution?: string;
    coordinates?: { lat: number; lng: number };
  };
}

export interface DiscoveryAlert {
  id: string;
  discovery_id: string;
  type: 'new_discovery' | 'priority_upgrade' | 'investigation_complete';
  message: string;
  timestamp: number;
  acknowledged: boolean;
}

export interface Investigation {
  id: string;
  discovery_id: string;
  assigned_investigator?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'critical';
  notes: string;
  start_time: number;
  end_time?: number;
  actions: InvestigationAction[];
}

export interface InvestigationAction {
  id: string;
  type: 'analysis' | 'verification' | 'coordination' | 'escalation';
  description: string;
  timestamp: number;
  completed: boolean;
}