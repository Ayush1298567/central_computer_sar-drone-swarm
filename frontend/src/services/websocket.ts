import { io, Socket } from 'socket.io-client';

export type WebSocketEventType = 
  | 'mission_update'
  | 'drone_telemetry'
  | 'chat_message'
  | 'discovery_update'
  | 'system_notification'
  | 'drone_command_update'
  | 'video_feed_update';

export interface WebSocketMessage {
  type: WebSocketEventType;
  data: any;
  timestamp: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(userId: string): void {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(`/api/v1/ws/client/${userId}`, {
      transports: ['websocket'],
      upgrade: true,
      rememberUpgrade: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, reconnect manually
        this.handleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    });
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.socket?.connect();
    }, delay);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribe(eventType: WebSocketEventType, callback: (data: any) => void): void {
    if (!this.socket) {
      console.warn('WebSocket not connected');
      return;
    }

    this.socket.on(eventType, callback);
  }

  unsubscribe(eventType: WebSocketEventType, callback?: (data: any) => void): void {
    if (!this.socket) {
      return;
    }

    if (callback) {
      this.socket.off(eventType, callback);
    } else {
      this.socket.off(eventType);
    }
  }

  subscribeMission(missionId: string): void {
    if (!this.socket) {
      console.warn('WebSocket not connected');
      return;
    }

    this.socket.emit('subscribe_mission', { mission_id: missionId });
  }

  unsubscribeMission(missionId: string): void {
    if (!this.socket) {
      return;
    }

    this.socket.emit('unsubscribe_mission', { mission_id: missionId });
  }

  subscribeDrone(droneId: string): void {
    if (!this.socket) {
      console.warn('WebSocket not connected');
      return;
    }

    this.socket.emit('subscribe_drone', { drone_id: droneId });
  }

  unsubscribeDrone(droneId: string): void {
    if (!this.socket) {
      return;
    }

    this.socket.emit('unsubscribe_drone', { drone_id: droneId });
  }

  sendMessage(type: WebSocketEventType, data: any): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket not connected');
      return;
    }

    this.socket.emit(type, data);
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const webSocketService = new WebSocketService();