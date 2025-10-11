import React, { useState, useEffect, useCallback } from 'react'
import { analyticsService, SystemAnalytics, SystemHealth, PerformanceTrend, DiscoveryTrend, BatteryReport } from '../../services/analytics'

interface AnalyticsDashboardProps {
  className?: string
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className = '' }) => {
  const [systemAnalytics, setSystemAnalytics] = useState<SystemAnalytics | null>(null)
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [performanceTrends, setPerformanceTrends] = useState<PerformanceTrend[]>([])
  const [discoveryTrends, setDiscoveryTrends] = useState<DiscoveryTrend[]>([])
  const [batteryReport, setBatteryReport] = useState<BatteryReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'trends' | 'battery' | 'health'>('overview')
  const [selectedMetric, setSelectedMetric] = useState('mission_efficiency')
  const [timeRange, setTimeRange] = useState(30)

  useEffect(() => {
    loadAnalyticsData()
  }, [timeRange])

  const loadAnalyticsData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [systemAnalyticsResponse, systemHealthResponse, trendsResponse, discoveryResponse, batteryResponse] = await Promise.all([
        analyticsService.getSystemAnalytics(timeRange),
        analyticsService.getSystemHealth(),
        analyticsService.getPerformanceTrends(selectedMetric, timeRange),
        analyticsService.getDiscoveryTrends(),
        analyticsService.getBatteryReport()
      ])

      setSystemAnalytics(systemAnalyticsResponse)
      setSystemHealth(systemHealthResponse)
      setPerformanceTrends(trendsResponse)
      setDiscoveryTrends(discoveryResponse.trends)
      setBatteryReport(batteryResponse)
    } catch (error) {
      console.error('Failed to load analytics data:', error)
      setError('Failed to load analytics data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange, selectedMetric])

  const handleMetricChange = useCallback((metric: string) => {
    setSelectedMetric(metric)
    loadAnalyticsData()
  }, [loadAnalyticsData])

  const handleTimeRangeChange = useCallback((days: number) => {
    setTimeRange(days)
  }, [])

  const getHealthStatusColor = (status: string) => {
    return analyticsService.getHealthStatusColor(status)
  }

  const getPerformanceGradeColor = (grade: string) => {
    return analyticsService.getPerformanceGradeColor(grade)
  }

  const getTrendDirection = (trend: number) => {
    return analyticsService.getTrendDirection(trend)
  }

  const getTrendIcon = (trend: number) => {
    return analyticsService.getTrendIcon(trend)
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Analytics Dashboard</h2>
        <p className="text-sm text-gray-600">Comprehensive system performance analysis and insights</p>
      </div>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <label htmlFor="time-range" className="text-sm font-medium text-gray-700">
            Time Range:
          </label>
          <select
            id="time-range"
            value={timeRange}
            onChange={(e) => handleTimeRangeChange(Number(e.target.value))}
            className="border-gray-300 rounded-md shadow-sm text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label htmlFor="metric" className="text-sm font-medium text-gray-700">
            Metric:
          </label>
          <select
            id="metric"
            value={selectedMetric}
            onChange={(e) => handleMetricChange(e.target.value)}
            className="border-gray-300 rounded-md shadow-sm text-sm"
          >
            <option value="mission_efficiency">Mission Efficiency</option>
            <option value="discovery_rate">Discovery Rate</option>
            <option value="battery_usage">Battery Usage</option>
            <option value="drone_performance">Drone Performance</option>
          </select>
        </div>
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
              onClick={() => setActiveTab('trends')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'trends'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Trends
            </button>
            <button
              onClick={() => setActiveTab('battery')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'battery'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Battery
            </button>
            <button
              onClick={() => setActiveTab('health')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'health'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Health
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
      {activeTab === 'overview' && systemAnalytics && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Missions</p>
                  <p className="text-2xl font-bold text-gray-900">{systemAnalytics.total_missions}</p>
                </div>
                <div className="text-2xl">📋</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Success Rate</p>
                  <p className="text-2xl font-bold text-green-600">
                    {systemAnalytics.total_missions > 0 
                      ? `${((systemAnalytics.successful_missions / systemAnalytics.total_missions) * 100).toFixed(1)}%`
                      : '0%'
                    }
                  </p>
                </div>
                <div className="text-2xl">✅</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Discoveries</p>
                  <p className="text-2xl font-bold text-blue-600">{systemAnalytics.total_discoveries}</p>
                </div>
                <div className="text-2xl">🔍</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">System Uptime</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {analyticsService.formatEfficiencyScore(systemAnalytics.system_uptime)}
                  </p>
                </div>
                <div className="text-2xl">⚡</div>
              </div>
            </div>
          </div>

          {/* Performance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Mission Performance</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Average Duration:</span>
                  <span className="font-medium">
                    {analyticsService.formatDuration(systemAnalytics.average_mission_duration)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Drone Utilization:</span>
                  <span className="font-medium">
                    {analyticsService.formatEfficiencyScore(systemAnalytics.average_drone_utilization)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Peak Performance:</span>
                  <span className="font-medium">{systemAnalytics.peak_performance_period}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Improvement Areas</h3>
              {systemAnalytics.improvement_areas.length > 0 ? (
                <ul className="space-y-1 text-sm">
                  {systemAnalytics.improvement_areas.slice(0, 3).map((area, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-yellow-500 mt-0.5">•</span>
                      <span className="text-gray-700">{area}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-green-600">No significant improvement areas identified</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Performance Trends Chart */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">
              {selectedMetric.replace('_', ' ').toUpperCase()} Trends
            </h3>
            {performanceTrends.length > 0 ? (
              <div className="space-y-2">
                {performanceTrends.slice(-7).map((trend, index) => {
                  const trendInfo = getTrendDirection(trend.value)
                  return (
                    <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
                      <span className="text-sm text-gray-600">
                        {new Date(trend.date).toLocaleDateString()}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-medium ${trendInfo.color}`}>
                          {trend.value.toFixed(2)}
                        </span>
                        <span className="text-lg">{getTrendIcon(trend.value)}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No trend data available</p>
            )}
          </div>

          {/* Discovery Trends */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Discovery Trends</h3>
            {discoveryTrends.length > 0 ? (
              <div className="space-y-2">
                {discoveryTrends.slice(-5).map((trend, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
                    <span className="text-sm text-gray-600">
                      {new Date(trend.date).toLocaleDateString()}
                    </span>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium text-blue-600">
                        {trend.discoveries} discoveries
                      </span>
                      <span className="text-xs text-gray-500">
                        Avg confidence: {(trend.confidence_avg * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No discovery trend data available</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'battery' && batteryReport && (
        <div className="space-y-6">
          {/* Battery Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Flight Time</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analyticsService.formatDuration(batteryReport.summary.total_flight_time)}
                  </p>
                </div>
                <div className="text-2xl">⏱️</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Avg Consumption</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {analyticsService.formatBatteryLevel(batteryReport.summary.average_battery_consumption)}
                  </p>
                </div>
                <div className="text-2xl">🔋</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Most Efficient</p>
                  <p className="text-lg font-bold text-green-600">
                    {batteryReport.summary.most_efficient_drone}
                  </p>
                </div>
                <div className="text-2xl">🏆</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Needs Optimization</p>
                  <p className="text-lg font-bold text-red-600">
                    {batteryReport.summary.least_efficient_drone}
                  </p>
                </div>
                <div className="text-2xl">⚠️</div>
              </div>
            </div>
          </div>

          {/* Drone Battery Breakdown */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Drone Battery Performance</h3>
            <div className="space-y-3">
              {batteryReport.drone_breakdown.map((drone) => (
                <div key={drone.drone_id} className="flex items-center justify-between p-3 bg-white rounded border">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-900">{drone.drone_id}</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      drone.efficiency_score > 0.8 ? 'bg-green-100 text-green-800' :
                      drone.efficiency_score > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {(drone.efficiency_score * 100).toFixed(0)}% efficient
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Flight: {analyticsService.formatDuration(drone.flight_time)}</span>
                    <span>Battery: {analyticsService.formatBatteryLevel(drone.battery_consumption)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Battery Recommendations */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-md font-semibold text-blue-900 mb-3">Battery Optimization Recommendations</h3>
            <ul className="space-y-2">
              {batteryReport.recommendations.map((recommendation, index) => (
                <li key={index} className="text-sm text-blue-800 flex items-start space-x-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'health' && systemHealth && (
        <div className="space-y-6">
          {/* Health Overview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-md font-semibold text-gray-900">System Health Score</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {(systemHealth.health_score * 100).toFixed(1)}%
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthStatusColor(systemHealth.health_status)}`}>
                {systemHealth.health_status.toUpperCase()}
              </span>
            </div>
            <div className="space-y-2">
              {systemHealth.health_factors.map((factor, index) => (
                <div key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                  <span className="text-green-500 mt-0.5">•</span>
                  <span>{factor}</span>
                </div>
              ))}
            </div>
          </div>

          {/* System Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-md font-semibold text-gray-900 mb-3">System Metrics</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Missions:</span>
                  <span className="font-medium">{systemHealth.system_metrics.total_missions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Successful Missions:</span>
                  <span className="font-medium">{systemHealth.system_metrics.successful_missions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">System Uptime:</span>
                  <span className="font-medium">
                    {analyticsService.formatEfficiencyScore(systemHealth.system_metrics.system_uptime)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Drone Utilization:</span>
                  <span className="font-medium">
                    {analyticsService.formatEfficiencyScore(systemHealth.system_metrics.average_drone_utilization)}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Health Recommendations</h3>
              <ul className="space-y-2 text-sm">
                {systemHealth.recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-blue-500 mt-0.5">•</span>
                    <span className="text-gray-700">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Improvement Areas */}
          {systemHealth.improvement_areas.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-md font-semibold text-yellow-900 mb-3">Areas for Improvement</h3>
              <ul className="space-y-2">
                {systemHealth.improvement_areas.map((area, index) => (
                  <li key={index} className="text-sm text-yellow-800 flex items-start space-x-2">
                    <span className="text-yellow-600 mt-0.5">•</span>
                    <span>{area}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading analytics...</span>
        </div>
      )}
    </div>
  )
}

export default AnalyticsDashboard