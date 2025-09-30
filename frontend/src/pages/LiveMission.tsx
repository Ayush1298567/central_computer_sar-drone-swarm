import React from 'react'
import { useParams } from 'react-router-dom'

const LiveMission: React.FC = () => {
  const { missionId } = useParams<{ missionId: string }>()

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Live Mission: {missionId}
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            Real-time mission monitoring and control interface.
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Mission Status */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Mission Status</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Status:</span>
                <span className="text-sm font-medium text-green-600">Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Progress:</span>
                <span className="text-sm font-medium">65%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Drones Active:</span>
                <span className="text-sm font-medium">3/3</span>
              </div>
            </div>
          </div>
        </div>

        {/* Emergency Controls */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Emergency Controls</h4>
            <div className="space-y-3">
              <button className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md">
                Emergency Stop All Drones
              </button>
              <button className="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-md">
                Return All to Home
              </button>
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md">
                Pause Mission
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Video Feeds Placeholder */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Live Video Feeds
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
              <span className="text-gray-500">Drone 1 Feed</span>
            </div>
            <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
              <span className="text-gray-500">Drone 2 Feed</span>
            </div>
            <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
              <span className="text-gray-500">Drone 3 Feed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LiveMission