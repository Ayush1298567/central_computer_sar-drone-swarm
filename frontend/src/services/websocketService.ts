/**
 * WebSocket service for real-time communication with the SAR Mission Commander backend.
 * Handles real-time updates for missions, drones, discoveries, and system status.
 */

import {
  WS_BASE_URL,
  ApiError,
  ApiErrorHandler,
} from './api';

import {
  MissionProgress,
  MissionEvent,
  DroneUpdateEvent,
  DroneAlert,
} from '../types/mission';

import {
  DroneTelemetry,
  DroneStatus,
  ConnectionStatus,
} from '../types/drone';

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  mission_id?: string;
  drone_id?: string;
}

export interface ConnectionHandler {
  (connected: boolean): void;
}

export interface MessageHandler {
  (message: WebSocketMessage): void;
}

export interface Subscription {
  type: string;
  handler: MessageHandler;
  mission_id?: string;
  drone_id?: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private subscriptions: Map<string, Subscription[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private heartbeatInterval: number | null = null;
  private isConnecting = false;
  private shouldReconnect = true;

  constructor(url: string = WS_BASE_URL) {
    this.url = url;
  }

  /**
   * Connect to the WebSocket server
   */
  async connect(url?: string): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    if (url) {
      this.url = url;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);

      return new Promise((resolve, reject) => {
        if (!this.ws) {
          this.isConnecting = false;
          reject(new Error('Failed to create WebSocket connection'));
          return;
        }

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startHeartbeat();

          // Notify connection handlers
          this.connectionHandlers.forEach(handler => {
            try {
              handler(true);
            } catch (error) {
              console.error('Error in connection handler:', error);
            }
          });

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();

          // Notify connection handlers
          this.connectionHandlers.forEach(handler => {
            try {
              handler(false);
            } catch (error) {
              console.error('Error in connection handler:', error);
            }
          });

          // Attempt to reconnect if not manually closed
          if (event.code !== 1000 && this.shouldReconnect) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;

          if (this.reconnectAttempts === 0) {
            reject(new Error('WebSocket connection failed'));
          }
        };

        // Timeout after 10 seconds
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false;
            this.ws?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);
      });
    } catch (error) {
      this.isConnecting = false;
      throw ApiErrorHandler.handleError(error);
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.shouldReconnect = false;

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.stopHeartbeat();
  }

  /**
   * Send a message through the WebSocket
   */
  send(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Subscribe to specific message types
   */
  subscribe(
    type: string,
    handler: MessageHandler,
    mission_id?: string,
    drone_id?: string
  ): () => void {
    const subscription: Subscription = {
      type,
      handler,
      mission_id,
      drone_id,
    };

    const key = this.getSubscriptionKey(type, mission_id, drone_id);
    if (!this.subscriptions.has(key)) {
      this.subscriptions.set(key, []);
    }

    this.subscriptions.get(key)!.push(subscription);

    // Send subscription message to server
    this.sendSubscriptionMessage('subscribe', type, mission_id, drone_id);

    // Return unsubscribe function
    return () => {
      this.unsubscribe(type, handler, mission_id, drone_id);
    };
  }

  /**
   * Unsubscribe from specific message types
   */
  unsubscribe(
    type: string,
    handler: MessageHandler,
    mission_id?: string,
    drone_id?: string
  ): void {
    const key = this.getSubscriptionKey(type, mission_id, drone_id);
    const subscriptions = this.subscriptions.get(key);

    if (subscriptions) {
      const index = subscriptions.findIndex(sub => sub.handler === handler);
      if (index !== -1) {
        subscriptions.splice(index, 1);
      }

      if (subscriptions.length === 0) {
        this.subscriptions.delete(key);
        // Send unsubscription message to server
        this.sendSubscriptionMessage('unsubscribe', type, mission_id, drone_id);
      }
    }
  }

  /**
   * Add connection status change handler
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);

    // Return unsubscribe function
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index !== -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  getConnectionState(): 'connecting' | 'connected' | 'disconnected' {
    if (this.isConnecting) {
      return 'connecting';
    }

    if (this.isConnected()) {
      return 'connected';
    }

    return 'disconnected';
  }

  /**
   * Get active subscription count
   */
  getSubscriptionCount(): number {
    let count = 0;
    for (const subscriptions of this.subscriptions.values()) {
      count += subscriptions.length;
    }
    return count;
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    const { type, payload, mission_id, drone_id } = message;

    // Handle heartbeat responses
    if (type === 'heartbeat') {
      return;
    }

    // Handle error messages
    if (type === 'error') {
      console.error('WebSocket server error:', payload);
      return;
    }

    // Find matching subscriptions
    const subscriptions = this.findMatchingSubscriptions(type, mission_id, drone_id);

    // Call handlers
    subscriptions.forEach(subscription => {
      try {
        subscription.handler(message);
      } catch (error) {
        console.error('Error in WebSocket message handler:', error);
      }
    });
  }

  /**
   * Find subscriptions that match the message
   */
  private findMatchingSubscriptions(
    type: string,
    mission_id?: string,
    drone_id?: string
  ): Subscription[] {
    const matching: Subscription[] = [];

    // Check specific subscriptions
    const specificKey = this.getSubscriptionKey(type, mission_id, drone_id);
    if (this.subscriptions.has(specificKey)) {
      matching.push(...this.subscriptions.get(specificKey)!);
    }

    // Check wildcard subscriptions (mission_id only)
    if (mission_id) {
      const missionKey = this.getSubscriptionKey(type, mission_id);
      if (this.subscriptions.has(missionKey)) {
        matching.push(...this.subscriptions.get(missionKey)!);
      }
    }

    // Check type-only subscriptions
    const typeKey = this.getSubscriptionKey(type);
    if (this.subscriptions.has(typeKey)) {
      matching.push(...this.subscriptions.get(typeKey)!);
    }

    return matching;
  }

  /**
   * Get subscription key for storage
   */
  private getSubscriptionKey(type: string, mission_id?: string, drone_id?: string): string {
    let key = type;
    if (mission_id) key += `:mission:${mission_id}`;
    if (drone_id) key += `:drone:${drone_id}`;
    return key;
  }

  /**
   * Send subscription message to server
   */
  private sendSubscriptionMessage(
    action: 'subscribe' | 'unsubscribe',
    type: string,
    mission_id?: string,
    drone_id?: string
  ): void {
    const message: WebSocketMessage = {
      type: 'subscription',
      payload: {
        action,
        message_type: type,
        mission_id,
        drone_id,
      },
      timestamp: new Date().toISOString(),
    };

    this.send(message);
  }

  /**
   * Start heartbeat mechanism
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'heartbeat',
          payload: { timestamp: new Date().toISOString() },
          timestamp: new Date().toISOString(),
        });
      }
    }, 30000); // Every 30 seconds
  }

  /**
   * Stop heartbeat mechanism
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);

    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect();
      }
    }, delay);
  }
}

// Global WebSocket service instance
export const websocketService = new WebSocketService();

// Convenience functions for common subscriptions
export const WebSocketSubscriptions = {
  /**
   * Subscribe to mission progress updates
   */
  subscribeToMissionProgress: (
    missionId: string,
    handler: (progress: MissionProgress) => void
  ): (() => void) => {
    return websocketService.subscribe('mission_progress', (message) => {
      if (message.payload?.mission_id === missionId) {
        handler(message.payload);
      }
    }, missionId);
  },

  /**
   * Subscribe to mission events
   */
  subscribeToMissionEvents: (
    missionId: string,
    handler: (event: MissionEvent) => void
  ): (() => void) => {
    return websocketService.subscribe('mission_event', (message) => {
      if (message.payload?.mission_id === missionId) {
        handler(message.payload);
      }
    }, missionId);
  },

  /**
   * Subscribe to drone telemetry updates
   */
  subscribeToDroneTelemetry: (
    droneId: string,
    handler: (telemetry: DroneTelemetry) => void
  ): (() => void) => {
    return websocketService.subscribe('drone_telemetry', (message) => {
      if (message.payload?.drone_id === droneId) {
        handler(message.payload);
      }
    }, undefined, droneId);
  },

  /**
   * Subscribe to drone alerts
   */
  subscribeToDroneAlerts: (
    droneId: string,
    handler: (alert: DroneAlert) => void
  ): (() => void) => {
    return websocketService.subscribe('drone_alert', (message) => {
      if (message.payload?.drone_id === droneId) {
        handler(message.payload);
      }
    }, undefined, droneId);
  },

  /**
   * Subscribe to system status updates
   */
  subscribeToSystemStatus: (
    handler: (status: any) => void
  ): (() => void) => {
    return websocketService.subscribe('system_status', handler);
  },

  /**
   * Subscribe to discovery updates
   */
  subscribeToDiscoveries: (
    missionId: string,
    handler: (discovery: any) => void
  ): (() => void) => {
    return websocketService.subscribe('discovery_update', (message) => {
      if (message.payload?.mission_id === missionId) {
        handler(message.payload);
      }
    }, missionId);
  },

  /**
   * Subscribe to all mission updates for a specific mission
   */
  subscribeToAllMissionUpdates: (
    missionId: string,
    handlers: {
      onProgress?: (progress: MissionProgress) => void;
      onEvent?: (event: MissionEvent) => void;
      onDiscovery?: (discovery: any) => void;
    }
  ): (() => void) => {
    const unsubscribers: (() => void)[] = [];

    if (handlers.onProgress) {
      unsubscribers.push(
        WebSocketSubscriptions.subscribeToMissionProgress(missionId, handlers.onProgress)
      );
    }

    if (handlers.onEvent) {
      unsubscribers.push(
        WebSocketSubscriptions.subscribeToMissionEvents(missionId, handlers.onEvent)
      );
    }

    if (handlers.onDiscovery) {
      unsubscribers.push(
        WebSocketSubscriptions.subscribeToDiscoveries(missionId, handlers.onDiscovery)
      );
    }

    // Return combined unsubscribe function
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  },
};

// Connection monitoring hook helper
export const useWebSocketConnection = () => {
  const [isConnected, setIsConnected] = React.useState(websocketService.isConnected());
  const [connectionState, setConnectionState] = React.useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  React.useEffect(() => {
    const unsubscribe = websocketService.onConnectionChange((connected) => {
      setIsConnected(connected);
      setConnectionState(connected ? 'connected' : 'disconnected');
    });

    // Set initial state
    setConnectionState(websocketService.getConnectionState());

    return unsubscribe;
  }, []);

  return { isConnected, connectionState };
};

// React import for the hook (this would be in a separate file in a real app)
import React from 'react';