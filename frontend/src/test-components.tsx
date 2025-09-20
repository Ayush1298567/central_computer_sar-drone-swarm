import React from 'react';
import ReactDOM from 'react-dom/client';
import { InteractiveMap } from './components/map/InteractiveMap';
import { ConversationalChat } from './components/mission/ConversationalChat';
import { MissionPreview } from './components/mission/MissionPreview';
import { DroneStatus } from './components/drone/DroneStatus';
import { DroneGrid } from './components/drone/DroneGrid';
import { DroneCommander } from './components/drone/DroneCommander';
import { VideoFeed } from './components/drone/VideoFeed';
import { Drone } from './types/drone';
import { Mission } from './types/mission';
import './index.css';

// Mock data for testing
const mockDrones: Drone[] = [
  {
    id: 'drone-1',
    name: 'Scout-01',
    model: 'DJI Matrice 300',
    status: 'active',
    battery_level: 85,
    signal_strength: 92,
    position: {
      latitude: 37.7749,
      longitude: -122.4194,
      altitude: 50,
    },
    last_seen: new Date().toISOString(),
    capabilities: {
      max_flight_time: 55,
      max_range: 15,
      camera_resolution: '4K',
      thermal_camera: true,
      night_vision: true,
      max_speed: 23,
      payload_capacity: 2.7,
    },
    telemetry: {
      timestamp: new Date().toISOString(),
      position: {
        latitude: 37.7749,
        longitude: -122.4194,
        altitude: 50,
      },
      velocity: { x: 2.1, y: 0.8, z: 0.0 },
      battery_level: 85,
      signal_strength: 92,
      temperature: 24,
      status: 'active',
      errors: [],
    },
  },
  {
    id: 'drone-2',
    name: 'Ranger-02',
    model: 'DJI Mavic 3',
    status: 'idle',
    battery_level: 67,
    signal_strength: 78,
    position: {
      latitude: 37.7849,
      longitude: -122.4094,
      altitude: 0,
    },
    last_seen: new Date().toISOString(),
    capabilities: {
      max_flight_time: 46,
      max_range: 15,
      camera_resolution: '5.1K',
      thermal_camera: false,
      night_vision: false,
      max_speed: 21,
      payload_capacity: 0.9,
    },
    telemetry: {
      timestamp: new Date().toISOString(),
      position: {
        latitude: 37.7849,
        longitude: -122.4094,
        altitude: 0,
      },
      velocity: { x: 0, y: 0, z: 0 },
      battery_level: 67,
      signal_strength: 78,
      temperature: 22,
      status: 'idle',
      errors: [],
    },
  },
];

const mockMission: Mission = {
  id: 'mission-1',
  name: 'Search Operation Alpha',
  description: 'Missing hiker in Golden Gate Park area',
  status: 'planning',
  priority: 'high',
  search_area: {
    type: 'Polygon',
    coordinates: [[
      [-122.4194, 37.7749],
      [-122.4094, 37.7749],
      [-122.4094, 37.7849],
      [-122.4194, 37.7849],
      [-122.4194, 37.7749],
    ]],
  },
  assigned_drones: ['drone-1', 'drone-2'],
  created_at: new Date().toISOString(),
  progress_percentage: 35,
  estimated_duration: 120,
  weather_conditions: {
    wind_speed: 8,
    visibility: 15,
    temperature: 18,
  },
};

const TestApp: React.FC = () => {
  const [selectedComponent, setSelectedComponent] = React.useState<string>('map');

  const renderComponent = () => {
    switch (selectedComponent) {
      case 'map':
        return (
          <InteractiveMap
            drones={mockDrones}
            missions={[mockMission]}
            drawingMode={false}
            className="h-96"
          />
        );
      
      case 'chat':
        return (
          <ConversationalChat
            className="h-96"
          />
        );
      
      case 'mission-preview':
        return (
          <MissionPreview
            mission={mockMission}
            assignedDrones={mockDrones}
          />
        );
      
      case 'drone-status':
        return (
          <DroneStatus
            drone={mockDrones[0]}
            showDetails={true}
          />
        );
      
      case 'drone-grid':
        return (
          <DroneGrid
            drones={mockDrones}
          />
        );
      
      case 'drone-commander':
        return (
          <DroneCommander
            drone={mockDrones[0]}
          />
        );
      
      case 'video-feed':
        return (
          <VideoFeed
            drone={mockDrones[0]}
            className="w-full max-w-2xl"
          />
        );
      
      default:
        return <div>Select a component to test</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          SAR Drone Components Test
        </h1>
        
        {/* Component Selector */}
        <div className="mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Component to Test:
          </label>
          <select
            value={selectedComponent}
            onChange={(e) => setSelectedComponent(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="map">Interactive Map</option>
            <option value="chat">Conversational Chat</option>
            <option value="mission-preview">Mission Preview</option>
            <option value="drone-status">Drone Status</option>
            <option value="drone-grid">Drone Grid</option>
            <option value="drone-commander">Drone Commander</option>
            <option value="video-feed">Video Feed</option>
          </select>
        </div>

        {/* Component Display */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 capitalize">
            {selectedComponent.replace('-', ' ')} Component
          </h2>
          {renderComponent()}
        </div>
      </div>
    </div>
  );
};

// Mount the test app
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TestApp />
  </React.StrictMode>,
);