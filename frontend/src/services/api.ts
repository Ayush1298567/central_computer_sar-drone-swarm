import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor for auth tokens
api.interceptors.request.use(
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

// API Service functions
export const apiService = {
  // Drones
  drones: {
    getAll: (params?: any) => api.get('/drones', { params }),
    getById: (droneId: string) => api.get(`/drones/${droneId}`),
    register: (droneId: string, data: any) => api.post(`/drones/${droneId}/register`, data),
    update: (droneId: string, data: any) => api.put(`/drones/${droneId}/update`, data),
    addTelemetry: (droneId: string, data: any) => api.post(`/drones/${droneId}/telemetry`, data),
    getTelemetry: (droneId: string, limit?: number) => api.get(`/drones/${droneId}/telemetry`, { params: { limit } }),
    unregister: (droneId: string) => api.delete(`/drones/${droneId}`),
  },

  // Missions
  missions: {
    getAll: (params?: any) => api.get('/missions', { params }),
    getById: (missionId: string) => api.get(`/missions/${missionId}`),
    create: (data: any) => api.post('/missions', data),
    start: (missionId: string) => api.put(`/missions/${missionId}/start`),
    pause: (missionId: string) => api.put(`/missions/${missionId}/pause`),
    resume: (missionId: string) => api.put(`/missions/${missionId}/resume`),
    complete: (missionId: string, success: boolean = true) => api.put(`/missions/${missionId}/complete`, { success }),
    getStatus: (missionId: string) => api.get(`/missions/${missionId}/status`),
  },

  // Discoveries
  discoveries: {
    getAll: (params?: any) => api.get('/discoveries', { params }),
    getById: (discoveryId: string) => api.get(`/discoveries/${discoveryId}`),
    create: (data: any) => api.post('/discoveries', data),
    update: (discoveryId: string, data: any) => api.put(`/discoveries/${discoveryId}/update`, data),
    uploadEvidence: (discoveryId: string, file: File, description?: string) => {
      const formData = new FormData();
      formData.append('file', file);
      if (description) formData.append('description', description);
      return api.post(`/discoveries/${discoveryId}/evidence`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    startInvestigation: (discoveryId: string, droneId: string) => api.put(`/discoveries/${discoveryId}/investigate`, { drone_id: droneId }),
    completeInvestigation: (discoveryId: string, result: any) => api.put(`/discoveries/${discoveryId}/complete-investigation`, result),
  },

  // Chat
  chat: {
    getSessions: (params?: any) => api.get('/chat/sessions', { params }),
    createSession: (data: any) => api.post('/chat/sessions', data),
    getSession: (sessionId: string) => api.get(`/chat/sessions/${sessionId}`),
    sendMessage: (sessionId: string, data: any) => api.post(`/chat/sessions/${sessionId}/messages`, data),
    generateMission: (sessionId: string, requirements: any) => api.post(`/chat/sessions/${sessionId}/generate-mission`, requirements),
    deleteSession: (sessionId: string) => api.delete(`/chat/sessions/${sessionId}`),
  },

  // Analytics
  analytics: {
    getSystemOverview: () => api.get('/analytics/system-overview'),
    getMissionAnalytics: (missionId: string) => api.get(`/analytics/missions/${missionId}`),
    getDroneAnalytics: (droneId: string, days?: number) => api.get(`/analytics/drones/${droneId}`, { params: { days } }),
  },

  // Coordination
  coordination: {
    getStatus: (missionId?: string) => api.get('/coordination/status', { params: { mission_id: missionId } }),
    processEmergency: (data: any) => api.post('/coordination/emergency', data),
  },

  // Tasks
  tasks: {
    getSystemStatus: () => api.get('/tasks/status'),
    getPendingTasks: () => api.get('/tasks/pending'),
    getTask: (taskId: string) => api.get(`/tasks/${taskId}`),
    createTask: (data: any) => api.post('/tasks', data),
    assignTask: (taskId: string, assignee: string) => api.post(`/tasks/${taskId}/assign`, { assignee }),
    startTask: (taskId: string) => api.post(`/tasks/${taskId}/start`),
    completeTask: (taskId: string, result?: any) => api.post(`/tasks/${taskId}/complete`, result || {}),
    failTask: (taskId: string, error: string) => api.post(`/tasks/${taskId}/fail`, { error }),
  },

  // Weather
  weather: {
    getCurrent: (lat: number, lng: number) => api.get('/weather/current', { params: { latitude: lat, longitude: lng } }),
    getForecast: (lat: number, lng: number, hours: number = 24) => api.get('/weather/forecast', { params: { latitude: lat, longitude: lng, hours } }),
    checkSuitability: (lat: number, lng: number) => api.get('/weather/suitability', { params: { latitude: lat, longitude: lng } }),
    getAlerts: (lat: number, lng: number) => api.get('/weather/alerts', { params: { latitude: lat, longitude: lng } }),
  },
};

export default api;