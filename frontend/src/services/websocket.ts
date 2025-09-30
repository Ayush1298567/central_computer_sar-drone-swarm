import { io, Socket } from 'socket.io-client'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface MissionUpdate {
  mission_id: string
  status: string
  progress?: number
  drone_positions?: Array<{
    drone_id: string
    position: { lat: number; lng: number; alt: number }
    battery: number
  }>
}

export interface DiscoveryAlert {
  discovery_id: string
  mission_id: string
  drone_id: string
  object_type: string
  confidence: number
  location: { lat: number; lng: number }
  priority: 'low' | 'medium' | 'high' | 'critical'
}

class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(): void {
    if (this.socket?.connected) {
      return
    }

    this.socket = io('/', {
      transports: ['websocket'],
      upgrade: true,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      this.attemptReconnect()
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.attemptReconnect()
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.connect()
    }, delay)
  }

  // Mission-related subscriptions
  subscribeToMission(missionId: string, callback: (update: MissionUpdate) => void): void {
    if (this.socket) {
      this.socket.emit('subscribe', { type: 'mission', id: missionId })
      this.socket.on(`mission_${missionId}`, callback)
    }
  }

  unsubscribeFromMission(missionId: string, callback: (update: MissionUpdate) => void): void {
    if (this.socket) {
      this.socket.off(`mission_${missionId}`, callback)
      this.socket.emit('unsubscribe', { type: 'mission', id: missionId })
    }
  }

  // Discovery alerts subscription
  subscribeToDiscoveries(callback: (alert: DiscoveryAlert) => void): void {
    if (this.socket) {
      this.socket.emit('subscribe', { type: 'discoveries' })
      this.socket.on('discovery_alert', callback)
    }
  }

  unsubscribeFromDiscoveries(callback: (alert: DiscoveryAlert) => void): void {
    if (this.socket) {
      this.socket.off('discovery_alert', callback)
      this.socket.emit('unsubscribe', { type: 'discoveries' })
    }
  }

  // Emergency alerts subscription
  subscribeToEmergencies(callback: (alert: any) => void): void {
    if (this.socket) {
      this.socket.emit('subscribe', { type: 'emergencies' })
      this.socket.on('emergency_alert', callback)
    }
  }

  unsubscribeFromEmergencies(callback: (alert: any) => void): void {
    if (this.socket) {
      this.socket.off('emergency_alert', callback)
      this.socket.emit('unsubscribe', { type: 'emergencies' })
    }
  }

  // Send commands to drones/mission
  sendCommand(command: {
    type: string
    target: string // drone_id or mission_id
    action: string
    data?: any
  }): void {
    if (this.socket) {
      this.socket.emit('command', command)
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected ?? false
  }
}

// Export singleton instance
export const websocketService = new WebSocketService()
export default websocketService