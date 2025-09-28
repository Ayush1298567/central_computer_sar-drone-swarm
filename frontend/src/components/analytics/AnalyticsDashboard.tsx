import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Target, Activity, Award, Download, RefreshCw } from 'lucide-react';
import { Mission, Drone } from '../../types';
import { apiService } from '../../utils/api';
import PerformanceCharts from './PerformanceCharts';

interface AnalyticsData {
  totalMissions: number;
  successfulMissions: number;
  totalFlightTime: number;
  totalCoverageArea: number;
  averageMissionDuration: number;
  averageCoverageEfficiency: number;
  discoveryRate: number;
  droneUtilization: number;
  systemUptime: number;
  recentTrends: {
    missionsCompleted: number;
    averageDuration: number;
    coverageEfficiency: number;
    discoveryRate: number;
  };
}

interface AnalyticsDashboardProps {
  missions: Mission[];
  drones: Drone[];
  onGenerateReport?: (missionId: string, reportType: string) => void;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  missions,
  drones,
  onGenerateReport
}) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadAnalyticsData();
    const interval = setInterval(loadAnalyticsData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [selectedTimeRange]);

  const loadAnalyticsData = async () => {
    setIsLoading(true);
    try {
      const [performanceData, missionAnalytics] = await Promise.all([
        apiService.getPerformanceMetrics(),
        // For now, we'll calculate some basic analytics from the provided data
        Promise.resolve(calculateAnalyticsFromData())
      ]);

      setAnalyticsData({
        ...performanceData,
        ...missionAnalytics
      });
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      // Fallback to calculated data
      setAnalyticsData(calculateAnalyticsFromData());
    } finally {
      setIsLoading(false);
    }
  };

  const calculateAnalyticsFromData = (): Partial<AnalyticsData> => {
    const completedMissions = missions.filter(m => m.status === 'completed');
    const activeMissions = missions.filter(m => m.status === 'active');

    const totalFlightTime = completedMissions.reduce((sum, m) => sum + (m.actual_duration || m.estimated_duration || 0), 0);
    const totalCoverageArea = completedMissions.reduce((sum, m) => sum + (m.coverage_percentage || 0), 0);

    return {
      totalMissions: missions.length,
      successfulMissions: completedMissions.length,
      totalFlightTime,
      totalCoverageArea,
      averageMissionDuration: completedMissions.length > 0 ? totalFlightTime / completedMissions.length : 0,
      averageCoverageEfficiency: completedMissions.length > 0 ? totalCoverageArea / completedMissions.length : 0,
      discoveryRate: 0.85, // Mock data
      droneUtilization: drones.filter(d => d.status === 'online' || d.status === 'flying').length / drones.length,
      systemUptime: 99.5, // Mock data
      recentTrends: {
        missionsCompleted: completedMissions.length,
        averageDuration: completedMissions.length > 0 ? totalFlightTime / completedMissions.length : 0,
        coverageEfficiency: completedMissions.length > 0 ? totalCoverageArea / completedMissions.length : 0,
        discoveryRate: 0.85,
      }
    };
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatArea = (percentage: number) => {
    return `${percentage.toFixed(1)}%`;
  };

  const getSuccessRate = () => {
    if (!analyticsData) return 0;
    return (analyticsData.successfulMissions / analyticsData.totalMissions) * 100;
  };

  const getEfficiencyColor = (value: number, thresholds: { good: number; average: number }) => {
    if (value >= thresholds.good) return 'text-green-600';
    if (value >= thresholds.average) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading && !analyticsData) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading analytics...</span>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No analytics data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <BarChart3 className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">Mission Analytics Dashboard</h2>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as typeof selectedTimeRange)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
          <button
            onClick={loadAnalyticsData}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-500">
            Updated: {lastUpdated.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center">
            <Target className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-blue-600">Total Missions</p>
              <p className="text-2xl font-bold text-blue-900">{analyticsData.totalMissions}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <Award className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-green-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-900">{getSuccessRate().toFixed(1)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-purple-600">Avg. Duration</p>
              <p className="text-2xl font-bold text-purple-900">
                {formatDuration(analyticsData.averageMissionDuration)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-orange-600">Coverage Efficiency</p>
              <p className="text-2xl font-bold text-orange-900">
                {formatArea(analyticsData.averageCoverageEfficiency)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Charts */}
      <div className="mb-8">
        <PerformanceCharts
          missions={missions}
          analyticsData={analyticsData}
          timeRange={selectedTimeRange}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Flight Performance */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Flight Performance</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Total Flight Time</span>
              <span className="text-lg font-bold text-gray-900">
                {formatDuration(analyticsData.totalFlightTime)}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Drone Utilization</span>
              <span className={`text-lg font-bold ${getEfficiencyColor(analyticsData.droneUtilization * 100, { good: 80, average: 60 })}`}>
                {(analyticsData.droneUtilization * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">System Uptime</span>
              <span className={`text-lg font-bold ${getEfficiencyColor(analyticsData.systemUptime, { good: 99, average: 95 })}`}>
                {analyticsData.systemUptime.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Mission Trends */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Trends</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Missions Completed</span>
              <span className="text-lg font-bold text-gray-900">
                {analyticsData.recentTrends.missionsCompleted}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Avg. Duration</span>
              <span className="text-lg font-bold text-gray-900">
                {formatDuration(analyticsData.recentTrends.averageDuration)}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Coverage Efficiency</span>
              <span className="text-lg font-bold text-gray-900">
                {formatArea(analyticsData.recentTrends.coverageEfficiency)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Generate Reports</h3>
            <p className="text-sm text-gray-600">
              Create detailed reports for missions, performance analysis, or system status.
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => onGenerateReport?.('', 'summary')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium flex items-center"
            >
              <Download className="h-4 w-4 mr-2" />
              Generate Summary Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;