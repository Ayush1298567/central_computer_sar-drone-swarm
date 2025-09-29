import React, { useState } from 'react'

const MissionPlanning: React.FC = () => {
  const [formData, setFormData] = useState({
    missionName: '',
    searchArea: '',
    droneCount: 1,
    priority: 'medium',
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement mission creation
    console.log('Creating mission:', formData)
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Plan New Mission</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="missionName" className="block text-sm font-medium text-gray-700">
              Mission Name
            </label>
            <input
              type="text"
              id="missionName"
              name="missionName"
              value={formData.missionName}
              onChange={handleInputChange}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>

          <div>
            <label htmlFor="searchArea" className="block text-sm font-medium text-gray-700">
              Search Area (coordinates)
            </label>
            <input
              type="text"
              id="searchArea"
              name="searchArea"
              value={formData.searchArea}
              onChange={handleInputChange}
              placeholder="e.g., 40.7128,-74.0060,41.0000,-73.0000"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            />
          </div>

          <div>
            <label htmlFor="droneCount" className="block text-sm font-medium text-gray-700">
              Number of Drones
            </label>
            <select
              id="droneCount"
              name="droneCount"
              value={formData.droneCount}
              onChange={handleInputChange}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              {[1, 2, 3, 4, 5].map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
              Priority Level
            </label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleInputChange}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Create Mission
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default MissionPlanning