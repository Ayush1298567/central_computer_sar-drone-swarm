import { io, Socket } from 'socket.io-client'
import {
  WebSocketMessage,
  DronePositionUpdate,
  MissionStatusUpdate,
  DiscoveryUpdate,
  EmergencyAlert,
  CoordinationCommand,
  SystemStatus,
} from '@/types'

export type WebSocketEventHandler<T = any> = (data: T) => void

export interface WebSocketServiceConfig {
  url: string
  options?: {
    autoConnect?: boolean
    reconnection?: boolean
    reconnectionAttempts?: number
    reconnectionDelay?: number
  }
}

class WebSocketService {
  private socket: Socket | null = null
  private config: WebSocketServiceConfig
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map()
  private isConnected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(config: WebSocketServiceConfig) {
    this.config = {
      options: {
        autoConnect: false,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        ...config.options,
      },
      ...config,
    }

    this.maxReconnectAttempts = this.config.options?.reconnectionAttempts || 5
    this.reconnectDelay = this.config.options?.reconnectionDelay || 1000
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve()
        return
      }

      this.socket = io(this.config.url, {
        autoConnect: false,
        reconnection: this.config.options?.reconnection || true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
      })

      this.socket.on('connect', () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.reconnectAttempts = 0
        resolve()
      })

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason)
        this.isConnected = false
        this.handleDisconnect(reason)
      })

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        this.handleConnectionError(error)
        reject(error)
      })

      // Register event handlers
      this.registerCoreEventHandlers()

      // Connect
      this.socket.connect()
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
      this.eventHandlers.clear()
    }
  }

  /**
   * Check if WebSocket is connected
   */
  get connected(): boolean {
    return this.isConnected && this.socket?.connected === true
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean
    reconnectAttempts: number
    maxReconnectAttempts: number
  } {
    return {
      connected: this.connected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  on<T = any>(event: string, handler: WebSocketEventHandler<T>): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set())
    }

    this.eventHandlers.get(event)!.add(handler)

    // Return unsubscribe function
    return () => {
      this.off(event, handler)
    }
  }

  /**
   * Unsubscribe from WebSocket events
   */
  off<T = any>(event: string, handler: WebSocketEventHandler<T>): void {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.eventHandlers.delete(event)
      }
    }
  }

  /**
   * Emit event to server
   */
  emit(event: string, data?: any): void {
    if (this.connected && this.socket) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected. Cannot emit event:', event)
    }
  }

  /**
   * Subscribe to drone position updates
   */
  onDroneUpdate(handler: WebSocketEventHandler<DronePositionUpdate>): () => void {
    return this.on('drone_update', handler)
  }

  /**
   * Subscribe to mission status updates
   */
  onMissionUpdate(handler: WebSocketEventHandler<MissionStatusUpdate>): () => void {
    return this.on('mission_update', handler)
  }

  /**
   * Subscribe to discovery updates
   */
  onDiscoveryUpdate(handler: WebSocketEventHandler<DiscoveryUpdate>): () => void {
    return this.on('discovery_update', handler)
  }

  /**
   * Subscribe to emergency alerts
   */
  onEmergencyAlert(handler: WebSocketEventHandler<EmergencyAlert>): () => void {
    return this.on('emergency_alert', handler)
  }

  /**
   * Subscribe to coordination commands
   */
  onCoordinationCommand(handler: WebSocketEventHandler<CoordinationCommand>): () => void {
    return this.on('coordination_command', handler)
  }

  /**
   * Subscribe to system status updates
   */
  onSystemStatus(handler: WebSocketEventHandler<SystemStatus>): () => void {
    return this.on('system_status', handler)
  }

  /**
   * Join mission room
   */
  joinMission(missionId: string): void {
    this.emit('join_mission', { mission_id: missionId })
  }

  /**
   * Leave mission room
   */
  leaveMission(missionId: string): void {
    this.emit('leave_mission', { mission_id: missionId })
  }

  /**
   * Join drone room
   */
  joinDrone(droneId: string): void {
    this.emit('join_drone', { drone_id: droneId })
  }

  /**
   * Leave drone room
   */
  leaveDrone(droneId: string): void {
    this.emit('leave_drone', { drone_id: droneId })
  }

  /**
   * Send chat message
   */
  sendChatMessage(missionId: string, message: string): void {
    this.emit('chat_message', {
      mission_id: missionId,
      message,
    })
  }

  /**
   * Acknowledge emergency alert
   */
  acknowledgeEmergency(alertId: string): void {
    this.emit('acknowledge_emergency', { alert_id: alertId })
  }

  /**
   * Send heartbeat to keep connection alive
   */
  sendHeartbeat(): void {
    this.emit('heartbeat')
  }

  /**
   * Request system status
   */
  requestSystemStatus(): void {
    this.emit('request_system_status')
  }

  private registerCoreEventHandlers(): void {
    if (!this.socket) return

    // Handle incoming messages
    this.socket.on('message', (message: WebSocketMessage) => {
      this.handleMessage(message)
    })

    // Handle heartbeat responses
    this.socket.on('heartbeat_response', (data: any) => {
      console.log('Heartbeat response:', data)
    })

    // Handle reconnection
    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts')
      this.isConnected = true
      this.reconnectAttempts = 0
    })

    // Handle reconnection attempts
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('WebSocket reconnection attempt:', attemptNumber)
      this.reconnectAttempts = attemptNumber
    })

    // Handle reconnection failed
    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed')
      this.isConnected = false
    })
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.payload)
        } catch (error) {
          console.error('Error in WebSocket event handler:', error)
        }
      })
    }
  }

  private handleDisconnect(reason: string): void {
    this.isConnected = false

    // Emit disconnect event
    const handlers = this.eventHandlers.get('disconnect')
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler({ reason })
        } catch (error) {
          console.error('Error in disconnect handler:', error)
        }
      })
    }

    // Auto-reconnect logic
    if (this.config.options?.reconnection && this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        if (!this.connected) {
          this.connect().catch(error => {
            console.error('Failed to reconnect:', error)
          })
        }
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts))
    }
  }

  private handleConnectionError(error: any): void {
    const handlers = this.eventHandlers.get('connection_error')
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(error)
        } catch (err) {
          console.error('Error in connection error handler:', err)
        }
      })
    }
  }
}

// Create and export default instance
const websocketService = new WebSocketService({
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  options: {
    autoConnect: false,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  },
})

export { WebSocketService }
export default websocketService