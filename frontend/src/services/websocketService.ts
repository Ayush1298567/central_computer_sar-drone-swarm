/**
 * WebSocket Service for SAR Drone System
 * Handles real-time communication with backend
 */

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
  id?: string;
}

export interface WebSocketEventCallback {
  (message: WebSocketMessage): void;
}

export interface ConnectionStatus {
  isConnected: boolean;
  isConnecting: boolean;
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private eventListeners: Map<string, WebSocketEventCallback[]> = new Map();
  private connectionStatus: ConnectionStatus = {
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0
  };

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
    this.connect();
  }

  /**
   * Establish WebSocket connection
   */
  private connect(): void {
    if (this.ws?.readyState === WebSocket.CONNECTING || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.updateConnectionStatus({ isConnecting: true, error: undefined });

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.updateConnectionStatus({
          isConnected: true,
          isConnecting: false,
          lastConnected: new Date(),
          reconnectAttempts: this.reconnectAttempts
        });

        // Send queued messages
        this.flushMessageQueue();

        // Start heartbeat
        this.startHeartbeat();
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
        this.updateConnectionStatus({
          isConnected: false,
          isConnecting: false,
          reconnectAttempts: this.reconnectAttempts
        });

        this.stopHeartbeat();

        // Attempt to reconnect if not manually closed
        if (event.code !== 1000) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus({
          error: 'Connection error occurred'
        });
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.updateConnectionStatus({
        isConnecting: false,
        error: 'Failed to create connection'
      });
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.updateConnectionStatus({
        error: 'Max reconnection attempts reached'
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start heartbeat to monitor connection health
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', payload: {}, timestamp: Date.now() });
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const callbacks = this.eventListeners.get(message.type) || [];
    const globalCallbacks = this.eventListeners.get('*') || [];

    // Call type-specific callbacks
    callbacks.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error(`Error in message callback for type ${message.type}:`, error);
      }
    });

    // Call global callbacks
    globalCallbacks.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in global message callback:', error);
      }
    });
  }

  /**
   * Send message through WebSocket
   */
  public send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for later sending
      this.messageQueue.push(message);
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Subscribe to message events
   */
  public subscribe(eventType: string, callback: WebSocketEventCallback): () => void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }

    this.eventListeners.get(eventType)!.push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.eventListeners.get(eventType);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * Unsubscribe from all events for a callback
   */
  public unsubscribe(callback: WebSocketEventCallback): void {
    this.eventListeners.forEach(callbacks => {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    });
  }

  /**
   * Update connection status
   */
  private updateConnectionStatus(updates: Partial<ConnectionStatus>): void {
    this.connectionStatus = { ...this.connectionStatus, ...updates };

    // Emit connection status change event
    this.handleMessage({
      type: 'connection_status',
      payload: this.connectionStatus,
      timestamp: Date.now()
    });
  }

  /**
   * Get current connection status
   */
  public getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  /**
   * Manually disconnect
   */
  public disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.updateConnectionStatus({
      isConnected: false,
      isConnecting: false
    });
  }

  /**
   * Get queued message count
   */
  public getQueueLength(): number {
    return this.messageQueue.length;
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();