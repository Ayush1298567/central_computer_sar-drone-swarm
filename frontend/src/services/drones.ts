import api from './api'
import { Drone, DroneCreate, DroneUpdate } from '../types/drone'

export const droneService = {
  // Get all drones
  async getDrones(params?: { skip?: number; limit?: number; status?: string }) {
    const response = await api.get('/drones', { params })
    return response.data
  },

  // Get drone by ID
  async getDrone(droneId: string) {
    const response = await api.get(`/drones/${droneId}`)
    return response.data
  },

  // Create new drone
  async createDrone(drone: DroneCreate) {
    const response = await api.post('/drones', drone)
    return response.data
  },

  // Update drone
  async updateDrone(droneId: string, drone: DroneUpdate) {
    const response = await api.put(`/drones/${droneId}`, drone)
    return response.data
  },

  // Delete drone
  async deleteDrone(droneId: string) {
    const response = await api.delete(`/drones/${droneId}`)
    return response.data
  },

  // Get drone status
  async getDroneStatus(droneId: string) {
    const response = await api.get(`/drones/${droneId}/status`)
    return response.data
  },

  // Update drone position
  async updateDronePosition(droneId: string, position: { lat: number; lng: number; alt: number }) {
    const response = await api.put(`/drones/${droneId}/position`, position)
    return response.data
  },

  // Get drone telemetry
  async getDroneTelemetry(droneId: string, params?: { start?: string; end?: string }) {
    const response = await api.get(`/drones/${droneId}/telemetry`, { params })
    return response.data
  },
}