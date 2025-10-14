import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface DroneTelemetry {
  id: string
  status?: string
  battery?: number
  position?: { lat: number; lon: number; alt?: number }
  mission_status?: any
  last_seen?: string
  last_update?: string
}

interface TelemetryState {
  connectionStatus: 'connected' | 'connecting' | 'disconnected'
  drones: Record<string, DroneTelemetry>
  updateDrone: (telemetry: DroneTelemetry) => void
  setConnectionStatus: (status: 'connected' | 'connecting' | 'disconnected') => void
  getDroneData: (id: string) => DroneTelemetry | undefined
  reset: () => void
}

export const useTelemetryStore = create<TelemetryState>()(
  persist(
    (set, get) => ({
      connectionStatus: 'disconnected',
      drones: {},
      updateDrone: (t) =>
        set((state) => ({
          drones: {
            ...state.drones,
            [t.id]: { ...(state.drones[t.id] || {}), ...t },
          },
        })),
      setConnectionStatus: (status) => set({ connectionStatus: status }),
      getDroneData: (id) => get().drones[id],
      reset: () => set({ connectionStatus: 'disconnected', drones: {} }),
    }),
    { name: 'telemetry-store', getStorage: () => sessionStorage }
  )
)


