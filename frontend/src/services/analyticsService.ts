/**
 * Analytics API Service
 *
 * Handles all analytics and reporting API calls including:
 * - Mission performance analytics
 * - Historical data retrieval
 * - Report generation requests
 * - Performance metrics display
 * - Data visualization helpers and export functions
 */

import {
  MissionAnalytics,
  DroneAnalytics,
  SystemAnalytics,
  AnalyticsReport,
  AnalyticsFilters,
  ExportOptions,
  ReportType,
  ChartType,
  ApiResponse,
  PaginationParams,
  PaginatedResponse,
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = 15000; // 15 seconds for analytics requests

// Error handling utility
class AnalyticsServiceError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'AnalyticsServiceError';
  }
}

// Retry configuration
const RETRY_CONFIG = {
  maxAttempts: 3,
  delayMs: 2000,
  backoffMultiplier: 2,
};

// Data visualization helpers
export class DataVisualizationHelper {
  /**
   * Format data for chart rendering
   */
  static formatChartData(
    data: any[],
    chartType: ChartType,
    xAxisKey: string,
    yAxisKey: string | string[],
    options: Record<string, any> = {}
  ): any {
    switch (chartType) {
      case 'line':
      case 'bar':
        return {
          labels: data.map(item => item[xAxisKey]),
          datasets: Array.isArray(yAxisKey)
            ? yAxisKey.map((key, index) => ({
                label: options.labels?.[index] || key,
                data: data.map(item => item[key]),
                backgroundColor: options.colors?.[index] || this.getDefaultColor(index),
                borderColor: options.colors?.[index] || this.getDefaultColor(index),
                ...options.datasetOptions?.[index],
              }))
            : [{
                label: options.label || yAxisKey,
                data: data.map(item => item[yAxisKey]),
                backgroundColor: options.color || this.getDefaultColor(0),
                borderColor: options.color || this.getDefaultColor(0),
                ...options.datasetOptions,
              }],
        };

      case 'pie':
      case 'doughnut':
        return {
          labels: data.map(item => item[xAxisKey]),
          datasets: [{
            data: data.map(item => item[yAxisKey]),
            backgroundColor: options.colors || this.generateColors(data.length),
            ...options.datasetOptions,
          }],
        };

      case 'scatter':
        return {
          datasets: [{
            label: options.label || 'Scatter Plot',
            data: data.map(item => ({
              x: item[xAxisKey],
              y: item[yAxisKey],
            })),
            backgroundColor: options.color || this.getDefaultColor(0),
            ...options.datasetOptions,
          }],
        };

      default:
        return data;
    }
  }

  /**
   * Generate color palette
   */
  static generateColors(count: number): string[] {
    const colors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
      '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
    ];
    return Array.from({ length: count }, (_, i) => colors[i % colors.length]);
  }

  /**
   * Get default color for index
   */
  private static getDefaultColor(index: number): string {
    const colors = this.generateColors(10);
    return colors[index % colors.length];
  }

  /**
   * Format number with appropriate units
   */
  static formatNumber(value: number, unit?: string): string {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M${unit ? ` ${unit}` : ''}`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K${unit ? ` ${unit}` : ''}`;
    }
    return `${value.toFixed(1)}${unit ? ` ${unit}` : ''}`;
  }

  /**
   * Format duration in human readable format
   */
  static formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  }

  /**
   * Calculate percentage change
   */
  static calculatePercentageChange(current: number, previous: number): number {
    if (previous === 0) return current === 0 ? 0 : 100;
    return ((current - previous) / previous) * 100;
  }

  /**
   * Format percentage with appropriate sign
   */
  static formatPercentage(value: number, showSign = true): string {
    const formatted = Math.abs(value).toFixed(1);
    const sign = value >= 0 ? (showSign ? '+' : '') : '-';
    return `${sign}${formatted}%`;
  }
}

// Generic API request wrapper with error handling and retry logic
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(url, {
      ...config,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new AnalyticsServiceError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code
      );
    }

    const data: ApiResponse<T> = await response.json();

    if (!data.success) {
      throw new AnalyticsServiceError(data.error || 'API request failed');
    }

    return data.data as T;
  } catch (error) {
    if (error instanceof AnalyticsServiceError) {
      throw error;
    }

    // Handle network errors and retries
    if (retryCount < RETRY_CONFIG.maxAttempts) {
      const delay = RETRY_CONFIG.delayMs * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount);
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiRequest<T>(endpoint, options, retryCount + 1);
    }

    // Final error after all retries
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new AnalyticsServiceError('Request timeout');
      }
      throw new AnalyticsServiceError(error.message);
    }

    throw new AnalyticsServiceError('Unknown error occurred');
  }
}

// Analytics API Service Class
export class AnalyticsService {
  /**
   * Get mission performance analytics
   */
  static async getMissionAnalytics(
    missionId?: string,
    filters?: AnalyticsFilters
  ): Promise<MissionAnalytics | MissionAnalytics[]> {
    const params = new URLSearchParams();

    if (missionId) {
      params.append('mission_id', missionId);
    }

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
      if (filters.mission_types) {
        filters.mission_types.forEach(type => params.append('mission_type', type));
      }
      if (filters.drone_ids) {
        filters.drone_ids.forEach(id => params.append('drone_id', id));
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/missions${queryString ? `?${queryString}` : ''}`;

    return apiRequest<MissionAnalytics | MissionAnalytics[]>(endpoint);
  }

  /**
   * Get drone utilization analytics
   */
  static async getDroneAnalytics(
    droneId?: string,
    filters?: AnalyticsFilters
  ): Promise<DroneAnalytics | DroneAnalytics[]> {
    const params = new URLSearchParams();

    if (droneId) {
      params.append('drone_id', droneId);
    }

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/drones${queryString ? `?${queryString}` : ''}`;

    return apiRequest<DroneAnalytics | DroneAnalytics[]>(endpoint);
  }

  /**
   * Get system-wide analytics
   */
  static async getSystemAnalytics(filters?: AnalyticsFilters): Promise<SystemAnalytics> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/system${queryString ? `?${queryString}` : ''}`;

    return apiRequest<SystemAnalytics>(endpoint);
  }

  /**
   * Get performance trends over time
   */
  static async getPerformanceTrends(
    metric: string,
    timeframe: 'hour' | 'day' | 'week' | 'month' = 'day',
    filters?: AnalyticsFilters
  ): Promise<Array<{
    timestamp: string;
    value: number;
    trend: 'up' | 'down' | 'stable';
  }>> {
    const params = new URLSearchParams();
    params.append('metric', metric);
    params.append('timeframe', timeframe);

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/trends${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Get incident reports and analysis
   */
  static async getIncidentAnalysis(
    filters?: AnalyticsFilters
  ): Promise<{
    total_incidents: number;
    incidents_by_type: Record<string, number>;
    incidents_by_severity: Record<string, number>;
    average_resolution_time: number;
    recurring_issues: string[];
    prevention_recommendations: string[];
    recent_incidents: Array<{
      id: string;
      type: string;
      severity: string;
      description: string;
      timestamp: string;
      status: 'open' | 'investigating' | 'resolved';
    }>;
  }> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/incidents${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Generate analytics report
   */
  static async generateReport(
    reportType: ReportType,
    filters?: AnalyticsFilters,
    options?: {
      includeCharts?: boolean;
      includeRecommendations?: boolean;
      format?: 'json' | 'pdf' | 'html';
    }
  ): Promise<AnalyticsReport> {
    const payload = {
      report_type: reportType,
      filters,
      options,
    };

    return apiRequest<AnalyticsReport>('/analytics/reports', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Get existing reports
   */
  static async getReports(
    filters?: {
      report_type?: ReportType;
      generated_after?: string;
      generated_by?: string;
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<AnalyticsReport>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/analytics/reports${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<AnalyticsReport>>(endpoint);
  }

  /**
   * Get specific report by ID
   */
  static async getReport(reportId: string): Promise<AnalyticsReport> {
    return apiRequest<AnalyticsReport>(`/analytics/reports/${reportId}`);
  }

  /**
   * Export report in specified format
   */
  static async exportReport(
    reportId: string,
    exportOptions: ExportOptions
  ): Promise<Blob> {
    const params = new URLSearchParams();
    Object.entries(exportOptions).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    const queryString = params.toString();
    const endpoint = `/analytics/reports/${reportId}/export${queryString ? `?${queryString}` : ''}`;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new AnalyticsServiceError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code
      );
    }

    return response.blob();
  }

  /**
   * Get real-time analytics dashboard data
   */
  static async getDashboardData(): Promise<{
    active_missions: number;
    total_drones: number;
    system_health: number;
    recent_incidents: number;
    performance_score: number;
    cost_savings: number;
    upcoming_maintenance: number;
    alerts: Array<{
      id: string;
      type: 'warning' | 'error' | 'info';
      message: string;
      timestamp: string;
    }>;
  }> {
    return apiRequest('/analytics/dashboard');
  }

  /**
   * Get predictive analytics
   */
  static async getPredictiveAnalytics(
    metric: string,
    days: number = 30
  ): Promise<{
    metric: string;
    predictions: Array<{
      date: string;
      predicted_value: number;
      confidence: number;
      trend: 'increasing' | 'decreasing' | 'stable';
    }>;
    recommendations: string[];
  }> {
    const params = new URLSearchParams();
    params.append('metric', metric);
    params.append('days', days.toString());

    const queryString = params.toString();
    const endpoint = `/analytics/predictive${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }

  /**
   * Get comparative analytics between time periods
   */
  static async getComparativeAnalytics(
    currentPeriod: { start: string; end: string },
    previousPeriod: { start: string; end: string },
    metrics: string[]
  ): Promise<{
    metrics: Record<string, {
      current_value: number;
      previous_value: number;
      change_percentage: number;
      trend: 'improving' | 'declining' | 'stable';
    }>;
    insights: string[];
  }> {
    const payload = {
      current_period: currentPeriod,
      previous_period: previousPeriod,
      metrics,
    };

    return apiRequest('/analytics/comparative', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Get cost-benefit analysis
   */
  static async getCostBenefitAnalysis(
    filters?: AnalyticsFilters
  ): Promise<{
    total_investment: number;
    operational_costs: number;
    benefits: {
      time_saved: number;
      accuracy_improvement: number;
      safety_improvement: number;
      environmental_benefit: number;
    };
    roi: number;
    payback_period: number;
    break_even_analysis: Array<{
      month: number;
      cumulative_cost: number;
      cumulative_benefit: number;
    }>;
    recommendations: string[];
  }> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.date_range) {
        params.append('start_date', filters.date_range.start);
        params.append('end_date', filters.date_range.end);
      }
    }

    const queryString = params.toString();
    const endpoint = `/analytics/cost-benefit${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }
}

// Export error class and helper for consumers
export { AnalyticsServiceError, DataVisualizationHelper };