import React, { useState, useEffect } from 'react';
import { DroneGrid } from '../components/drone/DroneGrid';
import { InteractiveMap } from '../components/map/InteractiveMap';
import { Drone } from '../types/drone';
import { Mission } from '../types/mission';
import { apiService } from '../services/api';
import { AlertTriangle, Activity, MapPin, Users } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [drones, setDrones] = useState<Drone[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [selectedDrone, setSelectedDrone] = useState<Drone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDrones: 0,
    activeDrones: 0,
    activeMissions: 0,
    totalMissions: 0,
  });

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [dronesResponse, missionsResponse] = await Promise.all([
          apiService.getDrones(),
          apiService.getMissions(),
        ]);

        setDrones(dronesResponse.drones);
        setMissions(missionsResponse.missions);

        // Calculate stats
        const activeDrones = dronesResponse.drones.filter(d => d.status === 'active').length;
        const activeMissions = missionsResponse.missions.filter(m => m.status === 'active').length;

        setStats({
          totalDrones: dronesResponse.drones.length,
          activeDrones,
          activeMissions,
          totalMissions: missionsResponse.missions.length,
        });
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleDiscoverDrones = async () => {
    try {
      const result = await apiService.discoverDrones();
      console.log('Discovered drones:', result);
      // Refresh drone list
      const response = await apiService.getDrones();
      setDrones(response.drones);
    } catch (error) {
      console.error('Failed to discover drones:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Drones</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalDrones}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Drones</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.activeDrones}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <MapPin className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Missions</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.activeMissions}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Missions</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalMissions}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Fleet Overview</h2>
            <div className="h-96">
              <InteractiveMap
                drones={drones}
                missions={missions}
                onDroneClick={setSelectedDrone}
                className="h-full"
              />
            </div>
          </div>
        </div>

        {/* Drone Details */}
        <div className="space-y-6">
          {selectedDrone && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Selected Drone
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-500">Name</p>
                  <p className="text-lg text-gray-900">{selectedDrone.name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Model</p>
                  <p className="text-gray-900">{selectedDrone.model}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Status</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedDrone.status === 'active' ? 'bg-green-100 text-green-800' :
                    selectedDrone.status === 'idle' ? 'bg-blue-100 text-blue-800' :
                    selectedDrone.status === 'charging' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {selectedDrone.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Battery</p>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          selectedDrone.battery_level > 60 ? 'bg-green-500' :
                          selectedDrone.battery_level > 30 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${selectedDrone.battery_level}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">{selectedDrone.battery_level}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Position</p>
                  <p className="text-xs text-gray-600 font-mono">
                    {selectedDrone.position.latitude.toFixed(6)}, {selectedDrone.position.longitude.toFixed(6)}
                  </p>
                  <p className="text-xs text-gray-600">
                    Altitude: {selectedDrone.position.altitude}m
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Recent Activity
            </h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">Mission Alpha completed successfully</p>
                  <p className="text-xs text-gray-500">2 minutes ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">Drone Scout-01 returned to base</p>
                  <p className="text-xs text-gray-500">5 minutes ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">Weather alert: High winds detected</p>
                  <p className="text-xs text-gray-500">12 minutes ago</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Drone Grid */}
      <DroneGrid
        drones={drones}
        onDroneSelect={setSelectedDrone}
        onDiscoverDrones={handleDiscoverDrones}
        className="w-full"
      />
    </div>
  );
};