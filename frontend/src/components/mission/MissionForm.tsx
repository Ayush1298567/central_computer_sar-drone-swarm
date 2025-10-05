import React, { useState, useEffect } from 'react'
import { Mission, Drone, MissionCreate, MissionUpdate } from '../../types'

interface MissionFormProps {
  mission?: Mission
  drones: Drone[]
  selectedArea?: any
  onSubmit: (data: MissionCreate | MissionUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

const MissionForm: React.FC<MissionFormProps> = ({
  mission,
  drones,
  selectedArea,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    mission_type: 'search',
    priority: 3,
    search_altitude: 30.0,
    max_drones: 1,
    search_pattern: 'lawnmower',
    overlap_percentage: 10.0,
    estimated_duration: 60,
    search_target: '',
    center_lat: 40.7128,
    center_lng: -74.0060,
    search_area: null as any,
    assigned_drones: [] as string[]
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (mission) {
      setFormData({
        name: mission.name || '',
        description: mission.description || '',
        mission_type: mission.mission_type || 'search',
        priority: mission.priority || 3,
        search_altitude: mission.search_altitude || 30.0,
        max_drones: mission.max_drones || 1,
        search_pattern: mission.search_pattern || 'lawnmower',
        overlap_percentage: mission.overlap_percentage || 10.0,
        estimated_duration: mission.estimated_duration || 60,
        search_target: mission.search_target || '',
        center_lat: mission.center_lat || 40.7128,
        center_lng: mission.center_lng || -74.0060,
        search_area: mission.search_area || null,
        assigned_drones: mission.assigned_drones || []
      })
    }
  }, [mission])

  useEffect(() => {
    if (selectedArea) {
      setFormData(prev => ({ ...prev, search_area: selectedArea }))
    }
  }, [selectedArea])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Mission name is required'
    }

    if (!formData.search_target.trim()) {
      newErrors.search_target = 'Search target is required'
    }

    if (formData.search_altitude <= 0) {
      newErrors.search_altitude = 'Search altitude must be greater than 0'
    }

    if (formData.max_drones <= 0) {
      newErrors.max_drones = 'Number of drones must be greater than 0'
    }

    if (formData.overlap_percentage < 0 || formData.overlap_percentage > 100) {
      newErrors.overlap_percentage = 'Overlap percentage must be between 0 and 100'
    }

    if (formData.estimated_duration <= 0) {
      newErrors.estimated_duration = 'Estimated duration must be greater than 0'
    }

    if (!formData.search_area) {
      newErrors.search_area = 'Search area is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      await onSubmit(formData)
    } catch (error) {
      console.error('Form submission error:', error)
    }
  }

  const handleChange = (field: string, value: string | number | string[]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleDroneToggle = (droneId: string) => {
    const assignedDrones = formData.assigned_drones.includes(droneId)
      ? formData.assigned_drones.filter(id => id !== droneId)
      : [...formData.assigned_drones, droneId]
    
    handleChange('assigned_drones', assignedDrones)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Mission Name *
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter mission name"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="mission_type" className="block text-sm font-medium text-gray-700 mb-1">
            Mission Type
          </label>
          <select
            id="mission_type"
            value={formData.mission_type}
            onChange={(e) => handleChange('mission_type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="search">Search & Rescue</option>
            <option value="surveillance">Surveillance</option>
            <option value="mapping">Mapping</option>
            <option value="delivery">Delivery</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe the mission objectives..."
        />
      </div>

      <div>
        <label htmlFor="search_target" className="block text-sm font-medium text-gray-700 mb-1">
          Search Target *
        </label>
        <input
          type="text"
          id="search_target"
          value={formData.search_target}
          onChange={(e) => handleChange('search_target', e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.search_target ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., Missing person, Lost hiker, Emergency supplies"
        />
        {errors.search_target && <p className="mt-1 text-sm text-red-600">{errors.search_target}</p>}
      </div>

      {/* Mission Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
            Priority Level
          </label>
          <select
            id="priority"
            value={formData.priority}
            onChange={(e) => handleChange('priority', parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>Critical</option>
            <option value={2}>High</option>
            <option value={3}>Medium</option>
            <option value={4}>Low</option>
          </select>
        </div>

        <div>
          <label htmlFor="search_altitude" className="block text-sm font-medium text-gray-700 mb-1">
            Search Altitude (m) *
          </label>
          <input
            type="number"
            id="search_altitude"
            value={formData.search_altitude}
            onChange={(e) => handleChange('search_altitude', parseFloat(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.search_altitude ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="500"
            step="0.1"
          />
          {errors.search_altitude && <p className="mt-1 text-sm text-red-600">{errors.search_altitude}</p>}
        </div>

        <div>
          <label htmlFor="max_drones" className="block text-sm font-medium text-gray-700 mb-1">
            Max Drones *
          </label>
          <input
            type="number"
            id="max_drones"
            value={formData.max_drones}
            onChange={(e) => handleChange('max_drones', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.max_drones ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="10"
          />
          {errors.max_drones && <p className="mt-1 text-sm text-red-600">{errors.max_drones}</p>}
        </div>
      </div>

      {/* Search Pattern */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label htmlFor="search_pattern" className="block text-sm font-medium text-gray-700 mb-1">
            Search Pattern
          </label>
          <select
            id="search_pattern"
            value={formData.search_pattern}
            onChange={(e) => handleChange('search_pattern', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="lawnmower">Lawnmower</option>
            <option value="spiral">Spiral</option>
            <option value="grid">Grid</option>
            <option value="circular">Circular</option>
          </select>
        </div>

        <div>
          <label htmlFor="overlap_percentage" className="block text-sm font-medium text-gray-700 mb-1">
            Overlap Percentage (%)
          </label>
          <input
            type="number"
            id="overlap_percentage"
            value={formData.overlap_percentage}
            onChange={(e) => handleChange('overlap_percentage', parseFloat(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.overlap_percentage ? 'border-red-500' : 'border-gray-300'
            }`}
            min="0"
            max="100"
            step="0.1"
          />
          {errors.overlap_percentage && <p className="mt-1 text-sm text-red-600">{errors.overlap_percentage}</p>}
        </div>

        <div>
          <label htmlFor="estimated_duration" className="block text-sm font-medium text-gray-700 mb-1">
            Estimated Duration (min)
          </label>
          <input
            type="number"
            id="estimated_duration"
            value={formData.estimated_duration}
            onChange={(e) => handleChange('estimated_duration', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.estimated_duration ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="480"
          />
          {errors.estimated_duration && <p className="mt-1 text-sm text-red-600">{errors.estimated_duration}</p>}
        </div>
      </div>

      {/* Center Coordinates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="center_lat" className="block text-sm font-medium text-gray-700 mb-1">
            Center Latitude
          </label>
          <input
            type="number"
            id="center_lat"
            value={formData.center_lat}
            onChange={(e) => handleChange('center_lat', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            step="0.000001"
          />
        </div>

        <div>
          <label htmlFor="center_lng" className="block text-sm font-medium text-gray-700 mb-1">
            Center Longitude
          </label>
          <input
            type="number"
            id="center_lng"
            value={formData.center_lng}
            onChange={(e) => handleChange('center_lng', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            step="0.000001"
          />
        </div>
      </div>

      {/* Drone Assignment */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Assign Drones
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {drones.map(drone => (
            <label key={drone.drone_id} className="flex items-center space-x-2 p-2 border border-gray-300 rounded-md hover:bg-gray-50">
              <input
                type="checkbox"
                checked={formData.assigned_drones.includes(drone.drone_id)}
                onChange={() => handleDroneToggle(drone.drone_id)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {drone.name} ({drone.status})
              </span>
            </label>
          ))}
        </div>
        {formData.assigned_drones.length === 0 && (
          <p className="mt-1 text-sm text-gray-500">No drones assigned</p>
        )}
      </div>

      {/* Search Area Status */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search Area
        </label>
        {formData.search_area ? (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-green-800">Search area selected</span>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-yellow-800">Please select a search area on the map</span>
            </div>
          </div>
        )}
        {errors.search_area && <p className="mt-1 text-sm text-red-600">{errors.search_area}</p>}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6 border-t">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md"
        >
          {isLoading ? 'Saving...' : mission ? 'Update Mission' : 'Create Mission'}
        </button>
      </div>
    </form>
  )
}

export default MissionForm
