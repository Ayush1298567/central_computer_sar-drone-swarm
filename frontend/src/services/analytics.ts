import api from './api'

export interface MissionAnalytics {
  total_duration: number
  area_covered: number
  discoveries_found: number
  average_discovery_confidence: number
  mission_efficiency_score: number
  battery_consumption: number
  drone_utilization: number
  weather_impact: number
  completion_rate: number
}

export interface DronePerformanceAnalytics {
  total_flight_time: number
  average_battery_efficiency: number
  discovery_contribution: number
  reliability_score: number
  maintenance_frequency: number
  average_speed: number
  altitude_efficiency: number
}

export interface SystemAnalytics {
  total_missions: number
  successful_missions: number
  average_mission_duration: number
  total_discoveries: number
  system_uptime: number
  average_drone_utilization: number
  peak_performance_period: string
  improvement_areas: string[]
}

export interface PerformanceTrend {
  date: string
  value: number
  count: number
}

export interface MissionSummary {
  performance_grade: string
  key_metrics: {
    efficiency_score: number
    discoveries_found: number
    duration_minutes: number
    area_covered_sqm: number
    battery_consumption_percent: number
  }
  insights: string[]
  recommendations: string[]
}

export interface DronePerformance {
  performance_score: number
  key_metrics: {
    reliability_score: number
    battery_efficiency: number
    discovery_contribution: number
    maintenance_frequency: number
    average_speed: number
    altitude_efficiency: number
    total_flight_time: number
  }
  insights: string[]
  recommendations: string[]
}

export interface SystemHealth {
  health_score: number
  health_status: string
  health_factors: string[]
  system_metrics: {
    total_missions: number
    successful_missions: number
    system_uptime: number
    average_drone_utilization: number
    total_discoveries: number
    average_mission_duration: number
  }
  improvement_areas: string[]
  recommendations: string[]
}

export interface DiscoveryTrend {
  date: string
  discoveries: number
  types: Record<string, number>
  confidence_avg: number
}

export interface BatteryReport {
  summary: {
    total_flight_time: number
    average_battery_consumption: number
    most_efficient_drone: string
    least_efficient_drone: string
  }
  drone_breakdown: Array<{
    drone_id: string
    flight_time: number
    battery_consumption: number
    efficiency_score: number
  }>
  recommendations: string[]
}

export const analyticsService = {
  /**
   * Get comprehensive analytics for a specific mission.
   */
  async getMissionAnalytics(missionId: string): Promise<MissionAnalytics> {
    const response = await api.get(`/analytics/missions/${missionId}/analytics`)
    return response.data.analytics
  },

  /**
   * Get comprehensive analytics for a specific drone over a given period.
   */
  async getDroneAnalytics(droneId: string, days: number = 30): Promise<DronePerformanceAnalytics> {
    const response = await api.get(`/analytics/drones/${droneId}/analytics`, {
      params: { days }
    })
    return response.data.analytics
  },

  /**
   * Get comprehensive analytics for the entire system over a given period.
   */
  async getSystemAnalytics(days: number = 30): Promise<SystemAnalytics> {
    const response = await api.get('/analytics/system/analytics', {
      params: { days }
    })
    return response.data.analytics
  },

  /**
   * Get performance trends for a specific metric type over time.
   */
  async getPerformanceTrends(metricType: string, days: number = 30): Promise<PerformanceTrend[]> {
    const response = await api.get(`/analytics/trends/${metricType}`, {
      params: { days }
    })
    return response.data.trends
  },

  /**
   * Get a summary of mission performance with key metrics and insights.
   */
  async getMissionSummary(missionId: string): Promise<MissionSummary> {
    const response = await api.get(`/analytics/missions/${missionId}/summary`)
    return response.data.summary
  },

  /**
   * Get detailed performance analysis for a specific drone.
   */
  async getDronePerformance(droneId: string, days: number = 30): Promise<DronePerformance> {
    const response = await api.get(`/analytics/drones/${droneId}/performance`, {
      params: { days }
    })
    return response.data.performance
  },

  /**
   * Get overall system health assessment.
   */
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get('/analytics/system/health')
    return response.data.health
  },

  /**
   * Get discovery trends and patterns over time.
   */
  async getDiscoveryTrends(params?: {
    start_date?: string
    end_date?: string
    type?: string
  }): Promise<{
    trends: DiscoveryTrend[]
    summary: {
      total_discoveries: number
      average_confidence: number
      most_common_type: string
      trend_direction: string
    }
  }> {
    const response = await api.get('/analytics/discoveries/trends', { params })
    return {
      trends: response.data.trends,
      summary: response.data.summary
    }
  },

  /**
   * Get comprehensive battery usage report.
   */
  async getBatteryReport(params?: {
    start_date?: string
    end_date?: string
    drone_id?: string
  }): Promise<BatteryReport> {
    const response = await api.get('/analytics/battery/report', { params })
    return response.data.report
  },

  // Utility functions for formatting and display
  formatEfficiencyScore(score: number): string {
    return `${(score * 100).toFixed(1)}%`
  },

  formatDuration(minutes: number): string {
    const hours = Math.floor(minutes / 60)
    const mins = Math.floor(minutes % 60)
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  },

  formatArea(squareMeters: number): string {
    if (squareMeters >= 1000000) {
      return `${(squareMeters / 1000000).toFixed(2)} km²`
    } else if (squareMeters >= 10000) {
      return `${(squareMeters / 10000).toFixed(2)} ha`
    } else {
      return `${squareMeters.toFixed(0)} m²`
    }
  },

  formatBatteryLevel(level: number): string {
    return `${level.toFixed(1)}%`
  },

  formatSpeed(speed: number): string {
    return `${speed.toFixed(1)} m/s`
  },

  getPerformanceGradeColor(grade: string): string {
    switch (grade) {
      case 'A': return 'text-green-600'
      case 'B': return 'text-blue-600'
      case 'C': return 'text-yellow-600'
      case 'D': return 'text-red-600'
      default: return 'text-gray-600'
    }
  },

  getHealthStatusColor(status: string): string {
    switch (status) {
      case 'excellent': return 'text-green-600'
      case 'good': return 'text-blue-600'
      case 'fair': return 'text-yellow-600'
      case 'poor': return 'text-red-600'
      default: return 'text-gray-600'
    }
  },

  getTrendDirection(trend: number): { direction: string; color: string } {
    if (trend > 0.1) {
      return { direction: 'up', color: 'text-green-600' }
    } else if (trend < -0.1) {
      return { direction: 'down', color: 'text-red-600' }
    } else {
      return { direction: 'stable', color: 'text-gray-600' }
    }
  },

  getTrendIcon(trend: number): string {
    if (trend > 0.1) return '📈'
    if (trend < -0.1) return '📉'
    return '➡️'
  }
}