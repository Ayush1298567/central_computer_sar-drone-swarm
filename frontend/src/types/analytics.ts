// Analytics Types
export interface MissionAnalytics {
  mission_id: string;
  mission_name: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  status: string;
  drone_count: number;
  waypoints_completed: number;
  total_waypoints: number;
  distance_covered: number;
  area_covered: number;
  weather_conditions: WeatherConditions[];
  performance_metrics: PerformanceMetrics;
  efficiency_score: number;
  cost_analysis: CostAnalysis;
  incidents: Incident[];
}

export interface DroneAnalytics {
  drone_id: string;
  drone_name: string;
  flight_time: number;
  missions_completed: number;
  missions_failed: number;
  average_battery_consumption: number;
  maintenance_events: number;
  sensor_accuracy: number;
  communication_uptime: number;
  performance_trends: PerformanceTrend[];
  utilization_rate: number;
  cost_per_hour: number;
}

export interface SystemAnalytics {
  total_missions: number;
  total_flight_time: number;
  total_distance_covered: number;
  active_drones: number;
  system_uptime: number;
  average_mission_duration: number;
  success_rate: number;
  cost_savings: number;
  efficiency_improvements: number;
  safety_incidents: number;
  environmental_impact: EnvironmentalImpact;
  resource_utilization: ResourceUtilization;
}

export interface PerformanceMetrics {
  average_speed: number;
  max_speed: number;
  average_altitude: number;
  max_altitude: number;
  fuel_efficiency: number;
  payload_capacity_utilization: number;
  communication_reliability: number;
  sensor_accuracy: number;
  response_time: number;
  error_rate: number;
}

export interface CostAnalysis {
  operational_cost: number;
  maintenance_cost: number;
  fuel_cost: number;
  equipment_cost: number;
  personnel_cost: number;
  total_cost: number;
  cost_per_mission: number;
  cost_per_kilometer: number;
  roi: number;
  savings_vs_traditional: number;
}

export interface Incident {
  id: string;
  type: IncidentType;
  severity: IncidentSeverity;
  description: string;
  timestamp: string;
  location?: {
    latitude: number;
    longitude: number;
  };
  drone_id?: string;
  mission_id?: string;
  root_cause?: string;
  resolution?: string;
  impact: string;
}

export interface WeatherConditions {
  timestamp: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  precipitation: number;
  visibility: number;
  conditions: string;
}

export interface PerformanceTrend {
  metric: string;
  trend: 'improving' | 'stable' | 'declining';
  change_percentage: number;
  timeframe: string;
  data_points: Array<{
    timestamp: string;
    value: number;
  }>;
}

export interface EnvironmentalImpact {
  carbon_footprint: number;
  fuel_consumption: number;
  noise_pollution: number;
  area_disturbed: number;
  wildlife_impact: number;
  sustainability_score: number;
}

export interface ResourceUtilization {
  drone_utilization: number;
  fuel_utilization: number;
  sensor_utilization: number;
  communication_utilization: number;
  storage_utilization: number;
  bandwidth_utilization: number;
}

export interface AnalyticsReport {
  id: string;
  title: string;
  type: ReportType;
  date_range: {
    start: string;
    end: string;
  };
  generated_at: string;
  generated_by: string;
  parameters: Record<string, any>;
  sections: ReportSection[];
  summary: ReportSummary;
  recommendations: string[];
  download_url?: string;
}

export interface ReportSection {
  id: string;
  title: string;
  type: SectionType;
  data: any;
  charts?: ChartConfig[];
  insights?: string[];
}

export interface ChartConfig {
  id: string;
  type: ChartType;
  title: string;
  data: any;
  options: Record<string, any>;
}

export interface ReportSummary {
  total_records: number;
  key_findings: string[];
  performance_score: number;
  trends: string[];
  anomalies: string[];
}

export interface AnalyticsFilters {
  date_range?: {
    start: string;
    end: string;
  };
  mission_types?: string[];
  drone_ids?: string[];
  locations?: Array<{
    latitude: number;
    longitude: number;
    radius?: number;
  }>;
  performance_thresholds?: {
    min_efficiency?: number;
    max_cost?: number;
    min_success_rate?: number;
  };
}

export interface ExportOptions {
  format: ExportFormat;
  include_charts: boolean;
  include_raw_data: boolean;
  sections?: string[];
  compression?: boolean;
  password?: string;
}

export type IncidentType =
  | 'mechanical_failure'
  | 'communication_loss'
  | 'battery_failure'
  | 'sensor_malfunction'
  | 'weather_related'
  | 'operator_error'
  | 'collision'
  | 'emergency_landing'
  | 'signal_interference'
  | 'software_error';

export type IncidentSeverity =
  | 'low'
  | 'medium'
  | 'high'
  | 'critical';

export type ReportType =
  | 'mission_performance'
  | 'drone_utilization'
  | 'system_overview'
  | 'cost_analysis'
  | 'safety_report'
  | 'environmental_impact'
  | 'custom';

export type SectionType =
  | 'summary'
  | 'metrics'
  | 'trends'
  | 'comparison'
  | 'breakdown'
  | 'insights'
  | 'recommendations';

export type ChartType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'doughnut'
  | 'scatter'
  | 'heatmap'
  | 'gauge'
  | 'map'
  | 'table';

export type ExportFormat =
  | 'pdf'
  | 'excel'
  | 'csv'
  | 'json'
  | 'xml';