import React, { useState, useEffect } from 'react'

interface Drone {
  id: string
  position: { lat: number; lng: number }
  status: 'online' | 'offline' | 'flying' | 'returning'
  battery: number
}

const LiveMission: React.FC = () => {
  const [drones, setDrones] = useState<Drone[]>([])
  const [missionStatus, setMissionStatus] = useState('active')

  useEffect(() => {
    // TODO: Connect to WebSocket for real-time updates
    // For now, simulate some drones
    const mockDrones: Drone[] = [
      {
        id: 'drone-1',
        position: { lat: 40.7128, lng: -74.0060 },
        status: 'flying',
        battery: 85
      },
      {
        id: 'drone-2',
        position: { lat: 40.7589, lng: -73.9851 },
        status: 'flying',
        battery: 72
      }
    ]
    setDrones(mockDrones)
  }, [])

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Section */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Live Mission View</h3>
            <div className="bg-gray-100 rounded-lg h-96 flex items-center justify-center">
              <p className="text-gray-500">Interactive Map Component (Coming Soon)</p>
            </div>
          </div>
        </div>

        {/* Status Panel */}
        <div className="space-y-6">
          {/* Mission Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Mission Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="text-green-600 font-medium capitalize">{missionStatus}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Active Drones:</span>
                <span className="font-medium">{drones.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Coverage:</span>
                <span className="font-medium">65%</span>
              </div>
            </div>
          </div>

          {/* Drone List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Drones</h3>
            <div className="space-y-3">
              {drones.map(drone => (
                <div key={drone.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                  <div>
                    <p className="font-medium text-gray-900">{drone.id}</p>
                    <p className="text-sm text-gray-500 capitalize">{drone.status}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{drone.battery}%</p>
                    <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${drone.battery}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Controls */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Mission Controls</h3>
            <div className="space-y-3">
              <button className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md font-medium">
                Emergency Stop
              </button>
              <button className="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded-md font-medium">
                Return All Drones
              </button>
              <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded-md font-medium">
                Update Mission
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LiveMission