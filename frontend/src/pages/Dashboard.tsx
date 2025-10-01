import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { missionService } from '../services/missions';
import { droneService } from '../services/drones';
import { Plus, Plane, Target, Activity } from 'lucide-react';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { data: missions = [], isLoading: missionsLoading } = useQuery({
    queryKey: ['missions'],
    queryFn: () => missionService.list(),
  });

  const { data: drones = [], isLoading: dronesLoading } = useQuery({
    queryKey: ['drones'],
    queryFn: () => droneService.list(),
  });

  const activeMissions = missions.filter((m) => m.status === 'active');
  const availableDrones = drones.filter((d) => d.status === 'online');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Mission Commander</h1>
              <p className="text-sm text-gray-600">SAR Drone Control System</p>
            </div>
            <button
              onClick={() => navigate('/planning')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              New Mission
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Missions</p>
                <p className="text-3xl font-bold text-gray-900">{activeMissions.length}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Target className="text-blue-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Available Drones</p>
                <p className="text-3xl font-bold text-gray-900">{availableDrones.length}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <Plane className="text-green-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Missions</p>
                <p className="text-3xl font-bold text-gray-900">{missions.length}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <Activity className="text-purple-600" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Missions List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Missions</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {missionsLoading ? (
              <div className="px-6 py-8 text-center text-gray-500">Loading missions...</div>
            ) : missions.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                No missions yet. Create your first mission to get started.
              </div>
            ) : (
              missions.slice(0, 10).map((mission) => (
                <div
                  key={mission.id}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/mission/${mission.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{mission.name}</h3>
                      <p className="text-sm text-gray-600">{mission.description || 'No description'}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          mission.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : mission.status === 'completed'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {mission.status}
                      </span>
                      <span className="text-sm text-gray-500">
                        {new Date(mission.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Drones List */}
        <div className="bg-white rounded-lg shadow mt-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Drone Fleet</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {dronesLoading ? (
              <div className="px-6 py-8 text-center text-gray-500">Loading drones...</div>
            ) : drones.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                No drones registered. Register drones to start missions.
              </div>
            ) : (
              drones.map((drone) => (
                <div key={drone.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{drone.name}</h3>
                      <p className="text-sm text-gray-600">Battery: {drone.battery_level.toFixed(1)}%</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          drone.status === 'online'
                            ? 'bg-green-100 text-green-800'
                            : drone.status === 'flying'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {drone.status}
                      </span>
                      <span className="text-sm text-gray-500">{drone.missions_completed} missions</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
