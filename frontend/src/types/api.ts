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