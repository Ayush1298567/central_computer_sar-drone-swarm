import { useSyncExternalStore } from 'react';

export interface DroneTelemetry {
  id: string;
  lat: number | null;
  lon: number | null;
  alt: number | null;
  battery: number | null;
  status?: string;
  last_seen?: string;
}

type Listener = () => void;

const state: { byId: Record<string, DroneTelemetry> } = {
  byId: {},
};

const listeners = new Set<Listener>();

function emit() {
  for (const l of Array.from(listeners)) l();
}

export const telemetryStore = {
  getSnapshot(): DroneTelemetry[] {
    return Object.values(state.byId);
  },
  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setDrones(drones: DroneTelemetry[] | undefined | null) {
    if (!Array.isArray(drones)) return;
    for (const d of drones) {
      if (!d?.id) continue;
      state.byId[d.id] = {
        id: d.id,
        lat: d.lat ?? null,
        lon: d.lon ?? null,
        alt: d.alt ?? null,
        battery: d.battery ?? null,
        status: d.status,
        last_seen: d.last_seen,
      };
    }
    emit();
  },
  clear() {
    state.byId = {};
    emit();
  },
};

export function useTelemetryStore(): DroneTelemetry[] {
  return useSyncExternalStore(
    telemetryStore.subscribe,
    telemetryStore.getSnapshot,
    telemetryStore.getSnapshot
  );
}

