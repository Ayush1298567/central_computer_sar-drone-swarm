import React, { useState, useEffect } from 'react';
import InteractiveMap from './components/map/InteractiveMap';
import ConversationalChat from './components/mission/ConversationalChat';
import MissionPreview from './components/mission/MissionPreview';
import { DroneGrid, DroneStatus, DroneCommander, VideoFeed } from './components/drone';
import { useDrones } from './hooks/useDrones';
import { useWebSocket } from './hooks/useWebSocket';
import { 
  Drone, 
  Mission, 
  ChatSession, 
  SearchArea, 
  MapViewport,
  DroneStatus as DroneStatusEnum,
  MissionStatus,
  MissionType,
  MissionPriority 
} from './types';

// Mock data for testing
const mockDrones: Drone[] = [
  {
    id: 'drone-001',
    name: 'Scout Alpha',
    type: 'Quadcopter',
    status: DroneStatusEnum.IDLE,
    position: {
      latitude: 40.7589,
      longitude: -73.9851,
      altitude: 100,
      heading: 45,
      speed: 0,
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
        speed: 0,
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
  },
  {
    id: 'drone-002',
    name: 'Scout Beta',
    type: 'Hexacopter',
    status: DroneStatusEnum.ACTIVE,
    position: {
      latitude: 40.7614,
      longitude: -73.9776,
      altitude: 120,
      heading: 180,
      speed: 12,
      timestamp: new Date()
    },
    battery: 67,
    signalStrength: 78,
    isConnected: true,
    capabilities: [],
    lastSeen: new Date()
  },
  {
    id: 'drone-003',
    name: 'Scout Gamma',
    type: 'Fixed Wing',
    status: DroneStatusEnum.RETURNING,
    position: {
      latitude: 40.7505,
      longitude: -73.9934,
      altitude: 200,
      heading: 270,
      speed: 25,
      timestamp: new Date()
    },
    battery: 34,
    signalStrength: 45,
    isConnected: true,
    capabilities: [],
    lastSeen: new Date()
  },
  {
    id: 'drone-004',
    name: 'Scout Delta',
    type: 'Quadcopter',
    status: DroneStatusEnum.OFFLINE,
    battery: 0,
    signalStrength: 0,
    isConnected: false,
    capabilities: [],
    lastSeen: new Date(Date.now() - 300000) // 5 minutes ago
  }
];

const mockMissions: Mission[] = [
  {
    id: 'mission-001',
    name: 'Central Park Search',
    description: 'Search and rescue operation in Central Park area',
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
      name: 'Central Park Area',
      description: 'Central Park search zone'
    },
    assignedDrones: ['drone-001', 'drone-002'],
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
    createdBy: 'operator-001'
  }
];

function App() {
  const [activeView, setActiveView] = useState<'dashboard' | 'map' | 'chat' | 'drones'>('dashboard');
  const [selectedDrone, setSelectedDrone] = useState<Drone | null>(null);
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null);
  const [chatSession, setChatSession] = useState<ChatSession | null>(null);
  const [mapViewport, setMapViewport] = useState<MapViewport>({
    center: [40.7589, -73.9851],
    zoom: 13
  });
  const [drawingEnabled, setDrawingEnabled] = useState(false);

  const webSocket = useWebSocket();
  const { drones: liveDrones, loading: dronesLoading } = useDrones();

  // Use live drones if available, otherwise use mock data
  const drones = liveDrones.length > 0 ? liveDrones : mockDrones;
  const missions = mockMissions;

  // Handle area selection from map
  const handleAreaSelected = (area: SearchArea) => {
    console.log('Area selected:', area);
    setDrawingEnabled(false);
    // In a real app, this would update the current mission or chat context
  };

  // Handle drone selection
  const handleDroneSelect = (drone: Drone) => {
    setSelectedDrone(drone);
  };

  // Handle mission selection
  const handleMissionSelect = (mission: Mission) => {
    setSelectedMission(mission);
  };

  // Handle chat session changes
  const handleChatSessionChange = (session: ChatSession) => {
    setChatSession(session);
  };

  // Handle mission generation from chat
  const handleMissionGenerated = (mission: Mission) => {
    console.log('Mission generated:', mission);
    setSelectedMission(mission);
    setActiveView('dashboard');
  };

  // Handle mission approval
  const handleMissionApprove = (mission: Mission) => {
    console.log('Mission approved:', mission);
    // In a real app, this would start the mission
  };

  // Handle mission rejection
  const handleMissionReject = (reason: string) => {
    console.log('Mission rejected:', reason);
  };

  // Handle drone commands
  const handleDroneCommand = (droneId: string, command: any) => {
    console.log('Drone command:', droneId, command);
    // Commands are handled by the useDrones hook
  };

  // Render navigation
  const renderNavigation = () => (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">SAR</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900">
            SAR Drone Mission Control
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {['dashboard', 'map', 'chat', 'drones'].map((view) => (
            <button
              key={view}
              onClick={() => setActiveView(view as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeView === view
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            webSocket.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {webSocket.isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </nav>
  );

  // Render dashboard view
  const renderDashboard = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Map and Mission Preview */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white rounded-lg border h-96">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Mission Overview</h2>
              <button
                onClick={() => setDrawingEnabled(!drawingEnabled)}
                className={`px-3 py-1 rounded-lg text-sm ${
                  drawingEnabled
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {drawingEnabled ? 'Stop Drawing' : 'Draw Area'}
              </button>
            </div>
          </div>
          <div className="h-80">
            <InteractiveMap
              drones={drones}
              missions={missions}
              selectedMission={selectedMission}
              onAreaSelected={handleAreaSelected}
              onDroneClick={handleDroneSelect}
              drawingEnabled={drawingEnabled}
              viewport={mapViewport}
              onViewportChange={setMapViewport}
              className="h-full"
            />
          </div>
        </div>

        {selectedMission && (
          <MissionPreview
            mission={selectedMission}
            drones={drones}
            onApprove={handleMissionApprove}
            onReject={handleMissionReject}
            isLive={selectedMission.status === MissionStatus.ACTIVE}
          />
        )}
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Drone Status */}
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">
              Active Drones ({drones.filter(d => d.status === DroneStatusEnum.ACTIVE).length})
            </h2>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {drones.slice(0, 3).map(drone => (
              <DroneStatus
                key={drone.id}
                drone={drone}
                onStatusClick={handleDroneSelect}
                onCommandSend={handleDroneCommand}
              />
            ))}
          </div>
        </div>

        {/* Selected Drone Details */}
        {selectedDrone && (
          <DroneStatus
            drone={selectedDrone}
            showDetails={true}
            onCommandSend={handleDroneCommand}
          />
        )}
      </div>
    </div>
  );

  // Render map view
  const renderMapView = () => (
    <div className="h-full">
      <InteractiveMap
        drones={drones}
        missions={missions}
        selectedMission={selectedMission}
        onAreaSelected={handleAreaSelected}
        onDroneClick={handleDroneSelect}
        drawingEnabled={drawingEnabled}
        viewport={mapViewport}
        onViewportChange={setMapViewport}
        className="h-full"
      />
    </div>
  );

  // Render chat view
  const renderChatView = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      <ConversationalChat
        onSessionChange={handleChatSessionChange}
        onMissionGenerated={handleMissionGenerated}
        className="h-full"
      />
      
      {chatSession?.missionDraft && (
        <MissionPreview
          mission={chatSession.missionDraft}
          drones={drones}
          progress={chatSession.progress}
          onApprove={handleMissionApprove}
          onReject={handleMissionReject}
        />
      )}
    </div>
  );

  // Render drones view
  const renderDronesView = () => (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 h-full">
      <div className="xl:col-span-2">
        <DroneGrid
          drones={drones}
          onDroneSelect={handleDroneSelect}
          onDroneCommand={handleDroneCommand}
        />
      </div>
      
      <div className="space-y-6">
        {selectedDrone && (
          <>
            <DroneCommander
              drone={selectedDrone}
              onCommand={(command) => handleDroneCommand(selectedDrone.id, command)}
            />
            
            <VideoFeed
              drone={selectedDrone}
              className="h-64"
            />
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {renderNavigation()}
      
      <main className="flex-1 p-6 overflow-auto">
        {activeView === 'dashboard' && renderDashboard()}
        {activeView === 'map' && renderMapView()}
        {activeView === 'chat' && renderChatView()}
        {activeView === 'drones' && renderDronesView()}
      </main>
    </div>
  );
}

export default App;