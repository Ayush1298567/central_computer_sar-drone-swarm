import React, { useState, useEffect } from 'react'
import { Drone, DroneCreate, DroneUpdate } from '../../types'

interface DroneFormProps {
  drone?: Drone
  onSubmit: (data: DroneCreate | DroneUpdate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

const DroneForm: React.FC<DroneFormProps> = ({
  drone,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const [formData, setFormData] = useState({
    name: '',
    model: '',
    max_flight_time: 30,
    max_altitude: 120,
    max_speed: 15,
    battery_level: 100,
    position_lat: 40.7128,
    position_lng: -74.0060,
    position_alt: 0
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (drone) {
      setFormData({
        name: drone.name || '',
        model: drone.model || '',
        max_flight_time: drone.max_flight_time || 30,
        max_altitude: drone.max_altitude || 120,
        max_speed: drone.max_speed || 15,
        battery_level: drone.battery_level || 100,
        position_lat: drone.current_position?.lat || 40.7128,
        position_lng: drone.current_position?.lng || -74.0060,
        position_alt: drone.current_position?.alt || 0
      })
    }
  }, [drone])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!formData.model.trim()) {
      newErrors.model = 'Model is required'
    }

    if (formData.max_flight_time <= 0) {
      newErrors.max_flight_time = 'Flight time must be greater than 0'
    }

    if (formData.max_altitude <= 0) {
      newErrors.max_altitude = 'Max altitude must be greater than 0'
    }

    if (formData.max_speed <= 0) {
      newErrors.max_speed = 'Max speed must be greater than 0'
    }

    if (formData.battery_level < 0 || formData.battery_level > 100) {
      newErrors.battery_level = 'Battery level must be between 0 and 100'
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

  const handleChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Drone Name *
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter drone name"
          />
          {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
        </div>

        <div>
          <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-1">
            Model *
          </label>
          <input
            type="text"
            id="model"
            value={formData.model}
            onChange={(e) => handleChange('model', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.model ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="e.g., DJI Matrice 300"
          />
          {errors.model && <p className="mt-1 text-sm text-red-600">{errors.model}</p>}
        </div>
      </div>

      {/* Specifications */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label htmlFor="max_flight_time" className="block text-sm font-medium text-gray-700 mb-1">
            Max Flight Time (minutes) *
          </label>
          <input
            type="number"
            id="max_flight_time"
            value={formData.max_flight_time}
            onChange={(e) => handleChange('max_flight_time', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.max_flight_time ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="120"
          />
          {errors.max_flight_time && <p className="mt-1 text-sm text-red-600">{errors.max_flight_time}</p>}
        </div>

        <div>
          <label htmlFor="max_altitude" className="block text-sm font-medium text-gray-700 mb-1">
            Max Altitude (meters) *
          </label>
          <input
            type="number"
            id="max_altitude"
            value={formData.max_altitude}
            onChange={(e) => handleChange('max_altitude', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.max_altitude ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="500"
          />
          {errors.max_altitude && <p className="mt-1 text-sm text-red-600">{errors.max_altitude}</p>}
        </div>

        <div>
          <label htmlFor="max_speed" className="block text-sm font-medium text-gray-700 mb-1">
            Max Speed (m/s) *
          </label>
          <input
            type="number"
            id="max_speed"
            value={formData.max_speed}
            onChange={(e) => handleChange('max_speed', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.max_speed ? 'border-red-500' : 'border-gray-300'
            }`}
            min="1"
            max="50"
          />
          {errors.max_speed && <p className="mt-1 text-sm text-red-600">{errors.max_speed}</p>}
        </div>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div>
          <label htmlFor="battery_level" className="block text-sm font-medium text-gray-700 mb-1">
            Battery Level (%)
          </label>
          <input
            type="number"
            id="battery_level"
            value={formData.battery_level}
            onChange={(e) => handleChange('battery_level', parseInt(e.target.value) || 0)}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.battery_level ? 'border-red-500' : 'border-gray-300'
            }`}
            min="0"
            max="100"
          />
          {errors.battery_level && <p className="mt-1 text-sm text-red-600">{errors.battery_level}</p>}
        </div>

        <div>
          <label htmlFor="position_lat" className="block text-sm font-medium text-gray-700 mb-1">
            Latitude
          </label>
          <input
            type="number"
            id="position_lat"
            value={formData.position_lat}
            onChange={(e) => handleChange('position_lat', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            step="0.000001"
          />
        </div>

        <div>
          <label htmlFor="position_lng" className="block text-sm font-medium text-gray-700 mb-1">
            Longitude
          </label>
          <input
            type="number"
            id="position_lng"
            value={formData.position_lng}
            onChange={(e) => handleChange('position_lng', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            step="0.000001"
          />
        </div>

        <div>
          <label htmlFor="position_alt" className="block text-sm font-medium text-gray-700 mb-1">
            Altitude (m)
          </label>
          <input
            type="number"
            id="position_alt"
            value={formData.position_alt}
            onChange={(e) => handleChange('position_alt', parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
          />
        </div>
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
          {isLoading ? 'Saving...' : drone ? 'Update Drone' : 'Create Drone'}
        </button>
      </div>
    </form>
  )
}

export default DroneForm
