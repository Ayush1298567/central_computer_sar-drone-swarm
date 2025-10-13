import { describe, it, expect, vi, beforeEach } from 'vitest';
import websocketService from '../services/websocketService';
import { telemetryStore } from '../stores/telemetry';

function delay(ms: number) { return new Promise(res => setTimeout(res, ms)); }

describe('websocket telemetry -> store', () => {
  beforeEach(() => {
    telemetryStore.clear();
    // @ts-ignore avoid real socket
    websocketService['ws'] = null;
  });

  it('stores drones on telemetry message', async () => {
    const payload = { type: 'telemetry', payload: { drones: [ { id: 'drone-001', lat: 1, lon: 2, alt: 3, battery: 90 } ] } };
    // Bridge: listen to ws messages and forward to store
    const handler = (msg: any) => {
      telemetryStore.setDrones(msg.payload?.drones);
    };
    websocketService.onMessage('telemetry', handler);
    websocketService.emitForTests(payload as any);
    await delay(0);
    const list = telemetryStore.getSnapshot();
    expect(list.find(d => d.id === 'drone-001')).toBeTruthy();
  });
});
