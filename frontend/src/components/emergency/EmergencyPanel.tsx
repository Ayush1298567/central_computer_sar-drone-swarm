import React, { useState, useEffect } from 'react'
import { emergencyService, websocketService } from '../../services'
import { Drone } from '../../types'

interface EmergencyPanelProps {
  drones: Drone[]
  onEmergencyAction?: (action: string, data?: any) => void
  className?: string
}

interface EmergencyAlert {
  id: number
  mission_id?: number
  drone_id?: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  initiated_by: string
  created_at: string
  status: 'active' | 'resolved'
}

const EmergencyPanel: React.FC<EmergencyPanelProps> = ({
  drones,
  onEmergencyAction,
  className = ''
}) => {
  const [isEmergencyMode, setIsEmergencyMode] = useState(false)
  const [emergencyAlerts, setEmergencyAlerts] = useState<EmergencyAlert[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [emergencyReason, setEmergencyReason] = useState('')
  const [initiatedBy, setInitiatedBy] = useState('operator')

  useEffect(() => {
    loadEmergencyHistory()

    const handleEmergencyAlert = (event: CustomEvent) => {
      const alertData = event.detail
      setEmergencyAlerts(prev => [alertData, ...prev])
      setIsEmergencyMode(true)
    }

    window.addEventListener('emergencyAlert', handleEmergencyAlert as EventListener)

    return () => {
      window.removeEventListener('emergencyAlert', handleEmergencyAlert as EventListener)
    }
  }, [])

  const loadEmergencyHistory = async () => {
    try {
      const history = await emergencyService.getEmergencyHistory({ limit: 10 })
      setEmergencyAlerts(history)
    } catch (error) {
      console.error('Failed to load emergency history:', error)
    }
  }

  const getSeverityColor = (severity: EmergencyAlert['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-600 text-white'
      case 'high': return 'bg-orange-600 text-white'
      case 'medium': return 'bg-yellow-600 text-white'
      case 'low': return 'bg-blue-600 text-white'
      default: return 'bg-gray-600 text-white'
    }
  }

  const getSeverityIcon = (severity: EmergencyAlert['severity']) => {
    switch (severity) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'medium': return '⚡'
      case 'low': return 'ℹ️'
      default: return '📢'
    }
  }

  const handleEmergencyStopAll = async () => {
    if (!emergencyReason.trim()) {
      alert('Please provide a reason for the emergency stop.')
      return
    }

    if (!confirm('Are you sure you want to EMERGENCY STOP ALL DRONES? This action cannot be undone.')) {
      return
    }

    try {
      setIsLoading(true)
      await emergencyService.emergencyStopAll(emergencyReason, initiatedBy)
      
      const newAlert: EmergencyAlert = {
        id: Date.now(),
        message: `Emergency stop all drones: ${emergencyReason}`,
        severity: 'critical',
        initiated_by: initiatedBy,
        created_at: new Date().toISOString(),
        status: 'active'
      }
      
      setEmergencyAlerts(prev => [newAlert, ...prev])
      setIsEmergencyMode(true)
      setEmergencyReason('')
      
      if (onEmergencyAction) {
        onEmergencyAction('emergency_stop_all', { reason: emergencyReason, initiatedBy })
      }
    } catch (error) {
      console.error('Failed to execute emergency stop:', error)
      alert('Failed to execute emergency stop. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReturnToHome = async (droneId: string) => {
    if (!emergencyReason.trim()) {
      alert('Please provide a reason for the return to home.')
      return
    }

    try {
      setIsLoading(true)
      await emergencyService.emergencyReturnToHome(droneId, emergencyReason, initiatedBy)
      
      const drone = drones.find(d => d.drone_id === droneId)
      const newAlert: EmergencyAlert = {
        id: Date.now(),
        drone_id: droneId,
        message: `Emergency return to home for ${drone?.name || droneId}: ${emergencyReason}`,
        severity: 'high',
        initiated_by: initiatedBy,
        created_at: new Date().toISOString(),
        status: 'active'
      }
      
      setEmergencyAlerts(prev => [newAlert, ...prev])
      setEmergencyReason('')
      
      if (onEmergencyAction) {
        onEmergencyAction('return_to_home', { droneId, reason: emergencyReason, initiatedBy })
      }
    } catch (error) {
      console.error('Failed to execute return to home:', error)
      alert('Failed to execute return to home. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResolveAlert = async (alertId: number) => {
    const resolutionNotes = prompt('Enter resolution notes:')
    if (!resolutionNotes) return

    try {
      await emergencyService.resolveEmergency(alertId, resolutionNotes, initiatedBy)
      setEmergencyAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, status: 'resolved' } : alert
      ))
    } catch (error) {
      console.error('Failed to resolve emergency:', error)
      alert('Failed to resolve emergency. Please try again.')
    }
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const activeAlerts = emergencyAlerts.filter(alert => alert.status === 'active')
  const hasActiveAlerts = activeAlerts.length > 0

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Emergency Controls</h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          hasActiveAlerts
            ? 'bg-red-100 text-red-800'
            : 'bg-green-100 text-green-800'
        }`}>
          {hasActiveAlerts ? `${activeAlerts.length} Active Alert${activeAlerts.length > 1 ? 's' : ''}` : 'All Clear'}
        </div>
      </div>

      {/* Emergency Status */}
      {hasActiveAlerts && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">🚨</span>
            <h3 className="text-lg font-semibold text-red-800">Active Emergency Alerts</h3>
          </div>
          <div className="space-y-2">
            {activeAlerts.map(alert => (
              <div key={alert.id} className="flex items-center justify-between p-2 bg-white rounded border">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getSeverityIcon(alert.severity)}</span>
                  <span className="text-sm text-gray-700">{alert.message}</span>
                  </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">{formatTime(alert.created_at)}</span>
                  <button
                    onClick={() => handleResolveAlert(alert.id)}
                    className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                  >
                    Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Emergency Controls */}
      <div className="space-y-4">
                  <div>
          <label htmlFor="emergency-reason" className="block text-sm font-medium text-gray-700 mb-1">
            Emergency Reason
          </label>
          <input
            type="text"
            id="emergency-reason"
            value={emergencyReason}
            onChange={(e) => setEmergencyReason(e.target.value)}
            placeholder="Enter reason for emergency action..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
                    </div>

        <div>
          <label htmlFor="initiated-by" className="block text-sm font-medium text-gray-700 mb-1">
            Initiated By
          </label>
          <select
            id="initiated-by"
            value={initiatedBy}
            onChange={(e) => setInitiatedBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="operator">Operator</option>
            <option value="system">System</option>
            <option value="safety">Safety Protocol</option>
            <option value="manual">Manual Override</option>
          </select>
                  </div>

        {/* Emergency Stop All */}
        <div className="border-t pt-4">
          <h3 className="text-md font-semibold text-gray-900 mb-3">Global Emergency Actions</h3>
                    <button
            onClick={handleEmergencyStopAll}
            disabled={isLoading || !emergencyReason.trim()}
            className="w-full px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-md font-semibold text-lg"
          >
            {isLoading ? 'Executing...' : '🚨 EMERGENCY STOP ALL DRONES 🚨'}
                    </button>
          <p className="text-xs text-gray-500 mt-1">
            This will immediately stop all drones and return them to safe positions
          </p>
                  </div>

        {/* Individual Drone Actions */}
        <div className="border-t pt-4">
          <h3 className="text-md font-semibold text-gray-900 mb-3">Individual Drone Actions</h3>
          <div className="space-y-2">
            {drones.map(drone => (
              <div key={drone.drone_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">{drone.name}</span>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${
                    drone.status === 'flying' ? 'bg-green-100 text-green-800' :
                    drone.status === 'online' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {drone.status}
                  </span>
                </div>
                <button
                  onClick={() => handleReturnToHome(drone.drone_id)}
                  disabled={isLoading || !emergencyReason.trim() || drone.status !== 'flying'}
                  className="px-3 py-1 text-sm bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded"
                >
                  Return Home
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Emergency History */}
      <div className="border-t pt-4 mt-6">
        <h3 className="text-md font-semibold text-gray-900 mb-3">Recent Emergency History</h3>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {emergencyAlerts.slice(0, 5).map(alert => (
            <div key={alert.id} className={`p-2 rounded border-l-4 ${
              alert.status === 'active' ? 'border-red-500 bg-red-50' : 'border-gray-300 bg-gray-50'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-sm">{getSeverityIcon(alert.severity)}</span>
                  <span className="text-sm text-gray-700">{alert.message}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${getSeverityColor(alert.severity)}`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-gray-500">{formatTime(alert.created_at)}</span>
          </div>
          </div>
          </div>
          ))}
          {emergencyAlerts.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">No emergency history</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default EmergencyPanel