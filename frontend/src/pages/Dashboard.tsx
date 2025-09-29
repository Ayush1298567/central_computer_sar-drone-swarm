import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Play,
  Plus,
  Activity,
  MapPin,
  Clock,
  CheckCircle,
  AlertTriangle,
  Users,
  TrendingUp
} from 'lucide-react'
import { MissionService } from '@/services/missionService'
import { Mission } from '@/types/mission'

const Dashboard: React.FC = () => {
  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    totalMissions: 0,
    activeMissions: 0,
    completedMissions: 0,
    averageDuration: 0
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load missions and summary data
      const [missionsResponse, summaryResponse] = await Promise.all([
        MissionService.getMissions(),
        MissionService.getMissionSummary()
      ])

      if (missionsResponse.success && missionsResponse.data) {
        setMissions(missionsResponse.data)
      }

      if (summaryResponse.success && summaryResponse.data) {
        setStats({
          totalMissions: summaryResponse.data.total_missions || 0,
          activeMissions: summaryResponse.data.active_missions || 0,
          completedMissions: summaryResponse.data.completed_missions || 0,
          averageDuration: summaryResponse.data.average_completion_time || 0
        })
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100'
      case 'completed':
        return 'text-blue-600 bg-blue-100'
      case 'planning':
        return 'text-yellow-600 bg-yellow-100'
      case 'failed':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Activity className="h-4 w-4" />
      case 'completed':
        return <CheckCircle className="h-4 w-4" />
      case 'planning':
        return <Clock className="h-4 w-4" />
      case 'failed':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <MapPin className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
            <div className="mt-4">
              <button
                onClick={loadDashboardData}
                className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mission Dashboard</h1>
          <p className="text-gray-600">Overview of all SAR missions and system status</p>
        </div>
        <Link
          to="/mission-planning"
          className="btn-primary flex items-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Mission
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MapPin className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Missions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalMissions}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Missions</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeMissions}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">{stats.completedMissions}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Duration</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round(stats.averageDuration)}m</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Missions */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Recent Missions</h2>
          <Link
            to="/missions"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View All
          </Link>
        </div>

        {missions.length === 0 ? (
          <div className="text-center py-12">
            <MapPin className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No missions yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating your first mission.</p>
            <div className="mt-6">
              <Link
                to="/mission-planning"
                className="btn-primary"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Mission
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {missions.slice(0, 5).map((mission) => (
              <div
                key={mission.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-lg ${getStatusColor(mission.status)}`}>
                    {getStatusIcon(mission.status)}
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{mission.name}</h3>
                    <p className="text-sm text-gray-500">
                      {mission.assigned_drone_count} drones • {mission.search_target}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(mission.status)}`}>
                    {mission.status}
                  </span>
                  <Link
                    to={`/live-mission?mission=${mission.id}`}
                    className="btn-secondary flex items-center text-sm"
                  >
                    {mission.status === 'active' ? (
                      <>
                        <Play className="h-3 w-3 mr-1" />
                        Monitor
                      </>
                    ) : (
                      'View'
                    )}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/mission-planning"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="text-center">
            <div className="p-3 bg-primary-100 rounded-lg w-fit mx-auto mb-4">
              <Plus className="h-6 w-6 text-primary-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Plan New Mission</h3>
            <p className="text-sm text-gray-600">Create and configure a new search and rescue mission</p>
          </div>
        </Link>

        <Link
          to="/drones"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="text-center">
            <div className="p-3 bg-green-100 rounded-lg w-fit mx-auto mb-4">
              <Users className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Manage Drones</h3>
            <p className="text-sm text-gray-600">Monitor drone fleet status and performance</p>
          </div>
        </Link>

        <Link
          to="/analytics"
          className="card hover:shadow-lg transition-shadow cursor-pointer"
        >
          <div className="text-center">
            <div className="p-3 bg-purple-100 rounded-lg w-fit mx-auto mb-4">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">View Analytics</h3>
            <p className="text-sm text-gray-600">Analyze mission performance and insights</p>
          </div>
        </Link>
      </div>
    </div>
  )
}

export default Dashboard