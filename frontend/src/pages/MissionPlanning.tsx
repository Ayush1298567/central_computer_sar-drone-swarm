import React, { useState, useEffect } from 'react';
import { wsService } from '../services/websocket';

interface MissionPlan {
  id: string;
  name: string;
  mission_type: string;
  area: any;
  coordinates: any[];
  estimated_duration_minutes: number;
  search_pattern: string;
  altitude: number;
  speed: number;
  status: string;
}

const MissionPlanning: React.FC = () => {
  const [userInput, setUserInput] = useState('');
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [currentMission, setCurrentMission] = useState<MissionPlan | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [understandingLevel, setUnderstandingLevel] = useState(0);

  const handleSubmit = async () => {
    if (!userInput.trim()) return;

    setIsPlanning(true);
    
    // Add user message to conversation
    const userMessage = { role: 'user', content: userInput };
    setConversationHistory(prev => [...prev, userMessage]);

    try {
      // Send planning request
      wsService.send({
        type: 'mission_planning_request',
        payload: {
          user_input: userInput,
          context: {
            drone_count: 5,
            weather: 'clear',
            time_constraints: 'none'
          },
          conversation_id: 'current_session'
        }
      });

      // Clear input
      setUserInput('');
    } catch (error) {
      console.error('Planning request failed:', error);
    } finally {
      setIsPlanning(false);
    }
  };

  useEffect(() => {
    // Listen for mission planning responses
    const unsubPlanning = wsService.on('mission_planning_response', (data) => {
      const aiMessage = { role: 'assistant', content: data.ai_response };
      setConversationHistory(prev => [...prev, aiMessage]);
      
      setUnderstandingLevel(data.understanding_level || 0);
      
      if (data.status === 'ready' && data.mission_plan) {
        setCurrentMission(data.mission_plan);
      }
    });

    return () => {
      unsubPlanning();
    };
  }, []);

  const startMission = () => {
    if (currentMission) {
      wsService.send({
        type: 'start_mission',
        payload: {
          mission_id: currentMission.id,
          mission_plan: currentMission
        }
      });
    }
  };

  const clearConversation = () => {
    setConversationHistory([]);
    setCurrentMission(null);
    setUnderstandingLevel(0);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Mission Planning</h1>
          <p className="text-gray-600 mt-2">AI-powered search and rescue mission planning</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Conversation Panel */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Mission Planning Chat</h2>
                <button
                  onClick={clearConversation}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Clear
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {/* Understanding Level Indicator */}
              {understandingLevel > 0 && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-blue-900">Mission Understanding</span>
                    <span className="text-sm text-blue-700">{(understandingLevel * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${understandingLevel * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Conversation History */}
              <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
                {conversationHistory.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>Start planning your SAR mission by describing:</p>
                    <ul className="mt-4 text-sm text-left space-y-1">
                      <li>• Search area location</li>
                      <li>• Number of missing persons</li>
                      <li>• Terrain type</li>
                      <li>• Any known hazards</li>
                      <li>• Time constraints</li>
                    </ul>
                  </div>
                ) : (
                  conversationHistory.map((message, index) => (
                    <div key={index} className={`p-4 rounded-lg ${
                      message.role === 'user' 
                        ? 'bg-blue-50 ml-8' 
                        : 'bg-gray-50 mr-8'
                    }`}>
                      <div className="flex items-start space-x-3">
                        <span className="text-lg">
                          {message.role === 'user' ? '👤' : '🤖'}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 mb-1">
                            {message.role === 'user' ? 'You' : 'AI Mission Planner'}
                          </p>
                          <p className="text-gray-700 whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Input Form */}
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                  placeholder="Describe your mission requirements..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isPlanning}
                />
                <button
                  onClick={handleSubmit}
                  disabled={isPlanning || !userInput.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isPlanning ? 'Planning...' : 'Send'}
                </button>
              </div>
            </div>
          </div>

          {/* Mission Plan Panel */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Generated Mission Plan</h2>
            </div>
            
            <div className="p-6">
              {!currentMission ? (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-4">📋</div>
                  <p>No mission plan generated yet</p>
                  <p className="text-sm mt-2">Continue the conversation to build your mission plan</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Mission Overview */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Mission Overview</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-600">Type:</span>
                        <span className="ml-2 text-gray-900 capitalize">{currentMission.mission_type}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Pattern:</span>
                        <span className="ml-2 text-gray-900 capitalize">{currentMission.search_pattern}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Duration:</span>
                        <span className="ml-2 text-gray-900">{currentMission.estimated_duration_minutes} min</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Altitude:</span>
                        <span className="ml-2 text-gray-900">{currentMission.altitude} m</span>
                      </div>
                    </div>
                  </div>

                  {/* Waypoints */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Search Waypoints</h3>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">
                        Generated {currentMission.coordinates?.length || 0} waypoints for comprehensive search coverage
                      </p>
                      {currentMission.coordinates && currentMission.coordinates.length > 0 && (
                        <div className="mt-3 max-h-32 overflow-y-auto">
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            {currentMission.coordinates.slice(0, 12).map((coord: any, index: number) => (
                              <div key={index} className="bg-white p-2 rounded border">
                                <div>#{coord.index || index}</div>
                                <div>{coord.lat?.toFixed(4)}, {coord.lon?.toFixed(4)}</div>
                                <div>{coord.alt}m</div>
                              </div>
                            ))}
                            {currentMission.coordinates.length > 12 && (
                              <div className="bg-white p-2 rounded border text-center">
                                +{currentMission.coordinates.length - 12} more
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-3">
                    <button
                      onClick={startMission}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                    >
                      🚀 Start Mission
                    </button>
                    <button
                      onClick={() => setCurrentMission(null)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      Discard
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionPlanning;