import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { MapPin, Clock, Users, Settings } from 'lucide-react'

const MissionPlanning: React.FC = () => {
  const [selectedStep, setSelectedStep] = useState(1)

  const steps = [
    { id: 1, name: 'Mission Details', completed: true },
    { id: 2, name: 'Area Selection', completed: false },
    { id: 3, name: 'Drone Assignment', completed: false },
    { id: 4, name: 'Weather Check', completed: false },
    { id: 5, name: 'Review & Launch', completed: false },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Mission Planning</h1>
        <Button>
          Save Draft
        </Button>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Mission Planning Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => setSelectedStep(step.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    selectedStep === step.id
                      ? 'bg-blue-100 text-blue-700'
                      : step.completed
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    step.completed ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
                  }`}>
                    {step.completed ? '✓' : step.id}
                  </div>
                  <span className="whitespace-nowrap">{step.name}</span>
                </button>
                {index < steps.length - 1 && (
                  <div className="w-8 h-0.5 bg-gray-300"></div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>
            {steps.find(s => s.id === selectedStep)?.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedStep === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mission Name
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter mission name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter mission description"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Estimated Duration (minutes)
                  </label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="120"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Area Size (km²)
                  </label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="10"
                  />
                </div>
              </div>
            </div>
          )}

          {selectedStep === 2 && (
            <div className="space-y-4">
              <div className="bg-gray-100 h-64 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Map interface for area selection</p>
                  <p className="text-sm text-gray-400">Click to select search area on map</p>
                </div>
              </div>
              <div className="flex justify-between">
                <Button variant="outline">Import KML</Button>
                <Button>Draw Area</Button>
              </div>
            </div>
          )}

          {selectedStep === 3 && (
            <div className="space-y-4">
              <div className="text-center py-8">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Drone assignment interface</p>
                <p className="text-sm text-gray-400">Select available drones for this mission</p>
              </div>
            </div>
          )}

          {selectedStep === 4 && (
            <div className="space-y-4">
              <div className="text-center py-8">
                <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Weather conditions check</p>
                <p className="text-sm text-gray-400">Verifying weather conditions for safe flight</p>
              </div>
            </div>
          )}

          {selectedStep === 5 && (
            <div className="space-y-4">
              <div className="text-center py-8">
                <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Review mission parameters</p>
                <p className="text-sm text-gray-400">Final review before launch</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          disabled={selectedStep === 1}
          onClick={() => setSelectedStep(prev => Math.max(1, prev - 1))}
        >
          Previous
        </Button>
        <Button
          onClick={() => setSelectedStep(prev => Math.min(steps.length, prev + 1))}
        >
          {selectedStep === steps.length ? 'Launch Mission' : 'Next'}
        </Button>
      </div>
    </div>
  )
}

export default MissionPlanning