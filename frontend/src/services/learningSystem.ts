import api from './api'

export interface LearningModel {
  model_id: string
  algorithm: string
  metric_type: string
  accuracy: number
  last_trained: string
  training_data_count: number
  model_parameters: Record<string, any>
}

export interface PerformanceImprovement {
  improvement_id: string
  metric_type: string
  current_value: number
  predicted_value: number
  improvement_percentage: number
  confidence: number
  recommendations: string[]
  implementation_priority: 'low' | 'medium' | 'high' | 'critical'
}

export interface LearningInsights {
  total_models: number
  active_models: number
  average_accuracy: number
  total_improvements: number
  performance_trends: Record<string, number>
  top_improvements: PerformanceImprovement[]
  learning_recommendations: string[]
}

export interface LearningAlgorithm {
  value: string
  name: string
  description: string
}

export interface PerformanceMetric {
  value: string
  name: string
  description: string
}

export interface LearningDataSummary {
  total_data_points: number
  data_by_metric: Record<string, number>
  recent_data_points: number
  data_quality_score: number
}

export interface LearningSystemStatus {
  health_score: number
  health_status: 'excellent' | 'good' | 'fair' | 'poor'
  health_factors: string[]
  learning_enabled: boolean
  total_models: number
  active_models: number
  total_improvements: number
  data_points: number
  last_updated: string
}

export const learningSystemService = {
  /**
   * Get comprehensive learning system insights
   */
  async getLearningInsights(): Promise<{ success: boolean; insights: LearningInsights }> {
    const response = await api.get('/learning-system/insights')
    return response.data
  },

  /**
   * Get all learning models and their status
   */
  async getLearningModels(): Promise<{ success: boolean; models: Record<string, LearningModel>; total_models: number }> {
    const response = await api.get('/learning-system/models')
    return response.data
  },

  /**
   * Get performance improvement recommendations
   */
  async getPerformanceImprovements(limit: number = 20): Promise<{ success: boolean; improvements: PerformanceImprovement[]; total_improvements: number }> {
    const response = await api.get('/learning-system/improvements', {
      params: { limit }
    })
    return response.data
  },

  /**
   * Apply a specific performance improvement
   */
  async applyImprovement(improvementId: string): Promise<{ success: boolean; message: string; improvement_id: string }> {
    const response = await api.post('/learning-system/apply-improvement', {
      improvement_id: improvementId
    })
    return response.data
  },

  /**
   * Get summary of learning data
   */
  async getLearningDataSummary(): Promise<{ success: boolean; data_summary: LearningDataSummary }> {
    const response = await api.get('/learning-system/data-summary')
    return response.data
  },

  /**
   * Disable the learning system
   */
  async disableLearning(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning-system/disable-learning')
    return response.data
  },

  /**
   * Enable the learning system
   */
  async enableLearning(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning-system/enable-learning')
    return response.data
  },

  /**
   * Reset all learning models
   */
  async resetLearningModels(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning-system/reset-models')
    return response.data
  },

  /**
   * Get available learning algorithms
   */
  async getLearningAlgorithms(): Promise<{ success: boolean; algorithms: LearningAlgorithm[] }> {
    const response = await api.get('/learning-system/algorithms')
    return response.data
  },

  /**
   * Get available performance metrics
   */
  async getPerformanceMetrics(): Promise<{ success: boolean; metrics: PerformanceMetric[] }> {
    const response = await api.get('/learning-system/metrics')
    return response.data
  },

  /**
   * Test endpoint for learning system functionality
   */
  async testLearningSystem(testData: any): Promise<{ success: boolean; test_results: any; summary: any }> {
    const response = await api.post('/learning-system/test-learning', testData)
    return response.data
  },

  /**
   * Get learning system status and health
   */
  async getLearningSystemStatus(): Promise<{ success: boolean; status: LearningSystemStatus }> {
    const response = await api.get('/learning-system/status')
    return response.data
  },

  /**
   * Utility function to get algorithm color
   */
  getAlgorithmColor(algorithm: string): string {
    switch (algorithm) {
      case 'reinforcement_learning': return 'text-blue-600 bg-blue-100'
      case 'supervised_learning': return 'text-green-600 bg-green-100'
      case 'unsupervised_learning': return 'text-yellow-600 bg-yellow-100'
      case 'deep_learning': return 'text-purple-600 bg-purple-100'
      case 'genetic_algorithm': return 'text-orange-600 bg-orange-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get metric color
   */
  getMetricColor(metric: string): string {
    switch (metric) {
      case 'mission_efficiency': return 'text-blue-600 bg-blue-100'
      case 'battery_optimization': return 'text-green-600 bg-green-100'
      case 'discovery_accuracy': return 'text-purple-600 bg-purple-100'
      case 'flight_path_optimization': return 'text-yellow-600 bg-yellow-100'
      case 'weather_adaptation': return 'text-orange-600 bg-orange-100'
      case 'drone_coordination': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get priority color
   */
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get health status color
   */
  getHealthStatusColor(status: string): string {
    switch (status) {
      case 'excellent': return 'text-green-600 bg-green-100'
      case 'good': return 'text-blue-600 bg-blue-100'
      case 'fair': return 'text-yellow-600 bg-yellow-100'
      case 'poor': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to format accuracy percentage
   */
  formatAccuracy(accuracy: number): string {
    return `${(accuracy * 100).toFixed(1)}%`
  },

  /**
   * Utility function to format improvement percentage
   */
  formatImprovement(improvement: number): string {
    const sign = improvement >= 0 ? '+' : ''
    return `${sign}${improvement.toFixed(1)}%`
  },

  /**
   * Utility function to format confidence score
   */
  formatConfidence(confidence: number): string {
    return `${(confidence * 100).toFixed(1)}%`
  },

  /**
   * Utility function to get trend direction
   */
  getTrendDirection(trend: number): { direction: 'up' | 'down' | 'stable'; color: string } {
    if (trend > 5) {
      return { direction: 'up', color: 'text-green-600' }
    } else if (trend < -5) {
      return { direction: 'down', color: 'text-red-600' }
    } else {
      return { direction: 'stable', color: 'text-gray-600' }
    }
  },

  /**
   * Utility function to get trend icon
   */
  getTrendIcon(trend: number): string {
    if (trend > 5) {
      return '📈'
    } else if (trend < -5) {
      return '📉'
    } else {
      return '➡️'
    }
  },

  /**
   * Utility function to calculate overall system health
   */
  calculateSystemHealth(status: LearningSystemStatus): { score: number; status: string; color: string } {
    const score = status.health_score
    let healthStatus = 'poor'
    let color = 'text-red-600'

    if (score >= 0.8) {
      healthStatus = 'excellent'
      color = 'text-green-600'
    } else if (score >= 0.6) {
      healthStatus = 'good'
      color = 'text-blue-600'
    } else if (score >= 0.4) {
      healthStatus = 'fair'
      color = 'text-yellow-600'
    }

    return { score, status: healthStatus, color }
  },

  /**
   * Utility function to validate improvement data
   */
  validateImprovement(improvement: PerformanceImprovement): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!improvement.improvement_id) {
      errors.push('Improvement ID is required')
    }

    if (improvement.current_value < 0 || improvement.current_value > 1) {
      errors.push('Current value must be between 0 and 1')
    }

    if (improvement.predicted_value < 0 || improvement.predicted_value > 1) {
      errors.push('Predicted value must be between 0 and 1')
    }

    if (improvement.confidence < 0 || improvement.confidence > 1) {
      errors.push('Confidence must be between 0 and 1')
    }

    if (improvement.recommendations.length === 0) {
      errors.push('At least one recommendation is required')
    }

    return {
      valid: errors.length === 0,
      errors
    }
  },

  /**
   * Utility function to get improvement impact level
   */
  getImprovementImpact(improvement: PerformanceImprovement): { level: string; color: string; description: string } {
    const score = improvement.improvement_percentage * improvement.confidence

    if (score > 20) {
      return {
        level: 'high',
        color: 'text-red-600 bg-red-100',
        description: 'Significant improvement opportunity'
      }
    } else if (score > 10) {
      return {
        level: 'medium',
        color: 'text-orange-600 bg-orange-100',
        description: 'Moderate improvement opportunity'
      }
    } else if (score > 5) {
      return {
        level: 'low',
        color: 'text-yellow-600 bg-yellow-100',
        description: 'Minor improvement opportunity'
      }
    } else {
      return {
        level: 'minimal',
        color: 'text-green-600 bg-green-100',
        description: 'Minimal improvement opportunity'
      }
    }
  }
}
