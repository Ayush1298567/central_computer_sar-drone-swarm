import React, { useState, useEffect, useCallback } from 'react'
import { DroneGrid } from '../components/drone/DroneGrid'
import { DroneForm } from '../components/drone/DroneForm'
import { DroneDetails } from '../components/drone/DroneDetails'
import { droneService, websocketService } from '../services'
import { Drone, DroneCreate, DroneUpdate } from '../types'

interface DroneManagementState {
  drones: Drone[]
  selectedDrone: Drone | null
  isCreating: boolean
  isEditing: boolean
  isLoading: boolean
  error: string | null
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
}

const DroneManagement: React.FC = () => {
  const [state, setState] = useState<DroneManagementState>({
    drones: [],
    selectedDrone: null,
    isCreating: false,
    isEditing: false,
    isLoading: true,
    error: null,
    connectionStatus: 'disconnected'
  })

  // Load drones on component mount
  useEffect(() => {
    loadDrones()
  }, [])

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        setState(prev => ({ ...prev, connectionStatus: 'reconnecting' }))
        await websocketService.connect()
        setState(prev => ({ ...prev, connectionStatus: 'connected' }))

        // Subscribe to drone updates
        websocketService.subscribeToEmergency()

        // Handle real-time drone updates
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

        window.addEventListener('droneUpdate', handleDroneUpdate as EventListener)

        return () => {
          websocketService.disconnect()
          window.removeEventListener('droneUpdate', handleDroneUpdate as EventListener)
        }
      } catch (error) {
        console.error('WebSocket connection failed:', error)
        setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
      }
    }

    connectWebSocket()
  }, [])

  const loadDrones = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const drones = await droneService.getDrones()
      setState(prev => ({ ...prev, drones, isLoading: false }))
    } catch (error) {
      console.error('Failed to load drones:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to load drones. Please try again.' 
      }))
    }
  }, [])

  const handleCreateDrone = useCallback(async (droneData: DroneCreate) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const newDrone = await droneService.createDrone(droneData)
      setState(prev => ({ 
        ...prev, 
        drones: [...prev.drones, newDrone],
        isLoading: false,
        isCreating: false
      }))
    } catch (error) {
      console.error('Failed to create drone:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to create drone. Please check your input and try again.' 
      }))
    }
  }, [])

  const handleUpdateDrone = useCallback(async (droneId: string, droneData: DroneUpdate) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const updatedDrone = await droneService.updateDrone(droneId, droneData)
      setState(prev => ({ 
        ...prev, 
        drones: prev.drones.map(drone =>
          drone.drone_id === droneId ? updatedDrone : drone
        ),
        isLoading: false,
        isEditing: false,
        selectedDrone: updatedDrone
      }))
    } catch (error) {
      console.error('Failed to update drone:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to update drone. Please try again.' 
      }))
    }
  }, [])

  const handleDeleteDrone = useCallback(async (droneId: string) => {
    if (!confirm('Are you sure you want to delete this drone? This action cannot be undone.')) {
      return
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      await droneService.deleteDrone(droneId)
      setState(prev => ({ 
        ...prev, 
        drones: prev.drones.filter(drone => drone.drone_id !== droneId),
        isLoading: false,
        selectedDrone: prev.selectedDrone?.drone_id === droneId ? null : prev.selectedDrone
      }))
    } catch (error) {
      console.error('Failed to delete drone:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to delete drone. Please try again.' 
      }))
    }
  }, [])

  const handleDroneSelect = useCallback((drone: Drone) => {
    setState(prev => ({ ...prev, selectedDrone: drone }))
  }, [])

  const handleStartCreating = useCallback(() => {
    setState(prev => ({ ...prev, isCreating: true, selectedDrone: null }))
  }, [])

  const handleStartEditing = useCallback(() => {
    setState(prev => ({ ...prev, isEditing: true }))
  }, [])

  const handleCancelForm = useCallback(() => {
    setState(prev => ({ ...prev, isCreating: false, isEditing: false }))
  }, [])

  const handleRefresh = useCallback(() => {
    loadDrones()
  }, [loadDrones])

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Drone Management</h1>
            <p className="text-gray-600">Manage your drone fleet and monitor their status</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
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

            {/* Action Buttons */}
            <button
              onClick={handleRefresh}
              disabled={state.isLoading}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md"
            >
              {state.isLoading ? 'Loading...' : 'Refresh'}
            </button>
            
            <button
              onClick={handleStartCreating}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
            >
              Add Drone
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {state.error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{state.error}</p>
              </div>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setState(prev => ({ ...prev, error: null }))}
                className="text-red-400 hover:text-red-600"
              >
                <span className="sr-only">Dismiss</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Drone List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Drone Fleet</h2>
              <span className="text-sm text-gray-500">{state.drones.length} drones</span>
            </div>
            
            <DroneGrid
              drones={state.drones}
              selectedDrone={state.selectedDrone?.drone_id || null}
              onDroneSelect={handleDroneSelect}
              showControls={false}
            />
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2">
          {state.isCreating ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Add New Drone</h2>
                <button
                  onClick={handleCancelForm}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <DroneForm
                onSubmit={handleCreateDrone}
                onCancel={handleCancelForm}
                isLoading={state.isLoading}
              />
            </div>
          ) : state.isEditing && state.selectedDrone ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Edit Drone</h2>
                <button
                  onClick={handleCancelForm}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <DroneForm
                drone={state.selectedDrone}
                onSubmit={(data) => handleUpdateDrone(state.selectedDrone!.drone_id, data)}
                onCancel={handleCancelForm}
                isLoading={state.isLoading}
              />
            </div>
          ) : state.selectedDrone ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Drone Details</h2>
                <div className="flex space-x-2">
                  <button
                    onClick={handleStartEditing}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteDrone(state.selectedDrone!.drone_id)}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <DroneDetails
                drone={state.selectedDrone}
                onDroneSelect={handleDroneSelect}
              />
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center text-gray-500 py-12">
                <div className="text-4xl mb-4">🚁</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Drone Selected</h3>
                <p className="text-gray-600">Select a drone from the list to view its details and controls.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DroneManagement
