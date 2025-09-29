import React from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  Activity,
  MapPin,
  Plane,
  AlertCircle,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { isConnected } = useWebSocket();

  // Fetch system overview data
  const { data: systemOverview, isLoading: overviewLoading } = useQuery(
    'system-overview',
    apiService.analytics.getSystemOverview,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch active missions
  const { data: missions, isLoading: missionsLoading } = useQuery(
    'missions',
    () => apiService.missions.getAll({ status_filter: 'active' }),
    {
      refetchInterval: 30000,
    }
  );

  // Fetch drones
  const { data: drones, isLoading: dronesLoading } = useQuery(
    'drones',
    () => apiService.drones.getAll({ status_filter: 'online' }),
    {
      refetchInterval: 30000,
    }
  );

  const StatCard = ({ title, value, icon: Icon, color = 'blue', trend }: any) => (
    <div className={`bg-white rounded-lg shadow p-6 border-l-4 border-${color}-500`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend && (
            <p className={`text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </p>
          )}
        </div>
        <Icon className={`h-8 w-8 text-${color}-500`} />
      </div>
    </div>
  );

  const MissionCard = ({ mission }: any) => (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{mission.name}</h3>
        <span className={`px-2 py-1 text-xs rounded-full ${
          mission.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
        }`}>
          {mission.status}
        </span>
      </div>
      <div className="space-y-1 text-sm text-gray-600">
        <div className="flex items-center">
          <MapPin className="h-4 w-4 mr-2" />
          {mission.center?.lat?.toFixed(4)}, {mission.center?.lng?.toFixed(4)}
        </div>
        <div className="flex items-center">
          <Clock className="h-4 w-4 mr-2" />
          {mission.progress_percentage?.toFixed(1)}% complete
        </div>
        <div className="flex items-center">
          <Plane className="h-4 w-4 mr-2" />
          {mission.assigned_drones?.length || 0} drones assigned
        </div>
      </div>
    </div>
  );

  const DroneCard = ({ drone }: any) => (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{drone.name}</h3>
        <span className={`px-2 py-1 text-xs rounded-full ${
          drone.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {drone.status}
        </span>
      </div>
      <div className="space-y-1 text-sm text-gray-600">
        <div className="flex items-center">
          <Activity className="h-4 w-4 mr-2" />
          Battery: {drone.battery_level?.toFixed(1)}%
        </div>
        <div className="flex items-center">
          <MapPin className="h-4 w-4 mr-2" />
          {drone.position?.lat?.toFixed(4)}, {drone.position?.lng?.toFixed(4)}
        </div>
        <div className="flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Speed: {drone.speed?.toFixed(1)} m/s
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isConnected ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Missions"
          value={systemOverview?.active_missions || 0}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Online Drones"
          value={systemOverview?.total_drones || 0}
          icon={Plane}
          color="blue"
        />
        <StatCard
          title="Total Discoveries"
          value={systemOverview?.total_discoveries || 0}
          icon={MapPin}
          color="purple"
        />
        <StatCard
          title="Success Rate"
          value={`${(systemOverview?.success_rate || 0) * 100}%`}
          icon={TrendingUp}
          color="orange"
        />
      </div>

      {/* Active Missions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Missions</h2>
        {missionsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {missions?.map((mission: any) => (
              <MissionCard key={mission.mission_id} mission={mission} />
            )) || []}
          </div>
        )}
      </div>

      {/* Online Drones */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Online Drones</h2>
        {dronesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {drones?.map((drone: any) => (
              <DroneCard key={drone.drone_id} drone={drone} />
            )) || []}
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-green-800">Backend API</p>
              <p className="text-xs text-green-600">Operational</p>
            </div>
            <CheckCircle className="h-6 w-6 text-green-500" />
          </div>
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-blue-800">WebSocket</p>
              <p className="text-xs text-blue-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </p>
            </div>
            {isConnected ? (
              <CheckCircle className="h-6 w-6 text-blue-500" />
            ) : (
              <XCircle className="h-6 w-6 text-red-500" />
            )}
          </div>
          <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-purple-800">Database</p>
              <p className="text-xs text-purple-600">Connected</p>
            </div>
            <CheckCircle className="h-6 w-6 text-purple-500" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;