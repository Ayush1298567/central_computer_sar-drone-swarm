import axios, { AxiosInstance, AxiosError } from 'axios';

<<<<<<< Current (Your changes)
// Prefer Vite-style env for backend base; default to current origin /api/v1
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || `${window.location.origin}/api/v1`;
=======
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
>>>>>>> Incoming (Background Agent changes)

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.data);
          throw new Error((error.response.data as any)?.message || 'API request failed');
        } else if (error.request) {
          // Request was made but no response
          console.error('Network Error:', error.message);
          throw new Error('Network error - please check your connection');
        } else {
          // Something else happened
          console.error('Error:', error.message);
          throw new Error(error.message);
        }
      }
    );
  }

  // Generic request methods
  async get<T>(url: string, params?: any): Promise<T> {
    return this.client.get(url, { params });
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.client.post(url, data);
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.client.put(url, data);
  }

  async delete<T>(url: string): Promise<T> {
    return this.client.delete(url);
  }
}

export const apiClient = new APIClient();

// Default export for backward compatibility
export default apiClient;

// Named exports for services
export const api = apiClient;
export const apiService = apiClient;

// Error handling utilities
export const handleApiError = (error: any) => {
  if (error.response) {
    console.error('API Error:', error.response.data);
    return error.response.data;
  } else if (error.request) {
    console.error('Network Error:', error.request);
    return { message: 'Network error occurred' };
  } else {
    console.error('Error:', error.message);
    return { message: error.message };
  }
};

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

export interface RequestConfig {
  timeout?: number;
  headers?: Record<string, string>;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp?: string;
}

export interface ConnectionHandler {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export interface MessageHandler {
  (message: WebSocketMessage): void;
}

export interface Subscription {
  topic: string;
  handler: MessageHandler;
}

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: '/health',
  METRICS: '/metrics',
  MISSIONS: '/missions',
  DRONES: '/drones',
  DISCOVERIES: '/discoveries',
  EMERGENCY: '/emergency',
  ANALYTICS: '/analytics',
  CHAT: '/chat',
  REAL_MISSION_EXECUTION: '/real-mission-execution',
  WEBSOCKET: '/ws'
} as const;

// Cache utilities
export class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();

  set(key: string, data: any, ttl: number = 300000) { // 5 minutes default
    this.cache.set(key, { data, timestamp: Date.now(), ttl });
  }

  get(key: string) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  clear() {
    this.cache.clear();
  }
}

export const apiCache = new ApiCache();

// Retry handler
export class RetryHandler {
  static async withRetry<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: any;
    
    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        if (i < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
      }
    }
    
    throw lastError;
  }
}

// Error handler
export class ApiErrorHandler {
  static handle(error: any): string {
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  }
}

// Convenience helpers for Phase 6
export async function getHealth(): Promise<{ status: string; drones_online: number; ai_enabled: boolean } | any> {
  return apiService.get(API_ENDPOINTS.HEALTH);
}

export async function getMetrics(): Promise<string> {
  // Return Prometheus text format
  const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.METRICS}`, { responseType: 'text' });
  return res.data as string;
}

export async function getDrones(): Promise<any> {
  return apiService.get(API_ENDPOINTS.DRONES);
}

export async function postMission(data: any): Promise<any> {
  return apiService.post(`${API_ENDPOINTS.REAL_MISSION_EXECUTION}/execute`, data);
}

export async function postAIMission(prompt: string, context: any = {}): Promise<any> {
  return apiService.post(`/ai/mission-plan`, { prompt, context });
}