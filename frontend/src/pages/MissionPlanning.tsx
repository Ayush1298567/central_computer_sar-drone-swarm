import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { MapPin, MessageSquare, Eye, Send, Loader2, CheckCircle } from 'lucide-react';
import ConversationalChat from '../components/mission/ConversationalChat';
import InteractiveMap from '../components/mission/InteractiveMap';
import MissionPreview from '../components/mission/MissionPreview';
import { apiService } from '../services/api';
import { CreateChatSessionRequest } from '../types/api';
import { Mission } from '../types/mission';

const MissionPlanning: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'map' | 'preview'>('chat');
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [missionDraft, setMissionDraft] = useState<Partial<Mission> | null>(null);
  
  // const queryClient = useQueryClient();

  // Create new chat session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data: CreateChatSessionRequest) => apiService.createChatSession(data),
    onSuccess: (response) => {
      setChatSessionId(response.data.id);
    },
  });

  // Generate mission from chat mutation
  const generateMissionMutation = useMutation({
    mutationFn: (sessionId: string) => apiService.generateMissionFromChat(sessionId),
    onSuccess: (response) => {
      setMissionDraft(response.data);
      setActiveTab('preview');
    },
  });

  // Start new mission planning session
  const startNewSession = () => {
    const sessionData: CreateChatSessionRequest = {
      mission_context: {
        mission_type: 'search_and_rescue',
        urgency_level: 'medium',
        initial_requirements: 'I need help planning a search and rescue mission',
      },
    };
    createSessionMutation.mutate(sessionData);
  };

  // Generate mission from current chat
  const generateMission = () => {
    if (chatSessionId) {
      generateMissionMutation.mutate(chatSessionId);
    }
  };

  const tabs = [
    {
      id: 'chat' as const,
      label: 'Conversational Planning',
      icon: MessageSquare,
      description: 'AI-powered mission planning through natural conversation'
    },
    {
      id: 'map' as const,
      label: 'Interactive Map',
      icon: MapPin,
      description: 'Visual mission area selection and planning'
    },
    {
      id: 'preview' as const,
      label: 'Mission Preview',
      icon: Eye,
      description: 'Review and finalize mission parameters'
    }
  ];

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Mission Planning</h1>
        <p className="text-gray-600">
          Plan your search and rescue mission using AI-powered conversational planning or interactive map tools.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
        {tabs.map((tab) => {
          const IconComponent = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-md transition-all ${
                activeTab === tab.id
                  ? 'bg-white shadow-sm text-primary-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <IconComponent className="w-5 h-5" />
              <span className="font-medium">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {activeTab === 'chat' && (
          <div className="h-full flex flex-col">
            {!chatSessionId ? (
              // Welcome screen
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center max-w-md">
                  <MessageSquare className="w-16 h-16 text-primary-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    AI Mission Planner
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Start a conversation with our AI to plan your search and rescue mission. 
                    The AI will ask clarifying questions to understand your requirements and 
                    help create an optimal mission plan.
                  </p>
                  <button
                    onClick={startNewSession}
                    disabled={createSessionMutation.isPending}
                    className="btn-primary flex items-center space-x-2"
                  >
                    {createSessionMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    <span>Start Mission Planning</span>
                  </button>
                </div>
              </div>
            ) : (
              // Chat interface
              <div className="h-full flex flex-col">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">Mission Planning Session</h3>
                    <p className="text-sm text-gray-600">Session ID: {chatSessionId}</p>
                  </div>
                  <button
                    onClick={generateMission}
                    disabled={generateMissionMutation.isPending}
                    className="btn-primary flex items-center space-x-2"
                  >
                    {generateMissionMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    <span>Generate Mission</span>
                  </button>
                </div>
                <ConversationalChat sessionId={chatSessionId} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'map' && (
          <div className="h-full">
            <InteractiveMap 
              onAreaSelected={(area) => {
                setMissionDraft(prev => ({
                  ...prev,
                  search_area: area
                }));
              }}
            />
          </div>
        )}

        {activeTab === 'preview' && (
          <div className="h-full">
            {missionDraft ? (
              <MissionPreview 
                mission={missionDraft}
                onMissionCreate={(mission) => {
                  // Handle mission creation
                  console.log('Creating mission:', mission);
                }}
              />
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <Eye className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No Mission to Preview
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Complete the conversational planning or map selection to generate a mission preview.
                  </p>
                  <button
                    onClick={() => setActiveTab('chat')}
                    className="btn-primary"
                  >
                    Start Planning
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MissionPlanning;