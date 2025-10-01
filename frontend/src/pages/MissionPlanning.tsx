import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tantml/react-query';
import { missionService } from '../services/missions';
import { droneService } from '../services/drones';
import { ArrowLeft, Send, MapPin, Plane } from 'lucide-react';
import { Mission } from '../types';

const MissionPlanning: React.FC = () => {
  const navigate = useNavigate();
  const [missionName, setMissionName] = useState('');
  const [description, setDescription] = useState('');
  const [searchTarget, setSearchTarget] = useState('');
  const [searchAltitude, setSearchAltitude] = useState(20);
  const [searchSpeed, setSearchSpeed] = useState<'fast' | 'thorough'>('thorough');

  const { data: drones = [] } = useQuery({
    queryKey: ['drones'],
    queryFn: () => droneService.list(),
  });

  const createMission = useMutation({
    mutationFn: (missionData: Partial<Mission>) => missionService.create(missionData),
    onSuccess: (mission) => {
      navigate(`/mission/${mission.id}`);
    },
  });

  const handleCreateMission = () => {
    if (!missionName.trim()) {
      alert('Please enter a mission name');
      return;
    }

    createMission.mutate({
      name: missionName,
      description,
      search_target: searchTarget,
      search_altitude: searchAltitude,
      search_speed: searchSpeed,
      recording_mode: 'continuous',
      status: 'planning',
    });
  };

  const availableDrones = drones.filter((d) => d.status === 'online' || d.status === 'offline');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Mission Planning</h1>
              <p className="text-sm text-gray-600">Create a new SAR mission</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Mission Details */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Mission Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mission Name *
                  </label>
                  <input
                    type="text"
                    value={missionName}
                    onChange={(e) => setMissionName(e.target.value)}
                    placeholder="e.g., Search Forest Area"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe the mission objectives..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Target
                  </label>
                  <input
                    type="text"
                    value={searchTarget}
                    onChange={(e) => setSearchTarget(e.target.value)}
                    placeholder="e.g., Missing person, debris"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Altitude (meters)
                  </label>
                  <input
                    type="number"
                    value={searchAltitude}
                    onChange={(e) => setSearchAltitude(Number(e.target.value))}
                    min="5"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Speed
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setSearchSpeed('fast')}
                      className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                        searchSpeed === 'fast'
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      Fast
                    </button>
                    <button
                      onClick={() => setSearchSpeed('thorough')}
                      className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                        searchSpeed === 'thorough'
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      Thorough
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Available Drones */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Drones</h2>
              <div className="space-y-2">
                {availableDrones.length === 0 ? (
                  <p className="text-sm text-gray-500">No drones available</p>
                ) : (
                  availableDrones.map((drone) => (
                    <div
                      key={drone.id}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Plane size={16} className="text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{drone.name}</p>
                          <p className="text-xs text-gray-500">Battery: {drone.battery_level.toFixed(1)}%</p>
                        </div>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          drone.status === 'online'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {drone.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Create Mission Button */}
            <button
              onClick={handleCreateMission}
              disabled={createMission.isPending}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {createMission.isPending ? (
                <>Creating Mission...</>
              ) : (
                <>
                  <Send size={20} />
                  Create Mission
                </>
              )}
            </button>
          </div>

          {/* Right Column - Map Preview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Search Area</h2>
            <div className="w-full h-[600px] bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <MapPin size={48} className="mx-auto mb-2 opacity-50" />
                <p>Interactive map will be displayed here</p>
                <p className="text-sm">Draw search area on the map</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default MissionPlanning;
