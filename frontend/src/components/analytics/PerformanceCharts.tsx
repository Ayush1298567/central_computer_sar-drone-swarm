import React, { useState, useEffect } from 'react';
import { TrendingUp, BarChart3, PieChart, Activity } from 'lucide-react';
import { Mission } from '../../types';

interface PerformanceChartsProps {
  missions: Mission[];
  analyticsData: any;
  timeRange: string;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
  }[];
}

const PerformanceCharts: React.FC<PerformanceChartsProps> = ({
  missions,
  analyticsData,
  timeRange
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'missions' | 'efficiency' | 'timeline'>('overview');
  const [chartData, setChartData] = useState<ChartData | null>(null);

  useEffect(() => {
    generateChartData();
  }, [missions, analyticsData, timeRange, activeTab]);

  const completedMissions = missions.filter(m => m.status === 'completed');
  
  const generateChartData = () => {
    const last7Days = getLastNDaysData(7);
    const last30Days = getLastNDaysData(30);

    switch (activeTab) {
      case 'overview':
        setChartData({
          labels: ['Success Rate', 'Avg Duration', 'Coverage', 'Efficiency'],
          datasets: [{
            label: 'Performance Metrics',
            data: [
              (completedMissions.length / missions.length) * 100 || 0,
              analyticsData?.averageMissionDuration || 0,
              analyticsData?.averageCoverageEfficiency || 0,
              analyticsData?.discoveryRate * 100 || 0,
            ],
            backgroundColor: 'rgba(34, 197, 94, 0.8)',
            borderColor: 'rgb(34, 197, 94)',
            borderWidth: 1,
          }],
        });
        break;

      case 'missions':
        setChartData({
          labels: ['Planning', 'Active', 'Completed', 'Aborted'],
          datasets: [{
            label: 'Mission Status',
            data: [
              missions.filter(m => m.status === 'planning').length,
              missions.filter(m => m.status === 'active').length,
              missions.filter(m => m.status === 'completed').length,
              missions.filter(m => m.status === 'aborted').length,
            ],
            backgroundColor: 'rgba(59, 130, 246, 0.8)',
            borderColor: 'rgb(59, 130, 246)',
            borderWidth: 1,
          }],
        });
        break;

      case 'efficiency':
        setChartData({
          labels: last7Days.map(d => d.date),
          datasets: [{
            label: 'Coverage Efficiency (%)',
            data: last7Days.map(d => d.efficiency),
            backgroundColor: 'rgba(34, 197, 94, 0.8)',
            borderColor: 'rgb(34, 197, 94)',
            borderWidth: 2,
            fill: false,
          }],
        });
        break;

      case 'timeline':
        setChartData({
          labels: last30Days.map(d => d.date),
          datasets: [
            {
              label: 'Missions Completed',
              data: last30Days.map(d => d.missions),
              backgroundColor: 'rgba(59, 130, 246, 0.8)',
              borderColor: 'rgb(59, 130, 246)',
              borderWidth: 2,
            },
            {
              label: 'Average Duration (min)',
              data: last30Days.map(d => d.avgDuration),
              backgroundColor: 'rgba(168, 85, 247, 0.8)',
              borderColor: 'rgb(168, 85, 247)',
              borderWidth: 2,
            },
          ],
        });
        break;
    }
  };

  const getLastNDaysData = (days: number) => {
    const data = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];

      // Mock data for demonstration
      data.push({
        date: dateStr,
        missions: Math.floor(Math.random() * 5),
        efficiency: Math.random() * 100,
        avgDuration: Math.random() * 60 + 30,
      });
    }
    return data;
  };

  const renderChart = () => {
    if (!chartData) return null;

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="h-64 flex items-center justify-center">
          {/* Placeholder for actual chart library (Chart.js, Recharts, etc.) */}
          <div className="text-center">
            <div className="text-gray-400 mb-4">
              {activeTab === 'overview' && <BarChart3 className="h-16 w-16 mx-auto" />}
              {activeTab === 'missions' && <PieChart className="h-16 w-16 mx-auto" />}
              {activeTab === 'efficiency' && <TrendingUp className="h-16 w-16 mx-auto" />}
              {activeTab === 'timeline' && <Activity className="h-16 w-16 mx-auto" />}
            </div>
            <p className="text-gray-600">
              Chart visualization would be rendered here with a charting library like Chart.js or Recharts
            </p>
            <div className="mt-4 text-xs text-gray-500">
              Data: {JSON.stringify(chartData, null, 2)}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Performance Charts</h3>
        <div className="flex space-x-2">
          {[
            { key: 'overview', label: 'Overview', icon: BarChart3 },
            { key: 'missions', label: 'Missions', icon: PieChart },
            { key: 'efficiency', label: 'Efficiency', icon: TrendingUp },
            { key: 'timeline', label: 'Timeline', icon: Activity },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as typeof activeTab)}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {renderChart()}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {missions.filter(m => m.status === 'completed').length}
          </div>
          <div className="text-sm text-blue-700">Completed Missions</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {(completedMissions.length / missions.length * 100 || 0).toFixed(1)}%
          </div>
          <div className="text-sm text-green-700">Success Rate</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {analyticsData?.averageMissionDuration?.toFixed(0) || 0}m
          </div>
          <div className="text-sm text-purple-700">Avg Duration</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-orange-600">
            {analyticsData?.averageCoverageEfficiency?.toFixed(1) || 0}%
          </div>
          <div className="text-sm text-orange-700">Coverage Efficiency</div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceCharts;
