// Base API Configuration
// Provides common API utilities and configuration

// API Configuration
export const API_CONFIG = {
  baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
};

// API Request/Response interceptors and utilities
class ApiClient {
  private token: string | null = null;
  private userId: string | null = null;

  constructor() {
    // Load token from localStorage on initialization
    this.loadStoredAuth();
  }

  // Authentication methods
  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('auth_token');
  }

  setUserId(userId: string) {
    this.userId = userId;
    localStorage.setItem('user_id', userId);
  }

  getUserId(): string | null {
    return this.userId || localStorage.getItem('user_id');
  }

  clearAuth() {
    this.token = null;
    this.userId = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
  }

  private loadStoredAuth() {
    this.token = localStorage.getItem('auth_token');
    this.userId = localStorage.getItem('user_id');
  }

  // Generic request method with retry logic
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.baseUrl}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    // Add authorization header if token is available
    const token = this.getToken();
    if (token) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`,
      };
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= API_CONFIG.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

        const response = await fetch(url, {
          ...config,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Try to parse JSON response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        } else {
          return response.text() as unknown as T;
        }
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (error instanceof Error && error.message.includes('HTTP 4')) {
          const statusCode = parseInt(error.message.match(/HTTP (\d+)/)?.[1] || '400');
          if (statusCode !== 429) {
            throw error;
          }
        }

        // Don't retry on abort errors
        if (error instanceof Error && error.name === 'AbortError') {
          throw error;
        }

        // Wait before retry (exponential backoff)
        if (attempt < API_CONFIG.retries) {
          await new Promise(resolve =>
            setTimeout(resolve, API_CONFIG.retryDelay * Math.pow(2, attempt))
          );
        }
      }
    }

    throw lastError;
  }

  // HTTP method helpers
  async get<T = any>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const searchParams = params ? new URLSearchParams(params).toString() : '';
    const url = searchParams ? `${endpoint}?${searchParams}` : endpoint;

    return this.request<T>(url, {
      method: 'GET',
    });
  }

  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // File upload helper
  async uploadFile<T = any>(
    endpoint: string,
    file: File,
    additionalFields?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.baseUrl}${endpoint}`;

    const config: RequestInit = {
      method: 'POST',
      body: formData,
      headers: {},
    };

    // Add authorization header if token is available
    const token = this.getToken();
    if (token) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`,
      };
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  // WebSocket helper
  createWebSocket(path: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}${path}`;

    return new WebSocket(url);
  }
}

// Error handling utilities
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Response validation helpers
export const validateResponse = <T>(response: any, schema?: any): T => {
  // Basic validation - in a real app, you'd use a library like Joi or Zod
  if (!response) {
    throw new ApiError('Empty response received');
  }

  return response as T;
};

// Export singleton instance
export const api = new ApiClient();

// Environment detection
export const isDevelopment = () => {
  return process.env.NODE_ENV === 'development';
};

export const isProduction = () => {
  return process.env.NODE_ENV === 'production';
};

// API health check
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    await api.get('/health');
    return true;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};