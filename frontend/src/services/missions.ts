import api from './api'
import { Mission, MissionCreate, MissionUpdate } from '../types/mission'

export const missionService = {
  // Get all missions
  async getMissions(params?: { skip?: number; limit?: number; status?: string }) {
    const response = await api.get('/missions', { params })
    return response.data
  },

  // Get mission by ID
  async getMission(missionId: string) {
    const response = await api.get(`/missions/${missionId}`)
    return response.data
  },

  // Create new mission
  async createMission(mission: MissionCreate) {
    const response = await api.post('/missions', mission)
    return response.data
  },

  // Update mission
  async updateMission(missionId: string, mission: MissionUpdate) {
    const response = await api.put(`/missions/${missionId}`, mission)
    return response.data
  },

  // Delete mission
  async deleteMission(missionId: string) {
    const response = await api.delete(`/missions/${missionId}`)
    return response.data
  },

  // Start mission
  async startMission(missionId: string) {
    const response = await api.post(`/missions/${missionId}/start`)
    return response.data
  },

  // Stop mission
  async stopMission(missionId: string) {
    const response = await api.post(`/missions/${missionId}/stop`)
    return response.data
  },

  // Get mission status
  async getMissionStatus(missionId: string) {
    const response = await api.get(`/missions/${missionId}/status`)
    return response.data
  },

  // Get mission progress
  async getMissionProgress(missionId: string) {
    const response = await api.get(`/missions/${missionId}/progress`)
    return response.data
  },

  // Assign drones to mission
  async assignDronesToMission(missionId: string, droneIds: string[]) {
    const response = await api.post(`/missions/${missionId}/assign-drones`, { droneIds })
    return response.data
  },
}