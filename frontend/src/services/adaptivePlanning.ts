import api from './api'

export interface OptimizationConstraints {
  max_duration_minutes: number
  min_battery_reserve: number
  max_altitude: number
  min_altitude: number
  weather_tolerance: 'light' | 'moderate' | 'severe'
  priority_areas: Array<{
    lat: number
    lng: number
    radius: number
    priority: 'low' | 'medium' | 'high' | 'critical'
  }>
  no_fly_zones: Array<{
    lat: number
    lng: number
    radius: number
    reason: string
  }>
}

export interface DroneCapabilities {
  drone_id: string
  max_flight_time: number
  max_altitude: number
  max_speed: number
  cruise_speed: number
  battery_capacity: number
  camera_width: number
  camera_height: number
  gimbal_stabilization: boolean
  obstacle_avoidance: boolean
  weather_resistance: 'light' | 'moderate' | 'severe'
}

export interface MissionContext {
  mission_id: string
  search_target: string
  area_size_km2: number
  terrain_type: 'urban' | 'rural' | 'mountainous' | 'coastal' | 'forest' | 'desert'
  time_of_day: 'dawn' | 'day' | 'dusk' | 'night'
  weather_conditions: {
    wind_speed?: number
    visibility?: number
    precipitation?: number
    temperature?: number
    humidity?: number
  }
  urgency_level: 'low' | 'medium' | 'high' | 'critical'
  available_drones: DroneCapabilities[]
  constraints: OptimizationConstraints
}

export interface OptimizationResult {
  success: boolean
  confidence_score: number
  estimated_duration: number
  estimated_battery_usage: number
  coverage_percentage: number
  risk_assessment: 'low' | 'medium' | 'high'
  recommendations: string[]
  optimized_plan: {
    mission_id: string
    search_pattern: string
    optimal_altitude: number
    waypoints: Array<{
      lat: number
      lng: number
      altitude: number
      type: string
      order: number
    }>
    drone_assignments: Array<{
      drone_id: string
      assigned_waypoints: any[]
      estimated_duration: number
      battery_usage: number
      priority: string
    }>
    estimated_duration: number
    safety_margins: {
      battery_reserve: number
      time_buffer: number
      altitude_buffer: number
      weather_buffer: number
    }
    optimization_applied?: string
    validation_passed?: boolean
    refinements_applied?: boolean
  }
}

export interface SearchPattern {
  value: string
  name: string
  description: string
}

export interface OptimizationStrategy {
  value: string
  name: string
  description: string
}

export interface PerformanceInsights {
  total_optimizations: number
  success_rate: number
  average_confidence: number
  average_duration: number
  average_coverage: number
  optimization_weights: {
    time_efficiency: number
    coverage_quality: number
    battery_conservation: number
    safety_margin: number
    weather_adaptation: number
  }
}

export const adaptivePlanningService = {
  /**
   * Optimize a mission plan using adaptive planning algorithms
   */
  async optimizeMission(
    missionData: MissionContext,
    strategy: string = 'adaptive'
  ): Promise<{ success: boolean; optimization_result: OptimizationResult; optimized_plan: any; strategy_used: string; mission_id: string }> {
    const response = await api.post('/adaptive-planning/optimize-mission', {
      ...missionData,
      strategy
    })
    return response.data
  },

  /**
   * Analyze mission context for optimization decisions
   */
  async analyzeMissionContext(missionData: MissionContext) {
    const response = await api.post('/adaptive-planning/analyze-mission-context', missionData)
    return response.data
  },

  /**
   * Generate search pattern waypoints for a mission area
   */
  async generateSearchPattern(patternData: {
    center_lat: number
    center_lng: number
    area_size_km2: number
    pattern_type: string
    altitude: number
    terrain_type?: string
    time_of_day?: string
    weather_conditions?: any
    urgency_level?: string
  }) {
    const response = await api.post('/adaptive-planning/generate-search-pattern', patternData)
    return response.data
  },

  /**
   * Optimize drone assignment for a mission
   */
  async optimizeDroneAssignment(assignmentData: {
    available_drones: DroneCapabilities[]
    waypoints: any[]
    mission_area_km2: number
    terrain_type?: string
    time_of_day?: string
    weather_conditions?: any
    urgency_level?: string
  }) {
    const response = await api.post('/adaptive-planning/optimize-drone-assignment', assignmentData)
    return response.data
  },

  /**
   * Get optimization history for analysis
   */
  async getOptimizationHistory(limit: number = 100) {
    const response = await api.get('/adaptive-planning/optimization-history', {
      params: { limit }
    })
    return response.data
  },

  /**
   * Get performance insights from optimization history
   */
  async getPerformanceInsights(): Promise<{ success: boolean; performance_insights: PerformanceInsights }> {
    const response = await api.get('/adaptive-planning/performance-insights')
    return response.data
  },

  /**
   * Update optimization weights based on performance
   */
  async updateOptimizationWeights(weights: {
    time_efficiency?: number
    coverage_quality?: number
    battery_conservation?: number
    safety_margin?: number
    weather_adaptation?: number
  }) {
    const response = await api.post('/adaptive-planning/update-optimization-weights', weights)
    return response.data
  },

  /**
   * Get available optimization strategies
   */
  async getOptimizationStrategies(): Promise<{ success: boolean; optimization_strategies: OptimizationStrategy[] }> {
    const response = await api.get('/adaptive-planning/optimization-strategies')
    return response.data
  },

  /**
   * Get available search patterns
   */
  async getSearchPatterns(): Promise<{ success: boolean; search_patterns: SearchPattern[] }> {
    const response = await api.get('/adaptive-planning/search-patterns')
    return response.data
  },

  /**
   * Test endpoint for adaptive planning functionality
   */
  async testOptimization(testData: any) {
    const response = await api.post('/adaptive-planning/test-optimization', testData)
    return response.data
  },

  /**
   * Utility function to create default mission context
   */
  createDefaultMissionContext(missionId: string, searchTarget: string): MissionContext {
    return {
      mission_id: missionId,
      search_target: searchTarget,
      area_size_km2: 1.0,
      terrain_type: 'rural',
      time_of_day: 'day',
      weather_conditions: {},
      urgency_level: 'medium',
      available_drones: [],
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
  },

  /**
   * Utility function to create default drone capabilities
   */
  createDefaultDroneCapabilities(droneId: string): DroneCapabilities {
    return {
      drone_id: droneId,
      max_flight_time: 30,
      max_altitude: 120.0,
      max_speed: 15.0,
      cruise_speed: 10.0,
      battery_capacity: 100.0,
      camera_width: 1920,
      camera_height: 1080,
      gimbal_stabilization: false,
      obstacle_avoidance: false,
      weather_resistance: 'light'
    }
  },

  /**
   * Utility function to get strategy color
   */
  getStrategyColor(strategy: string): string {
    switch (strategy) {
      case 'time_efficient': return 'text-blue-600 bg-blue-100'
      case 'coverage_optimal': return 'text-green-600 bg-green-100'
      case 'battery_conservative': return 'text-yellow-600 bg-yellow-100'
      case 'adaptive': return 'text-purple-600 bg-purple-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get pattern color
   */
  getPatternColor(pattern: string): string {
    switch (pattern) {
      case 'grid': return 'text-blue-600 bg-blue-100'
      case 'spiral': return 'text-green-600 bg-green-100'
      case 'concentric': return 'text-yellow-600 bg-yellow-100'
      case 'lawnmower': return 'text-purple-600 bg-purple-100'
      case 'adaptive': return 'text-orange-600 bg-orange-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get risk assessment color
   */
  getRiskColor(risk: string): string {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'high': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to format duration
   */
  formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes}m`
    } else {
      const hours = Math.floor(minutes / 60)
      const remainingMinutes = minutes % 60
      return `${hours}h ${remainingMinutes}m`
    }
  },

  /**
   * Utility function to format area size
   */
  formatAreaSize(km2: number): string {
    if (km2 < 1) {
      return `${(km2 * 1000000).toFixed(0)} m²`
    } else {
      return `${km2.toFixed(2)} km²`
    }
  },

  /**
   * Utility function to calculate confidence score color
   */
  getConfidenceColor(score: number): string {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  },

  /**
   * Utility function to validate mission context
   */
  validateMissionContext(context: MissionContext): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!context.mission_id) {
      errors.push('Mission ID is required')
    }

    if (!context.search_target) {
      errors.push('Search target is required')
    }

    if (context.area_size_km2 <= 0) {
      errors.push('Area size must be greater than 0')
    }

    if (context.available_drones.length === 0) {
      errors.push('At least one drone is required')
    }

    if (context.constraints.max_duration_minutes <= 0) {
      errors.push('Maximum duration must be greater than 0')
    }

    if (context.constraints.min_altitude >= context.constraints.max_altitude) {
      errors.push('Minimum altitude must be less than maximum altitude')
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }
}
