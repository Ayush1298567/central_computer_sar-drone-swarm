/**
 * Core API service configuration and utilities for the SAR Mission Commander frontend.
 */

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

// Request configuration
export interface RequestConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  headers?: Record<string, string>;
}

// Default configuration
const DEFAULT_CONFIG: RequestConfig = {
  timeout: 10000,
  retries: 3,
  retryDelay: 1000,
  headers: {
    'Content-Type': 'application/json',
  },
};

class ApiService {
  private baseURL: string;
  private config: RequestConfig;

  constructor(baseURL: string = API_BASE_URL, config: RequestConfig = {}) {
    this.baseURL = baseURL;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const requestConfig = { ...this.config, ...config };
    const url = `${this.baseURL}${endpoint}`;

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        ...this.config.headers,
        ...options.headers,
      },
    };

    let lastError: ApiError;

    for (let attempt = 0; attempt <= (requestConfig.retries || 0); attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), requestConfig.timeout);

        const response = await fetch(url, {
          ...requestOptions,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw {
            message: errorData.message || `HTTP ${response.status}: ${response.statusText}`,
            status: response.status,
            details: errorData,
          } as ApiError;
        }

        const data = await response.json();

        return {
          success: true,
          data,
          timestamp: new Date().toISOString(),
        };

      } catch (error: any) {
        lastError = error;

        // Don't retry on client errors (4xx) except 408, 429
        if (error.status && error.status >= 400 && error.status < 500 &&
            error.status !== 408 && error.status !== 429) {
          break;
        }

        // Don't retry on abort errors
        if (error.name === 'AbortError') {
          lastError = {
            message: 'Request timeout',
            status: 408,
          };
          break;
        }

        // Wait before retrying
        if (attempt < (requestConfig.retries || 0)) {
          await new Promise(resolve =>
            setTimeout(resolve, requestConfig.retryDelay! * Math.pow(2, attempt))
          );
        }
      }
    }

    return {
      success: false,
      error: lastError?.message || 'Network error',
      timestamp: new Date().toISOString(),
    };
  }

  // HTTP Methods
  async get<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'GET' }, config);
  }

  async post<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      config
    );
  }

  async put<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      config
    );
  }

  async patch<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      config
    );
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' }, config);
  }

  // File upload
  async uploadFile<T>(endpoint: string, file: File, config?: RequestConfig): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.makeRequest<T>(
      endpoint,
      {
        method: 'POST',
        body: formData,
        headers: {}, // Let browser set Content-Type for FormData
      },
      config
    );
  }

  // Batch requests
  async batch<T>(requests: Array<{ endpoint: string; options?: RequestInit }>): Promise<ApiResponse<T[]>> {
    try {
      const promises = requests.map(({ endpoint, options = {} }) =>
        this.makeRequest<T>(endpoint, options)
      );

      const results = await Promise.allSettled(promises);

      const data: T[] = [];
      const errors: string[] = [];

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          if (result.value.success && result.value.data) {
            data.push(result.value.data);
          } else {
            errors.push(result.value.error || `Request ${index} failed`);
          }
        } else {
          errors.push(`Request ${index} failed: ${result.reason}`);
        }
      });

      return {
        success: errors.length === 0,
        data,
        error: errors.length > 0 ? errors.join('; ') : undefined,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  }
}

// Global API service instance
export const apiService = new ApiService();

// API endpoint builders
export const API_ENDPOINTS = {
  // Mission endpoints
  MISSIONS: '/missions',
  MISSION_BY_ID: (id: string) => `/missions/${id}`,
  MISSION_START: (id: string) => `/missions/${id}/start`,
  MISSION_PAUSE: (id: string) => `/missions/${id}/pause`,
  MISSION_RESUME: (id: string) => `/missions/${id}/resume`,
  MISSION_ABORT: (id: string) => `/missions/${id}/abort`,

  // Drone endpoints
  DRONES: '/drones',
  DRONE_BY_ID: (id: string) => `/drones/${id}`,
  DRONE_TELEMETRY: (id: string) => `/drones/${id}/telemetry`,
  DRONE_COMMAND: (id: string) => `/drones/${id}/command`,

  // Discovery endpoints
  DISCOVERIES: '/discoveries',
  DISCOVERY_BY_ID: (id: string) => `/discoveries/${id}`,
  DISCOVERY_INVESTIGATE: (id: string) => `/discoveries/${id}/investigate`,
  DISCOVERY_VERIFY: (id: string) => `/discoveries/${id}/verify`,

  // Chat endpoints
  CHAT: '/chat',
  CHAT_SEND: '/chat/send',
  CHAT_HISTORY: (missionId: string) => `/chat/history/${missionId}`,

  // Analytics endpoints
  ANALYTICS: '/analytics',
  ANALYTICS_MISSION: (id: string) => `/analytics/mission/${id}`,
  ANALYTICS_OVERVIEW: '/analytics/overview',

  // System endpoints
  HEALTH: '/health',
  WEATHER: '/weather',
  WEATHER_FORECAST: '/weather/forecast',

  // File upload endpoints
  UPLOAD: '/upload',
  UPLOAD_MISSION_MEDIA: '/upload/mission-media',
  UPLOAD_EVIDENCE: '/upload/evidence',
} as const;

// Error handling utilities
export class ApiErrorHandler {
  static handleError(error: any): ApiError {
    if (error.status) {
      return {
        message: error.message || 'API request failed',
        status: error.status,
        details: error.details,
      };
    }

    if (error.name === 'AbortError') {
      return {
        message: 'Request timeout',
        status: 408,
      };
    }

    if (error.message) {
      return {
        message: error.message,
        status: 0,
      };
    }

    return {
      message: 'Unknown error occurred',
      status: 0,
    };
  }

  static isNetworkError(error: ApiError): boolean {
    return error.status === 0 || error.status >= 500;
  }

  static isClientError(error: ApiError): boolean {
    return error.status >= 400 && error.status < 500;
  }

  static isServerError(error: ApiError): boolean {
    return error.status >= 500;
  }

  static isTimeoutError(error: ApiError): boolean {
    return error.status === 408;
  }
}

// Retry utilities
export class RetryHandler {
  static async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;

        // Don't retry on client errors except specific cases
        if (error.status && error.status >= 400 && error.status < 500 &&
            error.status !== 408 && error.status !== 429) {
          throw error;
        }

        if (attempt < maxRetries) {
          const delay = baseDelay * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError;
  }
}

// Cache utilities
export class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();

  set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  size(): number {
    return this.cache.size;
  }
}

// Global cache instance
export const apiCache = new ApiCache();

// Cache-enabled API methods
export const cachedApiService = {
  get: async <T>(endpoint: string, ttl?: number): Promise<ApiResponse<T>> => {
    const cacheKey = `GET:${endpoint}`;
    const cached = apiCache.get<ApiResponse<T>>(cacheKey);

    if (cached) {
      return cached;
    }

    const result = await apiService.get<T>(endpoint);
    if (result.success) {
      apiCache.set(cacheKey, result, ttl);
    }

    return result;
  },

  post: async <T>(endpoint: string, data?: any): Promise<ApiResponse<T>> => {
    // Don't cache POST requests
    return apiService.post<T>(endpoint, data);
  },

  put: async <T>(endpoint: string, data?: any): Promise<ApiResponse<T>> => {
    // Invalidate related cache entries
    const cacheKey = `GET:${endpoint}`;
    apiCache.delete(cacheKey);

    return apiService.put<T>(endpoint, data);
  },

  delete: async <T>(endpoint: string): Promise<ApiResponse<T>> => {
    // Invalidate related cache entries
    const cacheKey = `GET:${endpoint}`;
    apiCache.delete(cacheKey);

    return apiService.delete<T>(endpoint);
  },

  clearCache: () => {
    apiCache.clear();
  },
};