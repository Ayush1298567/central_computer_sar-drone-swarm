import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Mission endpoints
export const missionApi = {
  create: (name, description) => api.post('/missions', null, { params: { name, description } }),
  getAll: () => api.get('/missions'),
  getById: (id) => api.get(`/missions/${id}`),
  start: (id) => api.post(`/missions/${id}/start`),
  pause: (id) => api.post(`/missions/${id}/pause`),
  resume: (id) => api.post(`/missions/${id}/resume`),
};

// Drone endpoints
export const droneApi = {
  create: (name, capabilities, batteryCapacity) => 
    api.post('/drones', null, { params: { name, capabilities, batteryCapacity } }),
  getAll: () => api.get('/drones'),
  getById: (id) => api.get(`/drones/${id}`),
  update: (id, data) => api.put(`/drones/${id}`, null, { params: data }),
  delete: (id) => api.delete(`/drones/${id}`),
};

// Mission planning endpoints
export const planningApi = {
  start: (description, sessionId) => 
    api.post('/mission-planning/start', null, { params: { description, session_id: sessionId } }),
  respond: (sessionId, response) => 
    api.post('/mission-planning/respond', null, { params: { session_id: sessionId, response } }),
  getStatus: (sessionId) => 
    api.get(`/mission-planning/status/${sessionId}`),
};

// Command endpoints
export const commandApi = {
  send: (command, droneId, sessionId) => 
    api.post('/commands/send', null, { params: { command, drone_id: droneId, session_id: sessionId } }),
  emergency: (command, sessionId) => 
    api.post('/commands/emergency', null, { params: { command, session_id: sessionId } }),
};

// Telemetry endpoints
export const telemetryApi = {
  getDrone: (droneId, limit) => 
    api.get(`/telemetry/drone/${droneId}`, { params: { limit } }),
  getMission: (missionId, limit) => 
    api.get(`/telemetry/mission/${missionId}`, { params: { limit } }),
};

// Discovery endpoints
export const discoveryApi = {
  getMission: (missionId) => 
    api.get(`/discoveries/mission/${missionId}`),
};

// Agent endpoints
export const agentApi = {
  getAll: () => api.get('/agents'),
  getClusters: () => api.get('/agents/clusters'),
  restart: (agentName) => api.post(`/agents/${agentName}/restart`),
};

// System endpoints
export const systemApi = {
  health: () => api.get('/health'),
  status: () => api.get('/status'),
};

export default api;