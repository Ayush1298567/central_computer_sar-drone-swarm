/**
 * Central export file for all SAR Mission Commander frontend services.
 */

// Core API services
export { default as api } from './api'
export { default as websocketService } from './websocket'

// Entity services
export { droneService } from './drones'
export { missionService } from './missions'
export { discoveryService } from './discoveries'
export { analyticsService } from './analytics'
export { emergencyService } from './emergency'
export { computerVisionService } from './computerVision'
export { adaptivePlanningService } from './adaptivePlanning'

// Legacy services (for backward compatibility)
export { default as chatService } from './chatService'
export { droneService as droneServiceLegacy } from './droneService'
export { missionService as missionServiceLegacy } from './missionService'
export { websocketService as websocketServiceLegacy } from './websocketService'

// Advanced API services
export {
  apiService,
  cachedApiService,
  API_ENDPOINTS,
  ApiErrorHandler,
  RetryHandler,
  ApiCache,
  apiCache,
} from './api';

export {
  MissionService,
  MissionErrorHandler,
} from './missionService';

export {
  websocketService as advancedWebSocketService,
  WebSocketSubscriptions,
  useWebSocketConnection,
} from './websocketService';

// Type exports
export type {
  ApiResponse,
  ApiError,
  RequestConfig,
  WebSocketMessage,
  ConnectionHandler,
  MessageHandler,
  Subscription,
} from './api';

export type {
  WebSocketMessage as AdvancedWebSocketMessage,
  ConnectionHandler as AdvancedConnectionHandler,
  MessageHandler as AdvancedMessageHandler,
  Subscription as AdvancedSubscription,
} from './websocketService';