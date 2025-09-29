import React from 'react';
import { useParams } from 'react-router-dom';

const LiveMission: React.FC = () => {
  const { missionId } = useParams<{ missionId: string }>();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Live Mission Control</h1>
        <p className="text-gray-600">Real-time mission monitoring and control - Mission #{missionId}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <div className="lg:col-span-2 bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Mission Map</h3>
          <div className="bg-gray-100 h-96 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">Interactive map will be displayed here</p>
          </div>
        </div>

        {/* Control Panel */}
        <div className="space-y-6">
          {/* Mission Status */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Mission Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Status</span>
                <span className="text-sm font-medium text-green-600">Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Duration</span>
                <span className="text-sm font-medium">00:45:23</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Coverage</span>
                <span className="text-sm font-medium">67%</span>
              </div>
            </div>
          </div>

          {/* Drone Status */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Active Drones</h3>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium">Drone {i}</p>
                    <p className="text-xs text-gray-500">85% battery</p>
                  </div>
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Controls */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Controls</h3>
            <div className="space-y-2">
              <button className="w-full bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700">
                Emergency Stop
              </button>
              <button className="w-full bg-yellow-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-yellow-700">
                Return to Base
              </button>
              <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                Manual Override
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;