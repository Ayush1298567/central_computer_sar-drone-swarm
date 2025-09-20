import React, { useState } from 'react';
import App from './App';
import ComponentValidation from './tests/ComponentValidation';
import APIIntegrationTest from './tests/APIIntegrationTest';
import ResponsiveTest from './tests/ResponsiveTest';

const TestApp: React.FC = () => {
  const [mode, setMode] = useState<'app' | 'validation' | 'api' | 'responsive'>('validation');

  return (
    <div>
      {/* Mode Switcher */}
      <div className="fixed top-4 right-4 z-50 bg-white border rounded-lg shadow-lg p-2">
        <div className="flex space-x-1">
          <button
            onClick={() => setMode('validation')}
            className={`px-2 py-1 rounded text-xs font-medium ${
              mode === 'validation'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Components
          </button>
          <button
            onClick={() => setMode('api')}
            className={`px-2 py-1 rounded text-xs font-medium ${
              mode === 'api'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            API
          </button>
          <button
            onClick={() => setMode('responsive')}
            className={`px-2 py-1 rounded text-xs font-medium ${
              mode === 'responsive'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Responsive
          </button>
          <button
            onClick={() => setMode('app')}
            className={`px-2 py-1 rounded text-xs font-medium ${
              mode === 'app'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Full App
          </button>
        </div>
      </div>

      {/* Render selected mode */}
      {mode === 'validation' && <ComponentValidation />}
      {mode === 'api' && <APIIntegrationTest />}
      {mode === 'responsive' && <ResponsiveTest />}
      {mode === 'app' && <App />}
    </div>
  );
};

export default TestApp;