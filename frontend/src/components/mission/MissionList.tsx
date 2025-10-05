import React from 'react'
import { Mission } from '../../types'

interface MissionListProps {
  missions: Mission[]
  onMissionSelect: (mission: Mission) => void
  onStartMission: (missionId: string) => void
  onStopMission: (missionId: string) => void
  onDeleteMission: (missionId: string) => void
}

const MissionList: React.FC<MissionListProps> = ({
  missions,
  onMissionSelect,
  onStartMission,
  onStopMission,
  onDeleteMission
}) => {
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

  const canStartMission = (mission: Mission) => {
    return mission.status === 'planning' && mission.assigned_drones && mission.assigned_drones.length > 0
  }

  const canStopMission = (mission: Mission) => {
    return mission.status === 'active'
  }

  if (missions.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        <div className="text-4xl mb-4">🎯</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Missions Found</h3>
        <p className="text-gray-600">Create your first mission to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {missions.map((mission) => (
        <div
          key={mission.id}
          className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onMissionSelect(mission)}
        >
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{mission.name}</h3>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(mission.status)}`}>
                  {mission.status.toUpperCase()}
                </span>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(mission.priority)}`}>
                  {getPriorityText(mission.priority)}
                </span>
              </div>
              
              {mission.description && (
                <p className="text-gray-600 text-sm mb-2">{mission.description}</p>
              )}
              
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span>Type: {mission.mission_type}</span>
                <span>Target: {mission.search_target}</span>
                <span>Drones: {mission.assigned_drones?.length || 0}/{mission.max_drones}</span>
                <span>Duration: {mission.estimated_duration}min</span>
              </div>
            </div>

            <div className="flex flex-col items-end space-y-2">
              <div className="text-sm text-gray-500">
                Created: {formatDate(mission.created_at)}
              </div>
              
              <div className="flex space-x-2">
                {canStartMission(mission) && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onStartMission(mission.id)
                    }}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium"
                  >
                    Start
                  </button>
                )}
                
                {canStopMission(mission) && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onStopMission(mission.id)
                    }}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium"
                  >
                    Stop
                  </button>
                )}
                
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onMissionSelect(mission)
                  }}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium"
                >
                  View
                </button>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteMission(mission.id)
                  }}
                  className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm font-medium"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          {/* Mission Progress */}
          {mission.status === 'active' && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Progress</span>
                <span>0%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '0%' }}></div>
              </div>
            </div>
          )}

          {/* Mission Statistics */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-gray-50 rounded p-2">
              <div className="text-gray-500">Search Altitude</div>
              <div className="font-medium text-gray-900">{mission.search_altitude}m</div>
            </div>
            <div className="bg-gray-50 rounded p-2">
              <div className="text-gray-500">Search Pattern</div>
              <div className="font-medium text-gray-900 capitalize">{mission.search_pattern}</div>
            </div>
            <div className="bg-gray-50 rounded p-2">
              <div className="text-gray-500">Overlap</div>
              <div className="font-medium text-gray-900">{mission.overlap_percentage}%</div>
            </div>
            <div className="bg-gray-50 rounded p-2">
              <div className="text-gray-500">Area Size</div>
              <div className="font-medium text-gray-900">
                {mission.search_area ? 'Selected' : 'Not Set'}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default MissionList
