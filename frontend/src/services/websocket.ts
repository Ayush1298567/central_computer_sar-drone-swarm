import { io, Socket } from 'socket.io-client'

class WebSocketService {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(serverUrl: string = 'ws://localhost:8000'): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = io(serverUrl, {
        transports: ['websocket'],
        timeout: 10000,
      })

      this.socket.on('connect', () => {
        console.log('Connected to WebSocket server')
        this.reconnectAttempts = 0
        resolve()
      })

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          setTimeout(() => {
            this.connect(serverUrl)
          }, this.reconnectDelay * this.reconnectAttempts)
        } else {
          reject(error)
        }
      })

      this.socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server')
      })

      // Set up event listeners
      this.setupEventListeners()
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  private setupEventListeners() {
    if (!this.socket) return

    // Drone updates
    this.socket.on('drone_update', (data) => {
      console.log('Drone update received:', data)
      // Dispatch custom event for React components
      window.dispatchEvent(new CustomEvent('droneUpdate', { detail: data }))
    })

    // Mission updates
    this.socket.on('mission_update', (data) => {
      console.log('Mission update received:', data)
      window.dispatchEvent(new CustomEvent('missionUpdate', { detail: data }))
    })

    // Discovery updates
    this.socket.on('discovery_update', (data) => {
      console.log('Discovery update received:', data)
      window.dispatchEvent(new CustomEvent('discoveryUpdate', { detail: data }))
    })

    // Emergency alerts
    this.socket.on('emergency_alert', (data) => {
      console.log('Emergency alert received:', data)
      window.dispatchEvent(new CustomEvent('emergencyAlert', { detail: data }))
    })
  }

  // Emit events
  emit(event: string, data: any) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected. Cannot emit event:', event)
    }
  }

  // Subscribe to drone updates
  subscribeToDrone(droneId: string) {
    this.emit('subscribe_drone', { droneId })
  }

  // Unsubscribe from drone updates
  unsubscribeFromDrone(droneId: string) {
    this.emit('unsubscribe_drone', { droneId })
  }

  // Subscribe to mission updates
  subscribeToMission(missionId: string) {
    this.emit('subscribe_mission', { missionId })
  }

  // Unsubscribe from mission updates
  unsubscribeFromMission(missionId: string) {
    this.emit('unsubscribe_mission', { missionId })
  }

  // Send command to drone
  sendDroneCommand(droneId: string, command: any) {
    this.emit('drone_command', { droneId, command })
  }

  // Send mission command
  sendMissionCommand(missionId: string, command: any) {
    this.emit('mission_command', { missionId, command })
  }
}

export const websocketService = new WebSocketService()
export default websocketService