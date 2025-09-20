import { io, Socket } from 'socket.io-client';
// import { WebSocketMessage } from '../types';

export type WebSocketEventHandler = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();

  constructor() {
    this.connect();
  }

  private connect(): void {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const userId = this.getUserId();

    this.socket = io(`${wsUrl}/api/v1/ws/client/${userId}`, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true,
    });

    this.setupEventListeners();
  }

  private getUserId(): string {
    // In a real app, get this from auth context
    return localStorage.getItem('user_id') || 'anonymous_user';
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('connection_status', { connected: false, reason });
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.handleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.emit('connection_error', { error: error.message });
      this.handleReconnect();
    });

    // Mission events
    this.socket.on('mission_created', (data) => {
      this.emit('mission_created', data);
    });

    this.socket.on('mission_updated', (data) => {
      this.emit('mission_updated', data);
    });

    this.socket.on('mission_started', (data) => {
      this.emit('mission_started', data);
    });

    this.socket.on('mission_completed', (data) => {
      this.emit('mission_completed', data);
    });

    this.socket.on('mission_aborted', (data) => {
      this.emit('mission_aborted', data);
    });

    // Drone events
    this.socket.on('drone_status_update', (data) => {
      this.emit('drone_status_update', data);
    });

    this.socket.on('drone_telemetry', (data) => {
      this.emit('drone_telemetry', data);
    });

    this.socket.on('drone_position_update', (data) => {
      this.emit('drone_position_update', data);
    });

    this.socket.on('drone_connected', (data) => {
      this.emit('drone_connected', data);
    });

    this.socket.on('drone_disconnected', (data) => {
      this.emit('drone_disconnected', data);
    });

    this.socket.on('drone_emergency', (data) => {
      this.emit('drone_emergency', data);
    });

    // Chat events
    this.socket.on('chat_message', (data) => {
      this.emit('chat_message', data);
    });

    this.socket.on('chat_progress_update', (data) => {
      this.emit('chat_progress_update', data);
    });

    this.socket.on('mission_plan_updated', (data) => {
      this.emit('mission_plan_updated', data);
    });

    // Discovery events
    this.socket.on('discovery_update', (data) => {
      this.emit('discovery_update', data);
    });

    // System events
    this.socket.on('system_alert', (data) => {
      this.emit('system_alert', data);
    });

    this.socket.on('heartbeat', (data) => {
      this.emit('heartbeat', data);
    });
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (this.socket) {
          this.socket.connect();
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('connection_failed', { maxAttemptsReached: true });
    }
  }

  // Event subscription methods
  on(event: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  // Mission subscription methods
  subscribeMission(missionId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_mission', { mission_id: missionId });
    }
  }

  unsubscribeMission(missionId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_mission', { mission_id: missionId });
    }
  }

  // Drone subscription methods
  subscribeDrone(droneId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_drone', { drone_id: droneId });
    }
  }

  unsubscribeDrone(droneId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_drone', { drone_id: droneId });
    }
  }

  // Chat subscription methods
  subscribeChatSession(sessionId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_chat', { session_id: sessionId });
    }
  }

  unsubscribeChatSession(sessionId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_chat', { session_id: sessionId });
    }
  }

  // Send commands
  sendDroneCommand(droneId: string, command: any): void {
    if (this.socket?.connected) {
      this.socket.emit('drone_command', {
        drone_id: droneId,
        command,
        timestamp: new Date().toISOString(),
      });
    }
  }

  sendChatMessage(sessionId: string, message: string): void {
    if (this.socket?.connected) {
      this.socket.emit('chat_message', {
        session_id: sessionId,
        content: message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Connection management
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.eventHandlers.clear();
  }

  reconnect(): void {
    this.disconnect();
    this.reconnectAttempts = 0;
    this.connect();
  }

  // Heartbeat
  sendHeartbeat(): void {
    if (this.socket?.connected) {
      this.socket.emit('heartbeat', {
        timestamp: new Date().toISOString(),
        client_type: 'web_dashboard',
      });
    }
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService();

// Start heartbeat
setInterval(() => {
  webSocketService.sendHeartbeat();
}, 30000);

export default webSocketService;