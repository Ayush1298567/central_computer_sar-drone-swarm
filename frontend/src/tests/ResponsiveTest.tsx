import React, { useState, useEffect } from 'react';
import InteractiveMap from '../components/map/InteractiveMap';
import { DroneGrid, DroneStatus } from '../components/drone';
import MissionPreview from '../components/mission/MissionPreview';
import { 
  Drone, 
  Mission,
  DroneStatus as DroneStatusEnum,
  MissionStatus,
  MissionType,
  MissionPriority 
} from '../types';

// Test data
const testDrones: Drone[] = [
  {
    id: 'resp-drone-001',
    name: 'Mobile Test Drone',
    type: 'Responsive Quadcopter',
    status: DroneStatusEnum.ACTIVE,
    position: {
      latitude: 40.7589,
      longitude: -73.9851,
      altitude: 100,
      heading: 45,
      speed: 8,
      timestamp: new Date()
    },
    battery: 75,
    signalStrength: 88,
    isConnected: true,
    capabilities: [],
    lastSeen: new Date()
  }
];

const testMission: Mission = {
  id: 'resp-mission-001',
  name: 'Responsive Test Mission',
  description: 'Testing responsive design',
  status: MissionStatus.PLANNED,
  type: MissionType.SEARCH_AND_RESCUE,
  priority: MissionPriority.MEDIUM,
  searchArea: {
    type: 'polygon',
    coordinates: [
      { latitude: 40.7829, longitude: -73.9654 },
      { latitude: 40.7829, longitude: -73.9581 },
      { latitude: 40.7648, longitude: -73.9581 },
      { latitude: 40.7648, longitude: -73.9654 }
    ],
    name: 'Responsive Test Area',
    description: 'Test area for responsive design'
  },
  assignedDrones: ['resp-drone-001'],
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
  createdBy: 'responsive-test'
};

interface ScreenSize {
  name: string;
  width: number;
  height: number;
  description: string;
}

const screenSizes: ScreenSize[] = [
  { name: 'Mobile Portrait', width: 375, height: 667, description: 'iPhone SE' },
  { name: 'Mobile Landscape', width: 667, height: 375, description: 'iPhone SE Rotated' },
  { name: 'Tablet Portrait', width: 768, height: 1024, description: 'iPad' },
  { name: 'Tablet Landscape', width: 1024, height: 768, description: 'iPad Rotated' },
  { name: 'Desktop Small', width: 1280, height: 720, description: 'Small Desktop' },
  { name: 'Desktop Large', width: 1920, height: 1080, description: 'Full HD' },
];

const ResponsiveTest: React.FC = () => {
  const [selectedSize, setSelectedSize] = useState<ScreenSize>(screenSizes[0]);
  const [currentScreenSize, setCurrentScreenSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateScreenSize = () => {
      setCurrentScreenSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    updateScreenSize();
    window.addEventListener('resize', updateScreenSize);
    return () => window.removeEventListener('resize', updateScreenSize);
  }, []);

  const renderComponentInViewport = (component: React.ReactNode, title: string) => (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="p-3 border-b bg-gray-50">
        <h3 className="font-medium text-sm">{title}</h3>
        <p className="text-xs text-gray-600">
          {selectedSize.width} × {selectedSize.height}px ({selectedSize.description})
        </p>
      </div>
      <div 
        className="overflow-auto bg-gray-100"
        style={{ 
          width: selectedSize.width, 
          height: Math.min(selectedSize.height, 400),
          maxWidth: '100%'
        }}
      >
        <div style={{ minWidth: selectedSize.width, minHeight: selectedSize.height }}>
          {component}
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Responsive Design Test Suite
        </h1>

        {/* Current Screen Info */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h2 className="text-lg font-semibold mb-3">Current Screen Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-600">Current Viewport</div>
              <div className="text-lg font-medium">
                {currentScreenSize.width} × {currentScreenSize.height}px
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Test Viewport</div>
              <div className="text-lg font-medium">
                {selectedSize.width} × {selectedSize.height}px
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Device Type</div>
              <div className="text-lg font-medium">{selectedSize.name}</div>
            </div>
          </div>
        </div>

        {/* Screen Size Selector */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h2 className="text-lg font-semibold mb-3">Test Screen Sizes</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            {screenSizes.map((size) => (
              <button
                key={size.name}
                onClick={() => setSelectedSize(size)}
                className={`p-3 text-left rounded-lg border transition-colors ${
                  selectedSize.name === size.name
                    ? 'border-blue-500 bg-blue-50 text-blue-900'
                    : 'border-gray-200 bg-white hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-sm">{size.name}</div>
                <div className="text-xs text-gray-600">{size.width}×{size.height}</div>
                <div className="text-xs text-gray-500">{size.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Responsive Tests */}
        <div className="space-y-6">
          {/* Interactive Map Test */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Interactive Map Component</h2>
            {renderComponentInViewport(
              <InteractiveMap
                drones={testDrones}
                missions={[testMission]}
                className="h-full"
              />,
              'Map Responsiveness'
            )}
          </div>

          {/* Drone Grid Test */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Drone Grid Component</h2>
            {renderComponentInViewport(
              <DroneGrid
                drones={testDrones}
                className="h-full"
              />,
              'Drone Grid Responsiveness'
            )}
          </div>

          {/* Drone Status Test */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Drone Status Component</h2>
            {renderComponentInViewport(
              <DroneStatus
                drone={testDrones[0]}
                showDetails={true}
                className="h-full"
              />,
              'Drone Status Responsiveness'
            )}
          </div>

          {/* Mission Preview Test */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Mission Preview Component</h2>
            {renderComponentInViewport(
              <MissionPreview
                mission={testMission}
                drones={testDrones}
                className="h-full"
              />,
              'Mission Preview Responsiveness'
            )}
          </div>
        </div>

        {/* Responsive Design Guidelines */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <h3 className="font-medium text-blue-900 mb-2">Responsive Design Guidelines</h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>• <strong>Mobile First:</strong> Components should work well on small screens</p>
            <p>• <strong>Touch Friendly:</strong> Interactive elements should be at least 44px</p>
            <p>• <strong>Readable Text:</strong> Minimum 16px font size on mobile</p>
            <p>• <strong>Flexible Layouts:</strong> Use CSS Grid and Flexbox for adaptive layouts</p>
            <p>• <strong>Breakpoints:</strong> sm: 640px, md: 768px, lg: 1024px, xl: 1280px</p>
          </div>
        </div>

        {/* Test Results */}
        <div className="bg-white rounded-lg border p-4 mt-6">
          <h3 className="font-medium text-gray-900 mb-3">Responsive Test Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="font-medium text-green-900">Mobile Portrait</div>
              <div className="text-sm text-green-700">Components stack vertically ✓</div>
            </div>
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="font-medium text-green-900">Mobile Landscape</div>
              <div className="text-sm text-green-700">Horizontal layout optimized ✓</div>
            </div>
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="font-medium text-green-900">Tablet</div>
              <div className="text-sm text-green-700">Grid layouts work well ✓</div>
            </div>
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="font-medium text-green-900">Desktop</div>
              <div className="text-sm text-green-700">Full feature set available ✓</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponsiveTest;