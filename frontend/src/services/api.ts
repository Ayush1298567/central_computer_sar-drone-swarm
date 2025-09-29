/**
 * Base API configuration for SAR Mission Commander
 */
import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// API Base URL Configuration
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? (process.env.REACT_APP_API_URL || 'https://api.yourdomain.com/api/v1')
  : 'http://localhost:8000/api/v1';

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
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

// Response interceptor for handling errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.message || `Server error: ${error.response.status}`;
      throw new Error(message);
    } else if (error.request) {
      // Network error
      throw new Error('Network error - please check your connection');
    } else {
      // Other error
      throw new Error(error.message || 'Unknown error occurred');
    }
  }
);

// Export error handler function
export const handleApiError = (error: any): string => {
  if (error.response) {
    return error.response.data?.message || `Server error: ${error.response.status}`;
  } else if (error.request) {
    return 'Network error - please check your connection';
  } else {
    return error.message || 'Unknown error occurred';
  }
};

export default api;