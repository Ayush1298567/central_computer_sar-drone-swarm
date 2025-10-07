/**
 * API Types
 *
 * Common API response types and utilities.
 */

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id?: string;
}

// API endpoint paths
export const API_ENDPOINTS = {
  MISSIONS: '/api/missions',
  DRONES: '/api/drones',
  DISCOVERIES: '/api/discoveries',
  CHAT: '/api/chat',
  WEBSOCKET: '/ws',
} as const;

// HTTP methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// Request configuration
export interface RequestConfig {
  method?: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
}

// Additional types for discoveries
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

export interface Evidence {
  id: number;
  discovery_id: number;
  evidence_type: 'image' | 'video' | 'audio' | 'sensor_data';
  file_url: string;
  metadata?: Record<string, any>;
  created_at: string;
}