<<<<<<< Current (Your changes)
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
  
  private wsUrl: string = (() => {
    const fromEnv = import.meta.env.VITE_WS_URL as string | undefined;
    if (fromEnv) return fromEnv;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/v1/ws`;
  })();

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
        
        // Subscribe to base topics
        this.subscribe(['telemetry', 'detections', 'alerts', 'mission_updates']);
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
      payload: { timestamp: new Date().toISOString() }
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
      payload: { reason, timestamp: new Date().toISOString() }
    });
  }

  // Convenience for LiveMission: subscribe/unsubscribe
  subscribeMission(_missionId: number) {
    this.subscribe(['mission_updates']);
  }

  unsubscribeMission(_missionId: number) {
    this.unsubscribe(['mission_updates']);
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
=======
import websocketServiceClass, { WebSocketService as AdvancedService } from './websocketService';

// Canonical singleton from websocketService.ts
export const websocketService: AdvancedService = websocketServiceClass;

// Thin compatibility wrapper exposing legacy wsService API
const wsService = {
  connect: (token?: string) => websocketService.connect(),
  disconnect: () => websocketService.disconnect(),
  send: (data: any) => websocketService.send(data),
  on: (type: string, handler: (payload: any) => void) => {
    const wrapped = (msg: any) => {
      const payload = (msg as any)?.payload ?? (msg as any)?.data ?? msg;
      handler(payload);
    };
    websocketService.onMessage(type, wrapped);
    return () => websocketService.offMessage(type, wrapped);
  },
  requestTelemetry: () => websocketService.send({ type: 'request_telemetry', payload: {} }),
  triggerEmergencyStop: (reason: string) => websocketService.send({ type: 'emergency_stop', payload: { reason, timestamp: new Date().toISOString() } }),
  getConnectionStatus: () => websocketService.getConnectionStatus(),
};

export { wsService };
>>>>>>> Incoming (Background Agent changes)
export default wsService;

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp?: string;
}