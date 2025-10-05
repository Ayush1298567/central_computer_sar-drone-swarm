/**
 * WebSocket service for SAR Mission Commander
 */
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  user_id?: string;
  mission_id?: string;
}

export interface NotificationMessage {
  id: string;
  type: 'mission_update' | 'drone_alert' | 'discovery' | 'emergency' | 'system' | 'weather';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  read: boolean;
  action_url?: string;
}

export interface WebSocketServiceConfig {
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  maxReconnectAttempts?: number;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000; // Start with 1 second
  private heartbeatInterval = 30000; // 30 seconds
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private messageHandlers: Map<string, ((message: WebSocketMessage) => void)[]> = new Map();
  private isConnected = false;
  private clientId: string;

  constructor(config?: WebSocketServiceConfig) {
    if (config) {
      this.maxReconnectAttempts = config.maxReconnectAttempts || this.maxReconnectAttempts;
      this.reconnectInterval = config.reconnectInterval || this.reconnectInterval;
      this.heartbeatInterval = config.heartbeatInterval || this.heartbeatInterval;
    }

    // Generate unique client ID
    this.clientId = this.generateClientId();
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = import.meta.env.PROD
          ? window.location.host
          : 'localhost:8000';

        const wsUrl = `${protocol}//${host}/ws/client/${this.clientId}`;

        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();

          // Send initial subscription
          this.send({
            type: 'subscribe',
            data: { subscriptions: ['notifications', 'chat_messages', 'mission_updates', 'system_alerts'] }
          });

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.stopHeartbeat();

          if (event.code !== 1000) { // Not a normal closure
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Send message to server
   */
  send(message: WebSocketMessage): void {
    if (this.isConnected && this.ws) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
    }
  }

  /**
   * Subscribe to message types
   */
  subscribe(types: string[]): void {
    this.send({
      type: 'subscribe',
      data: { subscriptions: types }
    });
  }

  /**
   * Unsubscribe from message types
   */
  unsubscribe(types: string[]): void {
    this.send({
      type: 'unsubscribe',
      data: { subscriptions: types }
    });
  }

  /**
   * Add message handler
   */
  onMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  /**
   * Remove message handler
   */
  offMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Check if connected
   */
  get isWebSocketConnected(): boolean {
    return this.isConnected;
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
  } {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle heartbeat
    if (message.type === 'pong') {
      return;
    }

    // Call registered handlers
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in WebSocket message handler:', error);
      }
    });

    // Call wildcard handlers
    const wildcardHandlers = this.messageHandlers.get('*') || [];
    wildcardHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in wildcard WebSocket message handler:', error);
      }
    });
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService({
  maxReconnectAttempts: 5,
  reconnectInterval: 1000,
  heartbeatInterval: 30000
});

export default websocketService;