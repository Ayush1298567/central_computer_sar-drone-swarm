import React, { useState, useEffect } from 'react'
import { Discovery } from '../../types'
import { discoveryService } from '../../services'

interface DiscoveryDetailsProps {
  discovery: Discovery
  onDiscoveryUpdate?: (discovery: Discovery) => void
  onClose?: () => void
}

const DiscoveryDetails: React.FC<DiscoveryDetailsProps> = ({
  discovery,
  onDiscoveryUpdate,
  onClose
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [investigationNotes, setInvestigationNotes] = useState(discovery.investigation_notes || '')
  const [resolution, setResolution] = useState('')
  const [isInvestigating, setIsInvestigating] = useState(false)

  const getStatusColor = (status: Discovery['status']) => {
    switch (status) {
      case 'pending': return 'text-blue-600 bg-blue-100'
      case 'investigating': return 'text-yellow-600 bg-yellow-100'
      case 'resolved': return 'text-green-600 bg-green-100'
      case 'false_positive': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getPriorityColor = (priority: Discovery['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'person': return '👤'
      case 'vehicle': return '🚗'
      case 'structure': return '🏢'
      case 'signal': return '📡'
      case 'animal': return '🐕'
      case 'debris': return '📦'
      case 'other': return '❓'
      default: return '❓'
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

  const handleStartInvestigation = async () => {
    try {
      setIsLoading(true)
      await discoveryService.startInvestigation(discovery.id.toString(), 'operator')
      setIsInvestigating(true)
      if (onDiscoveryUpdate) {
        onDiscoveryUpdate({ ...discovery, status: 'investigating' })
      }
    } catch (error) {
      console.error('Failed to start investigation:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCompleteInvestigation = async () => {
    if (!resolution.trim()) {
      alert('Please provide a resolution before completing the investigation.')
      return
    }

    try {
      setIsLoading(true)
      await discoveryService.completeInvestigation(
        discovery.id.toString(),
        resolution,
        investigationNotes
      )
      if (onDiscoveryUpdate) {
        onDiscoveryUpdate({ 
          ...discovery, 
          status: 'resolved',
          investigation_notes: investigationNotes
        })
      }
    } catch (error) {
      console.error('Failed to complete investigation:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMarkFalsePositive = async () => {
    try {
      setIsLoading(true)
      await discoveryService.completeInvestigation(
        discovery.id.toString(),
        'false_positive',
        'Marked as false positive'
      )
      if (onDiscoveryUpdate) {
        onDiscoveryUpdate({ 
          ...discovery, 
          status: 'false_positive',
          investigation_notes: 'Marked as false positive'
        })
      }
    } catch (error) {
      console.error('Failed to mark as false positive:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdatePriority = async (priority: Discovery['priority']) => {
    try {
      setIsLoading(true)
      await discoveryService.updateDiscoveryPriority(discovery.id.toString(), priority)
      if (onDiscoveryUpdate) {
        onDiscoveryUpdate({ ...discovery, priority })
      }
    } catch (error) {
      console.error('Failed to update priority:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const canStartInvestigation = discovery.status === 'pending'
  const canCompleteInvestigation = discovery.status === 'investigating'
  const isResolved = discovery.status === 'resolved' || discovery.status === 'false_positive'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="text-4xl">{getTypeIcon(discovery.discovery_type)}</div>
          <div>
            <h3 className="text-xl font-semibold text-gray-900">
              {discovery.discovery_type.charAt(0).toUpperCase() + discovery.discovery_type.slice(1)} Discovery
            </h3>
            <p className="text-sm text-gray-500">ID: {discovery.id}</p>
          </div>
          <div className="flex space-x-2">
            <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(discovery.status)}`}>
              {discovery.status.toUpperCase()}
            </span>
            <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getPriorityColor(discovery.priority)}`}>
              {discovery.priority.toUpperCase()}
            </span>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Description */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
        <p className="text-gray-700">
          {discovery.description || 'No description available'}
        </p>
      </div>

      {/* Discovery Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Discovery Details</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Type:</span>
              <span className="font-medium text-gray-900 capitalize">{discovery.discovery_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Confidence:</span>
              <span className="font-medium text-gray-900">{discovery.confidence}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Mission ID:</span>
              <span className="font-medium text-gray-900">{discovery.mission_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Drone ID:</span>
              <span className="font-medium text-gray-900">{discovery.drone_id}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Location</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Latitude:</span>
              <span className="font-medium text-gray-900 font-mono">
                {discovery.location_lat.toFixed(6)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Longitude:</span>
              <span className="font-medium text-gray-900 font-mono">
                {discovery.location_lng.toFixed(6)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Created:</span>
              <span className="font-medium text-gray-900">{formatDate(discovery.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Updated:</span>
              <span className="font-medium text-gray-900">{formatDate(discovery.updated_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Evidence */}
      {discovery.image_url && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Evidence</h4>
          <div className="space-y-3">
            <div className="relative">
              <img
                src={discovery.image_url}
                alt="Discovery evidence"
                className="w-full h-64 object-cover rounded-lg border border-gray-200"
              />
              <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                Evidence Image
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Investigation Notes */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Investigation Notes</h4>
        <textarea
          value={investigationNotes}
          onChange={(e) => setInvestigationNotes(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Add investigation notes..."
          disabled={isResolved}
        />
      </div>

      {/* Investigation Actions */}
      {!isResolved && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Investigation Actions</h4>
          
          {canStartInvestigation && (
            <div className="space-y-3">
              <button
                onClick={handleStartInvestigation}
                disabled={isLoading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
              >
                {isLoading ? 'Starting...' : 'Start Investigation'}
              </button>
            </div>
          )}

          {canCompleteInvestigation && (
            <div className="space-y-3">
              <div>
                <label htmlFor="resolution" className="block text-sm font-medium text-gray-700 mb-1">
                  Resolution *
                </label>
                <select
                  id="resolution"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select resolution...</option>
                  <option value="confirmed">Confirmed - Valid discovery</option>
                  <option value="false_positive">False Positive</option>
                  <option value="inconclusive">Inconclusive - Need more evidence</option>
                  <option value="duplicate">Duplicate - Already reported</option>
                </select>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleCompleteInvestigation}
                  disabled={isLoading || !resolution}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md font-medium"
                >
                  {isLoading ? 'Completing...' : 'Complete Investigation'}
                </button>
                
                <button
                  onClick={handleMarkFalsePositive}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-md font-medium"
                >
                  {isLoading ? 'Marking...' : 'Mark as False Positive'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Priority Management */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Priority Management</h4>
        <div className="flex space-x-2">
          {(['low', 'medium', 'high', 'critical'] as const).map(priority => (
            <button
              key={priority}
              onClick={() => handleUpdatePriority(priority)}
              disabled={isLoading}
              className={`px-3 py-1 rounded text-sm font-medium ${
                discovery.priority === priority
                  ? getPriorityColor(priority)
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {priority.charAt(0).toUpperCase() + priority.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Investigation Status */}
      {isResolved && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-green-800">Investigation Complete</h4>
              <p className="text-sm text-green-700">
                This discovery has been {discovery.status === 'false_positive' ? 'marked as false positive' : 'resolved'}.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DiscoveryDetails
