import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Activity, 
  MapPin, 
  Radio, 
  Search, 
  AlertTriangle, 
  Battery, 
  Clock,
  TrendingUp,
  Plus,
  Eye,
  Play,
  Pause,
  Users,
  Zap,
  CheckCircle,
  // XCircle
} from 'lucide-react';
import { apiService } from '../services/api';
import { MissionStatus, MissionPriority } from '../types/mission';
import { DroneStatus } from '../types/drone';

const Dashboard: React.FC = () => {
  // Fetch missions data
  const { data: missionsData, isLoading: missionsLoading } = useQuery({
    queryKey: ['missions', { page: 1, per_page: 5 }],
    queryFn: () => apiService.getMissions({ page: 1, per_page: 5 }),
  });

  // Fetch drones data
  const { data: dronesData, isLoading: dronesLoading } = useQuery({
    queryKey: ['drones', { page: 1, per_page: 10 }],
    queryFn: () => apiService.getDrones({ page: 1, per_page: 10 }),
  });

  // Fetch system status
  const { data: _systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiService.getSystemStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const missions = missionsData?.data?.items || [];
  const drones = dronesData?.data?.items || [];

  // Calculate statistics
  const activeMissions = missions.filter(m => m.status === MissionStatus.ACTIVE).length;
  const connectedDrones = drones.filter(d => d.status !== DroneStatus.OFFLINE).length;
  const totalDiscoveries = missions.reduce((acc, mission) => acc + (mission.discoveries?.length || 0), 0);

  const getStatusColor = (status: MissionStatus) => {
    const colors = {
      [MissionStatus.ACTIVE]: 'text-green-700 bg-green-100',
      [MissionStatus.PAUSED]: 'text-yellow-700 bg-yellow-100',
      [MissionStatus.COMPLETED]: 'text-blue-700 bg-blue-100',
      [MissionStatus.ABORTED]: 'text-red-700 bg-red-100',
      [MissionStatus.FAILED]: 'text-red-700 bg-red-100',
      [MissionStatus.PLANNING]: 'text-purple-700 bg-purple-100',
      [MissionStatus.READY]: 'text-gray-700 bg-gray-100',
    };
    return colors[status] || colors[MissionStatus.PLANNING];
  };

  const getPriorityColor = (priority: MissionPriority) => {
    const colors = {
      [MissionPriority.LOW]: 'text-green-600',
      [MissionPriority.MEDIUM]: 'text-yellow-600',
      [MissionPriority.HIGH]: 'text-orange-600',
      [MissionPriority.CRITICAL]: 'text-red-600',
    };
    return colors[priority] || colors[MissionPriority.MEDIUM];
  };

  const getDroneStatusColor = (status: DroneStatus) => {
    const colors = {
      [DroneStatus.ACTIVE]: 'text-green-600',
      [DroneStatus.IDLE]: 'text-blue-600',
      [DroneStatus.CHARGING]: 'text-yellow-600',
      [DroneStatus.MAINTENANCE]: 'text-orange-600',
      [DroneStatus.ERROR]: 'text-red-600',
      [DroneStatus.OFFLINE]: 'text-gray-600',
      [DroneStatus.RETURNING]: 'text-purple-600',
      [DroneStatus.LANDING]: 'text-indigo-600',
      [DroneStatus.EMERGENCY]: 'text-red-600',
    };
    return colors[status] || colors[DroneStatus.OFFLINE];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mission Command Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your search and rescue operations</p>
        </div>
        <Link
          to="/mission-planning"
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Mission</span>
        </Link>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Missions</p>
              <p className="text-2xl font-bold text-gray-900">{activeMissions}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Radio className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            <span className="text-green-600">2 started today</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Connected Drones</p>
              <p className="text-2xl font-bold text-gray-900">{connectedDrones}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm">
            <span className="text-gray-600">{drones.length} total drones</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Discoveries</p>
              <p className="text-2xl font-bold text-gray-900">{totalDiscoveries}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Search className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm">
            <span className="text-gray-600">Across all missions</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-green-600">Healthy</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm">
            <span className="text-green-600">All systems operational</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Missions */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Missions</h3>
            <Link to="/missions" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
          
          {missionsLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : missions.length > 0 ? (
            <div className="space-y-3">
              {missions.map((mission) => (
                <div key={mission.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="font-medium text-gray-900">{mission.name}</h4>
                      <span className={`status-badge ${getStatusColor(mission.status)}`}>
                        {mission.status}
                      </span>
                      <span className={`text-sm font-medium ${getPriorityColor(mission.priority)}`}>
                        {mission.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{mission.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span className="flex items-center">
                        <MapPin className="w-3 h-3 mr-1" />
                        {mission.search_area?.area_km2?.toFixed(1)} km²
                      </span>
                      <span className="flex items-center">
                        <Users className="w-3 h-3 mr-1" />
                        {mission.assigned_drones?.length || 0} drones
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {new Date(mission.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {mission.status === MissionStatus.ACTIVE && (
                      <Link
                        to={`/mission/${mission.id}`}
                        className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        title="View Live Mission"
                      >
                        <Eye className="w-4 h-4" />
                      </Link>
                    )}
                    {mission.status === MissionStatus.PAUSED && (
                      <button
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Resume Mission"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    {mission.status === MissionStatus.ACTIVE && (
                      <button
                        className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                        title="Pause Mission"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Radio className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 mb-2">No missions yet</p>
              <Link to="/mission-planning" className="btn-primary">
                Create First Mission
              </Link>
            </div>
          )}
        </div>

        {/* Drone Fleet Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Drone Fleet</h3>
            <Link to="/drone-fleet" className="text-sm text-primary-600 hover:text-primary-700">
              Manage
            </Link>
          </div>
          
          {dronesLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                </div>
              ))}
            </div>
          ) : drones.length > 0 ? (
            <div className="space-y-3">
              {drones.slice(0, 5).map((drone) => (
                <div key={drone.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{drone.name}</h4>
                      <span className={`text-xs font-medium ${getDroneStatusColor(drone.status)}`}>
                        {drone.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{drone.model}</p>
                    <div className="flex items-center space-x-3 mt-2">
                      <div className="flex items-center space-x-1">
                        <Battery className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{drone.battery_level}%</span>
                      </div>
                      {drone.current_mission_id && (
                        <div className="flex items-center space-x-1">
                          <Radio className="w-3 h-3 text-green-500" />
                          <span className="text-xs text-green-600">On Mission</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center">
                    {drone.status === DroneStatus.ERROR || drone.status === DroneStatus.EMERGENCY ? (
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                    ) : drone.status === DroneStatus.ACTIVE ? (
                      <Activity className="w-5 h-5 text-green-500" />
                    ) : (
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    )}
                  </div>
                </div>
              ))}
              {drones.length > 5 && (
                <div className="text-center pt-2">
                  <Link to="/drone-fleet" className="text-sm text-primary-600 hover:text-primary-700">
                    View {drones.length - 5} more drones
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 mb-2">No drones connected</p>
              <button className="btn-secondary">
                Discover Drones
              </button>
            </div>
          )}
        </div>
      </div>

      {/* System Health & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Service</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600">Online</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600">Connected</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">WebSocket</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600">Active</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">AI Service</span>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-green-600">Ready</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-2 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800">Weather Warning</p>
                <p className="text-xs text-yellow-700">High winds expected in sector 3</p>
                <p className="text-xs text-yellow-600 mt-1">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3 p-2 bg-blue-50 rounded-lg">
              <Zap className="w-4 h-4 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-800">System Update</p>
                <p className="text-xs text-blue-700">Drone firmware updated successfully</p>
                <p className="text-xs text-blue-600 mt-1">15 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3 p-2 bg-green-50 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">Mission Complete</p>
                <p className="text-xs text-green-700">Search mission Alpha-7 completed</p>
                <p className="text-xs text-green-600 mt-1">1 hour ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;