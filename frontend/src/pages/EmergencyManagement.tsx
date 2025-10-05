import React, { useState, useEffect, useCallback } from 'react'
import { EmergencyPanel } from '../components/emergency/EmergencyPanel'
import { emergencyService, websocketService, droneService } from '../services'
import { Drone } from '../types'

interface EmergencyManagementState {
  drones: Drone[]
  isLoading: boolean
  error: string | null
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
  emergencyHistory: any[]
  systemStatus: {
    overall: 'normal' | 'warning' | 'critical'
    batteryLevels: 'normal' | 'warning' | 'critical'
    communication: 'normal' | 'warning' | 'critical'
    weather: 'normal' | 'warning' | 'critical'
  }
}

const EmergencyManagement: React.FC = () => {
  const [state, setState] = useState<EmergencyManagementState>({
    drones: [],
    isLoading: true,
    error: null,
    connectionStatus: 'disconnected',
    emergencyHistory: [],
    systemStatus: {
      overall: 'normal',
      batteryLevels: 'normal',
      communication: 'normal',
      weather: 'normal'
    }
  })

  useEffect(() => {
    loadInitialData()
    connectWebSocket()

    const handleEmergencyAlert = (event: CustomEvent) => {
      const alertData = event.detail
      setState(prev => ({
        ...prev,
        emergencyHistory: [alertData, ...prev.emergencyHistory]
      }))
    }

    const handleDroneUpdate = (event: CustomEvent) => {
      const droneData = event.detail
      setState(prev => ({
        ...prev,
        drones: prev.drones.map(drone =>
          drone.drone_id === droneData.drone_id
            ? { ...drone, ...droneData }
            : drone
        )
      }))
    }

    window.addEventListener('emergencyAlert', handleEmergencyAlert as EventListener)
    window.addEventListener('droneUpdate', handleDroneUpdate as EventListener)

    return () => {
      websocketService.disconnect()
      window.removeEventListener('emergencyAlert', handleEmergencyAlert as EventListener)
      window.removeEventListener('droneUpdate', handleDroneUpdate as EventListener)
    }
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const [drones, emergencyHistory] = await Promise.all([
        droneService.getDrones(),
        emergencyService.getEmergencyHistory({ limit: 50 })
      ])
      
      setState(prev => ({
        ...prev,
        drones,
        emergencyHistory,
        isLoading: false
      }))
    } catch (error) {
      console.error('Failed to load initial data:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to load emergency management data. Please try again.' 
      }))
    }
  }, [])

  const connectWebSocket = async () => {
    try {
      setState(prev => ({ ...prev, connectionStatus: 'reconnecting' }))
      await websocketService.connect()
      setState(prev => ({ ...prev, connectionStatus: 'connected' }))
      
      // Subscribe to emergency and drone updates
      websocketService.subscribeToEmergency()
      websocketService.subscribeToDrone('all')
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
    }
  }

  const handleEmergencyAction = useCallback((action: string, data?: any) => {
    console.log('Emergency action executed:', action, data)
    // Additional handling can be added here
  }, [])

  const getSystemStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'text-green-600 bg-green-100'
      case 'warning': return 'text-yellow-600 bg-yellow-100'
      case 'critical': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getSystemStatusIcon = (status: string) => {
    switch (status) {
      case 'normal': return '✅'
      case 'warning': return '⚠️'
      case 'critical': return '🚨'
      default: return '❓'
    }
  }

  const calculateSystemStatus = () => {
    const { drones } = state
    
    // Check battery levels
    const lowBatteryDrones = drones.filter(drone => drone.battery_level < 20)
    const batteryStatus = lowBatteryDrones.length > 0 ? 'warning' : 'normal'
    
    // Check communication
    const offlineDrones = drones.filter(drone => drone.status === 'offline')
    const communicationStatus = offlineDrones.length > drones.length * 0.5 ? 'critical' : 
                               offlineDrones.length > 0 ? 'warning' : 'normal'
    
    // Overall status
    const overallStatus = communicationStatus === 'critical' ? 'critical' :
                         batteryStatus === 'warning' || communicationStatus === 'warning' ? 'warning' : 'normal'
    
    setState(prev => ({
      ...prev,
      systemStatus: {
        overall: overallStatus,
        batteryLevels: batteryStatus,
        communication: communicationStatus,
        weather: 'normal' // This would be integrated with weather API
      }
    }))
  }

  useEffect(() => {
    calculateSystemStatus()
  }, [state.drones])

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Emergency Management</h1>
            <p className="text-gray-600">Monitor system status and manage emergency protocols</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm ${
              state.connectionStatus === 'connected'
                ? 'bg-green-100 text-green-800'
                : state.connectionStatus === 'reconnecting'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {state.connectionStatus === 'connected' && 'Connected'}
              {state.connectionStatus === 'reconnecting' && 'Reconnecting...'}
              {state.connectionStatus === 'disconnected' && 'Disconnected'}
            </div>
            <button
              onClick={loadInitialData}
              disabled={state.isLoading}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md"
            >
              {state.isLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {state.error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4 text-red-800">
          <p>{state.error}</p>
        </div>
      )}

      {/* System Status Overview */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Overall Status</p>
              <p className="text-2xl font-bold text-gray-900">
                {getSystemStatusIcon(state.systemStatus.overall)}
              </p>
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(state.systemStatus.overall)}`}>
              {state.systemStatus.overall.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Battery Levels</p>
              <p className="text-2xl font-bold text-gray-900">
                {getSystemStatusIcon(state.systemStatus.batteryLevels)}
              </p>
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(state.systemStatus.batteryLevels)}`}>
              {state.systemStatus.batteryLevels.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Communication</p>
              <p className="text-2xl font-bold text-gray-900">
                {getSystemStatusIcon(state.systemStatus.communication)}
              </p>
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(state.systemStatus.communication)}`}>
              {state.systemStatus.communication.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Weather</p>
              <p className="text-2xl font-bold text-gray-900">
                {getSystemStatusIcon(state.systemStatus.weather)}
              </p>
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(state.systemStatus.weather)}`}>
              {state.systemStatus.weather.toUpperCase()}
            </div>
          </div>
        </div>
      </div>

      {/* Drone Status Summary */}
      <div className="mb-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Drone Fleet Status</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {state.drones.filter(d => d.status === 'flying').length}
            </div>
            <div className="text-sm text-gray-500">Flying</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {state.drones.filter(d => d.status === 'online').length}
            </div>
            <div className="text-sm text-gray-500">Online</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {state.drones.filter(d => d.status === 'charging').length}
            </div>
            <div className="text-sm text-gray-500">Charging</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {state.drones.filter(d => d.status === 'offline' || d.status === 'error').length}
            </div>
            <div className="text-sm text-gray-500">Offline/Error</div>
          </div>
        </div>
      </div>

      {/* Emergency Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EmergencyPanel
          drones={state.drones}
          onEmergencyAction={handleEmergencyAction}
        />

        {/* Emergency History */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Emergency History</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {state.emergencyHistory.map((alert, index) => (
              <div key={index} className="border-l-4 border-red-500 bg-red-50 p-3 rounded">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                    <p className="text-xs text-gray-500">
                      Initiated by: {alert.initiated_by} • {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-600 text-white' :
                    alert.severity === 'high' ? 'bg-orange-600 text-white' :
                    alert.severity === 'medium' ? 'bg-yellow-600 text-white' :
                    'bg-blue-600 text-white'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
              </div>
            ))}
            {state.emergencyHistory.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">✅</div>
                <p className="text-lg">No emergency history</p>
                <p className="text-sm">System is operating normally</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmergencyManagement
