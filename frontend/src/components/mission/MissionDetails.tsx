import React, { useState, useEffect } from 'react'
import { Mission, Drone } from '../../types'
import { missionService } from '../../services'

interface MissionDetailsProps {
  mission: Mission
  drones: Drone[]
  onStartMission: (missionId: string) => void
  onStopMission: (missionId: string) => void
}

const MissionDetails: React.FC<MissionDetailsProps> = ({
  mission,
  drones,
  onStartMission,
  onStopMission
}) => {
  const [missionProgress, setMissionProgress] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadMissionProgress()
  }, [mission.id])

  const loadMissionProgress = async () => {
    try {
      const progress = await missionService.getMissionProgress(mission.id)
      setMissionProgress(progress)
    } catch (error) {
      console.error('Failed to load mission progress:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100'
      case 'planning': return 'text-blue-600 bg-blue-100'
      case 'completed': return 'text-gray-600 bg-gray-100'
      case 'cancelled': return 'text-red-600 bg-red-100'
      case 'paused': return 'text-yellow-600 bg-yellow-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return 'text-red-600 bg-red-100'
      case 2: return 'text-orange-600 bg-orange-100'
      case 3: return 'text-yellow-600 bg-yellow-100'
      case 4: return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getPriorityText = (priority: number) => {
    switch (priority) {
      case 1: return 'Critical'
      case 2: return 'High'
      case 3: return 'Medium'
      case 4: return 'Low'
      default: return 'Unknown'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const canStartMission = () => {
    return mission.status === 'planning' && mission.assigned_drones && mission.assigned_drones.length > 0
  }

  const canStopMission = () => {
    return mission.status === 'active'
  }

  const assignedDrones = drones.filter(drone => 
    mission.assigned_drones?.includes(drone.drone_id)
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">{mission.name}</h3>
            <p className="text-sm text-gray-500">ID: {mission.id}</p>
          </div>
          <div className="flex space-x-2">
            <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(mission.status)}`}>
              {mission.status.toUpperCase()}
            </span>
            <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getPriorityColor(mission.priority)}`}>
              {getPriorityText(mission.priority)}
            </span>
          </div>
        </div>

        <div className="flex space-x-2">
          {canStartMission() && (
            <button
              onClick={() => onStartMission(mission.id)}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Starting...' : 'Start Mission'}
            </button>
          )}
          
          {canStopMission() && (
            <button
              onClick={() => onStopMission(mission.id)}
              disabled={isLoading}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Stopping...' : 'Stop Mission'}
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {mission.description && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
          <p className="text-gray-700">{mission.description}</p>
        </div>
      )}

      {/* Mission Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Mission Details</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Type:</span>
              <span className="font-medium text-gray-900 capitalize">{mission.mission_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Target:</span>
              <span className="font-medium text-gray-900">{mission.search_target}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Created:</span>
              <span className="font-medium text-gray-900">{formatDate(mission.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Updated:</span>
              <span className="font-medium text-gray-900">{formatDate(mission.updated_at)}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Search Parameters</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Altitude:</span>
              <span className="font-medium text-gray-900">{mission.search_altitude}m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Pattern:</span>
              <span className="font-medium text-gray-900 capitalize">{mission.search_pattern}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Overlap:</span>
              <span className="font-medium text-gray-900">{mission.overlap_percentage}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Duration:</span>
              <span className="font-medium text-gray-900">{mission.estimated_duration}min</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Drone Assignment</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Assigned:</span>
              <span className="font-medium text-gray-900">{assignedDrones.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Max Drones:</span>
              <span className="font-medium text-gray-900">{mission.max_drones}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Available:</span>
              <span className="font-medium text-gray-900">{drones.filter(d => d.status === 'online').length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Assigned Drones */}
      {assignedDrones.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Assigned Drones</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {assignedDrones.map(drone => (
              <div key={drone.drone_id} className="bg-white rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-gray-900">{drone.name}</h5>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    drone.status === 'online' ? 'bg-green-100 text-green-800' :
                    drone.status === 'flying' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {drone.status}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  <div>Battery: {drone.battery_level}%</div>
                  <div>Model: {drone.model}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mission Progress */}
      {mission.status === 'active' && missionProgress && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Mission Progress</h4>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Overall Progress</span>
                <span>{missionProgress.overall_progress || 0}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${missionProgress.overall_progress || 0}%` }}
                ></div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-gray-500">Area Covered</div>
                <div className="font-medium text-gray-900">{missionProgress.area_covered || 0}%</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Time Elapsed</div>
                <div className="font-medium text-gray-900">{missionProgress.time_elapsed || 0}min</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Discoveries</div>
                <div className="font-medium text-gray-900">{missionProgress.discoveries || 0}</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Active Drones</div>
                <div className="font-medium text-gray-900">{missionProgress.active_drones || 0}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Area Information */}
      {mission.search_area && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Search Area</h4>
          <div className="text-sm text-gray-600">
            <p>Center: {mission.center_lat.toFixed(6)}, {mission.center_lng.toFixed(6)}</p>
            <p>Area: {mission.search_area.type}</p>
            <p>Coordinates: {mission.search_area.coordinates?.length || 0} points</p>
          </div>
        </div>
      )}

      {/* Mission Statistics */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Mission Statistics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <div className="text-gray-500">Total Waypoints</div>
            <div className="font-medium text-gray-900">{missionProgress?.total_waypoints || 0}</div>
          </div>
          <div className="text-center">
            <div className="text-gray-500">Completed Waypoints</div>
            <div className="font-medium text-gray-900">{missionProgress?.completed_waypoints || 0}</div>
          </div>
          <div className="text-center">
            <div className="text-gray-500">Average Speed</div>
            <div className="font-medium text-gray-900">{missionProgress?.average_speed || 0} m/s</div>
          </div>
          <div className="text-center">
            <div className="text-gray-500">Battery Usage</div>
            <div className="font-medium text-gray-900">{missionProgress?.battery_usage || 0}%</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MissionDetails
