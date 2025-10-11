import React, { useState, useEffect, useCallback } from 'react'
import { DiscoveryList } from '../components/discovery/DiscoveryList'
import { DiscoveryDetails } from '../components/discovery/DiscoveryDetails'
import { discoveryService, websocketService } from '../services'
import { Discovery } from '../types'

interface DiscoveryManagementState {
  discoveries: Discovery[]
  selectedDiscovery: Discovery | null
  isLoading: boolean
  error: string | null
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
  filters: {
    status: string[]
    priority: string[]
    type: string[]
  }
  sortBy: 'created_at' | 'priority' | 'confidence' | 'status'
  sortOrder: 'asc' | 'desc'
}

const DiscoveryManagement: React.FC = () => {
  const [state, setState] = useState<DiscoveryManagementState>({
    discoveries: [],
    selectedDiscovery: null,
    isLoading: true,
    error: null,
    connectionStatus: 'disconnected',
    filters: {
      status: [],
      priority: [],
      type: []
    },
    sortBy: 'created_at',
    sortOrder: 'desc'
  })

  useEffect(() => {
    loadDiscoveries()
    connectWebSocket()

    const handleDiscoveryUpdate = (event: CustomEvent) => {
      const discoveryData = event.detail
      setState(prev => ({
        ...prev,
        discoveries: prev.discoveries.map(discovery =>
          discovery.id === discoveryData.id
            ? { ...discovery, ...discoveryData }
            : discovery
        ),
        selectedDiscovery: prev.selectedDiscovery?.id === discoveryData.id
          ? { ...prev.selectedDiscovery, ...discoveryData } as Discovery
          : prev.selectedDiscovery
      }))
    }

    window.addEventListener('discoveryUpdate', handleDiscoveryUpdate as EventListener)

    return () => {
      websocketService.disconnect()
      window.removeEventListener('discoveryUpdate', handleDiscoveryUpdate as EventListener)
    }
  }, [])

  const loadDiscoveries = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const discoveries = await discoveryService.getDiscoveries()
      setState(prev => ({ ...prev, discoveries, isLoading: false }))
    } catch (error) {
      console.error('Failed to load discoveries:', error)
      setState(prev => ({ ...prev, isLoading: false, error: 'Failed to load discoveries. Please try again.' }))
    }
  }, [])

  const connectWebSocket = async () => {
    try {
      setState(prev => ({ ...prev, connectionStatus: 'reconnecting' }))
      await websocketService.connect()
      setState(prev => ({ ...prev, connectionStatus: 'connected' }))
      websocketService.subscribeToDiscoveries()
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
    }
  }

  const handleDiscoverySelect = useCallback((discovery: Discovery) => {
    setState(prev => ({ ...prev, selectedDiscovery: discovery }))
  }, [])

  const handleDiscoveryUpdate = useCallback((updatedDiscovery: Discovery) => {
    setState(prev => ({
      ...prev,
      discoveries: prev.discoveries.map(discovery =>
        discovery.id === updatedDiscovery.id ? updatedDiscovery : discovery
      ),
      selectedDiscovery: updatedDiscovery
    }))
  }, [])

  const handleCloseDetails = useCallback(() => {
    setState(prev => ({ ...prev, selectedDiscovery: null }))
  }, [])

  const handleStatusChange = useCallback(async (discoveryId: number, status: Discovery['status']) => {
    try {
      await discoveryService.updateDiscovery(discoveryId.toString(), { status })
      setState(prev => ({
        ...prev,
        discoveries: prev.discoveries.map(discovery =>
          discovery.id === discoveryId ? { ...discovery, status } : discovery
        ),
        selectedDiscovery: prev.selectedDiscovery?.id === discoveryId
          ? { ...prev.selectedDiscovery, status } as Discovery
          : prev.selectedDiscovery
      }))
    } catch (error) {
      console.error('Failed to update discovery status:', error)
    }
  }, [])

  const handlePriorityChange = useCallback(async (discoveryId: number, priority: Discovery['priority']) => {
    try {
      await discoveryService.updateDiscoveryPriority(discoveryId.toString(), priority)
      setState(prev => ({
        ...prev,
        discoveries: prev.discoveries.map(discovery =>
          discovery.id === discoveryId ? { ...discovery, priority } : discovery
        ),
        selectedDiscovery: prev.selectedDiscovery?.id === discoveryId
          ? { ...prev.selectedDiscovery, priority } as Discovery
          : prev.selectedDiscovery
      }))
    } catch (error) {
      console.error('Failed to update discovery priority:', error)
    }
  }, [])

  const handleFilterChange = useCallback((filterType: 'status' | 'priority' | 'type', value: string) => {
    setState(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        [filterType]: prev.filters[filterType].includes(value)
          ? prev.filters[filterType].filter(f => f !== value)
          : [...prev.filters[filterType], value]
      }
    }))
  }, [])

  const handleSortChange = useCallback((sortBy: DiscoveryManagementState['sortBy']) => {
    setState(prev => ({
      ...prev,
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'desc' ? 'asc' : 'desc'
    }))
  }, [])

  const clearFilters = useCallback(() => {
    setState(prev => ({
      ...prev,
      filters: {
        status: [],
        priority: [],
        type: []
      }
    }))
  }, [])

  const filteredAndSortedDiscoveries = React.useMemo(() => {
    let filtered = state.discoveries

    // Apply filters
    if (state.filters.status.length > 0) {
      filtered = filtered.filter(discovery => state.filters.status.includes(discovery.status))
    }
    if (state.filters.priority.length > 0) {
      filtered = filtered.filter(discovery => state.filters.priority.includes(discovery.priority))
    }
    if (state.filters.type.length > 0) {
      filtered = filtered.filter(discovery => state.filters.type.includes(discovery.discovery_type))
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any

      switch (state.sortBy) {
        case 'created_at':
          aValue = new Date(a.created_at).getTime()
          bValue = new Date(b.created_at).getTime()
          break
        case 'priority':
          const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
          aValue = priorityOrder[a.priority]
          bValue = priorityOrder[b.priority]
          break
        case 'confidence':
          aValue = a.confidence
          bValue = b.confidence
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        default:
          return 0
      }

      if (state.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    return filtered
  }, [state.discoveries, state.filters, state.sortBy, state.sortOrder])

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Discovery Management</h1>
            <p className="text-gray-600">Investigate and manage SAR discoveries</p>
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
              onClick={loadDiscoveries}
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Discoveries</h2>
            
            {/* Filters */}
            <div className="mb-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <div className="space-y-1">
                  {['pending', 'investigating', 'resolved', 'false_positive'].map(status => (
                    <label key={status} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={state.filters.status.includes(status)}
                        onChange={() => handleFilterChange('status', status)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{status}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <div className="space-y-1">
                  {['low', 'medium', 'high', 'critical'].map(priority => (
                    <label key={priority} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={state.filters.priority.includes(priority)}
                        onChange={() => handleFilterChange('priority', priority)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{priority}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <div className="space-y-1">
                  {['person', 'vehicle', 'structure', 'signal', 'animal', 'debris', 'other'].map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={state.filters.type.includes(type)}
                        onChange={() => handleFilterChange('type', type)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                onClick={clearFilters}
                className="w-full px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded hover:bg-gray-50"
              >
                Clear Filters
              </button>
            </div>

            {/* Sort */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
              <div className="space-y-1">
                {[
                  { value: 'created_at', label: 'Date Created' },
                  { value: 'priority', label: 'Priority' },
                  { value: 'confidence', label: 'Confidence' },
                  { value: 'status', label: 'Status' }
                ].map(option => (
                  <button
                    key={option.value}
                    onClick={() => handleSortChange(option.value as DiscoveryManagementState['sortBy'])}
                    className={`w-full text-left px-2 py-1 text-sm rounded ${
                      state.sortBy === option.value
                        ? 'bg-blue-100 text-blue-800'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {option.label} {state.sortBy === option.value && (state.sortOrder === 'desc' ? '↓' : '↑')}
                  </button>
                ))}
              </div>
            </div>

            <DiscoveryList
              discoveries={filteredAndSortedDiscoveries}
              selectedDiscoveryId={state.selectedDiscovery?.id}
              onDiscoverySelect={handleDiscoverySelect}
              onStatusChange={handleStatusChange}
              onPriorityChange={handlePriorityChange}
              filterByType={state.filters.type}
              compactView={true}
            />
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            {state.selectedDiscovery ? (
              <>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Discovery Details</h2>
                <DiscoveryDetails
                  discovery={state.selectedDiscovery}
                  onDiscoveryUpdate={handleDiscoveryUpdate}
                  onClose={handleCloseDetails}
                />
              </>
            ) : (
              <div className="text-center text-gray-500 py-12">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-lg">Select a discovery to view details</p>
                <p className="text-sm">Use the filters and sorting options to find specific discoveries</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DiscoveryManagement
