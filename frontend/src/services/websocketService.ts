import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from '../types/api';

export type EventCallback = (data: any) => void;
export type ConnectionCallback = () => void;

export class WebSocketService {
  private socket: Socket | null = null;
  private eventListeners: Map<string, EventCallback[]> = new Map();
  private connectionListeners: Map<string, ConnectionCallback[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private isConnected = false;
  private isConnecting = false;

  constructor(private url: string = 'ws://localhost:8000') {
    this.connect();
  }

  /**
   * Initialize WebSocket connection with automatic reconnection
   */
  private connect(): void {
    if (this.isConnecting || this.isConnected) return;

    this.isConnecting = true;
    console.log('Attempting to connect to WebSocket...');

    this.socket = io(this.url, {
      transports: ['websocket'],
      timeout: 5000,
      reconnection: false, // We'll handle reconnection manually
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected successfully');
      this.isConnected = true;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.startHeartbeat();

      // Process queued messages
      this.processMessageQueue();

      // Notify connection listeners
      this.notifyConnectionListeners('connect');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.isConnected = false;
      this.isConnecting = false;
      this.stopHeartbeat();

      // Notify connection listeners
      this.notifyConnectionListeners('disconnect');

      // Attempt reconnection if not manually disconnected
      if (reason !== 'io client disconnect') {
        this.scheduleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;

      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      } else {
        console.error('Max reconnection attempts reached');
        this.notifyConnectionListeners('max_reconnect_attempts');
      }
    });

    // Listen for all events and route them to registered listeners
    this.socket.onAny((eventName: string, data: any) => {
      this.notifyEventListeners(eventName, data);
    });
  }

  /**
   * Schedule reconnection attempt with exponential backoff
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (!this.isConnected && !this.isConnecting) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Start heartbeat to monitor connection health
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.socket) {
        this.socket.emit('heartbeat', { timestamp: Date.now() });
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  /**
   * Stop heartbeat monitoring
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Process queued messages when connection is restored
   */
  private processMessageQueue(): void {
    if (this.messageQueue.length > 0) {
      console.log(`Processing ${this.messageQueue.length} queued messages`);
      this.messageQueue.forEach(message => {
        this.emit(message.type, message.payload);
      });
      this.messageQueue = [];
    }
  }

  /**
   * Notify all listeners registered for a specific event
   */
  private notifyEventListeners(eventName: string, data: any): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${eventName}:`, error);
        }
      });
    }
  }

  /**
   * Notify all connection status listeners
   */
  private notifyConnectionListeners(status: string): void {
    const listeners = this.connectionListeners.get(status);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback();
        } catch (error) {
          console.error(`Error in connection listener for ${status}:`, error);
        }
      });
    }
  }

  /**
   * Register event listener
   */
  public on(eventName: string, callback: EventCallback): void {
    if (!this.eventListeners.has(eventName)) {
      this.eventListeners.set(eventName, []);
    }
    this.eventListeners.get(eventName)!.push(callback);
  }

  /**
   * Unregister event listener
   */
  public off(eventName: string, callback?: EventCallback): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      if (callback) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      } else {
        this.eventListeners.delete(eventName);
      }
    }
  }

  /**
   * Register connection status listener
   */
  public onConnection(status: 'connect' | 'disconnect' | 'max_reconnect_attempts', callback: ConnectionCallback): void {
    if (!this.connectionListeners.has(status)) {
      this.connectionListeners.set(status, []);
    }
    this.connectionListeners.get(status)!.push(callback);
  }

  /**
   * Emit event to server
   */
  public emit(eventName: string, data: any): void {
    const message: WebSocketMessage = {
      type: eventName,
      payload: data,
      timestamp: Date.now()
    };

    if (this.isConnected && this.socket) {
      this.socket.emit(eventName, data);
    } else {
      // Queue message for later delivery
      if (this.messageQueue.length < 100) { // Prevent unlimited queue growth
        this.messageQueue.push(message);
        console.log(`Message queued: ${eventName}`, message);
      } else {
        console.warn('Message queue full, dropping message:', eventName);
      }
    }
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): {
    connected: boolean;
    connecting: boolean;
    reconnectAttempts: number;
    queueSize: number;
  } {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      queueSize: this.messageQueue.length
    };
  }

  /**
   * Manually disconnect from server
   */
  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
    }
    this.stopHeartbeat();
    this.isConnected = false;
    this.isConnecting = false;
  }

  /**
   * Force reconnection
   */
  public reconnect(): void {
    this.disconnect();
    setTimeout(() => {
      this.connect();
    }, 1000);
  }

  /**
   * Clean up resources
   */
  public destroy(): void {
    this.disconnect();
    this.eventListeners.clear();
    this.connectionListeners.clear();
    this.messageQueue = [];
  }
}

// Export singleton instance for global use
export const websocketService = new WebSocketService();