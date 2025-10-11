import api from './api'
import websocketService from './websocket'

export interface EmergencyAlert {
  id: string
  type: 'drone_failure' | 'communication_loss' | 'weather_emergency' | 'discovery_urgent' | 'system_failure'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  drone_id?: string
  mission_id?: string
  location?: {
    lat: number
    lng: number
    alt: number
  }
  timestamp: string
  resolved: boolean
  resolution?: string
}

export interface EmergencyResponse {
  alert_id: string
  response_type: 'acknowledge' | 'escalate' | 'resolve'
  responder: string
  notes?: string
  timestamp: string
}

export const emergencyService = {
  // Get all emergency alerts
  async getEmergencyAlerts(params?: { 
    severity?: string
    resolved?: boolean
    startDate?: string
    endDate?: string
  }) {
    const response = await api.get('/emergency/alerts', { params })
    return response.data
  },

  // Get active emergency alerts
  async getActiveAlerts() {
    const response = await api.get('/emergency/alerts/active')
    return response.data
  },

  // Create emergency alert
  async createEmergencyAlert(alert: Omit<EmergencyAlert, 'id' | 'timestamp' | 'resolved'>) {
    const response = await api.post('/emergency/alerts', alert)
    return response.data
  },

  // Acknowledge emergency alert
  async acknowledgeAlert(alertId: string, responder: string, notes?: string) {
    const response = await api.post(`/emergency/alerts/${alertId}/acknowledge`, {
      responder,
      notes
    })
    return response.data
  },

  // Resolve emergency alert
  async resolveAlert(alertId: string, resolution: string, responder: string) {
    const response = await api.post(`/emergency/alerts/${alertId}/resolve`, {
      resolution,
      responder
    })
    return response.data
  },

  // Escalate emergency alert
  async escalateAlert(alertId: string, escalationReason: string, responder: string) {
    const response = await api.post(`/emergency/alerts/${alertId}/escalate`, {
      escalationReason,
      responder
    })
    return response.data
  },

  // Emergency stop all drones
  async emergencyStopAll(reason: string, operator: string) {
    const response = await api.post('/emergency/stop-all', {
      reason,
      operator
    })
    return response.data
  },

  // Emergency return to home for specific drone
  async emergencyReturnToHome(droneId: string, reason: string, operator: string) {
    const response = await api.post(`/emergency/drones/${droneId}/return-home`, {
      reason,
      operator
    })
    return response.data
  },

  // Emergency landing for specific drone
  async emergencyLanding(droneId: string, location: { lat: number; lng: number }, reason: string, operator: string) {
    const response = await api.post(`/emergency/drones/${droneId}/land`, {
      location,
      reason,
      operator
    })
    return response.data
  },

  // Get emergency procedures
  async getEmergencyProcedures() {
    const response = await api.get('/emergency/procedures')
    return response.data
  },

  // Test emergency systems
  async testEmergencySystems() {
    const response = await api.post('/emergency/test')
    return response.data
  },

  // Get emergency statistics
  async getEmergencyStats(params?: { startDate?: string; endDate?: string }) {
    const response = await api.get('/emergency/stats', { params })
    return response.data
  },

  // WebSocket emergency subscription
  subscribeToEmergencyAlerts(callback: (alert: EmergencyAlert) => void) {
    websocketService.subscribeToEmergency()
    
    const handleEmergencyAlert = (event: CustomEvent) => {
      callback(event.detail)
    }
    
    window.addEventListener('emergencyAlert', handleEmergencyAlert as EventListener)
    
    return () => {
      window.removeEventListener('emergencyAlert', handleEmergencyAlert as EventListener)
      websocketService.unsubscribeFromEmergency()
    }
  },

  // Broadcast emergency alert via WebSocket
  async broadcastEmergencyAlert(alert: EmergencyAlert) {
    const response = await api.post('/emergency/broadcast', alert)
    return response.data
  }
}
