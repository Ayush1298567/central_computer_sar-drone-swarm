import React, { useState, useEffect, useCallback } from 'react'
import { learningSystemService, LearningInsights, LearningModel, PerformanceImprovement, LearningSystemStatus } from '../../services/learningSystem'

interface LearningSystemProps {
  onImprovementApplied?: (improvement: PerformanceImprovement) => void
  className?: string
}

const LearningSystem: React.FC<LearningSystemProps> = ({
  onImprovementApplied,
  className = ''
}) => {
  const [insights, setInsights] = useState<LearningInsights | null>(null)
  const [models, setModels] = useState<Record<string, LearningModel>>({})
  const [improvements, setImprovements] = useState<PerformanceImprovement[]>([])
  const [status, setStatus] = useState<LearningSystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'improvements' | 'status'>('overview')

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [insightsResponse, modelsResponse, improvementsResponse, statusResponse] = await Promise.all([
        learningSystemService.getLearningInsights(),
        learningSystemService.getLearningModels(),
        learningSystemService.getPerformanceImprovements(10),
        learningSystemService.getLearningSystemStatus()
      ])

      if (insightsResponse.success) {
        setInsights(insightsResponse.insights)
      }

      if (modelsResponse.success) {
        setModels(modelsResponse.models)
      }

      if (improvementsResponse.success) {
        setImprovements(improvementsResponse.improvements)
      }

      if (statusResponse.success) {
        setStatus(statusResponse.status)
      }
    } catch (error) {
      console.error('Failed to load learning system data:', error)
      setError('Failed to load learning system data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleApplyImprovement = useCallback(async (improvement: PerformanceImprovement) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await learningSystemService.applyImprovement(improvement.improvement_id)
      
      if (response.success) {
        // Remove applied improvement from list
        setImprovements(prev => prev.filter(imp => imp.improvement_id !== improvement.improvement_id))
        
        if (onImprovementApplied) {
          onImprovementApplied(improvement)
        }
        
        // Refresh data
        await loadInitialData()
      } else {
        setError('Failed to apply improvement. Please try again.')
      }
    } catch (error) {
      console.error('Failed to apply improvement:', error)
      setError('Failed to apply improvement. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [onImprovementApplied, loadInitialData])

  const handleEnableLearning = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await learningSystemService.enableLearning()
      
      if (response.success) {
        await loadInitialData()
      } else {
        setError('Failed to enable learning system.')
      }
    } catch (error) {
      console.error('Failed to enable learning:', error)
      setError('Failed to enable learning system.')
    } finally {
      setIsLoading(false)
    }
  }, [loadInitialData])

  const handleDisableLearning = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await learningSystemService.disableLearning()
      
      if (response.success) {
        await loadInitialData()
      } else {
        setError('Failed to disable learning system.')
      }
    } catch (error) {
      console.error('Failed to disable learning:', error)
      setError('Failed to disable learning system.')
    } finally {
      setIsLoading(false)
    }
  }, [loadInitialData])

  const getAlgorithmColor = (algorithm: string) => {
    return learningSystemService.getAlgorithmColor(algorithm)
  }

  const getMetricColor = (metric: string) => {
    return learningSystemService.getMetricColor(metric)
  }

  const getPriorityColor = (priority: string) => {
    return learningSystemService.getPriorityColor(priority)
  }

  const getHealthStatusColor = (status: string) => {
    return learningSystemService.getHealthStatusColor(status)
  }

  const formatAccuracy = (accuracy: number) => {
    return learningSystemService.formatAccuracy(accuracy)
  }

  const formatImprovement = (improvement: number) => {
    return learningSystemService.formatImprovement(improvement)
  }

  const formatConfidence = (confidence: number) => {
    return learningSystemService.formatConfidence(confidence)
  }

  const getTrendIcon = (trend: number) => {
    return learningSystemService.getTrendIcon(trend)
  }

  const getTrendDirection = (trend: number) => {
    return learningSystemService.getTrendDirection(trend)
  }

  const getImprovementImpact = (improvement: PerformanceImprovement) => {
    return learningSystemService.getImprovementImpact(improvement)
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Learning System</h2>
        <p className="text-sm text-gray-600">AI-powered performance improvement and continuous learning</p>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('models')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'models'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Models
            </button>
            <button
              onClick={() => setActiveTab('improvements')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'improvements'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Improvements
            </button>
            <button
              onClick={() => setActiveTab('status')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'status'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Status
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
      {activeTab === 'overview' && insights && (
        <div className="space-y-6">
          {/* System Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Models</p>
                  <p className="text-2xl font-bold text-gray-900">{insights.total_models}</p>
                </div>
                <div className="text-2xl">🤖</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Active Models</p>
                  <p className="text-2xl font-bold text-blue-600">{insights.active_models}</p>
                </div>
                <div className="text-2xl">⚡</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Avg Accuracy</p>
                  <p className="text-2xl font-bold text-green-600">{formatAccuracy(insights.average_accuracy)}</p>
                </div>
                <div className="text-2xl">🎯</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Improvements</p>
                  <p className="text-2xl font-bold text-purple-600">{insights.total_improvements}</p>
                </div>
                <div className="text-2xl">📈</div>
              </div>
            </div>
          </div>

          {/* Performance Trends */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Performance Trends</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(insights.performance_trends).map(([metric, trend]) => {
                const trendInfo = getTrendDirection(trend)
                return (
                  <div key={metric} className="flex items-center justify-between p-3 bg-white rounded border">
                    <div>
                      <p className="text-sm font-medium text-gray-900 capitalize">
                        {metric.replace('_', ' ')}
                      </p>
                      <p className={`text-sm ${trendInfo.color}`}>
                        {formatImprovement(trend)}
                      </p>
                    </div>
                    <div className="text-lg">{getTrendIcon(trend)}</div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Top Improvements */}
          {insights.top_improvements.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Top Improvement Opportunities</h3>
              <div className="space-y-3">
                {insights.top_improvements.slice(0, 3).map((improvement) => {
                  const impact = getImprovementImpact(improvement)
                  return (
                    <div key={improvement.improvement_id} className="flex items-center justify-between p-3 bg-white rounded border">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-1 text-xs rounded-full ${getMetricColor(improvement.metric_type)}`}>
                          {improvement.metric_type.replace('_', ' ')}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {formatImprovement(improvement.improvement_percentage)} improvement
                          </p>
                          <p className="text-xs text-gray-600">
                            Confidence: {formatConfidence(improvement.confidence)}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${impact.color}`}>
                        {impact.level}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Learning Recommendations */}
          {insights.learning_recommendations.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-md font-semibold text-blue-900 mb-3">Learning Recommendations</h3>
              <ul className="space-y-2">
                {insights.learning_recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-start space-x-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === 'models' && (
        <div className="space-y-4">
          {Object.keys(models).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(models).map(([modelId, model]) => (
                <div key={modelId} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-gray-900">{model.model_id}</h4>
                    <span className={`px-2 py-1 text-xs rounded-full ${getAlgorithmColor(model.algorithm)}`}>
                      {model.algorithm.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Metric:</span>
                      <span className="font-medium capitalize">{model.metric_type.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Accuracy:</span>
                      <span className="font-medium text-green-600">{formatAccuracy(model.accuracy)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Training Data:</span>
                      <span className="font-medium">{model.training_data_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last Trained:</span>
                      <span className="font-medium">{new Date(model.last_trained).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <div className="text-4xl mb-2">🤖</div>
              <p className="text-sm">No learning models available</p>
              <p className="text-xs">Models will appear as the system learns from mission data</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'improvements' && (
        <div className="space-y-4">
          {improvements.length > 0 ? (
            <div className="space-y-3">
              {improvements.map((improvement) => {
                const impact = getImprovementImpact(improvement)
                return (
                  <div key={improvement.improvement_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${getMetricColor(improvement.metric_type)}`}>
                          {improvement.metric_type.replace('_', ' ')}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(improvement.implementation_priority)}`}>
                          {improvement.implementation_priority}
                        </span>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${impact.color}`}>
                        {impact.level}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3 text-sm">
                      <div>
                        <p className="text-gray-600">Current Value</p>
                        <p className="font-medium">{improvement.current_value.toFixed(3)}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Predicted Value</p>
                        <p className="font-medium">{improvement.predicted_value.toFixed(3)}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Improvement</p>
                        <p className="font-medium text-green-600">
                          {formatImprovement(improvement.improvement_percentage)}
                        </p>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-sm text-gray-600 mb-2">Recommendations:</p>
                      <ul className="text-sm space-y-1">
                        {improvement.recommendations.map((recommendation, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <span className="text-gray-400 mt-0.5">•</span>
                            <span>{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        Confidence: {formatConfidence(improvement.confidence)}
                      </div>
                      <button
                        onClick={() => handleApplyImprovement(improvement)}
                        disabled={isLoading}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded text-sm"
                      >
                        {isLoading ? 'Applying...' : 'Apply'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <div className="text-4xl mb-2">📈</div>
              <p className="text-sm">No improvement opportunities available</p>
              <p className="text-xs">The system is performing optimally</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'status' && status && (
        <div className="space-y-6">
          {/* System Health */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">System Health</h3>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-gray-600">Overall Health Score</p>
                <p className="text-2xl font-bold text-gray-900">{(status.health_score * 100).toFixed(1)}%</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthStatusColor(status.health_status)}`}>
                {status.health_status.toUpperCase()}
              </span>
            </div>
            <div className="space-y-2">
              {status.health_factors.map((factor, index) => (
                <div key={index} className="text-sm text-gray-600">
                  • {factor}
                </div>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Learning Status</h4>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  status.learning_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {status.learning_enabled ? 'Enabled' : 'Disabled'}
                </span>
                {status.learning_enabled ? (
                  <button
                    onClick={handleDisableLearning}
                    disabled={isLoading}
                    className="text-xs text-red-600 hover:text-red-800"
                  >
                    Disable
                  </button>
                ) : (
                  <button
                    onClick={handleEnableLearning}
                    disabled={isLoading}
                    className="text-xs text-green-600 hover:text-green-800"
                  >
                    Enable
                  </button>
                )}
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Data Points</h4>
              <p className="text-2xl font-bold text-gray-900">{status.data_points.toLocaleString()}</p>
              <p className="text-xs text-gray-600">Total learning data points</p>
            </div>
          </div>

          {/* System Metrics */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">System Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Total Models</p>
                <p className="font-medium text-lg">{status.total_models}</p>
              </div>
              <div>
                <p className="text-gray-600">Active Models</p>
                <p className="font-medium text-lg">{status.active_models}</p>
              </div>
              <div>
                <p className="text-gray-600">Improvements</p>
                <p className="font-medium text-lg">{status.total_improvements}</p>
              </div>
              <div>
                <p className="text-gray-600">Last Updated</p>
                <p className="font-medium text-lg">{new Date(status.last_updated).toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading...</span>
        </div>
      )}
    </div>
  )
}

export default LearningSystem
