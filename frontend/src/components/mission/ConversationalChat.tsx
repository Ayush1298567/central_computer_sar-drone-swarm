/**
 * Conversational Chat Component for SAR Mission Commander.
 * Provides AI-powered conversational interface for mission planning.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Loader2, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

// Import types
import {
  ChatMessage,
  MessageSender,
  MessageType,
  ConversationContext,
  Mission,
  MissionPlan,
  WeatherImpact,
  RiskAssessment,
} from '../../types';

// Import services
import { MissionService, MissionErrorHandler } from '../../services';

interface ConversationalChatProps {
  mission?: Mission;
  onMissionUpdate?: (mission: Partial<Mission>) => void;
  onAreaSelect?: (area: any) => void;
  className?: string;
  height?: string;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationContext: ConversationContext;
}

export const ConversationalChat: React.FC<ConversationalChatProps> = ({
  mission,
  onMissionUpdate,
  onAreaSelect,
  className = '',
  height = '500px',
}) => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    conversationContext: {
      current_phase: 'initial_request',
      mission_parameters: {},
      pending_questions: [],
      user_preferences: {},
    },
  });

  const [inputMessage, setInputMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages, scrollToBottom]);

  // Focus input on component mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle mission updates
  useEffect(() => {
    if (mission) {
      setChatState(prev => ({
        ...prev,
        conversationContext: {
          ...prev.conversationContext,
          current_phase: 'mission_approval',
          mission_parameters: {
            ...prev.conversationContext.mission_parameters,
            ...mission,
          },
        },
      }));
    }
  }, [mission]);

  // Send message to AI
  const sendMessage = async (message: string) => {
    if (!message.trim() || chatState.isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      mission_id: mission?.id || '',
      sender: 'user',
      content: message,
      message_type: 'text',
      created_at: new Date().toISOString(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    setInputMessage('');
    setShowSuggestions(false);

    try {
      // Send message to AI service
      const response = await MissionService.sendChatMessage(userMessage.content, chatState.conversationContext);

      const aiMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        mission_id: mission?.id || '',
        sender: 'ai',
        content: response.data?.content || '',
        message_type: response.data?.message_type || 'text',
        ai_confidence: response.data?.confidence,
        processing_time: response.data?.processing_time,
        created_at: new Date().toISOString(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, aiMessage],
        isLoading: false,
        conversationContext: {
          ...prev.conversationContext,
          ...response.data?.conversation_context,
        },
      }));

      // Handle AI responses that update mission
      if (response.data?.mission_updates) {
        onMissionUpdate?.(response.data.mission_updates);
      }

      // Handle area selection suggestions
      if (response.data?.area_suggestion && onAreaSelect) {
        onAreaSelect(response.data.area_suggestion);
      }

    } catch (error) {
      const errorInfo = MissionErrorHandler.handleMissionError(error);

      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 2}`,
        mission_id: mission?.id || '',
        sender: 'system',
        content: `Error: ${errorInfo.message}. ${errorInfo.action}`,
        message_type: 'error',
        created_at: new Date().toISOString(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
        error: errorInfo.message,
      }));
    }
  };

  // Handle key press in input
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputMessage);
    }
  };

  // Suggested conversation starters
  const conversationStarters = [
    "I need to search a collapsed building for survivors",
    "Plan a search mission for a missing hiker in the mountains",
    "Search a rural area for a missing vehicle",
    "Create a mission to survey damage after a natural disaster",
  ];

  // Quick suggestions based on conversation phase
  const getPhaseSuggestions = (): string[] => {
    const phase = chatState.conversationContext.current_phase;

    switch (phase) {
      case 'initial_request':
        return conversationStarters;
      case 'area_selection':
        return [
          "The search area is a 2km radius around these coordinates",
          "Search the entire park area",
          "Focus on the residential neighborhood",
        ];
      case 'parameter_gathering':
        return [
          "Search at 50 meters altitude",
          "Use fast search speed for quick coverage",
          "Record continuously during the mission",
          "Search for people and vehicles",
        ];
      case 'plan_review':
        return [
          "This plan looks good, let's proceed",
          "Can we adjust the search altitude?",
          "Add more drones to speed up the search",
        ];
      default:
        return [];
    }
  };

  // Message component
  const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
    const isUser = message.sender === 'user';
    const isAI = message.sender === 'ai';
    const isSystem = message.sender === 'system';

    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div
          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-blue-500 text-white'
              : isAI
              ? 'bg-gray-100 text-gray-800'
              : isSystem
              ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          <div className="flex items-center mb-1">
            {isUser ? (
              <User className="w-4 h-4 mr-1" />
            ) : isAI ? (
              <Bot className="w-4 h-4 mr-1" />
            ) : (
              <AlertCircle className="w-4 h-4 mr-1" />
            )}
            <span className="text-xs opacity-75">
              {isUser ? 'You' : isAI ? 'AI Assistant' : 'System'}
            </span>
            {message.ai_confidence && (
              <span className="text-xs opacity-75 ml-2">
                ({Math.round(message.ai_confidence * 100)}% confidence)
              </span>
            )}
          </div>

          <div className="text-sm whitespace-pre-wrap">{message.content}</div>

          {message.message_type === 'question' && (
            <div className="mt-2 text-xs opacity-75">Waiting for your response...</div>
          )}

          {message.processing_time && (
            <div className="text-xs opacity-50 mt-1">
              Processed in {message.processing_time.toFixed(1)}s
            </div>
          )}
        </div>
      </div>
    );
  };

  // Typing indicator
  const TypingIndicator: React.FC = () => (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
        <div className="flex items-center">
          <Bot className="w-4 h-4 mr-2" />
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    </div>
  );

  // Suggestion chips
  const SuggestionChip: React.FC<{ text: string; onClick: () => void }> = ({ text, onClick }) => (
    <button
      onClick={() => {
        setInputMessage(text);
        inputRef.current?.focus();
      }}
      className="inline-block bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm px-3 py-1 rounded-full mr-2 mb-2 transition-colors"
    >
      {text}
    </button>
  );

  return (
    <div className={`flex flex-col bg-white border rounded-lg shadow-sm ${className}`}>
      {/* Chat Header */}
      <div className="p-4 border-b bg-gray-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Bot className="w-5 h-5 mr-2 text-blue-500" />
            <h3 className="font-semibold text-gray-800">Mission Planning Assistant</h3>
          </div>
          <div className="flex items-center space-x-2">
            {chatState.conversationContext.current_phase !== 'initial_request' && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                {chatState.conversationContext.current_phase.replace('_', ' ')}
              </span>
            )}
            {chatState.isLoading && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4" style={{ height: `calc(${height} - 140px)` }}>
        {chatState.messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">Start a conversation</p>
            <p className="text-sm">Describe your search and rescue mission to get started</p>
          </div>
        ) : (
          <>
            {chatState.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {chatState.isLoading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {showSuggestions && chatState.messages.length < 3 && (
        <div className="p-4 border-t bg-gray-50">
          <p className="text-sm text-gray-600 mb-2">Try saying:</p>
          <div className="flex flex-wrap">
            {getPhaseSuggestions().map((suggestion, index) => (
              <SuggestionChip
                key={index}
                text={suggestion}
                onClick={() => {
                  sendMessage(suggestion);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                chatState.conversationContext.current_phase === 'initial_request'
                  ? "Describe your search and rescue mission..."
                  : "Continue the conversation..."
              }
              className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${target.scrollHeight}px`;
              }}
            />
          </div>
          <button
            onClick={() => sendMessage(inputMessage)}
            disabled={!inputMessage.trim() || chatState.isLoading}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white p-2 rounded-lg transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Error Display */}
        {chatState.error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center">
            <XCircle className="w-4 h-4 mr-2" />
            {chatState.error}
            <button
              onClick={() => setChatState(prev => ({ ...prev, error: null }))}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Context Info */}
        {chatState.conversationContext.pending_questions.length > 0 && (
          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-blue-700 text-sm">
            <p className="font-medium">Pending questions:</p>
            <ul className="list-disc list-inside mt-1">
              {chatState.conversationContext.pending_questions.map((question, index) => (
                <li key={index}>{question}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// Chat message service integration
export class ChatService {
  /**
   * Send a chat message to the AI service
   */
  static async sendChatMessage(
    message: string,
    context: ConversationContext
  ): Promise<{
    content: string;
    message_type: MessageType;
    confidence?: number;
    processing_time?: number;
    conversation_context?: Partial<ConversationContext>;
    mission_updates?: Partial<Mission>;
    area_suggestion?: any;
  }> {
    try {
      const response = await MissionService.sendChatMessage(message, context);

      return {
        content: response.data?.content || '',
        message_type: response.data?.message_type || 'text',
        confidence: response.data?.confidence,
        processing_time: response.data?.processing_time,
        conversation_context: response.data?.conversation_context,
        mission_updates: response.data?.mission_updates,
        area_suggestion: response.data?.area_suggestion,
      };
    } catch (error) {
      const errorInfo = MissionErrorHandler.handleMissionError(error);

      return {
        content: `I'm sorry, I encountered an error: ${errorInfo.message}. ${errorInfo.action}`,
        message_type: 'error',
      };
    }
  }

  /**
   * Get conversation history for a mission
   */
  static async getConversationHistory(missionId: string): Promise<ChatMessage[]> {
    try {
      const response = await MissionService.getChatHistory(missionId);
      return response.data || [];
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      return [];
    }
  }

  /**
   * Export conversation for reporting
   */
  static async exportConversation(missionId: string): Promise<Blob | null> {
    try {
      const response = await MissionService.exportChatHistory(missionId);
      return response.data || null;
    } catch (error) {
      console.error('Failed to export conversation:', error);
      return null;
    }
  }
}

export default ConversationalChat;