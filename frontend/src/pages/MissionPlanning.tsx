import React, { useState, useEffect } from 'react';
import { ConversationalChat } from '../components/mission/ConversationalChat';
import { MissionPreview } from '../components/mission/MissionPreview';
import { InteractiveMap } from '../components/map/InteractiveMap';
import { ChatSession } from '../types/chat';
import { Mission, MissionPlan } from '../types/mission';
import { Drone } from '../types/drone';
import { apiService } from '../services/api';
import { MessageSquare, Map, Eye, Plus } from 'lucide-react';

export const MissionPlanning: React.FC = () => {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [generatedMission, setGeneratedMission] = useState<Mission | null>(null);
  const [missionPlan, setMissionPlan] = useState<MissionPlan | null>(null);
  const [assignedDrones, setAssignedDrones] = useState<Drone[]>([]);
  const [availableDrones, setAvailableDrones] = useState<Drone[]>([]);
  const [selectedArea, setSelectedArea] = useState<number[][][]>([]);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'map' | 'preview'>('chat');

  // Load available drones
  useEffect(() => {
    const loadDrones = async () => {
      try {
        const response = await apiService.getDrones();
        setAvailableDrones(response.drones);
      } catch (error) {
        console.error('Failed to load drones:', error);
      }
    };

    loadDrones();
  }, []);

  // Load mission details when generated
  useEffect(() => {
    if (generatedMission) {
      loadMissionDetails(generatedMission.id);
    }
  }, [generatedMission]);

  const loadMissionDetails = async (missionId: string) => {
    try {
      const mission = await apiService.getMission(missionId);
      setGeneratedMission(mission);

      // Get assigned drones
      const drones = availableDrones.filter(drone => 
        mission.assigned_drones.includes(drone.id)
      );
      setAssignedDrones(drones);

      // TODO: Load mission plan from API
      // const plan = await apiService.getMissionPlan(missionId);
      // setMissionPlan(plan);
    } catch (error) {
      console.error('Failed to load mission details:', error);
    }
  };

  const handleSessionChange = (session: ChatSession) => {
    setCurrentSession(session);
  };

  const handleMissionGenerated = async (missionId: string) => {
    try {
      const mission = await apiService.getMission(missionId);
      setGeneratedMission(mission);
      setActiveTab('preview');
    } catch (error) {
      console.error('Failed to load generated mission:', error);
    }
  };

  const handleAreaSelected = (area: number[][][]) => {
    setSelectedArea(area);
    setIsDrawingMode(false);
    
    // Send area to chat if session exists
    if (currentSession) {
      // TODO: Send area coordinates to chat session
      console.log('Selected area:', area);
    }
  };

  const handleMissionApprove = async () => {
    if (!generatedMission) return;

    try {
      await apiService.updateMission(generatedMission.id, { status: 'ready' });
      setGeneratedMission(prev => prev ? { ...prev, status: 'ready' } : null);
    } catch (error) {
      console.error('Failed to approve mission:', error);
    }
  };

  const handleMissionReject = async (_reason: string) => {
    if (!generatedMission) return;

    try {
      await apiService.updateMission(generatedMission.id, { 
        status: 'planning',
        // TODO: Add rejection reason to mission
      });
      setGeneratedMission(null);
      setActiveTab('chat');
    } catch (error) {
      console.error('Failed to reject mission:', error);
    }
  };

  const handleMissionModify = () => {
    setActiveTab('chat');
  };

  const createNewSession = async () => {
    try {
      const session = await apiService.createChatSession('New Mission Planning');
      setCurrentSession(session);
      setGeneratedMission(null);
      setMissionPlan(null);
      setAssignedDrones([]);
      setSelectedArea([]);
      setActiveTab('chat');
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mission Planning</h1>
          <p className="text-gray-600">
            Use AI-powered conversation to plan your search and rescue mission
          </p>
        </div>

        <button
          onClick={createNewSession}
          className="btn btn-primary"
        >
          <Plus size={20} className="mr-2" />
          New Mission
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <MessageSquare size={16} className="inline mr-2" />
              AI Planning Chat
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
              Area Selection
            </button>
            
            {generatedMission && (
              <button
                onClick={() => setActiveTab('preview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'preview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Eye size={16} className="inline mr-2" />
                Mission Preview
              </button>
            )}
          </nav>
        </div>

        <div className="p-6">
          {/* Chat Tab */}
          {activeTab === 'chat' && (
            <div className="h-96">
              <ConversationalChat
                sessionId={currentSession?.id}
                onSessionChange={handleSessionChange}
                onMissionGenerated={handleMissionGenerated}
                className="h-full"
              />
            </div>
          )}

          {/* Map Tab */}
          {activeTab === 'map' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Select Search Area
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setIsDrawingMode(!isDrawingMode)}
                    className={`btn text-sm ${
                      isDrawingMode ? 'btn-danger' : 'btn-primary'
                    }`}
                  >
                    {isDrawingMode ? 'Cancel Drawing' : 'Draw Area'}
                  </button>
                  {selectedArea.length > 0 && (
                    <button
                      onClick={() => setSelectedArea([])}
                      className="btn btn-secondary text-sm"
                    >
                      Clear Area
                    </button>
                  )}
                </div>
              </div>
              
              <div className="h-96 rounded-lg overflow-hidden">
                <InteractiveMap
                  drones={availableDrones}
                  missions={generatedMission ? [generatedMission] : []}
                  drawingMode={isDrawingMode}
                  onAreaSelected={handleAreaSelected}
                  className="h-full"
                />
              </div>

              {selectedArea.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">
                    Area Selected
                  </h4>
                  <p className="text-sm text-blue-700">
                    Search area defined with {selectedArea[0]?.length || 0} coordinates.
                    You can now continue the conversation in the AI Planning Chat.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Preview Tab */}
          {activeTab === 'preview' && generatedMission && (
            <MissionPreview
              mission={generatedMission}
              missionPlan={missionPlan || undefined}
              assignedDrones={assignedDrones}
              onApprove={handleMissionApprove}
              onReject={handleMissionReject}
              onModify={handleMissionModify}
            />
          )}

          {/* Empty state for preview */}
          {activeTab === 'preview' && !generatedMission && (
            <div className="text-center py-12">
              <Eye size={48} className="mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No Mission Generated Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Complete the planning conversation to generate a mission preview.
              </p>
              <button
                onClick={() => setActiveTab('chat')}
                className="btn btn-primary"
              >
                Start Planning
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {currentSession && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <MessageSquare className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Current Session</p>
                <p className="text-lg font-semibold text-gray-900">{currentSession.name}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Map className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Available Drones</p>
                <p className="text-lg font-semibold text-gray-900">{availableDrones.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Eye className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Mission Status</p>
                <p className="text-lg font-semibold text-gray-900">
                  {generatedMission ? generatedMission.status : 'Planning'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};