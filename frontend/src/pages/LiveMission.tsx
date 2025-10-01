import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { missionService } from '../services/missions';
import { discoveryService } from '../services/discoveries';
import { websocketService } from '../services/websocket';
import { ArrowLeft, Play, Pause, Square, AlertTriangle } from 'lucide-react';

const LiveMission: React.FC = () => {
  const { missionId } = useParams<{ missionId: string }>();
  const navigate = useNavigate();

  const { data: mission, isLoading } = useQuery({
    queryKey: ['mission', missionId],
    queryFn: () => missionService.get(Number(missionId)),
    enabled: !!missionId,
  });

  const { data: discoveries = [] } = useQuery({
    queryKey: ['discoveries', missionId],
    queryFn: () => discoveryService.list(Number(missionId)),
    enabled: !!missionId,
  });

  useEffect(() => {
    if (missionId) {
      websocketService.subscribeMission(Number(missionId));
    }

    return () => {
      if (missionId) {
        websocketService.unsubscribeMission(Number(missionId));
      }
    };
  }, [missionId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading mission...</div>
      </div>
    );
  }

  if (!mission) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Mission not found</div>
      </div>
    );
  }

  const criticalDiscoveries = discoveries.filter((d) => d.priority_level >= 3);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{mission.name}</h1>
                <p className="text-sm text-gray-600">{mission.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-4 py-2 rounded-lg font-medium ${
                  mission.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : mission.status === 'completed'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {mission.status}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Map and Controls */}
          <div className="lg:col-span-2 space-y-6">
            {/* Mission Map */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Live Mission View</h2>
              <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">Real-time map with drone positions will be displayed here</p>
              </div>
            </div>

            {/* Mission Controls */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Mission Controls</h2>
              <div className="flex gap-3">
                <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                  <Play size={20} />
                  Start
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
                  <Pause size={20} />
                  Pause
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                  <Square size={20} />
                  Stop
                </button>
              </div>
            </div>

            {/* Discoveries */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Discoveries</h2>
              <div className="space-y-3">
                {discoveries.length === 0 ? (
                  <p className="text-sm text-gray-500">No discoveries yet</p>
                ) : (
                  discoveries.map((discovery) => (
                    <div
                      key={discovery.id}
                      className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {discovery.priority_level >= 3 && (
                        <AlertTriangle className="text-red-500 flex-shrink-0" size={20} />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-medium text-gray-900">{discovery.object_type}</p>
                          <span className="text-sm text-gray-500">
                            {(discovery.confidence_score * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Location: {discovery.latitude.toFixed(6)}, {discovery.longitude.toFixed(6)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(discovery.discovered_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Mission Stats */}
          <div className="space-y-6">
            {/* Mission Progress */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Progress</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Coverage</span>
                    <span className="font-medium">{mission.coverage_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${mission.coverage_percentage}%` }}
                    />
                  </div>
                </div>
                
                <div className="pt-4 border-t border-gray-200">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Drones Assigned</span>
                      <span className="font-medium">{mission.assigned_drone_count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Discoveries</span>
                      <span className="font-medium">{discoveries.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Critical Findings</span>
                      <span className="font-medium text-red-600">{criticalDiscoveries.length}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mission Parameters */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Parameters</h2>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Search Altitude</span>
                  <span className="font-medium">{mission.search_altitude}m</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Search Speed</span>
                  <span className="font-medium capitalize">{mission.search_speed}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Target</span>
                  <span className="font-medium">{mission.search_target || 'General'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveMission;
