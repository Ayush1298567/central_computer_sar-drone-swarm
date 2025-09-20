import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { webSocketService } from '../services/websocket';

interface APITestResult {
  endpoint: string;
  method: string;
  status: 'pending' | 'success' | 'error' | 'skipped';
  responseTime?: number;
  error?: string;
  response?: any;
}

const APIIntegrationTest: React.FC = () => {
  const [testResults, setTestResults] = useState<APITestResult[]>([]);
  const [currentTest, setCurrentTest] = useState<string>('Ready to start testing');
  const [isRunning, setIsRunning] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Initialize WebSocket connection test
  useEffect(() => {
    const checkWebSocketConnection = () => {
      const connected = webSocketService.isConnected();
      setWsConnected(connected);
    };

    // Check immediately and then every 5 seconds
    checkWebSocketConnection();
    const interval = setInterval(checkWebSocketConnection, 5000);

    return () => clearInterval(interval);
  }, []);

  const runAPITests = async () => {
    setIsRunning(true);
    setTestResults([]);
    const results: APITestResult[] = [];

    // Test 1: Drone Discovery
    setCurrentTest('Testing drone discovery...');
    const droneDiscoveryTest: APITestResult = {
      endpoint: '/api/v1/drones/discover',
      method: 'POST',
      status: 'pending'
    };
    results.push(droneDiscoveryTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      await apiService.discoverDrones();
      droneDiscoveryTest.status = 'success';
      droneDiscoveryTest.responseTime = Date.now() - startTime;
    } catch (error) {
      droneDiscoveryTest.status = 'error';
      droneDiscoveryTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    // Test 2: Get Drones
    setCurrentTest('Testing get drones...');
    const getDronesTest: APITestResult = {
      endpoint: '/api/v1/drones/',
      method: 'GET',
      status: 'pending'
    };
    results.push(getDronesTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      const drones = await apiService.getDrones();
      getDronesTest.status = 'success';
      getDronesTest.responseTime = Date.now() - startTime;
      getDronesTest.response = `Found ${drones.length} drones`;
    } catch (error) {
      getDronesTest.status = 'error';
      getDronesTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    // Test 3: Get Missions
    setCurrentTest('Testing get missions...');
    const getMissionsTest: APITestResult = {
      endpoint: '/api/v1/missions/',
      method: 'GET',
      status: 'pending'
    };
    results.push(getMissionsTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      const missions = await apiService.getMissions();
      getMissionsTest.status = 'success';
      getMissionsTest.responseTime = Date.now() - startTime;
      getMissionsTest.response = `Found ${missions.length} missions`;
    } catch (error) {
      getMissionsTest.status = 'error';
      getMissionsTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    // Test 4: Create Chat Session
    setCurrentTest('Testing create chat session...');
    const createChatTest: APITestResult = {
      endpoint: '/api/v1/chat/sessions',
      method: 'POST',
      status: 'pending'
    };
    results.push(createChatTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      const session = await apiService.createChatSession('Test Session');
      createChatTest.status = 'success';
      createChatTest.responseTime = Date.now() - startTime;
      createChatTest.response = `Created session: ${session.id}`;
    } catch (error) {
      createChatTest.status = 'error';
      createChatTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    // Test 5: Get Chat Sessions
    setCurrentTest('Testing get chat sessions...');
    const getChatSessionsTest: APITestResult = {
      endpoint: '/api/v1/chat/sessions',
      method: 'GET',
      status: 'pending'
    };
    results.push(getChatSessionsTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      const sessions = await apiService.getChatSessions();
      getChatSessionsTest.status = 'success';
      getChatSessionsTest.responseTime = Date.now() - startTime;
      getChatSessionsTest.response = `Found ${sessions.length} chat sessions`;
    } catch (error) {
      getChatSessionsTest.status = 'error';
      getChatSessionsTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    // Test 6: WebSocket Connection Test
    setCurrentTest('Testing WebSocket connection...');
    const wsTest: APITestResult = {
      endpoint: 'WebSocket Connection',
      method: 'WS',
      status: 'pending'
    };
    results.push(wsTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      
      if (webSocketService.isConnected()) {
        wsTest.status = 'success';
        wsTest.responseTime = Date.now() - startTime;
        wsTest.response = 'WebSocket connection established';
      } else {
        // Try to reconnect
        webSocketService.reconnect();
        
        // Wait a bit and check again
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (webSocketService.isConnected()) {
          wsTest.status = 'success';
          wsTest.responseTime = Date.now() - startTime;
          wsTest.response = 'WebSocket reconnected successfully';
        } else {
          wsTest.status = 'error';
          wsTest.error = 'WebSocket connection failed';
        }
      }
    } catch (error) {
      wsTest.status = 'error';
      wsTest.error = error instanceof Error ? error.message : 'WebSocket connection error';
    }
    setTestResults([...results]);

    // Test 7: WebSocket Connections Info
    setCurrentTest('Testing WebSocket connections info...');
    const wsInfoTest: APITestResult = {
      endpoint: '/api/v1/ws/connections',
      method: 'GET',
      status: 'pending'
    };
    results.push(wsInfoTest);
    setTestResults([...results]);

    try {
      const startTime = Date.now();
      const connections = await apiService.getWebSocketConnections();
      wsInfoTest.status = 'success';
      wsInfoTest.responseTime = Date.now() - startTime;
      wsInfoTest.response = `Active connections: ${JSON.stringify(connections)}`;
    } catch (error) {
      wsInfoTest.status = 'error';
      wsInfoTest.error = error instanceof Error ? error.message : 'Unknown error';
    }
    setTestResults([...results]);

    setCurrentTest('API testing completed!');
    setIsRunning(false);
  };

  const renderTestResult = (result: APITestResult, index: number) => {
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'success': return 'text-green-600 bg-green-50 border-green-200';
        case 'error': return 'text-red-600 bg-red-50 border-red-200';
        case 'pending': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
        default: return 'text-gray-600 bg-gray-50 border-gray-200';
      }
    };

    const getStatusIcon = (status: string) => {
      switch (status) {
        case 'success': return '✅';
        case 'error': return '❌';
        case 'pending': return '⏳';
        default: return '⚪';
      }
    };

    return (
      <div key={index} className={`p-3 border rounded-lg ${getStatusColor(result.status)}`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span>{getStatusIcon(result.status)}</span>
            <span className="font-medium">{result.method}</span>
            <span className="text-sm">{result.endpoint}</span>
          </div>
          {result.responseTime && (
            <span className="text-xs bg-white px-2 py-1 rounded">
              {result.responseTime}ms
            </span>
          )}
        </div>
        
        {result.response && (
          <div className="text-sm mb-1">
            <strong>Response:</strong> {result.response}
          </div>
        )}
        
        {result.error && (
          <div className="text-sm">
            <strong>Error:</strong> {result.error}
          </div>
        )}
      </div>
    );
  };

  const getTestSummary = () => {
    const total = testResults.length;
    const success = testResults.filter(r => r.status === 'success').length;
    const error = testResults.filter(r => r.status === 'error').length;
    const pending = testResults.filter(r => r.status === 'pending').length;
    
    return { total, success, error, pending };
  };

  const summary = getTestSummary();

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          API Integration Test Suite
        </h1>

        {/* WebSocket Status */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h2 className="text-lg font-semibold mb-3">WebSocket Status</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className={wsConnected ? 'text-green-700' : 'text-red-700'}>
              {wsConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Test Controls */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Test Controls</h2>
              <p className="text-sm text-gray-600">{currentTest}</p>
            </div>
            <button
              onClick={runAPITests}
              disabled={isRunning}
              className={`px-4 py-2 rounded-lg font-medium ${
                isRunning
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {isRunning ? 'Running Tests...' : 'Run API Tests'}
            </button>
          </div>
        </div>

        {/* Test Summary */}
        {testResults.length > 0 && (
          <div className="bg-white rounded-lg border p-4 mb-6">
            <h2 className="text-lg font-semibold mb-3">Test Summary</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{summary.total}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{summary.success}</div>
                <div className="text-sm text-gray-600">Success</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{summary.error}</div>
                <div className="text-sm text-gray-600">Error</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{summary.pending}</div>
                <div className="text-sm text-gray-600">Pending</div>
              </div>
            </div>
          </div>
        )}

        {/* Test Results */}
        {testResults.length > 0 && (
          <div className="bg-white rounded-lg border p-4">
            <h2 className="text-lg font-semibold mb-4">Test Results</h2>
            <div className="space-y-3">
              {testResults.map((result, index) => renderTestResult(result, index))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {testResults.length === 0 && !isRunning && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">Testing Instructions</h3>
            <div className="text-sm text-blue-800 space-y-2">
              <p>• This test suite will validate all major API endpoints</p>
              <p>• WebSocket connection status is monitored in real-time</p>
              <p>• Tests will run against the configured API endpoint</p>
              <p>• Some tests may fail if the backend is not running</p>
              <p>• Click "Run API Tests" to start the validation</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default APIIntegrationTest;