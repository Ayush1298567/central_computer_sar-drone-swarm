import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Mission Commander Dashboard
              </h1>
              <p className="text-gray-600 mb-8">
                SAR Drone Control System - Foundation Setup Complete
              </p>
              <div className="space-y-2">
                <div className="text-green-600">✅ Backend structure created</div>
                <div className="text-green-600">✅ Frontend structure created</div>
                <div className="text-green-600">✅ Dependencies configured</div>
                <div className="text-yellow-600">🔄 Ready for Phase 2 implementation</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;