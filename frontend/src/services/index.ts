// Export all services
export { apiService, ApiService } from './api'
export { missionService, MissionService } from './missionService'
export { droneService, DroneService } from './droneService'
export { authService, AuthService } from './authService'
export { default as websocketService, WebSocketService } from './websocketService'

// Import services for initialization functions
import { authService } from './authService'
import websocketService from './websocketService'

// Re-export types for convenience
export type {
  ApiResponse,
  ApiError,
  Mission,
  Drone,
  Discovery,
  User,
  WebSocketMessage,
  WebSocketMessageType,
} from '@/types'

// Export commonly used types
export type {
  MissionListResponse,
  MissionDetailResponse,
  MissionCreateRequest,
  MissionUpdateRequest,
  DroneListResponse,
  DroneDetailResponse,
  LoginRequest,
  LoginResponse,
} from '@/types/api'

// Service initialization function
export const initializeServices = () => {
  // Initialize WebSocket connection
  websocketService.connect().catch(error => {
    console.error('Failed to initialize WebSocket service:', error)
  })

  // Ensure auth token is valid
  authService.ensureValidToken().catch(error => {
    console.error('Failed to validate auth token:', error)
  })
}

// Cleanup function
export const cleanupServices = () => {
  websocketService.disconnect()
}