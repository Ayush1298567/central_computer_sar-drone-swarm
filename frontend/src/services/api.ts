import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios'
import { ApiResponse, ApiError, ApiServiceConfig } from '@/types'

class ApiService {
  private client: AxiosInstance
  private config: ApiServiceConfig

  constructor(config: Partial<ApiServiceConfig> = {}) {
    this.config = {
      baseURL: config.baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
      timeout: config.timeout || 30000,
      retries: config.retries || 3,
      retryDelay: config.retryDelay || 1000,
      ...config,
    }

    this.client = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor for auth tokens
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config

        // Handle token refresh
        if (error.response?.status === 401 && originalRequest && !originalRequest.url?.includes('/auth/refresh')) {
          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await axios.post('/auth/refresh', { refresh_token: refreshToken })
              const { access_token } = response.data.data.tokens

              localStorage.setItem('access_token', access_token)

              // Retry original request
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access_token}`
              }
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
          }
        }

        return Promise.reject(this.handleError(error))
      }
    )
  }

  private handleError(error: AxiosError): any {
    if (error.response) {
      // Server responded with error status
      return {
        message: (error.response.data as any)?.message || 'An error occurred',
        status: error.response.status,
        code: (error.response.data as any)?.code,
        details: (error.response.data as any)?.details,
        timestamp: new Date().toISOString(),
      }
    } else if (error.request) {
      // Request made but no response received
      return {
        message: 'Network error - please check your connection',
        status: 0,
        code: 'NETWORK_ERROR',
        timestamp: new Date().toISOString(),
      }
    } else {
      // Something else happened
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        code: 'UNKNOWN_ERROR',
        timestamp: new Date().toISOString(),
      }
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    retries: number = this.config.retries
  ): Promise<AxiosResponse<T>> {
    try {
      return await requestFn()
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error as AxiosError)) {
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay))
        return this.retryRequest(requestFn, retries - 1)
      }
      throw error
    }
  }

  private shouldRetry(error: AxiosError): boolean {
    if (error.response) {
      // Don't retry client errors (4xx) except 408, 429
      const status = error.response.status
      return status >= 500 || status === 408 || status === 429
    }
    // Retry network errors
    return !error.response
  }

  async get<T>(url: string, config?: any): Promise<T> {
    const response = await this.retryRequest(() =>
      this.client.get<ApiResponse<T>>(url, config)
    )
    return response.data as T
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.retryRequest(() =>
      this.client.post<ApiResponse<T>>(url, data, config)
    )
    return response.data as T
  }

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.retryRequest(() =>
      this.client.put<ApiResponse<T>>(url, data, config)
    )
    return response.data as T
  }

  async patch<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.retryRequest(() =>
      this.client.patch<ApiResponse<T>>(url, data, config)
    )
    return response.data as T
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    const response = await this.retryRequest(() =>
      this.client.delete<ApiResponse<T>>(url, config)
    )
    return response.data as T
  }

  // Utility method to check if response is successful
  isSuccess<T>(response: ApiResponse<T>): response is ApiResponse<T> & { data: T } {
    return response.success && response.data !== undefined
  }

  // Utility method to get error message
  getErrorMessage(error: unknown): string {
    if (this.isApiError(error)) {
      return error.message
    }
    return 'An unexpected error occurred'
  }

  private isApiError(error: unknown): error is ApiError {
    return typeof error === 'object' && error !== null && 'message' in error
  }
}

// Export singleton instance
export const apiService = new ApiService()

// Export class for testing or custom instances
export { ApiService }