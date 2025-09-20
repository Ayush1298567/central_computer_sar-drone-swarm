import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  PaperAirplaneIcon, 
  PaperClipIcon, 
  XMarkIcon,
  DocumentIcon,
  PhotoIcon,
  MapIcon
} from '@heroicons/react/24/outline';
import { ChatSession, ChatMessage, PlanningProgress, Mission } from '../../types';
import { apiService } from '../../services/api';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ConversationalChatProps {
  sessionId?: string;
  onSessionChange?: (session: ChatSession) => void;
  onMissionGenerated?: (mission: Mission) => void;
  className?: string;
}

interface FileAttachment {
  file: File;
  preview?: string;
  type: 'image' | 'document' | 'other';
}

const ConversationalChat: React.FC<ConversationalChatProps> = ({
  sessionId,
  onSessionChange,
  onMissionGenerated,
  className = ''
}) => {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [progress, setProgress] = useState<PlanningProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const webSocket = useWebSocket();

  // Scroll to bottom of messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Load session data
  const loadSession = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const sessionData = await apiService.getChatSession(id);
      setSession(sessionData);
      setMessages(sessionData.messages);
      setProgress(sessionData.progress);
      onSessionChange?.(sessionData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat session');
    } finally {
      setIsLoading(false);
    }
  }, [onSessionChange]);

  // Create new session
  const createSession = useCallback(async (name: string = 'New Mission Planning') => {
    setIsLoading(true);
    setError(null);
    try {
      const newSession = await apiService.createChatSession(name);
      setSession(newSession);
      setMessages([]);
      setProgress(newSession.progress);
      onSessionChange?.(newSession);
      return newSession;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create chat session');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [onSessionChange]);

  // Send message
  const sendMessage = useCallback(async () => {
    if (!inputMessage.trim() && attachments.length === 0) return;
    if (!session) return;

    const messageContent = inputMessage.trim();
    const messageAttachments = attachments.map(a => a.file);

    // Clear input immediately
    setInputMessage('');
    setAttachments([]);
    setIsTyping(true);
    setError(null);

    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
      attachments: attachments.map(a => ({
        id: `temp-${Date.now()}`,
        name: a.file.name,
        type: a.file.type,
        size: a.file.size,
        url: a.preview || ''
      }))
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await apiService.sendChatMessage(
        session.id,
        messageContent,
        messageAttachments.length > 0 ? messageAttachments : undefined
      );

      // Replace temp message with real one
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id ? { ...userMessage, id: response.id } : msg
        )
      );

      // WebSocket will handle the AI response
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      // Remove the temp message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsTyping(false);
    }
  }, [inputMessage, attachments, session]);

  // Handle file attachment
  const handleFileAttachment = useCallback((files: FileList) => {
    const newAttachments: FileAttachment[] = [];

    Array.from(files).forEach(file => {
      const attachment: FileAttachment = {
        file,
        type: file.type.startsWith('image/') ? 'image' : 
              file.type.includes('document') || file.type.includes('pdf') ? 'document' : 'other'
      };

      // Create preview for images
      if (attachment.type === 'image') {
        const reader = new FileReader();
        reader.onload = (e) => {
          attachment.preview = e.target?.result as string;
          setAttachments(prev => [...prev, attachment]);
        };
        reader.readAsDataURL(file);
      } else {
        newAttachments.push(attachment);
      }
    });

    if (newAttachments.length > 0) {
      setAttachments(prev => [...prev, ...newAttachments]);
    }
  }, []);

  // Remove attachment
  const removeAttachment = useCallback((index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  }, []);

  // Generate mission from chat
  const generateMission = useCallback(async () => {
    if (!session) return;

    setIsLoading(true);
    setError(null);
    try {
      const mission = await apiService.generateMissionFromChat(session.id);
      onMissionGenerated?.(mission);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate mission');
    } finally {
      setIsLoading(false);
    }
  }, [session, onMissionGenerated]);

  // WebSocket event handlers
  useEffect(() => {
    if (!session) return;

    webSocket.subscribeChatSession(session.id);

    webSocket.subscribe('chat_message', (data) => {
      if (data.session_id === session.id) {
        setMessages(prev => {
          // Check if message already exists
          if (prev.some(msg => msg.id === data.message.id)) {
            return prev;
          }
          return [...prev, data.message];
        });
        setIsTyping(false);
      }
    });

    webSocket.subscribe('chat_progress_update', (data) => {
      if (data.session_id === session.id) {
        setProgress(data.progress);
      }
    });

    webSocket.subscribe('mission_plan_updated', (data) => {
      if (data.session_id === session.id) {
        setSession(prev => prev ? { ...prev, missionDraft: data.mission_draft } : null);
      }
    });

    return () => {
      webSocket.unsubscribeChatSession(session.id);
      webSocket.unsubscribe('chat_message');
      webSocket.unsubscribe('chat_progress_update');
      webSocket.unsubscribe('mission_plan_updated');
    };
  }, [session, webSocket]);

  // Load session on mount or sessionId change
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    } else if (!session) {
      createSession();
    }
  }, [sessionId, loadSession, createSession, session]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  // Render message
  const renderMessage = useCallback((message: ChatMessage) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-100 text-gray-900 border'
        }`}>
          <div className="whitespace-pre-wrap">{message.content}</div>
          
          {/* Render attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 space-y-2">
              {message.attachments.map((attachment, index) => (
                <div key={index} className="flex items-center space-x-2 text-sm">
                  {attachment.type.startsWith('image/') ? (
                    <PhotoIcon className="w-4 h-4" />
                  ) : (
                    <DocumentIcon className="w-4 h-4" />
                  )}
                  <span>{attachment.name}</span>
                  <span className="text-xs opacity-70">
                    ({Math.round(attachment.size / 1024)}KB)
                  </span>
                </div>
              ))}
            </div>
          )}
          
          <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  }, []);

  // Render progress indicator
  const renderProgress = useCallback(() => {
    if (!progress) return null;

    const progressPercentage = (progress.completedStages.length / 6) * 100;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-blue-900">Mission Planning Progress</h3>
          <span className="text-sm text-blue-700">{Math.round(progressPercentage)}%</span>
        </div>
        
        <div className="w-full bg-blue-200 rounded-full h-2 mb-3">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">Current Stage: {progress.stage}</p>
          {progress.currentQuestions.length > 0 && (
            <div>
              <p className="mb-1">Pending Questions:</p>
              <ul className="list-disc list-inside space-y-1">
                {progress.currentQuestions.map((question, index) => (
                  <li key={index} className="text-sm">{question}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  }, [progress]);

  if (isLoading && !session) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-sm border ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {session?.name || 'Mission Planning Chat'}
          </h2>
          <p className="text-sm text-gray-500">
            AI-powered mission planning assistant
          </p>
        </div>
        
        {progress && progress.stage === 'approved' && session?.missionDraft && (
          <button
            onClick={generateMission}
            disabled={isLoading}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Generate Mission
          </button>
        )}
      </div>

      {/* Progress indicator */}
      {renderProgress()}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        
        {messages.map(renderMessage)}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 border">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className="border-t p-4">
          <div className="flex flex-wrap gap-2">
            {attachments.map((attachment, index) => (
              <div key={index} className="relative bg-gray-100 rounded-lg p-2 flex items-center space-x-2">
                {attachment.type === 'image' ? (
                  <PhotoIcon className="w-4 h-4 text-gray-500" />
                ) : (
                  <DocumentIcon className="w-4 h-4 text-gray-500" />
                )}
                <span className="text-sm text-gray-700 truncate max-w-32">
                  {attachment.file.name}
                </span>
                <button
                  onClick={() => removeAttachment(index)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your search and rescue mission requirements..."
              className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-400 hover:text-gray-600"
              title="Attach file"
            >
              <PaperClipIcon className="w-5 h-5" />
            </button>
            
            <button
              onClick={sendMessage}
              disabled={isLoading || (!inputMessage.trim() && attachments.length === 0)}
              className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.pdf,.doc,.docx,.txt,.json,.kml,.gpx"
        onChange={(e) => e.target.files && handleFileAttachment(e.target.files)}
        className="hidden"
      />
    </div>
  );
};

export default ConversationalChat;