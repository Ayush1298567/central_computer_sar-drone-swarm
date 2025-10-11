import React, { useState, useEffect, useCallback } from 'react'
import { ComputerVision } from '../components/computerVision/ComputerVision'
import { computerVisionService, Detection } from '../services/computerVision'
import { missionService } from '../services'

interface ComputerVisionManagementState {
  missions: any[]
  selectedMission: any | null
  recentDetections: Detection[]
  isLoading: boolean
  error: string | null
  statistics: {
    totalDetections: number
    highPriorityDetections: number
    averageConfidence: number
    mostDetectedClass: string
  }
}

const ComputerVisionManagement: React.FC = () => {
  const [state, setState] = useState<ComputerVisionManagementState>({
    missions: [],
    selectedMission: null,
    recentDetections: [],
    isLoading: true,
    error: null,
    statistics: {
      totalDetections: 0,
      highPriorityDetections: 0,
      averageConfidence: 0,
      mostDetectedClass: 'N/A'
    }
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const missions = await missionService.getMissions()
      setState(prev => ({
        ...prev,
        missions,
        isLoading: false
      }))
    } catch (error) {
      console.error('Failed to load initial data:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to load computer vision data. Please try again.' 
      }))
    }
  }, [])

  const handleDetectionComplete = useCallback((detections: Detection[]) => {
    setState(prev => ({
      ...prev,
      recentDetections: [...detections, ...prev.recentDetections].slice(0, 20), // Keep last 20
      statistics: calculateStatistics([...detections, ...prev.recentDetections])
    }))
  }, [])

  const calculateStatistics = (detections: Detection[]) => {
    if (detections.length === 0) {
      return {
        totalDetections: 0,
        highPriorityDetections: 0,
        averageConfidence: 0,
        mostDetectedClass: 'N/A'
      }
    }

    const highPriorityCount = detections.filter(d => 
      d.priority === 'high' || d.priority === 'critical'
    ).length

    const averageConfidence = detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length

    // Find most detected class
    const classCounts = detections.reduce((counts, d) => {
      counts[d.class_name] = (counts[d.class_name] || 0) + 1
      return counts
    }, {} as Record<string, number>)

    const mostDetectedClass = Object.entries(classCounts)
      .sort(([, a], [, b]) => b - a)[0]?.[0] || 'N/A'

    return {
      totalDetections: detections.length,
      highPriorityDetections: highPriorityCount,
      averageConfidence: averageConfidence,
      mostDetectedClass
    }
  }

  const handleMissionSelect = useCallback((mission: any) => {
    setState(prev => ({ ...prev, selectedMission: mission }))
  }, [])

  const clearRecentDetections = useCallback(() => {
    setState(prev => ({
      ...prev,
      recentDetections: [],
      statistics: {
        totalDetections: 0,
        highPriorityDetections: 0,
        averageConfidence: 0,
        mostDetectedClass: 'N/A'
      }
    }))
  }, [])

  const getPriorityColor = (priority: string) => {
    return computerVisionService.getPriorityColor(priority)
  }

  const getPriorityIcon = (priority: string) => {
    return computerVisionService.getPriorityIcon(priority)
  }

  const formatConfidence = (confidence: number) => {
    return computerVisionService.formatConfidence(confidence)
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Computer Vision Management</h1>
            <p className="text-gray-600">AI-powered object detection and image analysis for SAR operations</p>
          </div>
          <div className="flex items-center space-x-4">
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

      {/* Statistics Overview */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Detections</p>
              <p className="text-2xl font-bold text-gray-900">{state.statistics.totalDetections}</p>
            </div>
            <div className="text-2xl">🔍</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">High Priority</p>
              <p className="text-2xl font-bold text-orange-600">{state.statistics.highPriorityDetections}</p>
            </div>
            <div className="text-2xl">⚠️</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Avg Confidence</p>
              <p className="text-2xl font-bold text-blue-600">
                {(state.statistics.averageConfidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="text-2xl">📊</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Most Detected</p>
              <p className="text-2xl font-bold text-green-600 capitalize">
                {state.statistics.mostDetectedClass}
              </p>
            </div>
            <div className="text-2xl">🎯</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Computer Vision Interface */}
        <div className="lg:col-span-2">
          <ComputerVision
            onDetectionComplete={handleDetectionComplete}
            missionContext={state.selectedMission ? {
              missionId: state.selectedMission.id,
              searchTarget: state.selectedMission.search_target
            } : undefined}
          />
        </div>

        {/* Mission Context & Recent Detections */}
        <div className="space-y-6">
          {/* Mission Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Mission Context</h2>
            
            {state.missions.length > 0 ? (
              <div className="space-y-3">
                <label htmlFor="mission-select" className="block text-sm font-medium text-gray-700">
                  Select Mission for Context
                </label>
                <select
                  id="mission-select"
                  value={state.selectedMission?.id || ''}
                  onChange={(e) => {
                    const mission = state.missions.find(m => m.id === e.target.value)
                    handleMissionSelect(mission || null)
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No mission selected</option>
                  {state.missions.map(mission => (
                    <option key={mission.id} value={mission.id}>
                      {mission.name} - {mission.search_target}
                    </option>
                  ))}
                </select>
                
                {state.selectedMission && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <h3 className="text-sm font-semibold text-blue-900">Selected Mission</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      <strong>Target:</strong> {state.selectedMission.search_target}
                    </p>
                    <p className="text-sm text-blue-700">
                      <strong>Status:</strong> {state.selectedMission.status}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-4">
                <p className="text-sm">No missions available</p>
                <p className="text-xs">Create a mission to provide context for detection</p>
              </div>
            )}
          </div>

          {/* Recent Detections */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Detections</h2>
              {state.recentDetections.length > 0 && (
                <button
                  onClick={clearRecentDetections}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              )}
            </div>
            
            {state.recentDetections.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {state.recentDetections.slice(0, 10).map((detection, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">{getPriorityIcon(detection.priority)}</span>
                        <span className="text-sm font-medium text-gray-900 capitalize">
                          {detection.class_name}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getPriorityColor(detection.priority)}`}>
                        {detection.priority}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <p><strong>Confidence:</strong> {formatConfidence(detection.confidence)}</p>
                      <p><strong>Time:</strong> {new Date(detection.timestamp).toLocaleTimeString()}</p>
                      <p><strong>Model:</strong> {detection.model_used}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">🔍</div>
                <p className="text-sm">No recent detections</p>
                <p className="text-xs">Upload and analyze images to see results here</p>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => {
                  // Open file dialog programmatically
                  const input = document.createElement('input')
                  input.type = 'file'
                  input.accept = 'image/*'
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0]
                    if (file) {
                      // This would trigger the ComputerVision component
                      console.log('File selected:', file.name)
                    }
                  }
                  input.click()
                }}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
              >
                📁 Upload Image
              </button>
              
              <button
                onClick={() => {
                  // Navigate to mission planning
                  window.location.href = '/mission-planning'
                }}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
              >
                📋 Create Mission
              </button>
              
              <button
                onClick={() => {
                  // Navigate to discovery management
                  window.location.href = '/discovery-management'
                }}
                className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium"
              >
                🔍 View Discoveries
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ComputerVisionManagement
