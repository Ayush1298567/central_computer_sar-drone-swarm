import React from 'react';

const MissionPlanning: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mission Planning</h1>
        <p className="text-gray-600">AI-powered conversational mission planning interface</p>
      </div>

      <div className="bg-white p-8 rounded-lg border border-gray-200">
        <div className="text-center">
          <h2 className="text-lg font-medium text-gray-900 mb-2">Mission Planning Interface</h2>
          <p className="text-gray-500 mb-6">
            This interface will allow you to have a conversation with the AI to plan your SAR mission.
          </p>
          <div className="bg-gray-50 p-6 rounded-lg">
            <p className="text-sm text-gray-600">
              The conversational mission planner will ask questions about your search requirements
              and automatically generate an optimal mission plan with drone assignments and flight paths.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionPlanning;