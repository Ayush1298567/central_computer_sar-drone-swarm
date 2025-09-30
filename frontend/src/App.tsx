import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import MissionPlanning from './pages/MissionPlanning'
import LiveMission from './pages/LiveMission'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-primary-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold">Mission Commander</h1>
              <span className="ml-2 text-sm bg-primary-700 px-2 py-1 rounded">
                SAR Drone Control System
              </span>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="/" className="hover:bg-primary-700 px-3 py-2 rounded-md">
                Dashboard
              </a>
              <a href="/planning" className="hover:bg-primary-700 px-3 py-2 rounded-md">
                Mission Planning
              </a>
              <a href="/missions" className="hover:bg-primary-700 px-3 py-2 rounded-md">
                Active Missions
              </a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/planning" element={<MissionPlanning />} />
          <Route path="/mission/:missionId" element={<LiveMission />} />
        </Routes>
      </main>
    </div>
  )
}

export default App