import React from 'react'
import { CheckCircle, XCircle, Clock, MapPin, Zap } from 'lucide-react'

interface MissionPreviewProps {
  mission: any
}

const MissionPreview: React.FC<MissionPreviewProps> = ({ mission }) => {
  if (!mission) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg text-center">
        <div className="text-gray-500">
          <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No mission plan yet</p>
          <p className="text-sm">Describe your mission to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Mission Preview</h3>
        <span className={`px-2 py-1 text-xs rounded-full ${
          mission.status === 'planning'
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-green-100 text-green-800'
        }`}>
          {mission.status || 'Planning'}
        </span>
      </div>

      {/* Mission Details */}
      <div className="bg-white p-4 rounded-lg border">
        <h4 className="font-medium mb-3 flex items-center">
          <MapPin className="w-4 h-4 mr-2" />
          Mission Details
        </h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Search Area:</span>
            <span className="font-medium">~{(Math.random() * 10 + 5).toFixed(1)} km²</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Est. Duration:</span>
            <span className="font-medium">~{Math.floor(Math.random() * 30 + 15)} min</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Drones Needed:</span>
            <span className="font-medium">{Math.floor(Math.random() * 3 + 1)}</span>
          </div>
        </div>
      </div>

      {/* Next Action Required */}
      {mission.next_action && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h4 className="font-medium mb-2 flex items-center text-blue-900">
            <Zap className="w-4 h-4 mr-2" />
            Next Step Required
          </h4>
          <p className="text-sm text-blue-700 capitalize">
            {mission.next_action.replace('_', ' ')}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md flex items-center justify-center">
          <CheckCircle className="w-4 h-4 mr-2" />
          Approve Plan
        </button>
        <button className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md flex items-center justify-center">
          <XCircle className="w-4 h-4 mr-2" />
          Request Changes
        </button>
      </div>

      {/* Mission Timeline */}
      <div className="bg-white p-4 rounded-lg border">
        <h4 className="font-medium mb-3 flex items-center">
          <Clock className="w-4 h-4 mr-2" />
          Mission Timeline
        </h4>
        <div className="space-y-2">
          <div className="flex items-center text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
            <span>Takeoff and Navigation</span>
            <span className="ml-auto text-gray-500">~5 min</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span>Area Search</span>
            <span className="ml-auto text-gray-500">~20 min</span>
          </div>
          <div className="flex items-center text-sm">
            <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3"></div>
            <span>Return to Base</span>
            <span className="ml-auto text-gray-500">~3 min</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MissionPreview