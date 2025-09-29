import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Activity,
  Plane,
  Search,
  Clock,
  AlertTriangle,
  TrendingUp,
  Plus,
  Play,
  MapPin
} from 'lucide-react';
import { api } from '../utils/api';
import { Mission, Drone, Discovery } from '../types/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

const Dashboard: React.FC = () => {
  // Fetch data
  const { data: missions, isLoading: missionsLoading } = useQuery('missions', () =>
    api.missions.getAll({ limit: 5 })
  );

  const { data: drones, isLoading: dronesLoading } = useQuery('drones', () =>
    api.drones.getAll({ limit: 10 })
  );

  const { data: discoveries, isLoading: discoveriesLoading } = useQuery('discoveries', () =>
    api.discoveries.getAll({ limit: 10 })
  );

  const activeMissions = missions?.filter(m => m.status === 'active') || [];
  const availableDrones = drones?.filter(d => d.status === 'available') || [];
  const pendingDiscoveries = discoveries?.filter(d => d.status === 'new' || d.status === 'investigating') || [];

  const stats = [
    {
      name: 'Active Missions',
      value: activeMissions.length,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      change: '+2 from yesterday',
    },
    {
      name: 'Available Drones',
      value: availableDrones.length,
      icon: Plane,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      change: '3 ready for deployment',
    },
    {
      name: 'Pending Discoveries',
      value: pendingDiscoveries.length,
      icon: Search,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      change: 'Requires attention',
    },
    {
      name: 'Avg Response Time',
      value: '12m',
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      change: '-2m from last week',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mission Control Dashboard</h1>
          <p className="text-gray-600">Overview of all SAR operations and system status</p>
        </div>
        <div className="flex space-x-3">
          <Button asChild>
            <Link to="/mission-planning">
              <Plus className="h-4 w-4 mr-2" />
              New Mission
            </Link>
          </Button>
          <Button variant="outline">
            <Play className="h-4 w-4 mr-2" />
            Quick Deploy
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.name}>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                    <p className="text-xs text-gray-500">{stat.change}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Missions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MapPin className="h-5 w-5 mr-2" />
              Recent Missions
            </CardTitle>
            <CardDescription>
              Latest mission activities and status updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            {missionsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {missions?.slice(0, 5).map((mission) => (
                  <div key={mission.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">{mission.name}</h4>
                      <p className="text-sm text-gray-500">
                        {mission.area_size_km2} km² • {mission.search_altitude}m altitude
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        mission.status === 'active' ? 'bg-green-100 text-green-800' :
                        mission.status === 'planning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {mission.status}
                      </span>
                      <Button size="sm" variant="outline" asChild>
                        <Link to={`/live-mission/${mission.id}`}>
                          View
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))}
                {(!missions || missions.length === 0) && (
                  <p className="text-gray-500 text-center py-4">No missions found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Drone Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Plane className="h-5 w-5 mr-2" />
              Drone Fleet Status
            </CardTitle>
            <CardDescription>
              Current status and availability of drone fleet
            </CardDescription>
          </CardHeader>
          <CardContent>
            {dronesLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {drones?.slice(0, 5).map((drone) => (
                  <div key={drone.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">{drone.name}</h4>
                      <p className="text-sm text-gray-500">
                        {drone.model} • {drone.battery_level}% battery
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        drone.is_connected ? 'bg-green-400' : 'bg-red-400'
                      }`}></div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        drone.status === 'available' ? 'bg-green-100 text-green-800' :
                        drone.status === 'active' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {drone.status}
                      </span>
                    </div>
                  </div>
                ))}
                {(!drones || drones.length === 0) && (
                  <p className="text-gray-500 text-center py-4">No drones found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Discoveries */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="h-5 w-5 mr-2" />
            Recent Discoveries
          </CardTitle>
          <CardDescription>
            Latest findings and points of interest from active missions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {discoveriesLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {pendingDiscoveries.slice(0, 5).map((discovery) => (
                <div key={discovery.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div>
                    <h4 className="font-medium text-gray-900 capitalize">
                      {discovery.discovery_type}
                    </h4>
                    <p className="text-sm text-gray-500">
                      Confidence: {discovery.confidence * 100}% • Priority: {discovery.priority}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      discovery.status === 'new' ? 'bg-blue-100 text-blue-800' :
                      discovery.status === 'investigating' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {discovery.status}
                    </span>
                    <Button size="sm" variant="outline">
                      Investigate
                    </Button>
                  </div>
                </div>
              ))}
              {pendingDiscoveries.length === 0 && (
                <p className="text-gray-500 text-center py-4">No pending discoveries</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and shortcuts for mission management
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center" asChild>
              <Link to="/mission-planning">
                <Plus className="h-6 w-6 mb-2" />
                <span className="text-sm">New Mission</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center" asChild>
              <Link to="/drones">
                <Plane className="h-6 w-6 mb-2" />
                <span className="text-sm">Manage Drones</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center" asChild>
              <Link to="/discoveries">
                <Search className="h-6 w-6 mb-2" />
                <span className="text-sm">View Discoveries</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center" asChild>
              <Link to="/analytics">
                <TrendingUp className="h-6 w-6 mb-2" />
                <span className="text-sm">Analytics</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;