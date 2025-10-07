import React, { useState, useEffect } from 'react'
import { Drone } from '../../types'
import { droneService, emergencyService } from '../../services'

interface DroneDetailsProps {
  drone: Drone
  onDroneSelect?: (drone: Drone) => void
}

const DroneDetails: React.FC<DroneDetailsProps> = ({ drone, onDroneSelect }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [telemetryData, setTelemetryData] = useState<any>(null)

  useEffect(() => {
    loadTelemetryData()
  }, [drone.drone_id])

  const loadTelemetryData = async () => {
    try {
      const data = await droneService.getDroneTelemetryByString(drone.drone_id)
      setTelemetryData(data)
    } catch (error) {
      console.error('Failed to load telemetry data:', error)
    }
  }

  const handleCommand = async (command: string) => {
    setIsLoading(true)
    try {
      switch (command) {
        case 'takeoff':
          await droneService.updateDrone(drone.drone_id, { status: 'flying' })
          break
        case 'land':
          await droneService.updateDrone(drone.drone_id, { status: 'idle' })
          break
        case 'return_home':
          await emergencyService.emergencyReturnToHome(drone.drone_id, 'Manual return to home', 'operator')
          break
        case 'emergency_stop':
          await emergencyService.emergencyStopAll('Manual emergency stop', 'operator')
          break
        default:
          console.log(`Command ${command} not implemented`)
      }
    } catch (error) {
      console.error(`Failed to execute ${command}:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flying': return 'text-green-600 bg-green-100'
      case 'online': return 'text-blue-600 bg-blue-100'
      case 'idle': return 'text-yellow-600 bg-yellow-100'
      case 'charging': return 'text-purple-600 bg-purple-100'
      case 'maintenance': return 'text-orange-600 bg-orange-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'offline': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'text-green-600'
    if (battery > 30) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getDroneIcon = (status: string) => {
    switch (status) {
      case 'flying': return '🚁'
      case 'online': return '🟢'
      case 'idle': return '⏸️'
      case 'charging': return '🔋'
      case 'maintenance': return '🔧'
      case 'error': return '❌'
      case 'offline': return '⚫'
      default: return '🚁'
    }
  }

  const isFlying = drone.status === 'flying'
  const isOnline = drone.status === 'online' || drone.status === 'flying'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <div className="text-4xl">{getDroneIcon(drone.status)}</div>
        <div>
          <h3 className="text-xl font-semibold text-gray-900">{drone.name}</h3>
          <p className="text-sm text-gray-500">ID: {drone.drone_id}</p>
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(drone.status)}`}>
            {drone.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Specifications */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-lg font-medium text-gray-900 mb-3">Specifications</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Model</div>
            <div className="font-medium text-gray-900">{drone.model || 'N/A'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Max Flight Time</div>
            <div className="font-medium text-gray-900">{drone.max_flight_time || 0} min</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Max Altitude</div>
            <div className="font-medium text-gray-900">{drone.max_altitude || 0} m</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Max Speed</div>
            <div className="font-medium text-gray-900">{drone.max_speed || 0} m/s</div>
          </div>
        </div>
      </div>

      {/* Current Status */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-lg font-medium text-gray-900 mb-3">Current Status</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Battery Level</div>
            <div className={`font-medium ${getBatteryColor(drone.battery_level)}`}>
              {drone.battery_level}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  drone.battery_level > 60 ? 'bg-green-500' :
                  drone.battery_level > 30 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${drone.battery_level}%` }}
              />
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-500">Current Altitude</div>
            <div className="font-medium text-gray-900">
              {drone.current_position?.alt?.toFixed(1) || '0.0'} m
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-500">Cruise Speed</div>
            <div className="font-medium text-gray-900">
              {drone.cruise_speed || 0} m/s
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-500">Flight Time Remaining</div>
            <div className="font-medium text-gray-900">
              {drone.max_flight_time || 0} min
            </div>
          </div>
        </div>
      </div>

      {/* Position Information */}
      {drone.current_position && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-lg font-medium text-gray-900 mb-3">Position</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Latitude</div>
              <div className="font-medium text-gray-900 font-mono">
                {drone.current_position.lat.toFixed(6)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Longitude</div>
              <div className="font-medium text-gray-900 font-mono">
                {drone.current_position.lng.toFixed(6)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Altitude</div>
              <div className="font-medium text-gray-900">
                {drone.current_position.alt.toFixed(1)} m
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Telemetry Data */}
      {telemetryData && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-lg font-medium text-gray-900 mb-3">Recent Telemetry</h4>
          <div className="text-sm text-gray-600">
            <p>Last updated: {new Date(telemetryData.timestamp).toLocaleString()}</p>
            {telemetryData.data && (
              <div className="mt-2 space-y-1">
                <p>GPS Signal: {telemetryData.data.gps_signal || 'N/A'}</p>
                <p>Wind Speed: {telemetryData.data.wind_speed || 'N/A'} m/s</p>
                <p>Temperature: {telemetryData.data.temperature || 'N/A'}°C</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-lg font-medium text-gray-900 mb-3">Drone Controls</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {isOnline && !isFlying && (
            <button
              onClick={() => handleCommand('takeoff')}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium"
            >
              {isLoading ? '...' : 'Takeoff'}
            </button>
          )}

          {isFlying && (
            <button
              onClick={() => handleCommand('land')}
              disabled={isLoading}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium"
            >
              {isLoading ? '...' : 'Land'}
            </button>
          )}

          {isOnline && (
            <button
              onClick={() => handleCommand('return_home')}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium"
            >
              {isLoading ? '...' : 'Return Home'}
            </button>
          )}

          <button
            onClick={() => handleCommand('emergency_stop')}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium"
          >
            {isLoading ? '...' : 'Emergency Stop'}
          </button>
        </div>
      </div>

      {/* Additional Actions */}
      <div className="flex justify-between items-center pt-4 border-t">
        <button
          onClick={() => loadTelemetryData()}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md text-sm"
        >
          Refresh Data
        </button>
        
        {onDroneSelect && (
          <button
            onClick={() => onDroneSelect(drone)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm"
          >
            Select for Mission
          </button>
        )}
      </div>
    </div>
  )
}

export default DroneDetails
