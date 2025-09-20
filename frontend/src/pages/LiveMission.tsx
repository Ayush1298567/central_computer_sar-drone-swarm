import React, { useState, useEffect } from 'react';
import { InteractiveMap } from '../components/map/InteractiveMap';
import { DroneStatus } from '../components/drone/DroneStatus';
import { DroneCommander } from '../components/drone/DroneCommander';
import { VideoFeed } from '../components/drone/VideoFeed';
import { MissionPreview } from '../components/mission/MissionPreview';
import { Mission } from '../types/mission';
import { Drone, DroneCommand } from '../types/drone';
import { apiService } from '../services/api';
import { webSocketService } from '../services/websocket';
import { 
  Play, 
  Pause, 
  Square, 
  AlertTriangle, 
  Activity,
  Video,
  Command,
  Map,
  BarChart3
} from 'lucide-react';

export const LiveMission: React.FC = () => {
  const [activeMissions, setActiveMissions] = useState<Mission[]>([]);
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null);
  const [missionDrones, setMissionDrones] = useState<Drone[]>([]);
  const [selectedDrone, setSelectedDrone] = useState<Drone | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'map' | 'video' | 'command'>('overview');
  const [isLoading, setIsLoading] = useState(true);

  // Load active missions
  useEffect(() => {
    const loadActiveMissions = async () => {
      try {
        const response = await apiService.getMissions({ status: 'active' });
        setActiveMissions(response.missions);
        
        if (response.missions.length > 0 && !selectedMission) {
          setSelectedMission(response.missions[0]);
        }
      } catch (error) {
        console.error('Failed to load active missions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadActiveMissions();
  }, [selectedMission]);

  // Load mission drones when mission changes
  useEffect(() => {
    if (selectedMission) {
      const loadMissionDrones = async () => {
        try {
          // Get all drones and filter by mission assignment
          const response = await apiService.getDrones();
          const assignedDrones = response.drones.filter(drone =>
            selectedMission.assigned_drones.includes(drone.id)
          );
          setMissionDrones(assignedDrones);
          
          if (assignedDrones.length > 0 && !selectedDrone) {
            setSelectedDrone(assignedDrones[0]);
          }
        } catch (error) {
          console.error('Failed to load mission drones:', error);
        }
      };

      loadMissionDrones();
    }
  }, [selectedMission, selectedDrone]);

  // Subscribe to real-time mission updates
  useEffect(() => {
    if (selectedMission) {
      const handleMissionUpdate = (data: any) => {
        if (data.mission_id === selectedMission.id) {
          setSelectedMission(prev => prev ? { ...prev, ...data } : null);
          
          // Update in active missions list
          setActiveMissions(prev =>
            prev.map(mission =>
              mission.id === data.mission_id ? { ...mission, ...data } : mission
            )
          );
        }
      };

      webSocketService.subscribe('mission_update', handleMissionUpdate);
      webSocketService.subscribeMission(selectedMission.id);

      return () => {
        webSocketService.unsubscribe('mission_update', handleMissionUpdate);
        webSocketService.unsubscribeMission(selectedMission.id);
      };
    }
  }, [selectedMission]);

  const handleMissionControl = async (action: 'start' | 'pause' | 'resume' | 'abort') => {
    if (!selectedMission) return;

    try {
      let result;
      switch (action) {
        case 'start':
          result = await apiService.startMission(selectedMission.id);
          break;
        case 'pause':
          result = await apiService.pauseMission(selectedMission.id);
          break;
        case 'resume':
          result = await apiService.resumeMission(selectedMission.id);
          break;
        case 'abort':
          result = await apiService.abortMission(selectedMission.id, 'User requested abort');
          break;
      }
      
      console.log(`Mission ${action} result:`, result);
    } catch (error) {
      console.error(`Failed to ${action} mission:`, error);
    }
  };

  const handleDroneSelect = (drone: Drone) => {
    setSelectedDrone(drone);
    if (activeTab !== 'video' && activeTab !== 'command') {
      setActiveTab('command');
    }
  };

  const handleCommandSent = (command: DroneCommand) => {
    console.log('Command sent:', command);
  };

  const handleEmergencyStop = async (drone: Drone) => {
    try {
      await apiService.emergencyStopDrone(drone.id);
      console.log('Emergency stop sent to drone:', drone.id);
    } catch (error) {
      console.error('Failed to send emergency stop:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading live missions...</p>
        </div>
      </div>
    );
  }

  if (activeMissions.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertTriangle size={48} className="mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Active Missions
        </h3>
        <p className="text-gray-600 mb-6">
          There are currently no active search and rescue missions.
        </p>
        <button
          onClick={() => window.location.href = '#/planning'}
          className="btn btn-primary"
        >
          Plan New Mission
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Live Mission Control</h1>
          <p className="text-gray-600">
            Monitor and control active search and rescue operations
          </p>
        </div>

        {/* Mission Selector */}
        {activeMissions.length > 1 && (
          <select
            value={selectedMission?.id || ''}
            onChange={(e) => {
              const mission = activeMissions.find(m => m.id === e.target.value);
              setSelectedMission(mission || null);
            }}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {activeMissions.map(mission => (
              <option key={mission.id} value={mission.id}>
                {mission.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {selectedMission && (
        <>
          {/* Mission Controls */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {selectedMission.name}
                </h2>
                <div className="flex items-center space-x-4 mt-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedMission.status === 'active' ? 'bg-green-100 text-green-800' :
                    selectedMission.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    <Activity size={12} className="mr-1" />
                    {selectedMission.status}
                  </span>
                  <span className="text-sm text-gray-600">
                    {selectedMission.progress_percentage}% complete
                  </span>
                  <span className="text-sm text-gray-600">
                    {missionDrones.length} drones assigned
                  </span>
                </div>
              </div>

              <div className="flex space-x-2">
                {selectedMission.status === 'paused' && (
                  <button
                    onClick={() => handleMissionControl('resume')}
                    className="btn btn-success text-sm"
                  >
                    <Play size={16} className="mr-1" />
                    Resume
                  </button>
                )}
                
                {selectedMission.status === 'active' && (
                  <button
                    onClick={() => handleMissionControl('pause')}
                    className="btn btn-warning text-sm"
                  >
                    <Pause size={16} className="mr-1" />
                    Pause
                  </button>
                )}
                
                <button
                  onClick={() => handleMissionControl('abort')}
                  className="btn btn-danger text-sm"
                >
                  <Square size={16} className="mr-1" />
                  Abort
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="progress-bar">
              <div 
                className="progress-fill bg-blue-600"
                style={{ width: `${selectedMission.progress_percentage}%` }}
              ></div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'overview'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <BarChart3 size={16} className="inline mr-2" />
                  Overview
                </button>
                
                <button
                  onClick={() => setActiveTab('map')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'map'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Map size={16} className="inline mr-2" />
                  Live Map
                </button>
                
                {selectedDrone && (
                  <>
                    <button
                      onClick={() => setActiveTab('video')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === 'video'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Video size={16} className="inline mr-2" />
                      Video Feed
                    </button>
                    
                    <button
                      onClick={() => setActiveTab('command')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === 'command'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Command size={16} className="inline mr-2" />
                      Drone Control
                    </button>
                  </>
                )}
              </nav>
            </div>

            <div className="p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <MissionPreview
                    mission={selectedMission}
                    assignedDrones={missionDrones}
                    isReadOnly={true}
                  />
                  
                  {/* Drone Grid */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Assigned Drones
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {missionDrones.map(drone => (
                        <DroneStatus
                          key={drone.id}
                          drone={drone}
                          showDetails={true}
                          onStatusClick={handleDroneSelect}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Map Tab */}
              {activeTab === 'map' && (
                <div className="h-96">
                  <InteractiveMap
                    drones={missionDrones}
                    missions={[selectedMission]}
                    selectedMission={selectedMission}
                    onDroneClick={handleDroneSelect}
                    className="h-full"
                  />
                </div>
              )}

              {/* Video Tab */}
              {activeTab === 'video' && selectedDrone && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Live Video Feed - {selectedDrone.name}
                    </h3>
                    
                    <select
                      value={selectedDrone.id}
                      onChange={(e) => {
                        const drone = missionDrones.find(d => d.id === e.target.value);
                        setSelectedDrone(drone || null);
                      }}
                      className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {missionDrones.map(drone => (
                        <option key={drone.id} value={drone.id}>
                          {drone.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <VideoFeed
                    drone={selectedDrone}
                    onRecordingStart={() => console.log('Recording started')}
                    onRecordingStop={() => console.log('Recording stopped')}
                    onScreenshot={() => console.log('Screenshot taken')}
                    className="w-full"
                  />
                </div>
              )}

              {/* Command Tab */}
              {activeTab === 'command' && selectedDrone && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Drone Commander - {selectedDrone.name}
                    </h3>
                    
                    <select
                      value={selectedDrone.id}
                      onChange={(e) => {
                        const drone = missionDrones.find(d => d.id === e.target.value);
                        setSelectedDrone(drone || null);
                      }}
                      className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {missionDrones.map(drone => (
                        <option key={drone.id} value={drone.id}>
                          {drone.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <DroneCommander
                    drone={selectedDrone}
                    onCommandSent={handleCommandSent}
                    onEmergencyStop={handleEmergencyStop}
                  />
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};