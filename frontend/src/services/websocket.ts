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
export default wsService;

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp?: string;
}