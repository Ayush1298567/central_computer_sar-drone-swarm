import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  MapPin,
  Clock,
  Users,
  Settings,
  Send,
  MessageSquare,
  Plus,
  Save
} from 'lucide-react';

const MissionPlanning: React.FC = () => {
  const { sendMessage } = useWebSocket();
  const [activeTab, setActiveTab] = useState<'manual' | 'conversational'>('manual');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]);

  // Fetch available drones
  const { data: drones } = useQuery(
    'drones',
    () => apiService.drones.getAll({ status_filter: 'online' })
  );

  // Form state for manual mission planning
  const [missionForm, setMissionForm] = useState({
    name: '',
    description: '',
    center: { lat: 40.7128, lng: -74.0060 }, // Default to NYC
    search_area: '',
    search_altitude: 30,
    estimated_duration: 60,
    max_drones: 1,
    search_pattern: 'lawnmower',
    priority: 3,
    mission_type: 'search'
  });

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    // Add user message to history
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: chatInput,
      timestamp: new Date()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatInput('');

    try {
      // Send to backend
      const response = await apiService.chat.sendMessage('default', {
        content: chatInput,
        message_type: 'text'
      });

      // Add AI response to history
      const aiMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.ai_response,
        timestamp: new Date()
      };

      setChatHistory(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    }
  };

  const handleCreateMission = async () => {
    try {
      await apiService.missions.create(missionForm);
      // Reset form or redirect
      alert('Mission created successfully!');
    } catch (error) {
      console.error('Error creating mission:', error);
      alert('Error creating mission');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Mission Planning</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('manual')}
            className={`px-4 py-2 rounded-lg ${
              activeTab === 'manual'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Manual Planning
          </button>
          <button
            onClick={() => setActiveTab('conversational')}
            className={`px-4 py-2 rounded-lg ${
              activeTab === 'conversational'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            AI Assistant
          </button>
        </div>
      </div>

      {activeTab === 'manual' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Mission Form */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Mission Details</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mission Name
                </label>
                <input
                  type="text"
                  value={missionForm.name}
                  onChange={(e) => setMissionForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter mission name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={missionForm.description}
                  onChange={(e) => setMissionForm(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe the mission objectives"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={missionForm.center.lat}
                    onChange={(e) => setMissionForm(prev => ({
                      ...prev,
                      center: { ...prev.center, lat: parseFloat(e.target.value) }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={missionForm.center.lng}
                    onChange={(e) => setMissionForm(prev => ({
                      ...prev,
                      center: { ...prev.center, lng: parseFloat(e.target.value) }
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Altitude (m)
                  </label>
                  <input
                    type="number"
                    value={missionForm.search_altitude}
                    onChange={(e) => setMissionForm(prev => ({ ...prev, search_altitude: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Duration (min)
                  </label>
                  <input
                    type="number"
                    value={missionForm.estimated_duration}
                    onChange={(e) => setMissionForm(prev => ({ ...prev, estimated_duration: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Drones
                  </label>
                  <select
                    value={missionForm.max_drones}
                    onChange={(e) => setMissionForm(prev => ({ ...prev, max_drones: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {[1, 2, 3, 4, 5].map(num => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={missionForm.priority}
                    onChange={(e) => setMissionForm(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={1}>Low</option>
                    <option value={2}>Medium</option>
                    <option value={3}>High</option>
                    <option value={4}>Critical</option>
                    <option value={5}>Emergency</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleCreateMission}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Create Mission
              </button>
            </div>
          </div>

          {/* Map Preview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Area Preview</h2>
            <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500">Interactive map will be displayed here</p>
                <p className="text-sm text-gray-400 mt-1">
                  Lat: {missionForm.center.lat.toFixed(4)}, Lng: {missionForm.center.lng.toFixed(4)}
                </p>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Available Drones:</span>
                <span className="font-medium">{drones?.length || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Search Pattern:</span>
                <span className="font-medium capitalize">{missionForm.search_pattern}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Mission Type:</span>
                <span className="font-medium capitalize">{missionForm.mission_type}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Conversational AI Interface */
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <MessageSquare className="h-6 w-6 mr-2" />
              AI Mission Planning Assistant
            </h2>
            <p className="text-gray-600 mt-1">
              Describe your mission requirements in natural language and I'll help you create an optimal plan.
            </p>
          </div>

          <div className="p-6">
            {/* Chat History */}
            <div className="h-96 overflow-y-auto mb-4 space-y-4">
              {chatHistory.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleChatSubmit} className="flex space-x-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Describe your mission requirements..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <Send className="h-5 w-5" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MissionPlanning;