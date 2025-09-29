import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { missionService, droneService } from '@/services'
import { AnalyticsData } from '@/types'
import { Activity, MapPin, Clock, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)

  // Fetch missions
  const { data: missionsData, isLoading: missionsLoading } = useQuery({
    queryKey: ['missions'],
    queryFn: () => missionService.getMissions({ limit: 10 }),
  })

  // Fetch drones
  const { data: dronesData, isLoading: dronesLoading } = useQuery({
    queryKey: ['drones'],
    queryFn: () => droneService.getDrones({ limit: 10 }),
  })

  const missions = missionsData?.data || []
  const drones = dronesData?.data || []

  // Calculate analytics
  useEffect(() => {
    if (missions.length > 0 || drones.length > 0) {
      const mockAnalytics: AnalyticsData = {
        total_missions: missions.length,
        active_missions: missions.filter((m: any) => m.status === 'active').length,
        completed_missions: missions.filter((m: any) => m.status === 'completed').length,
        total_discoveries: 0, // Would be fetched from discoveries API
        confirmed_discoveries: 0,
        average_mission_duration: 0,
        drone_utilization_rate: 0,
        system_uptime: 99.9,
        discoveries_by_type: {} as Record<string, number>,
        mission_success_rate: 95.0,
        response_time_metrics: {
          average_detection_time: 0,
          average_investigation_time: 0,
          average_mission_completion_time: 0,
        },
      }
      setAnalytics(mockAnalytics)
    }
  }, [missions, drones])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getDroneStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'flying':
        return <Activity className="h-4 w-4 text-blue-500" />
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <Button>
          New Mission
        </Button>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Missions</CardTitle>
              <MapPin className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_missions}</div>
              <p className="text-xs text-muted-foreground">
                {analytics.active_missions} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Drones</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {drones.filter((d: any) => d.status === 'online' || d.status === 'flying').length}
              </div>
              <p className="text-xs text-muted-foreground">
                {drones.filter((d: any) => d.status === 'offline').length} offline
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.mission_success_rate}%</div>
              <p className="text-xs text-muted-foreground">
                Mission completion rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.system_uptime}%</div>
              <p className="text-xs text-muted-foreground">
                Last 30 days
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Missions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Missions</CardTitle>
          </CardHeader>
          <CardContent>
            {missionsLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : missions.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No missions yet</p>
            ) : (
              <div className="space-y-4">
                {missions.slice(0, 5).map((mission: any) => (
                  <div key={mission.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{mission.name}</h4>
                      <p className="text-sm text-gray-500">
                        {mission.description.length > 50
                          ? `${mission.description.substring(0, 50)}...`
                          : mission.description
                        }
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Created: {new Date(mission.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge className={getStatusColor(mission.status)}>
                      {mission.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Drone Status */}
        <Card>
          <CardHeader>
            <CardTitle>Drone Status</CardTitle>
          </CardHeader>
          <CardContent>
            {dronesLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : drones.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No drones connected</p>
            ) : (
              <div className="space-y-4">
                {drones.slice(0, 5).map((drone: any) => (
                  <div key={drone.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getDroneStatusIcon(drone.status)}
                      <div>
                        <h4 className="font-medium">{drone.name}</h4>
                        <p className="text-sm text-gray-500">{drone.model}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{drone.battery_level}%</p>
                      <p className="text-xs text-gray-400">{drone.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="h-20 flex-col space-y-2">
              <MapPin className="h-6 w-6" />
              <span>Plan New Mission</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Activity className="h-6 w-6" />
              <span>View Live Missions</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <AlertTriangle className="h-6 w-6" />
              <span>Emergency Response</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard