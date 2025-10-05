/**
 * Intelligent Mission Planner Component
 * AI-powered conversational mission planning with decision integration
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Brain, 
  Send, 
  Bot, 
  User, 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Target,
  MapPin,
  Users,
  Clock,
  Shield,
  Zap,
  Activity,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface MissionContext {
  mission_type: string;
  terrain_type: string;
  weather_conditions: Record<string, any>;
  area_size: number;
  urgency_level: string;
  available_drones: any[];
  constraints: Record<string, any>;
  objectives: string[];
}

interface AIDecision {
  decision_id: string;
  decision_type: string;
  status: string;
  confidence_score: number;
  authority_level: string;
  human_approval_required: boolean;
  recommendation: string;
  reasoning_chain: string[];
  risk_assessment: {
    overall_risk_level: string;
    risk_factors: Record<string, any>;
    risk_score: number;
  };
  expected_impact: Record<string, any>;
  created_at: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai' | 'system';
  content: string;
  message_type: 'text' | 'question' | 'decision' | 'recommendation';
  timestamp: string;
  ai_confidence?: number;
  processing_time?: number;
  decision?: AIDecision;
  mission_updates?: Partial<MissionContext>;
}

interface IntelligentMissionPlannerProps {
  className?: string;
  onMissionCreated?: (mission: any) => void;
  onDecisionRequired?: (decision: AIDecision) => void;
}

const IntelligentMissionPlanner: React.FC<IntelligentMissionPlannerProps> = ({
  className = '',
  onMissionCreated,
  onDecisionRequired
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [missionContext, setMissionContext] = useState<MissionContext>({
    mission_type: '',
    terrain_type: '',
    weather_conditions: {},
    area_size: 0,
    urgency_level: 'medium',
    available_drones: [],
    constraints: {},
    objectives: []
  });
  const [showContext, setShowContext] = useState(false);
  const [pendingDecisions, setPendingDecisions] = useState<AIDecision[]>([]);
  const [conversationPhase, setConversationPhase] = useState<'initial' | 'gathering' | 'planning' | 'review' | 'approved'>('initial');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on component mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      sender: 'ai',
      content: "Hello! I'm your AI Mission Planning Assistant. I can help you create intelligent search and rescue missions with real-time decision making. What type of mission would you like to plan?",
      message_type: 'text',
      timestamp: new Date().toISOString(),
      ai_confidence: 1.0
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      sender: 'user',
      content: message,
      message_type: 'text',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      // Send message to AI service
      const response = await fetch('/api/v1/ai-decisions/analyze-context', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          context_data: {
            ...missionContext,
            user_input: message,
            conversation_phase: conversationPhase
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Create AI response message
        const aiMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          sender: 'ai',
          content: data.analysis?.structured_plan?.raw_response || 'I understand your request. Let me analyze this and provide recommendations.',
          message_type: 'text',
          timestamp: new Date().toISOString(),
          ai_confidence: 0.8,
          processing_time: 1.2
        };

        setMessages(prev => [...prev, aiMessage]);

        // Check if AI wants to make a decision
        if (data.analysis?.recommendations?.length > 0) {
          await handleAIDecisionRequest(data.analysis);
        }

        // Update conversation phase
        updateConversationPhase(message, data.analysis);

      } else {
        throw new Error('Failed to analyze context');
      }

    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 2}`,
        sender: 'system',
        content: `I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}. Please try again.`,
        message_type: 'text',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, missionContext, conversationPhase]);

  const handleAIDecisionRequest = useCallback(async (analysis: any) => {
    try {
      // Make AI decision for mission planning
      const response = await fetch('/api/v1/ai-decisions/make', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          decision_type: 'mission_planning',
          context_data: {
            ...missionContext,
            analysis: analysis
          },
          mission_id: `mission_${Date.now()}`
        })
      });

      if (response.ok) {
        const data = await response.json();
        const decision = data.decision;

        // Add decision to pending decisions
        setPendingDecisions(prev => [...prev, decision]);

        // Create decision message
        const decisionMessage: ChatMessage = {
          id: `decision_${Date.now()}`,
          sender: 'ai',
          content: `I've made a decision about your mission planning: ${decision.recommendation}`,
          message_type: 'decision',
          timestamp: new Date().toISOString(),
          ai_confidence: decision.confidence_score,
          decision: decision
        };

        setMessages(prev => [...prev, decisionMessage]);

        // Notify parent component
        onDecisionRequired?.(decision);

      }
    } catch (err) {
      console.error('Failed to make AI decision:', err);
    }
  }, [missionContext, onDecisionRequired]);

  const updateConversationPhase = useCallback((userInput: string, analysis: any) => {
    const input = userInput.toLowerCase();
    
    if (input.includes('mission') || input.includes('search') || input.includes('rescue')) {
      setConversationPhase('gathering');
    } else if (input.includes('plan') || input.includes('strategy') || input.includes('approach')) {
      setConversationPhase('planning');
    } else if (input.includes('review') || input.includes('check') || input.includes('approve')) {
      setConversationPhase('review');
    } else if (input.includes('yes') || input.includes('approve') || input.includes('confirm')) {
      setConversationPhase('approved');
    }
  }, []);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputMessage);
    }
  };

  const getPhaseSuggestions = (): string[] => {
    switch (conversationPhase) {
      case 'initial':
        return [
          "I need to plan a search mission for a missing person",
          "Create a rescue mission for a collapsed building",
          "Plan a disaster response mission",
          "I want to search a large area for survivors"
        ];
      case 'gathering':
        return [
          "The search area is mountainous terrain",
          "We have 3 drones available",
          "The mission is high priority",
          "Weather conditions are clear"
        ];
      case 'planning':
        return [
          "Use a grid search pattern",
          "Deploy all available drones",
          "Search at 50 meters altitude",
          "Record all video footage"
        ];
      case 'review':
        return [
          "This plan looks good",
          "I need to modify the search area",
          "Add more safety measures",
          "Proceed with the mission"
        ];
      default:
        return [];
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'initial': return 'text-blue-600 bg-blue-100';
      case 'gathering': return 'text-yellow-600 bg-yellow-100';
      case 'planning': return 'text-purple-600 bg-purple-100';
      case 'review': return 'text-orange-600 bg-orange-100';
      case 'approved': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

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

          {message.decision && (
            <div className="mt-2 p-2 bg-white bg-opacity-50 rounded border">
              <div className="flex items-center space-x-2 mb-1">
                <Brain className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-medium">AI Decision</span>
                <span className={`px-2 py-1 rounded text-xs ${message.decision.human_approval_required ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'}`}>
                  {message.decision.human_approval_required ? 'Approval Required' : 'Autonomous'}
                </span>
              </div>
              <p className="text-xs">{message.decision.recommendation}</p>
            </div>
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

  const SuggestionChip: React.FC<{ text: string; onClick: () => void }> = ({ text, onClick }) => (
    <button
      onClick={onClick}
      className="inline-block bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm px-3 py-1 rounded-full mr-2 mb-2 transition-colors"
    >
      {text}
    </button>
  );

  return (
    <div className={`flex flex-col bg-white border rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b bg-gray-50 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-blue-500" />
            <div>
              <h3 className="font-semibold text-gray-800">Intelligent Mission Planner</h3>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getPhaseColor(conversationPhase)}`}>
                  {conversationPhase.toUpperCase()}
                </span>
                {pendingDecisions.length > 0 && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
                    {pendingDecisions.length} Pending Decisions
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowContext(!showContext)}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              {showContext ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {isLoading && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
          </div>
        </div>
      </div>

      {/* Mission Context Panel */}
      {showContext && (
        <div className="p-4 border-b bg-gray-50">
          <h4 className="font-medium text-gray-900 mb-3">Mission Context</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Type:</span>
              <span className="ml-2 font-medium">{missionContext.mission_type || 'Not set'}</span>
            </div>
            <div>
              <span className="text-gray-600">Terrain:</span>
              <span className="ml-2 font-medium">{missionContext.terrain_type || 'Not set'}</span>
            </div>
            <div>
              <span className="text-gray-600">Area:</span>
              <span className="ml-2 font-medium">{missionContext.area_size || 0} km²</span>
            </div>
            <div>
              <span className="text-gray-600">Urgency:</span>
              <span className="ml-2 font-medium capitalize">{missionContext.urgency_level}</span>
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4" style={{ height: '500px' }}>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
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
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {getPhaseSuggestions().length > 0 && (
        <div className="p-4 border-t bg-gray-50">
          <p className="text-sm text-gray-600 mb-2">Try saying:</p>
          <div className="flex flex-wrap">
            {getPhaseSuggestions().map((suggestion, index) => (
              <SuggestionChip
                key={index}
                text={suggestion}
                onClick={() => {
                  setInputMessage(suggestion);
                  inputRef.current?.focus();
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
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                conversationPhase === 'initial'
                  ? "Describe your search and rescue mission..."
                  : "Continue the conversation..."
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => sendMessage(inputMessage)}
            disabled={!inputMessage.trim() || isLoading}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white p-2 rounded-lg transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center">
            <XCircle className="w-4 h-4 mr-2" />
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligentMissionPlanner;