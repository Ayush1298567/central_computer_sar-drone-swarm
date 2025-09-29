/**
 * Central export file for all SAR Mission Commander frontend types.
 */

// Mission types
export * from './mission';

// Discovery type (mock for now)
export interface Discovery {
  id: string;
  mission_id: string;
  latitude: number;
  longitude: number;
  discovery_type: string;
  priority: number;
  status: string;
  description?: string;
  timestamp: string;
}

// Drone types (excluding duplicate GeoJsonPolygon)
export type {
  Drone,
  CreateDroneRequest,
  UpdateDroneRequest,
  DroneTelemetry,
  DroneCommand,
  DronePosition,
  CameraSpecs,
  SensorSpecs,
  DroneStatus,
  ConnectionStatus,
  DroneCommandType,
  CommandPriority,
  DroneResponse,
  DronesResponse,
  DroneTelemetryResponse,
  DroneCommandResponse,
  DroneFleet,
  DronePerformanceMetrics,
  MaintenanceInterval,
  DroneUpdateEvent,
  DroneAlert,
  DroneAlertType,
  AlertSeverity,
  FlightPlan,
  Waypoint,
  WaypointAction,
  SearchPattern,
  GimbalSettings,
  DroneMissionAssignment,
  SearchParameters,
} from './drone';

// API types (from api.ts)
export type {
  ApiResponse,
  ApiError,
  RequestConfig,
} from '../services/api';

export {
  ApiErrorHandler,
  RetryHandler,
  ApiCache,
  apiCache,
} from '../services/api';

// WebSocket types (from websocketService.ts)
export type {
  WebSocketMessage,
  ConnectionHandler,
  MessageHandler,
  Subscription,
} from '../services/websocketService';

export {
  websocketService,
  WebSocketSubscriptions,
  useWebSocketConnection,
} from '../services/websocketService';