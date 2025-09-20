import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { apiService } from '../../services/api';
import { ChatMessage, PlanningStage } from '../../types/mission';
import { SendMessageRequest } from '../../types/api';

interface ConversationalChatProps {
  sessionId: string;
}

const ConversationalChat: React.FC<ConversationalChatProps> = ({ sessionId }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch chat session data
  const { data: sessionData, isLoading } = useQuery({
    queryKey: ['chat-session', sessionId],
    queryFn: () => apiService.getChatSession(sessionId),
    refetchInterval: 2000, // Poll for new messages
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (data: SendMessageRequest) => apiService.sendMessage(sessionId, data),
    onMutate: () => setIsTyping(true),
    onSettled: () => setIsTyping(false),
    onSuccess: () => {
      setInputMessage('');
      queryClient.invalidateQueries({ queryKey: ['chat-session', sessionId] });
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessionData?.data?.messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !sendMessageMutation.isPending) {
      sendMessageMutation.mutate({
        content: inputMessage.trim(),
        message_type: 'response',
      });
    }
  };

  const getPlanningStageDisplay = (stage: PlanningStage) => {
    const stages = {
      [PlanningStage.INITIAL]: { label: 'Initial Planning', color: 'bg-blue-100 text-blue-800' },
      [PlanningStage.AREA_DEFINITION]: { label: 'Area Definition', color: 'bg-purple-100 text-purple-800' },
      [PlanningStage.REQUIREMENTS_GATHERING]: { label: 'Requirements Gathering', color: 'bg-yellow-100 text-yellow-800' },
      [PlanningStage.DRONE_SELECTION]: { label: 'Drone Selection', color: 'bg-green-100 text-green-800' },
      [PlanningStage.WEATHER_CHECK]: { label: 'Weather Check', color: 'bg-cyan-100 text-cyan-800' },
      [PlanningStage.SAFETY_VALIDATION]: { label: 'Safety Validation', color: 'bg-orange-100 text-orange-800' },
      [PlanningStage.FINAL_REVIEW]: { label: 'Final Review', color: 'bg-red-100 text-red-800' },
      [PlanningStage.COMPLETED]: { label: 'Completed', color: 'bg-green-100 text-green-800' },
    };
    return stages[stage] || stages[PlanningStage.INITIAL];
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  const messages: ChatMessage[] = sessionData?.data?.messages || [];
  const planningStage = sessionData?.data?.planning_stage || PlanningStage.INITIAL;
  const stageDisplay = getPlanningStageDisplay(planningStage);

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Planning Stage Indicator */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-700">Planning Stage:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${stageDisplay.color}`}>
              {stageDisplay.label}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {messages.length} messages
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-lg font-medium mb-2">AI Mission Planner Ready</p>
            <p className="text-sm">
              I'll help you plan your search and rescue mission by asking clarifying questions.
              Let's start by telling me about your mission requirements.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.role === 'assistant' && (
                    <Bot className="w-5 h-5 mt-0.5 text-primary-600" />
                  )}
                  {message.role === 'user' && (
                    <User className="w-5 h-5 mt-0.5 text-white" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    {message.metadata?.suggestions && (
                      <div className="mt-2 space-y-1">
                        {message.metadata.suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => setInputMessage(suggestion)}
                            className="block w-full text-left text-xs bg-white bg-opacity-20 hover:bg-opacity-30 rounded px-2 py-1 transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-primary-200' : 'text-gray-500'
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                      {message.metadata?.confidence_score && (
                        <span className="ml-2">
                          Confidence: {Math.round(message.metadata.confidence_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Bot className="w-5 h-5 text-primary-600" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200">
        <div className="flex space-x-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message or mission requirements..."
            className="flex-1 input-field"
            disabled={sendMessageMutation.isPending}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || sendMessageMutation.isPending}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>Send</span>
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500">
          The AI will ask clarifying questions to help plan your mission. Be as specific as possible about your requirements.
        </div>
      </form>
    </div>
  );
};

export default ConversationalChat;