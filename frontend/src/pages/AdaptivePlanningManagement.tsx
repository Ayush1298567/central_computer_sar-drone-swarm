import React, { useState, useEffect, useCallback } from 'react'
import { AdaptivePlanning } from '../components/adaptivePlanning/AdaptivePlanning'
import { adaptivePlanningService, OptimizationResult, PerformanceInsights } from '../services/adaptivePlanning'

interface AdaptivePlanningManagementState {
  recentOptimizations: OptimizationResult[]
  performanceInsights: PerformanceInsights | null
  isLoading: boolean
  error: string | null
  selectedOptimization: OptimizationResult | null
}

const AdaptivePlanningManagement: React.FC = () => {
  const [state, setState] = useState<AdaptivePlanningManagementState>({
    recentOptimizations: [],
    performanceInsights: null,
    isLoading: true,
    error: null,
    selectedOptimization: null
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const [historyResponse, insightsResponse] = await Promise.all([
        adaptivePlanningService.getOptimizationHistory(10),
        adaptivePlanningService.getPerformanceInsights()
      ])
      
      setState(prev => ({
        ...prev,
        recentOptimizations: historyResponse.optimization_history || [],
        performanceInsights: insightsResponse.performance_insights,
        isLoading: false
      }))
    } catch (error) {
      console.error('Failed to load initial data:', error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: 'Failed to load adaptive planning data. Please try again.' 
      }))
    }
  }, [])

  const handleOptimizationComplete = useCallback((result: OptimizationResult) => {
    setState(prev => ({
      ...prev,
      recentOptimizations: [result, ...prev.recentOptimizations].slice(0, 10),
      selectedOptimization: result
    }))
    
    // Refresh performance insights
    loadInitialData()
  }, [loadInitialData])

  const handleOptimizationSelect = useCallback((optimization: OptimizationResult) => {
    setState(prev => ({ ...prev, selectedOptimization: optimization }))
  }, [])

  const getRiskColor = (risk: string) => {
    return adaptivePlanningService.getRiskColor(risk)
  }

  const formatDuration = (minutes: number) => {
    return adaptivePlanningService.formatDuration(minutes)
  }

  const getConfidenceColor = (score: number) => {
    return adaptivePlanningService.getConfidenceColor(score)
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Adaptive Planning Management</h1>
            <p className="text-gray-600">AI-powered mission optimization and dynamic planning</p>
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

      {/* Performance Overview */}
      {state.performanceInsights && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Optimizations</p>
                <p className="text-2xl font-bold text-gray-900">{state.performanceInsights.total_optimizations}</p>
              </div>
              <div className="text-2xl">📊</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {(state.performanceInsights.success_rate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Confidence</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(state.performanceInsights.average_confidence * 100).toFixed(1)}%
                </p>
              </div>
              <div className="text-2xl">🎯</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Duration</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatDuration(Math.round(state.performanceInsights.average_duration))}
                </p>
              </div>
              <div className="text-2xl">⏱️</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Avg Coverage</p>
                <p className="text-2xl font-bold text-purple-600">
                  {state.performanceInsights.average_coverage.toFixed(1)}%
                </p>
              </div>
              <div className="text-2xl">🗺️</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Adaptive Planning Interface */}
        <div className="lg:col-span-2">
          <AdaptivePlanning
            onOptimizationComplete={handleOptimizationComplete}
          />
        </div>

        {/* Recent Optimizations & Performance */}
        <div className="space-y-6">
          {/* Recent Optimizations */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Optimizations</h2>
            
            {state.recentOptimizations.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {state.recentOptimizations.map((optimization, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                      state.selectedOptimization === optimization
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleOptimizationSelect(optimization)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">Optimization #{index + 1}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${getRiskColor(optimization.risk_assessment)}`}>
                          {optimization.risk_assessment}
                        </span>
                      </div>
                      <span className={`text-xs font-medium ${getConfidenceColor(optimization.confidence_score)}`}>
                        {(optimization.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <p><strong>Duration:</strong> {formatDuration(optimization.estimated_duration)}</p>
                      <p><strong>Battery:</strong> {optimization.estimated_battery_usage.toFixed(1)}%</p>
                      <p><strong>Coverage:</strong> {optimization.coverage_percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-2">📈</div>
                <p className="text-sm">No recent optimizations</p>
                <p className="text-xs">Create and optimize missions to see results here</p>
              </div>
            )}
          </div>

          {/* Optimization Weights */}
          {state.performanceInsights && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Optimization Weights</h2>
              <div className="space-y-3">
                {Object.entries(state.performanceInsights.optimization_weights).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">
                      {key.replace('_', ' ')}
                    </span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${value * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500 w-8">
                        {(value * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => {
                  // Navigate to mission planning
                  window.location.href = '/mission-planning'
                }}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
              >
                📋 Create New Mission
              </button>
              
              <button
                onClick={() => {
                  // Navigate to computer vision
                  window.location.href = '/computer-vision'
                }}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
              >
                🔍 Computer Vision Analysis
              </button>
              
              <button
                onClick={() => {
                  // Navigate to drone management
                  window.location.href = '/drone-management'
                }}
                className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium"
              >
                🚁 Manage Drones
              </button>
              
              <button
                onClick={async () => {
                  try {
                    // Test optimization functionality
                    const testData = {
                      mission_id: 'test-mission',
                      search_target: 'test target',
                      area_size_km2: 1.0,
                      terrain_type: 'rural',
                      urgency_level: 'medium',
                      available_drones: [adaptivePlanningService.createDefaultDroneCapabilities('test-drone')],
                      constraints: {
                        max_duration_minutes: 120,
                        min_battery_reserve: 20.0,
                        max_altitude: 150.0,
                        min_altitude: 30.0,
                        weather_tolerance: 'moderate',
                        priority_areas: [],
                        no_fly_zones: []
                      }
                    }
                    
                    const response = await adaptivePlanningService.testOptimization(testData)
                    console.log('Test results:', response)
                    alert('Test completed. Check console for results.')
                  } catch (error) {
                    console.error('Test failed:', error)
                    alert('Test failed. Check console for details.')
                  }
                }}
                className="w-full px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-md text-sm font-medium"
              >
                🧪 Test Optimization
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdaptivePlanningManagement
