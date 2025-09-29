import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MapPin,
  Save,
  Send,
  AlertCircle,
  CheckCircle,
  Clock,
  Users,
  Target
} from 'lucide-react'
import { InteractiveMap } from '@/components/map/InteractiveMap'
import { MissionService } from '@/services/missionService'
import { GeoJsonPolygon, Coordinate, CreateMissionRequest } from '@/types/mission'

interface MissionFormData {
  name: string
  description: string
  searchTarget: string
  searchAltitude: number
  searchSpeed: 'fast' | 'thorough' | 'custom'
  recordingMode: 'continuous' | 'event_triggered' | 'manual'
  assignedDrones: string[]
}

const MissionPlanning: React.FC = () => {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [isDrawing, setIsDrawing] = useState(false)
  const [selectedArea, setSelectedArea] = useState<GeoJsonPolygon | null>(null)
  const [launchPoint, setLaunchPoint] = useState<Coordinate>({ lat: 40.7128, lng: -74.0060 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [formData, setFormData] = useState<MissionFormData>({
    name: '',
    description: '',
    searchTarget: '',
    searchAltitude: 50,
    searchSpeed: 'thorough',
    recordingMode: 'event_triggered',
    assignedDrones: []
  })

  const [availableDrones, setAvailableDrones] = useState<any[]>([])

  useEffect(() => {
    loadAvailableDrones()
  }, [])

  const loadAvailableDrones = async () => {
    try {
      // This would typically fetch from a drone service
      // For now, we'll use mock data
      setAvailableDrones([
        { id: 'drone-1', name: 'Alpha-1', status: 'online', battery_level: 85 },
        { id: 'drone-2', name: 'Bravo-2', status: 'online', battery_level: 92 },
        { id: 'drone-3', name: 'Charlie-3', status: 'charging', battery_level: 45 },
        { id: 'drone-4', name: 'Delta-4', status: 'online', battery_level: 78 },
      ])
    } catch (error) {
      console.error('Failed to load drones:', error)
    }
  }

  const handleAreaSelect = useCallback((area: GeoJsonPolygon) => {
    setSelectedArea(area)
    setIsDrawing(false)
  }, [])

  const handleMapClick = useCallback((lat: number, lng: number) => {
    setLaunchPoint({ lat, lng })
  }, [])

  const handleInputChange = (field: keyof MissionFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleDroneToggle = (droneId: string) => {
    setFormData(prev => ({
      ...prev,
      assignedDrones: prev.assignedDrones.includes(droneId)
        ? prev.assignedDrones.filter(id => id !== droneId)
        : [...prev.assignedDrones, droneId]
    }))
  }

  const validateStep = (stepNumber: number): boolean => {
    switch (stepNumber) {
      case 1:
        return !!(formData.name.trim() && formData.searchTarget.trim())
      case 2:
        return !!selectedArea
      case 3:
        return formData.assignedDrones.length > 0
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(prev => Math.min(prev + 1, 4))
    }
  }

  const handlePrevious = () => {
    setStep(prev => Math.max(prev - 1, 1))
  }

  const handleSaveDraft = async () => {
    try {
      setLoading(true)
      setError(null)

      const missionData: CreateMissionRequest = {
        name: formData.name,
        description: formData.description,
        search_area: selectedArea!,
        launch_point: launchPoint,
        search_target: formData.searchTarget,
        search_altitude: formData.searchAltitude,
        search_speed: formData.searchSpeed,
        recording_mode: formData.recordingMode,
        assigned_drones: formData.assignedDrones
      }

      const response = await MissionService.createMission(missionData)

      if (response.success) {
        setSuccess('Mission saved as draft successfully!')
        setTimeout(() => {
          navigate(`/live-mission?mission=${response.data!.id}`)
        }, 2000)
      } else {
        setError(response.message || 'Failed to save mission')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save mission')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    try {
      setLoading(true)
      setError(null)

      const missionData: CreateMissionRequest = {
        name: formData.name,
        description: formData.description,
        search_area: selectedArea!,
        launch_point: launchPoint,
        search_target: formData.searchTarget,
        search_altitude: formData.searchAltitude,
        search_speed: formData.searchSpeed,
        recording_mode: formData.recordingMode,
        assigned_drones: formData.assignedDrones
      }

      const response = await MissionService.createMission(missionData)

      if (response.success) {
        // Start the mission immediately
        await MissionService.startMission(response.data!.id)

        setSuccess('Mission created and started successfully!')
        setTimeout(() => {
          navigate(`/live-mission?mission=${response.data!.id}`)
        }, 2000)
      } else {
        setError(response.message || 'Failed to create mission')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create mission')
    } finally {
      setLoading(false)
    }
  }

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {[1, 2, 3, 4].map((stepNumber) => (
        <React.Fragment key={stepNumber}>
          <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
            stepNumber <= step ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'
          }`}>
            {stepNumber < step ? (
              <CheckCircle className="h-5 w-5" />
            ) : (
              stepNumber
            )}
          </div>
          {stepNumber < 4 && (
            <div className={`w-16 h-1 ${
              stepNumber < step ? 'bg-primary-600' : 'bg-gray-200'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  )

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Mission Details</h2>
              <p className="text-gray-600">Provide basic information about your mission</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mission Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="input"
                  placeholder="Enter mission name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Target *
                </label>
                <input
                  type="text"
                  value={formData.searchTarget}
                  onChange={(e) => handleInputChange('searchTarget', e.target.value)}
                  className="input"
                  placeholder="What are you searching for?"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={3}
                className="input resize-none"
                placeholder="Optional mission description..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Altitude (m)
                </label>
                <input
                  type="number"
                  value={formData.searchAltitude}
                  onChange={(e) => handleInputChange('searchAltitude', parseInt(e.target.value) || 50)}
                  className="input"
                  min="10"
                  max="200"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Speed
                </label>
                <select
                  value={formData.searchSpeed}
                  onChange={(e) => handleInputChange('searchSpeed', e.target.value)}
                  className="input"
                >
                  <option value="fast">Fast</option>
                  <option value="thorough">Thorough</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recording Mode
                </label>
                <select
                  value={formData.recordingMode}
                  onChange={(e) => handleInputChange('recordingMode', e.target.value)}
                  className="input"
                >
                  <option value="continuous">Continuous</option>
                  <option value="event_triggered">Event Triggered</option>
                  <option value="manual">Manual</option>
                </select>
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Search Area</h2>
              <p className="text-gray-600">Define the area to be searched</p>
            </div>

            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <MapPin className="h-5 w-5 text-blue-600 mr-3" />
                <span className="text-blue-800">
                  {isDrawing ? 'Click and drag on the map to draw the search area' : 'Draw search area on map'}
                </span>
              </div>
              <button
                onClick={() => setIsDrawing(!isDrawing)}
                className={`btn-primary ${isDrawing ? 'bg-red-600 hover:bg-red-700' : ''}`}
              >
                {isDrawing ? 'Cancel Drawing' : 'Draw Area'}
              </button>
            </div>

            <div className="relative">
              <InteractiveMap
                height="400px"
                center={launchPoint}
                isDrawing={isDrawing}
                onAreaSelect={handleAreaSelect}
              />

              {launchPoint && (
                <div className="absolute bottom-4 right-4 bg-white p-2 rounded shadow text-xs">
                  <div>Launch Point: {launchPoint.lat.toFixed(6)}, {launchPoint.lng.toFixed(6)}</div>
                  {selectedArea && (
                    <div>Area Selected: {selectedArea.coordinates[0].length} points</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Drone Assignment</h2>
              <p className="text-gray-600">Select drones for this mission</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableDrones.map((drone) => (
                <div
                  key={drone.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    formData.assignedDrones.includes(drone.id)
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleDroneToggle(drone.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{drone.name}</h3>
                      <p className="text-sm text-gray-500">
                        {drone.status} • {drone.battery_level}% battery
                      </p>
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 ${
                      formData.assignedDrones.includes(drone.id)
                        ? 'bg-primary-500 border-primary-500'
                        : 'border-gray-300'
                    }`}>
                      {formData.assignedDrones.includes(drone.id) && (
                        <CheckCircle className="w-4 h-4 text-white" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {formData.assignedDrones.length > 0 && (
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <Users className="h-5 w-5 text-green-600 mr-2" />
                  <span className="text-green-800">
                    {formData.assignedDrones.length} drone{formData.assignedDrones.length > 1 ? 's' : ''} selected
                  </span>
                </div>
              </div>
            )}
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Review & Launch</h2>
              <p className="text-gray-600">Review your mission configuration before launching</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Mission Details</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Name:</strong> {formData.name}</div>
                    <div><strong>Target:</strong> {formData.searchTarget}</div>
                    <div><strong>Altitude:</strong> {formData.searchAltitude}m</div>
                    <div><strong>Speed:</strong> {formData.searchSpeed}</div>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Search Area</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Points:</strong> {selectedArea?.coordinates[0]?.length || 0}</div>
                    <div><strong>Launch Point:</strong> {launchPoint.lat.toFixed(6)}, {launchPoint.lng.toFixed(6)}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Assigned Drones</h3>
                  <div className="space-y-2 text-sm">
                    {formData.assignedDrones.map(droneId => {
                      const drone = availableDrones.find(d => d.id === droneId)
                      return drone ? (
                        <div key={droneId}>{drone.name} ({drone.battery_level}%)</div>
                      ) : null
                    })}
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Estimated Duration</h3>
                  <div className="flex items-center text-sm">
                    <Clock className="h-4 w-4 mr-2" />
                    <span>~{MissionService.calculateEstimatedDuration(1, formData.assignedDrones.length, formData.searchSpeed)} minutes</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {renderStepIndicator()}

      <div className="card">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <div className="ml-3">
                <p className="text-sm text-green-700">{success}</p>
              </div>
            </div>
          </div>
        )}

        {renderStepContent()}
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={step === 1}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>

        <div className="flex space-x-3">
          {step === 4 ? (
            <>
              <button
                onClick={handleSaveDraft}
                disabled={loading || !validateStep(4)}
                className="btn-secondary disabled:opacity-50"
              >
                <Save className="h-4 w-4 mr-2" />
                Save Draft
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading || !validateStep(4)}
                className="btn-primary disabled:opacity-50"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                ) : (
                  <Send className="h-4 w-4 mr-2" />
                )}
                Launch Mission
              </button>
            </>
          ) : (
            <button
              onClick={handleNext}
              disabled={!validateStep(step)}
              className="btn-primary disabled:opacity-50"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default MissionPlanning