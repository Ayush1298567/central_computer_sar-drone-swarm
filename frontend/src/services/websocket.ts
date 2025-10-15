import { toast } from 'react-hot-toast';

export type MessageHandler = (data: any) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private isIntentionallyClosed = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  private wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

  connect(token?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.isIntentionallyClosed = false;
    const url = token ? `${this.wsUrl}?token=${token}` : this.wsUrl;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
        toast.success('Connected to mission control');
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Subscribe to all topics
        this.subscribe(['telemetry', 'detections', 'alerts', 'mission_updates', 'ai_decisions']);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle heartbeat response
          if (data.type === 'pong') {
            return;
          }
          
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast.error('Connection error');
      };

      this.ws.onclose = (event) => {
        console.warn('WebSocket disconnected:', event.code, event.reason);
        this.ws = null;
        this.stopHeartbeat();
        
        if (!this.isIntentionallyClosed) {
          this.reconnect();
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.reconnect();
    }
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      toast.error('Unable to connect to mission control');
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  private handleMessage(data: any) {
    const { type, payload } = data;
    
    // Call all handlers for this message type
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(payload);
        } catch (error) {
          console.error(`Handler error for ${type}:`, error);
        }
      });
    }
  }

  subscribe(topics: string[]) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        payload: { topics }
      }));
    }
  }

  unsubscribe(topics: string[]) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        payload: { topics }
      }));
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      this.messageHandlers.get(type)?.delete(handler);
    };
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
      toast.error('Not connected to mission control');
    }
  }

  // Mission control specific methods
  sendDroneCommand(droneId: string, command: string, params: any = {}) {
    this.send({
      type: 'drone_command',
      payload: {
        drone_id: droneId,
        command,
        params,
        timestamp: new Date().toISOString()
      }
    });
  }

  requestTelemetry() {
    this.send({
      type: 'request_telemetry',
      payload: {
        timestamp: new Date().toISOString()
      }
    });
  }

  reportDetection(detection: any) {
    this.send({
      type: 'detection_report',
      payload: {
        ...detection,
        timestamp: new Date().toISOString()
      }
    });
  }

  triggerEmergencyStop(reason: string) {
    this.send({
      type: 'emergency_stop',
      payload: {
        reason,
        timestamp: new Date().toISOString()
      }
    });
  }

  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      default:
        return 'disconnected';
    }
  }

  disconnect() {
    this.isIntentionallyClosed = true;
    this.stopHeartbeat();
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    this.ws?.close();
    this.ws = null;
    
    // Clear all handlers
    this.messageHandlers.clear();
  }
}

export const wsService = new WebSocketService();

// Default export for backward compatibility
export default wsService;

// Named export for backward compatibility
export const webSocketService = wsService;

// WebSocket message type
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp?: string;
}

// Connection handler types
export interface ConnectionHandler {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export interface MessageHandler {
  (message: WebSocketMessage): void;
}

export interface Subscription {
  topic: string;
  handler: MessageHandler;
}

// WebSocket subscriptions manager
export class WebSocketSubscriptions {
  private subscriptions = new Map<string, Set<MessageHandler>>();

  subscribe(topic: string, handler: MessageHandler) {
    if (!this.subscriptions.has(topic)) {
      this.subscriptions.set(topic, new Set());
    }
    this.subscriptions.get(topic)!.add(handler);
  }

  unsubscribe(topic: string, handler: MessageHandler) {
    const handlers = this.subscriptions.get(topic);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.subscriptions.delete(topic);
      }
    }
  }

  getSubscriptions(topic: string): Set<MessageHandler> {
    return this.subscriptions.get(topic) || new Set();
  }
}

// React hook for WebSocket connection
export function useWebSocketConnection() {
  return {
    connect: (token?: string) => wsService.connect(token),
    disconnect: () => wsService.disconnect(),
    send: (data: any) => wsService.send(data),
    on: (type: string, handler: MessageHandler) => wsService.on(type, handler),
    getConnectionStatus: () => wsService.getConnectionStatus()
  };
}