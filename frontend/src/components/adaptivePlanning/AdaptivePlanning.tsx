import React, { useState, useEffect, useCallback } from 'react'
import { adaptivePlanningService, MissionContext, OptimizationResult, DroneCapabilities, OptimizationConstraints } from '../../services/adaptivePlanning'

interface AdaptivePlanningProps {
  onOptimizationComplete?: (result: OptimizationResult) => void
  initialMissionContext?: Partial<MissionContext>
  className?: string
}

const AdaptivePlanning: React.FC<AdaptivePlanningProps> = ({
  onOptimizationComplete,
  initialMissionContext,
  className = ''
}) => {
  const [missionContext, setMissionContext] = useState<MissionContext>(
    initialMissionContext ? 
    { ...adaptivePlanningService.createDefaultMissionContext('', ''), ...initialMissionContext } :
    adaptivePlanningService.createDefaultMissionContext('', '')
  )
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'context' | 'optimization' | 'results'>('context')
  const [availableStrategies, setAvailableStrategies] = useState<any[]>([])
  const [availablePatterns, setAvailablePatterns] = useState<any[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState('adaptive')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      const [strategiesResponse, patternsResponse] = await Promise.all([
        adaptivePlanningService.getOptimizationStrategies(),
        adaptivePlanningService.getSearchPatterns()
      ])

      if (strategiesResponse.success) {
        setAvailableStrategies(strategiesResponse.optimization_strategies)
      }

      if (patternsResponse.success) {
        setAvailablePatterns(patternsResponse.search_patterns)
      }
    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }, [])

  const handleContextChange = useCallback((field: string, value: any) => {
    setMissionContext(prev => ({
      ...prev,
      [field]: value
    }))
  }, [])

  const handleConstraintsChange = useCallback((field: string, value: any) => {
    setMissionContext(prev => ({
      ...prev,
      constraints: {
        ...prev.constraints,
        [field]: value
      }
    }))
  }, [])

  const handleAddDrone = useCallback(() => {
    const newDrone = adaptivePlanningService.createDefaultDroneCapabilities(`drone-${Date.now()}`)
    setMissionContext(prev => ({
      ...prev,
      available_drones: [...prev.available_drones, newDrone]
    }))
  }, [])

  const handleRemoveDrone = useCallback((index: number) => {
    setMissionContext(prev => ({
      ...prev,
      available_drones: prev.available_drones.filter((_, i) => i !== index)
    }))
  }, [])

  const handleDroneChange = useCallback((index: number, field: string, value: any) => {
    setMissionContext(prev => ({
      ...prev,
      available_drones: prev.available_drones.map((drone, i) => 
        i === index ? { ...drone, [field]: value } : drone
      )
    }))
  }, [])

  const handleOptimizeMission = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Validate mission context
      const validation = adaptivePlanningService.validateMissionContext(missionContext)
      if (!validation.valid) {
        setError(`Validation failed: ${validation.errors.join(', ')}`)
        return
      }

      const response = await adaptivePlanningService.optimizeMission(missionContext, selectedStrategy)
      
      if (response.success) {
        setOptimizationResult(response.optimization_result)
        setActiveTab('results')
        if (onOptimizationComplete) {
          onOptimizationComplete(response.optimization_result)
        }
      } else {
        setError('Optimization failed')
      }
    } catch (error) {
      console.error('Optimization error:', error)
      setError('Failed to optimize mission. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [missionContext, selectedStrategy, onOptimizationComplete])

  const handleAnalyzeContext = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await adaptivePlanningService.analyzeMissionContext(missionContext)
      
      if (response.success) {
        console.log('Context analysis:', response.context_analysis)
        // You could display this in a modal or additional panel
      }
    } catch (error) {
      console.error('Context analysis error:', error)
      setError('Failed to analyze mission context.')
    } finally {
      setIsLoading(false)
    }
  }, [missionContext])

  const getStrategyColor = (strategy: string) => {
    return adaptivePlanningService.getStrategyColor(strategy)
  }

  const getRiskColor = (risk: string) => {
    return adaptivePlanningService.getRiskColor(risk)
  }

  const formatDuration = (minutes: number) => {
    return adaptivePlanningService.formatDuration(minutes)
  }

  const formatAreaSize = (km2: number) => {
    return adaptivePlanningService.formatAreaSize(km2)
  }

  const getConfidenceColor = (score: number) => {
    return adaptivePlanningService.getConfidenceColor(score)
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Adaptive Mission Planning</h2>
        <p className="text-sm text-gray-600">Optimize mission plans based on real-time conditions and constraints</p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('context')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'context'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mission Context
            </button>
            <button
              onClick={() => setActiveTab('optimization')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'optimization'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Optimization
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'results'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Results
            </button>
          </nav>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4 text-red-800">
          <p>{error}</p>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'context' && (
        <div className="space-y-6">
          {/* Basic Mission Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mission ID</label>
              <input
                type="text"
                value={missionContext.mission_id}
                onChange={(e) => handleContextChange('mission_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter mission ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Search Target</label>
              <input
                type="text"
                value={missionContext.search_target}
                onChange={(e) => handleContextChange('search_target', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter search target"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Area Size (km²)</label>
              <input
                type="number"
                value={missionContext.area_size_km2}
                onChange={(e) => handleContextChange('area_size_km2', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0.1"
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Terrain Type</label>
              <select
                value={missionContext.terrain_type}
                onChange={(e) => handleContextChange('terrain_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="rural">Rural</option>
                <option value="urban">Urban</option>
                <option value="mountainous">Mountainous</option>
                <option value="coastal">Coastal</option>
                <option value="forest">Forest</option>
                <option value="desert">Desert</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Urgency Level</label>
              <select
                value={missionContext.urgency_level}
                onChange={(e) => handleContextChange('urgency_level', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Weather Conditions */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Weather Conditions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Wind Speed (m/s)</label>
                <input
                  type="number"
                  value={missionContext.weather_conditions.wind_speed || ''}
                  onChange={(e) => handleContextChange('weather_conditions', {
                    ...missionContext.weather_conditions,
                    wind_speed: parseFloat(e.target.value) || undefined
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Visibility (m)</label>
                <input
                  type="number"
                  value={missionContext.weather_conditions.visibility || ''}
                  onChange={(e) => handleContextChange('weather_conditions', {
                    ...missionContext.weather_conditions,
                    visibility: parseFloat(e.target.value) || undefined
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Precipitation (mm/h)</label>
                <input
                  type="number"
                  value={missionContext.weather_conditions.precipitation || ''}
                  onChange={(e) => handleContextChange('weather_conditions', {
                    ...missionContext.weather_conditions,
                    precipitation: parseFloat(e.target.value) || undefined
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          {/* Constraints */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Mission Constraints</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Duration (minutes)</label>
                <input
                  type="number"
                  value={missionContext.constraints.max_duration_minutes}
                  onChange={(e) => handleConstraintsChange('max_duration_minutes', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Battery Reserve (%)</label>
                <input
                  type="number"
                  value={missionContext.constraints.min_battery_reserve}
                  onChange={(e) => handleConstraintsChange('min_battery_reserve', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="100"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Altitude (m)</label>
                <input
                  type="number"
                  value={missionContext.constraints.min_altitude}
                  onChange={(e) => handleConstraintsChange('min_altitude', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Altitude (m)</label>
                <input
                  type="number"
                  value={missionContext.constraints.max_altitude}
                  onChange={(e) => handleConstraintsChange('max_altitude', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          {/* Available Drones */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-md font-semibold text-gray-900">Available Drones</h3>
              <button
                onClick={handleAddDrone}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm"
              >
                Add Drone
              </button>
            </div>
            
            {missionContext.available_drones.length > 0 ? (
              <div className="space-y-3">
                {missionContext.available_drones.map((drone, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900">Drone {index + 1}</h4>
                      <button
                        onClick={() => handleRemoveDrone(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>
                        <label className="block text-xs text-gray-600">ID</label>
                        <input
                          type="text"
                          value={drone.drone_id}
                          onChange={(e) => handleDroneChange(index, 'drone_id', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Flight Time (min)</label>
                        <input
                          type="number"
                          value={drone.max_flight_time}
                          onChange={(e) => handleDroneChange(index, 'max_flight_time', parseInt(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                          min="1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Max Altitude (m)</label>
                        <input
                          type="number"
                          value={drone.max_altitude}
                          onChange={(e) => handleDroneChange(index, 'max_altitude', parseFloat(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                          min="0"
                          step="0.1"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600">Cruise Speed (m/s)</label>
                        <input
                          type="number"
                          value={drone.cruise_speed}
                          onChange={(e) => handleDroneChange(index, 'cruise_speed', parseFloat(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                          min="0"
                          step="0.1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No drones added. Click "Add Drone" to add drones to the mission.</p>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleAnalyzeContext}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Analyzing...' : 'Analyze Context'}
            </button>
            <button
              onClick={() => setActiveTab('optimization')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium"
            >
              Next: Optimization
            </button>
          </div>
        </div>
      )}

      {activeTab === 'optimization' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-md font-semibold text-gray-900 mb-3">Optimization Strategy</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableStrategies.map((strategy) => (
                <div
                  key={strategy.value}
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    selectedStrategy === strategy.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedStrategy(strategy.value)}
                >
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      checked={selectedStrategy === strategy.value}
                      onChange={() => setSelectedStrategy(strategy.value)}
                      className="text-blue-600"
                    />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{strategy.name}</h4>
                      <p className="text-xs text-gray-600">{strategy.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Mission Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Area Size</p>
                <p className="font-medium">{formatAreaSize(missionContext.area_size_km2)}</p>
              </div>
              <div>
                <p className="text-gray-600">Terrain</p>
                <p className="font-medium capitalize">{missionContext.terrain_type}</p>
              </div>
              <div>
                <p className="text-gray-600">Urgency</p>
                <p className="font-medium capitalize">{missionContext.urgency_level}</p>
              </div>
              <div>
                <p className="text-gray-600">Drones</p>
                <p className="font-medium">{missionContext.available_drones.length}</p>
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setActiveTab('context')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md font-medium"
            >
              Back: Context
            </button>
            <button
              onClick={handleOptimizeMission}
              disabled={isLoading || missionContext.available_drones.length === 0}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Optimizing...' : 'Optimize Mission'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'results' && optimizationResult && (
        <div className="space-y-6">
          {/* Optimization Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Confidence Score</p>
              <p className={`text-2xl font-bold ${getConfidenceColor(optimizationResult.confidence_score)}`}>
                {(optimizationResult.confidence_score * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Estimated Duration</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatDuration(optimizationResult.estimated_duration)}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Battery Usage</p>
              <p className="text-2xl font-bold text-gray-900">
                {optimizationResult.estimated_battery_usage.toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Coverage</p>
              <p className="text-2xl font-bold text-gray-900">
                {optimizationResult.coverage_percentage.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Risk Assessment</h3>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(optimizationResult.risk_assessment)}`}>
                {optimizationResult.risk_assessment.toUpperCase()}
              </span>
              <span className="text-sm text-gray-600">
                {optimizationResult.risk_assessment === 'low' && 'Low risk mission'}
                {optimizationResult.risk_assessment === 'medium' && 'Moderate risk mission'}
                {optimizationResult.risk_assessment === 'high' && 'High risk mission'}
              </span>
            </div>
          </div>

          {/* Recommendations */}
          {optimizationResult.recommendations.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-md font-semibold text-blue-900 mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {optimizationResult.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-start space-x-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Optimized Plan Details */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Optimized Plan Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Search Pattern</p>
                <p className="font-medium capitalize">{optimizationResult.optimized_plan.search_pattern}</p>
              </div>
              <div>
                <p className="text-gray-600">Optimal Altitude</p>
                <p className="font-medium">{optimizationResult.optimized_plan.optimal_altitude.toFixed(1)}m</p>
              </div>
              <div>
                <p className="text-gray-600">Total Waypoints</p>
                <p className="font-medium">{optimizationResult.optimized_plan.waypoints.length}</p>
              </div>
              <div>
                <p className="text-gray-600">Drone Assignments</p>
                <p className="font-medium">{optimizationResult.optimized_plan.drone_assignments.length}</p>
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setActiveTab('optimization')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md font-medium"
            >
              Back: Optimization
            </button>
            <button
              onClick={() => {
                // You could implement plan export or mission creation here
                console.log('Export optimized plan:', optimizationResult)
              }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md font-medium"
            >
              Export Plan
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdaptivePlanning
