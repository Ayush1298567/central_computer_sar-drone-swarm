import { useState, useEffect, useCallback } from 'react';
import { Drone, DroneStatus } from '../types';
import { apiService } from '../services/api';
import { useWebSocket } from './useWebSocket';

export function useDrones() {
  const [drones, setDrones] = useState<Drone[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const webSocket = useWebSocket();

  // Load drones from API
  const loadDrones = useCallback(async (params?: { status?: string; limit?: number; offset?: number }) => {
    setLoading(true);
    setError(null);
    try {
      const dronesData = await apiService.getDrones(params);
      setDrones(dronesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load drones');
    } finally {
      setLoading(false);
    }
  }, []);

  // Discover new drones
  const discoverDrones = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const discoveredDrones = await apiService.discoverDrones();
      // Merge with existing drones
      setDrones(prevDrones => {
        const existingIds = new Set(prevDrones.map(d => d.id));
        const newDrones = discoveredDrones.filter(d => !existingIds.has(d.id));
        return [...prevDrones, ...newDrones];
      });
      return discoveredDrones;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to discover drones');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Register a new drone
  const registerDrone = useCallback(async (droneData: Partial<Drone>) => {
    try {
      const newDrone = await apiService.registerDrone(droneData);
      setDrones(prevDrones => [...prevDrones, newDrone]);
      return newDrone;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register drone');
      throw err;
    }
  }, []);

  // Update drone
  const updateDrone = useCallback(async (id: string, updates: Partial<Drone>) => {
    try {
      const updatedDrone = await apiService.updateDrone(id, updates);
      setDrones(prevDrones => 
        prevDrones.map(drone => drone.id === id ? updatedDrone : drone)
      );
      return updatedDrone;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update drone');
      throw err;
    }
  }, []);

  // Send command to drone
  const sendCommand = useCallback(async (droneId: string, command: any) => {
    try {
      const result = await apiService.sendDroneCommand(droneId, command);
      // Also send via WebSocket for real-time updates
      webSocket.emit('drone_command', { droneId, command });
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send command');
      throw err;
    }
  }, [webSocket]);

  // Emergency stop
  const emergencyStop = useCallback(async (droneId: string) => {
    try {
      await apiService.emergencyStopDrone(droneId);
      // Update drone status immediately
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === droneId
            ? { ...drone, status: DroneStatus.EMERGENCY }
            : drone
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to emergency stop drone');
      throw err;
    }
  }, []);

  // Unregister drone
  const unregisterDrone = useCallback(async (droneId: string) => {
    try {
      await apiService.unregisterDrone(droneId);
      setDrones(prevDrones => prevDrones.filter(drone => drone.id !== droneId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unregister drone');
      throw err;
    }
  }, []);

  // Get drone telemetry
  const getDroneTelemetry = useCallback(async (droneId: string, params?: { 
    start_time?: string; 
    end_time?: string; 
    limit?: number; 
  }) => {
    try {
      return await apiService.getDroneTelemetry(droneId, params);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get telemetry');
      throw err;
    }
  }, []);

  // Perform health check
  const performHealthCheck = useCallback(async (droneId: string) => {
    try {
      return await apiService.performDroneHealthCheck(droneId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to perform health check');
      throw err;
    }
  }, []);

  // Get diagnostics
  const getDiagnostics = useCallback(async (droneId: string) => {
    try {
      return await apiService.getDroneDiagnostics(droneId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get diagnostics');
      throw err;
    }
  }, []);

  // Subscribe to drone updates
  const subscribeToDrone = useCallback((droneId: string) => {
    webSocket.subscribeDrone(droneId);
  }, [webSocket]);

  const unsubscribeFromDrone = useCallback((droneId: string) => {
    webSocket.unsubscribeDrone(droneId);
  }, [webSocket]);

  // WebSocket event handlers
  useEffect(() => {
    webSocket.subscribe('drone_status_update', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, status: data.status, lastSeen: new Date() }
            : drone
        )
      );
    });

    webSocket.subscribe('drone_telemetry', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, telemetry: data.telemetry, lastSeen: new Date() }
            : drone
        )
      );
    });

    webSocket.subscribe('drone_position_update', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, position: data.position, lastSeen: new Date() }
            : drone
        )
      );
    });

    webSocket.subscribe('drone_connected', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, isConnected: true, lastSeen: new Date() }
            : drone
        )
      );
    });

    webSocket.subscribe('drone_disconnected', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, isConnected: false, status: DroneStatus.OFFLINE }
            : drone
        )
      );
    });

    webSocket.subscribe('drone_emergency', (data) => {
      setDrones(prevDrones =>
        prevDrones.map(drone =>
          drone.id === data.drone_id
            ? { ...drone, status: DroneStatus.EMERGENCY, lastSeen: new Date() }
            : drone
        )
      );
    });

    return () => {
      webSocket.unsubscribe('drone_status_update');
      webSocket.unsubscribe('drone_telemetry');
      webSocket.unsubscribe('drone_position_update');
      webSocket.unsubscribe('drone_connected');
      webSocket.unsubscribe('drone_disconnected');
      webSocket.unsubscribe('drone_emergency');
    };
  }, [webSocket]);

  // Load drones on mount
  useEffect(() => {
    loadDrones();
  }, [loadDrones]);

  return {
    drones,
    loading,
    error,
    loadDrones,
    discoverDrones,
    registerDrone,
    updateDrone,
    sendCommand,
    emergencyStop,
    unregisterDrone,
    getDroneTelemetry,
    performHealthCheck,
    getDiagnostics,
    subscribeToDrone,
    unsubscribeFromDrone,
    clearError: () => setError(null),
  };
}

export default useDrones;