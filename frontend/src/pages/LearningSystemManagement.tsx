import React from 'react'
import LearningSystem from '../components/learningSystem/LearningSystem'

const LearningSystemManagement: React.FC = () => {
  const handleImprovementApplied = (improvement: any) => {
    console.log('Improvement applied:', improvement)
    // You can add additional logic here, such as showing a success message
    // or refreshing other components that might be affected
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Learning System Management</h1>
        <p className="text-gray-600">Monitor and manage AI-powered performance improvement systems</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <LearningSystem onImprovementApplied={handleImprovementApplied} />
      </div>
    </div>
  )
}

export default LearningSystemManagement
