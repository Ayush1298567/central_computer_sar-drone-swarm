// Analytics API Service
// Handles analytics data retrieval, report generation, and data visualization helpers

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

// TypeScript interfaces for analytics requests/responses
export interface MissionAnalytics {
  total_missions: number;
  active_missions: number;
  completed_missions: number;
  success_rate: number;
  average_duration: number;
  total_area_covered: number;
  efficiency_trends: {
    date: string;
    efficiency: number;
    missions_completed: number;
  }[];
  performance_by_pattern: {
    pattern: string;
    average_efficiency: number;
    total_missions: number;
  }[];
  drone_utilization: {
    drone_id: string;
    drone_name: string;
    missions_completed: number;
    total_flight_time: number;
    efficiency_score: number;
  }[];
}

export interface DroneAnalytics {
  fleet_overview: {
    total_drones: number;
    online_drones: number;
    busy_drones: number;
    maintenance_drones: number;
    error_drones: number;
    average_battery_level: number;
    fleet_efficiency: number;
  };
  performance_metrics: {
    average_flight_time: number;
    average_battery_consumption: number;
    average_speed: number;
    average_altitude: number;
    signal_strength_average: number;
  };
  maintenance_schedule: {
    drone_id: string;
    next_maintenance: string;
    maintenance_type: string;
    estimated_duration: number;
  }[];
  battery_health: {
    drone_id: string;
    current_level: number;
    health_score: number;
    cycles_remaining: number;
    last_charged: string;
  }[];
}

export interface SystemAnalytics {
  uptime_percentage: number;
  total_requests: number;
  average_response_time: number;
  error_rate: number;
  resource_usage: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_bandwidth: number;
  };
  api_endpoints_performance: {
    endpoint: string;
    total_requests: number;
    average_response_time: number;
    error_rate: number;
  }[];
}

export interface ReportConfig {
  title: string;
  type: 'mission_summary' | 'drone_performance' | 'system_health' | 'custom';
  date_range: {
    start: string;
    end: string;
  };
  filters: Record<string, any>;
  format: 'pdf' | 'excel' | 'json';
  include_charts: boolean;
  recipients?: string[];
}

export interface AnalyticsDataPoint {
  timestamp: string;
  value: number;
  category?: string;
  metadata?: Record<string, any>;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    fill?: boolean;
  }[];
}

export interface HeatmapData {
  x: string[];
  y: string[];
  z: number[][];
}

// Data visualization helpers
class DataVisualizationHelpers {
  // Convert analytics data to Chart.js format
  static convertToChartData(data: AnalyticsDataPoint[], label: string, color = '#3B82F6'): ChartData {
    const labels = data.map(point => new Date(point.timestamp).toLocaleDateString());
    const values = data.map(point => point.value);

    return {
      labels,
      datasets: [{
        label,
        data: values,
        borderColor: color,
        backgroundColor: color + '20',
        fill: true,
      }]
    };
  }

  // Create pie chart data
  static createPieChartData(data: { label: string; value: number; color?: string }[]): ChartData {
    const labels = data.map(item => item.label);
    const values = data.map(item => item.value);
    const colors = data.map(item => item.color || this.getRandomColor());

    return {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 2,
      }]
    };
  }

  // Create heatmap data
  static createHeatmapData(
    xLabels: string[],
    yLabels: string[],
    values: number[][]
  ): HeatmapData {
    return {
      x: xLabels,
      y: yLabels,
      z: values
    };
  }

  // Calculate trend analysis
  static calculateTrend(data: number[]): 'increasing' | 'decreasing' | 'stable' {
    if (data.length < 3) return 'stable';

    const firstHalf = data.slice(0, Math.floor(data.length / 2));
    const secondHalf = data.slice(Math.floor(data.length / 2));

    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;

    const change = (secondAvg - firstAvg) / firstAvg;

    if (Math.abs(change) < 0.05) return 'stable';
    return change > 0 ? 'increasing' : 'decreasing';
  }

  // Format duration for display
  static formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  // Format file size for display
  static formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  // Get random color for charts
  private static getRandomColor(): string {
    const colors = [
      '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
      '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  // Calculate percentage change
  static calculatePercentageChange(current: number, previous: number): number {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  }

  // Format percentage for display
  static formatPercentage(value: number, decimals = 1): string {
    return `${value.toFixed(decimals)}%`;
  }

  // Create time series data for the last N days
  static getLastNDaysData(days: number, baseValue: number, variance = 0.2): AnalyticsDataPoint[] {
    const data: AnalyticsDataPoint[] = [];
    const now = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      const randomVariance = (Math.random() - 0.5) * 2 * variance;
      const value = baseValue * (1 + randomVariance);

      data.push({
        timestamp: date.toISOString(),
        value: Math.round(value * 100) / 100,
      });
    }

    return data;
  }

  // Export data to CSV
  static exportToCSV(data: Record<string, any>[], filename: string): void {
    if (data.length === 0) return;

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row =>
        headers.map(header => {
          const value = row[header];
          // Escape commas and quotes in values
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Export data to JSON
  static exportToJSON(data: any, filename: string): void {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

// API service class with error handling and retry logic
export class AnalyticsService {
  private queryClient: ReturnType<typeof useQueryClient>;

  constructor() {
    // Query client will be injected when using hooks
  }

  setQueryClient(client: ReturnType<typeof useQueryClient>) {
    this.queryClient = client;
  }

  // Get mission analytics
  static async getMissionAnalytics(timeRange = '30d'): Promise<MissionAnalytics> {
    try {
      const response = await fetch(`${api.baseUrl}/analytics/missions?timeRange=${timeRange}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch mission analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching mission analytics:', error);
      throw error;
    }
  }

  // Get drone analytics
  static async getDroneAnalytics(timeRange = '30d'): Promise<DroneAnalytics> {
    try {
      const response = await fetch(`${api.baseUrl}/analytics/drones?timeRange=${timeRange}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch drone analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching drone analytics:', error);
      throw error;
    }
  }

  // Get system analytics
  static async getSystemAnalytics(timeRange = '24h'): Promise<SystemAnalytics> {
    try {
      const response = await fetch(`${api.baseUrl}/analytics/system?timeRange=${timeRange}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch system analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching system analytics:', error);
      throw error;
    }
  }

  // Generate custom report
  static async generateReport(config: ReportConfig): Promise<{ report_id: string; download_url: string }> {
    try {
      const response = await fetch(`${api.baseUrl}/analytics/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate report: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error generating report:', error);
      throw error;
    }
  }

  // Get historical data
  static async getHistoricalData(
    metric: string,
    startDate: string,
    endDate: string,
    granularity: 'hour' | 'day' | 'week' = 'day'
  ): Promise<AnalyticsDataPoint[]> {
    try {
      const params = new URLSearchParams({
        metric,
        startDate,
        endDate,
        granularity,
      });

      const response = await fetch(`${api.baseUrl}/analytics/historical?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch historical data: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  }

  // Get real-time metrics
  static async getRealTimeMetrics(): Promise<{
    active_missions: number;
    online_drones: number;
    system_load: number;
    network_traffic: number;
    last_updated: string;
  }> {
    try {
      const response = await fetch(`${api.baseUrl}/analytics/realtime`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch real-time metrics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching real-time metrics:', error);
      throw error;
    }
  }

  // Get performance comparison
  static async getPerformanceComparison(
    metric: string,
    compareWith: string[],
    timeRange: string
  ): Promise<{
    metric: string;
    comparisons: {
      label: string;
      value: number;
      change_percentage: number;
    }[];
  }> {
    try {
      const params = new URLSearchParams({
        metric,
        compareWith: compareWith.join(','),
        timeRange,
      });

      const response = await fetch(`${api.baseUrl}/analytics/comparison?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch performance comparison: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching performance comparison:', error);
      throw error;
    }
  }

  // Export analytics data
  static async exportAnalytics(
    type: 'mission' | 'drone' | 'system',
    format: 'csv' | 'json' | 'pdf',
    timeRange: string,
    filters?: Record<string, any>
  ): Promise<{ download_url: string; expires_at: string }> {
    try {
      const params = new URLSearchParams({
        type,
        format,
        timeRange,
        ...(filters && { filters: JSON.stringify(filters) }),
      });

      const response = await fetch(`${api.baseUrl}/analytics/export?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to export analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error exporting analytics:', error);
      throw error;
    }
  }
}

// Export singleton instances and helpers
export const analyticsService = new AnalyticsService();
export const visualizationHelpers = DataVisualizationHelpers;

// React Query hooks
export const useMissionAnalytics = (timeRange = '30d') => {
  return useQuery({
    queryKey: ['missionAnalytics', timeRange],
    queryFn: () => analyticsService.getMissionAnalytics(timeRange),
    staleTime: 300000, // 5 minutes
    retry: 3,
  });
};

export const useDroneAnalytics = (timeRange = '30d') => {
  return useQuery({
    queryKey: ['droneAnalytics', timeRange],
    queryFn: () => analyticsService.getDroneAnalytics(timeRange),
    staleTime: 300000, // 5 minutes
    retry: 3,
  });
};

export const useSystemAnalytics = (timeRange = '24h') => {
  return useQuery({
    queryKey: ['systemAnalytics', timeRange],
    queryFn: () => analyticsService.getSystemAnalytics(timeRange),
    staleTime: 60000, // 1 minute
    retry: 3,
  });
};

export const useGenerateReport = () => {
  return useMutation({
    mutationFn: analyticsService.generateReport,
    retry: 2,
  });
};

export const useHistoricalData = (
  metric: string,
  startDate: string,
  endDate: string,
  granularity: 'hour' | 'day' | 'week' = 'day'
) => {
  return useQuery({
    queryKey: ['historicalData', metric, startDate, endDate, granularity],
    queryFn: () => analyticsService.getHistoricalData(metric, startDate, endDate, granularity),
    enabled: !!(metric && startDate && endDate),
    staleTime: 300000, // 5 minutes
    retry: 3,
  });
};

export const useRealTimeMetrics = () => {
  return useQuery({
    queryKey: ['realTimeMetrics'],
    queryFn: analyticsService.getRealTimeMetrics,
    refetchInterval: 30000, // Poll every 30 seconds
    retry: 3,
  });
};

export const usePerformanceComparison = (
  metric: string,
  compareWith: string[],
  timeRange: string
) => {
  return useQuery({
    queryKey: ['performanceComparison', metric, compareWith, timeRange],
    queryFn: () => analyticsService.getPerformanceComparison(metric, compareWith, timeRange),
    enabled: !!(metric && compareWith.length > 0 && timeRange),
    staleTime: 300000, // 5 minutes
    retry: 3,
  });
};

export const useExportAnalytics = () => {
  return useMutation({
    mutationFn: ({
      type,
      format,
      timeRange,
      filters
    }: {
      type: 'mission' | 'drone' | 'system';
      format: 'csv' | 'json' | 'pdf';
      timeRange: string;
      filters?: Record<string, any>;
    }) => analyticsService.exportAnalytics(type, format, timeRange, filters),
    retry: 2,
  });
};