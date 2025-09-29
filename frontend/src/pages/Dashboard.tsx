import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import MissionMap from '../components/map/MissionMap'
import { droneService } from '../services/drones'
import { missionService } from '../services/missions'
import { Drone } from '../types/drone'
import { Mission } from '../types/mission'
import toast from 'react-hot-toast'

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    activeMissions: 0,
    availableDrones: 0,
    discoveries: 0,
    systemHealth: 'good'
  })
  const [recentMissions, setRecentMissions] = useState<Mission[]>([])
  const [drones, setDrones] = useState<Drone[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load drones
      const dronesData = await droneService.getDrones({ limit: 10 })
      setDrones(dronesData)

      // Load missions
      const missionsData = await missionService.getMissions({ limit: 5 })
      setRecentMissions(missionsData)

      // Calculate stats
      const activeMissions = missionsData.filter((m: Mission) => m.status === 'active').length
      const availableDrones = dronesData.filter((d: Drone) => d.status === 'online').length

      setStats({
        activeMissions,
        availableDrones,
        discoveries: 0, // Would come from discoveries API
        systemHealth: activeMissions > 0 ? 'good' : 'idle'
      })

    } catch (error) {
      console.error('Error loading dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const handleStartMission = () => {
    window.location.href = '/mission-planning'
  }

  const handleViewLiveMission = () => {
    window.location.href = '/live-mission'
  }

  const getSystemHealthColor = () => {
    switch (stats.systemHealth) {
      case 'good': return 'text-green-600'
      case 'warning': return 'text-yellow-600'
      case 'critical': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">SAR Drone Command Center</h1>
        <p className="text-lg text-gray-600">
          Advanced Search and Rescue Drone Swarm Management System
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Missions</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600">{stats.activeMissions}</div>
            <p className="text-xs text-muted-foreground">
              {stats.activeMissions > 0 ? 'Currently in progress' : 'No active missions'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Drones</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.availableDrones}</div>
            <p className="text-xs text-muted-foreground">
              Ready for deployment
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Discoveries</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.discoveries}</div>
            <p className="text-xs text-muted-foreground">
              Found this session
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getSystemHealthColor()}`}>
              {stats.systemHealth.toUpperCase()}
            </div>
            <p className="text-xs text-muted-foreground">
              All systems operational
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Live Map */}
        <Card>
          <CardHeader>
            <CardTitle>Live Mission Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <MissionMap
              drones={drones.map(d => ({
                id: d.drone_id,
                position: [d.position_lat, d.position_lng],
                status: d.status,
                battery: d.battery_level
              }))}
              height="400px"
            />
          </CardContent>
        </Card>

        {/* Recent Missions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Missions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentMissions.length > 0 ? (
                recentMissions.map(mission => (
                  <div key={mission.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                    <div>
                      <p className="font-medium text-gray-900">{mission.name}</p>
                      <p className="text-sm text-gray-500 capitalize">{mission.status}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {mission.priority} priority
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(mission.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No recent missions</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button onClick={handleStartMission} size="lg">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Start New Mission
            </Button>
            <Button variant="outline" onClick={handleViewLiveMission} size="lg">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              View Live Mission
            </Button>
            <Button variant="secondary" size="lg">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V17a2 2 0 01-2 2z" />
              </svg>
              View Reports
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard