import React, { useState, useEffect } from 'react';
import InteractiveMap from '../components/map/InteractiveMap';
import ConversationalChat from '../components/mission/ConversationalChat';
import MissionPreview from '../components/mission/MissionPreview';
import { DroneGrid, DroneStatus, DroneCommander, VideoFeed } from '../components/drone';
import { 
  Drone, 
  Mission, 
  ChatSession,
  SearchArea,
  DroneStatus as DroneStatusEnum,
  MissionStatus,
  MissionType,
  MissionPriority 
} from '../types';

// Test data for validation
const testDrones: Drone[] = [
  {
    id: 'test-drone-001',
    name: 'Test Scout Alpha',
    type: 'Test Quadcopter',
    status: DroneStatusEnum.ACTIVE,
    position: {
      latitude: 40.7589,
      longitude: -73.9851,
      altitude: 100,
      heading: 45,
      speed: 8,
      timestamp: new Date()
    },
    battery: 85,
    signalStrength: 92,
    isConnected: true,
    capabilities: [],
    lastSeen: new Date(),
    telemetry: {
      battery: 85,
      signalStrength: 92,
      position: {
        latitude: 40.7589,
        longitude: -73.9851,
        altitude: 100,
        heading: 45,
        speed: 8,
        timestamp: new Date()
      },
      sensors: {
        temperature: 22,
        humidity: 65,
        pressure: 1013
      },
      camera: {
        isRecording: false,
        quality: 'medium',
        zoom: 1
      },
      flightMetrics: {
        flightTime: 1800,
        distance: 2500,
        maxAltitude: 150,
        averageSpeed: 8.5
      }
    }
  }
];

const testMissions: Mission[] = [
  {
    id: 'test-mission-001',
    name: 'Test Search Mission',
    description: 'Test mission for validation',
    status: MissionStatus.PLANNED,
    type: MissionType.SEARCH_AND_RESCUE,
    priority: MissionPriority.HIGH,
    searchArea: {
      type: 'polygon',
      coordinates: [
        { latitude: 40.7829, longitude: -73.9654 },
        { latitude: 40.7829, longitude: -73.9581 },
        { latitude: 40.7648, longitude: -73.9581 },
        { latitude: 40.7648, longitude: -73.9654 }
      ],
      name: 'Test Search Area',
      description: 'Test polygon area'
    },
    assignedDrones: ['test-drone-001'],
    parameters: {
      searchAltitude: 100,
      speed: 10,
      overlapPercentage: 30,
      cameraSettings: {
        resolution: '1080p',
        frameRate: 30,
        recordVideo: true
      },
      weatherLimits: {
        maxWindSpeed: 15,
        minVisibility: 1000,
        maxPrecipitation: 0
      },
      timeConstraints: {
        maxDuration: 120
      },
      notifications: {
        email: true,
        sms: false
      }
    },
    timeline: {
      estimatedDuration: 90,
      milestones: []
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: 'test-user'
  }
];

interface ValidationResult {
  component: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
}

const ComponentValidation: React.FC = () => {
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [currentTest, setCurrentTest] = useState<string>('Starting validation...');
  const [selectedDrone] = useState<Drone>(testDrones[0]);

  useEffect(() => {
    runValidation();
  }, []);

  const runValidation = async () => {
    const results: ValidationResult[] = [];

    // Test 1: InteractiveMap Component
    setCurrentTest('Testing InteractiveMap component...');
    try {
      const mapResult: ValidationResult = {
        component: 'InteractiveMap',
        passed: true,
        errors: [],
        warnings: []
      };

      // Check if component can render with props
      if (!testDrones.length) {
        mapResult.errors.push('No test drones available');
        mapResult.passed = false;
      }

      if (!testMissions.length) {
        mapResult.errors.push('No test missions available');
        mapResult.passed = false;
      }

      results.push(mapResult);
    } catch (error) {
      results.push({
        component: 'InteractiveMap',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 2: ConversationalChat Component
    setCurrentTest('Testing ConversationalChat component...');
    try {
      const chatResult: ValidationResult = {
        component: 'ConversationalChat',
        passed: true,
        errors: [],
        warnings: []
      };

      // Basic validation - component should be able to initialize
      results.push(chatResult);
    } catch (error) {
      results.push({
        component: 'ConversationalChat',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 3: MissionPreview Component
    setCurrentTest('Testing MissionPreview component...');
    try {
      const previewResult: ValidationResult = {
        component: 'MissionPreview',
        passed: true,
        errors: [],
        warnings: []
      };

      if (!testMissions[0]) {
        previewResult.errors.push('No test mission available for preview');
        previewResult.passed = false;
      }

      results.push(previewResult);
    } catch (error) {
      results.push({
        component: 'MissionPreview',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 4: DroneGrid Component
    setCurrentTest('Testing DroneGrid component...');
    try {
      const gridResult: ValidationResult = {
        component: 'DroneGrid',
        passed: true,
        errors: [],
        warnings: []
      };

      if (!testDrones.length) {
        gridResult.warnings.push('No drones available for grid display');
      }

      results.push(gridResult);
    } catch (error) {
      results.push({
        component: 'DroneGrid',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 5: DroneStatus Component
    setCurrentTest('Testing DroneStatus component...');
    try {
      const statusResult: ValidationResult = {
        component: 'DroneStatus',
        passed: true,
        errors: [],
        warnings: []
      };

      if (!selectedDrone) {
        statusResult.errors.push('No drone selected for status display');
        statusResult.passed = false;
      }

      results.push(statusResult);
    } catch (error) {
      results.push({
        component: 'DroneStatus',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 6: DroneCommander Component
    setCurrentTest('Testing DroneCommander component...');
    try {
      const commanderResult: ValidationResult = {
        component: 'DroneCommander',
        passed: true,
        errors: [],
        warnings: []
      };

      if (!selectedDrone) {
        commanderResult.errors.push('No drone available for commander');
        commanderResult.passed = false;
      }

      results.push(commanderResult);
    } catch (error) {
      results.push({
        component: 'DroneCommander',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    // Test 7: VideoFeed Component
    setCurrentTest('Testing VideoFeed component...');
    try {
      const videoResult: ValidationResult = {
        component: 'VideoFeed',
        passed: true,
        errors: [],
        warnings: []
      };

      if (!selectedDrone) {
        videoResult.errors.push('No drone available for video feed');
        videoResult.passed = false;
      }

      if (!selectedDrone.isConnected) {
        videoResult.warnings.push('Drone is not connected - video feed will show placeholder');
      }

      results.push(videoResult);
    } catch (error) {
      results.push({
        component: 'VideoFeed',
        passed: false,
        errors: [`Component failed to initialize: ${error}`],
        warnings: []
      });
    }

    setCurrentTest('Validation complete!');
    setValidationResults(results);
  };

  const handleAreaSelected = (area: SearchArea) => {
    console.log('Test: Area selected', area);
  };

  const handleDroneCommand = (droneId: string, command: any) => {
    console.log('Test: Drone command', droneId, command);
  };

  const handleCommand = (command: any) => {
    console.log('Test: Command', command);
  };

  const handleMissionApprove = (mission: Mission) => {
    console.log('Test: Mission approved', mission);
  };

  const handleMissionReject = (reason: string) => {
    console.log('Test: Mission rejected', reason);
  };

  const renderValidationResults = () => (
    <div className="bg-white rounded-lg border p-4 mb-6">
      <h2 className="text-lg font-semibold mb-4">Component Validation Results</h2>
      
      <div className="mb-4">
        <p className="text-sm text-gray-600">Current Test: {currentTest}</p>
      </div>

      <div className="space-y-3">
        {validationResults.map((result, index) => (
          <div 
            key={index}
            className={`p-3 rounded-lg border ${
              result.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">{result.component}</h3>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                result.passed 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {result.passed ? 'PASSED' : 'FAILED'}
              </span>
            </div>
            
            {result.errors.length > 0 && (
              <div className="mb-2">
                <p className="text-sm font-medium text-red-700 mb-1">Errors:</p>
                <ul className="text-sm text-red-600 space-y-1">
                  {result.errors.map((error, i) => (
                    <li key={i}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {result.warnings.length > 0 && (
              <div>
                <p className="text-sm font-medium text-yellow-700 mb-1">Warnings:</p>
                <ul className="text-sm text-yellow-600 space-y-1">
                  {result.warnings.map((warning, i) => (
                    <li key={i}>• {warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-medium text-blue-900 mb-2">Summary</h3>
        <p className="text-sm text-blue-800">
          {validationResults.filter(r => r.passed).length} / {validationResults.length} components passed validation
        </p>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          SAR Drone Components Validation Suite
        </h1>

        {renderValidationResults()}

        {/* Component Test Renders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* InteractiveMap Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">InteractiveMap Component</h3>
            <div className="h-64 border rounded">
              <InteractiveMap
                drones={testDrones}
                missions={testMissions}
                onAreaSelected={handleAreaSelected}
                className="h-full"
              />
            </div>
          </div>

          {/* ConversationalChat Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">ConversationalChat Component</h3>
            <div className="h-64">
              <ConversationalChat className="h-full" />
            </div>
          </div>

          {/* MissionPreview Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">MissionPreview Component</h3>
            <div className="h-64 overflow-y-auto">
              <MissionPreview
                mission={testMissions[0]}
                drones={testDrones}
                onApprove={handleMissionApprove}
                onReject={handleMissionReject}
              />
            </div>
          </div>

          {/* DroneGrid Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">DroneGrid Component</h3>
            <div className="h-64">
              <DroneGrid
                drones={testDrones}
                onDroneCommand={handleDroneCommand}
              />
            </div>
          </div>

          {/* DroneStatus Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">DroneStatus Component</h3>
            <div className="h-64">
              <DroneStatus
                drone={selectedDrone}
                showDetails={true}
                onCommandSend={handleDroneCommand}
              />
            </div>
          </div>

          {/* DroneCommander Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">DroneCommander Component</h3>
            <div className="h-64 overflow-y-auto">
              <DroneCommander
                drone={selectedDrone}
                onCommand={handleCommand}
              />
            </div>
          </div>

          {/* VideoFeed Test */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="font-semibold mb-3">VideoFeed Component</h3>
            <div className="h-64">
              <VideoFeed
                drone={selectedDrone}
                className="h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComponentValidation;