import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { MapPin, Activity, Battery, Signal, AlertTriangle, Pause, Play, Square } from 'lucide-react'

const LiveMission: React.FC = () => {
  const [missionStatus] = useState('active')
  const [drones] = useState([
    {
      id: '1',
      name: 'Drone-001',
      status: 'flying',
      battery: 85,
      position: { lat: 40.7128, lng: -74.0060 },
      speed: 25,
      altitude: 100,
    },
    {
      id: '2',
      name: 'Drone-002',
      status: 'flying',
      battery: 72,
      position: { lat: 40.7138, lng: -74.0070 },
      speed: 22,
      altitude: 95,
    },
  ])

  const [discoveries] = useState([
    {
      id: '1',
      type: 'person',
      position: { lat: 40.7120, lng: -74.0050 },
      priority: 'high',
      status: 'detected',
      time: '2 minutes ago',
    },
    {
      id: '2',
      type: 'vehicle',
      position: { lat: 40.7140, lng: -74.0080 },
      priority: 'medium',
      status: 'investigating',
      time: '5 minutes ago',
    },
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getDroneStatusColor = (status: string) => {
    switch (status) {
      case 'flying':
        return 'bg-blue-100 text-blue-800'
      case 'returning':
        return 'bg-yellow-100 text-yellow-800'
      case 'charging':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-red-100 text-red-800'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-blue-100 text-blue-800'
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Mission: SAR-001</h1>
          <p className="text-gray-600">Urban Search and Rescue Operation</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge className={getStatusColor(missionStatus)}>
            {missionStatus.toUpperCase()}
          </Badge>
          <div className="flex space-x-2">
            {missionStatus === 'active' ? (
              <Button variant="outline" size="sm">
                <Pause className="h-4 w-4 mr-2" />
                Pause
              </Button>
            ) : (
              <Button variant="outline" size="sm">
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
            )}
            <Button variant="destructive" size="sm">
              <Square className="h-4 w-4 mr-2" />
              Stop
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mission Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Mission Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">2h 34m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Area Covered:</span>
                <span className="font-medium">65%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Discoveries:</span>
                <span className="font-medium">{discoveries.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Active Drones:</span>
                <span className="font-medium">{drones.filter(d => d.status === 'flying').length}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Drones */}
        <Card>
          <CardHeader>
            <CardTitle>Active Drones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {drones.map((drone) => (
                <div key={drone.id} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{drone.name}</span>
                    <Badge className={getDroneStatusColor(drone.status)}>
                      {drone.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center space-x-1">
                      <Battery className="h-3 w-3" />
                      <span>{drone.battery}%</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Signal className="h-3 w-3" />
                      <span>{drone.speed} km/h</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <MapPin className="h-3 w-3" />
                      <span>{drone.altitude}m</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Activity className="h-3 w-3" />
                      <span>{drone.position.lat.toFixed(4)}, {drone.position.lng.toFixed(4)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Discoveries */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Discoveries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {discoveries.map((discovery) => (
                <div key={discovery.id} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium capitalize">{discovery.type}</span>
                    <Badge className={getPriorityColor(discovery.priority)}>
                      {discovery.priority}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    Status: <span className="capitalize">{discovery.status}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {discovery.time} • {discovery.position.lat.toFixed(4)}, {discovery.position.lng.toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Map Area */}
      <Card>
        <CardHeader>
          <CardTitle>Live Mission Map</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-100 h-96 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <MapPin className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Interactive mission map</p>
              <p className="text-sm text-gray-400">Real-time drone positions and discoveries</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span>Emergency Controls</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button variant="destructive" className="h-20 flex-col space-y-2">
              <AlertTriangle className="h-6 w-6" />
              <span>Emergency Stop All</span>
            </Button>
            <Button variant="destructive" className="h-20 flex-col space-y-2">
              <MapPin className="h-6 w-6" />
              <span>Return All to Base</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Signal className="h-6 w-6" />
              <span>Emergency Broadcast</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Activity className="h-6 w-6" />
              <span>Manual Override</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default LiveMission