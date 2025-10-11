import React from 'react'
import AnalyticsDashboard from '../components/analytics/AnalyticsDashboard'

const AnalyticsManagement: React.FC = () => {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Management</h1>
        <p className="text-gray-600">Comprehensive system performance analysis and insights</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <AnalyticsDashboard />
      </div>
    </div>
  )
}

export default AnalyticsManagement
