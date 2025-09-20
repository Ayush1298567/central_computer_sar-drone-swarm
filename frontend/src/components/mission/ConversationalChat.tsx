import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Paperclip, X, FileText, Image, MapPin, Clock, AlertCircle } from 'lucide-react';
import { ChatSession, ChatMessage, PlanningProgress } from '../../types/chat';
import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';

interface ConversationalChatProps {
  sessionId?: string;
  onSessionChange?: (session: ChatSession) => void;
  onMissionGenerated?: (missionId: string) => void;
  className?: string;
}

interface FileUpload {
  id: string;
  file: File;
  preview?: string;
}

export const ConversationalChat: React.FC<ConversationalChatProps> = ({
  sessionId,
  onSessionChange,
  onMissionGenerated,
  className = '',
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [, setCurrentSession] = useState<ChatSession | null>(null);
  const [planningProgress, setPlanningProgress] = useState<PlanningProgress | null>(null);
  const [fileUploads, setFileUploads] = useState<FileUpload[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Load session and messages
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId]);

  // Subscribe to real-time chat updates
  useEffect(() => {
    if (!sessionId) return;

    const handleChatMessage = (data: ChatMessage) => {
      if (data.session_id === sessionId) {
        setMessages(prev => {
          // Avoid duplicates
          if (prev.some(msg => msg.id === data.id)) return prev;
          return [...prev, data];
        });
        scrollToBottom();
      }
    };

    webSocketService.subscribe('chat_message', handleChatMessage);

    return () => {
      webSocketService.unsubscribe('chat_message', handleChatMessage);
    };
  }, [sessionId, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [inputValue]);

  const loadSession = async (id: string) => {
    try {
      const response = await apiService.getChatMessages(id);
      setMessages(response.messages);
      
      // Load planning progress
      const progress = await apiService.getPlanningProgress(id);
      setPlanningProgress(progress);
      
      scrollToBottom();
    } catch (error) {
      console.error('Failed to load chat session:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const session = await apiService.createChatSession('New Mission Planning');
      setCurrentSession(session);
      onSessionChange?.(session);
      return session;
    } catch (error) {
      console.error('Failed to create chat session:', error);
      return null;
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() && fileUploads.length === 0) return;

    let activeSessionId = sessionId;
    
    // Create session if none exists
    if (!activeSessionId) {
      const newSession = await createNewSession();
      if (!newSession) return;
      activeSessionId = newSession.id;
    }

    const messageContent = inputValue.trim();
    const files = fileUploads.map(upload => upload.file);

    // Clear input immediately for better UX
    setInputValue('');
    setFileUploads([]);
    setIsLoading(true);

    try {
      // Add user message to UI immediately
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        session_id: activeSessionId,
        sender: 'user',
        content: messageContent,
        timestamp: new Date().toISOString(),
        message_type: 'text',
        attachments: files.map(file => ({
          id: `temp-${file.name}`,
          filename: file.name,
          file_type: file.type,
          file_size: file.size,
          url: URL.createObjectURL(file),
        })),
      };

      setMessages(prev => [...prev, userMessage]);
      scrollToBottom();

      // Send message to backend
      const response = await apiService.sendChatMessage(activeSessionId, messageContent, files);
      
      // Replace temp message with actual response
      setMessages(prev => 
        prev.map(msg => msg.id === userMessage.id ? response : msg)
      );

      // Update planning progress
      const progress = await apiService.getPlanningProgress(activeSessionId);
      setPlanningProgress(progress);

    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove temp message on error
      setMessages(prev => prev.filter(msg => msg.id !== `temp-${Date.now()}`));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addFiles(files);
  };

  const addFiles = (files: File[]) => {
    const newUploads: FileUpload[] = files.map(file => ({
      id: `${Date.now()}-${file.name}`,
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }));

    setFileUploads(prev => [...prev, ...newUploads]);
  };

  const removeFile = (id: string) => {
    setFileUploads(prev => {
      const upload = prev.find(u => u.id === id);
      if (upload?.preview) {
        URL.revokeObjectURL(upload.preview);
      }
      return prev.filter(u => u.id !== id);
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
  };

  const generateMission = async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      const mission = await apiService.generateMissionFromChat(sessionId);
      onMissionGenerated?.(mission.id);
    } catch (error) {
      console.error('Failed to generate mission:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.sender === 'user';
    
    return (
      <div key={message.id} className={`chat-message ${isUser ? 'user' : 'ai'} fade-in`}>
        <div className={`chat-bubble ${isUser ? 'user' : 'ai'}`}>
          <div className="text-sm">{message.content}</div>
          
          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 space-y-1">
              {message.attachments.map(attachment => (
                <div key={attachment.id} className="flex items-center space-x-2 text-xs opacity-75">
                  {attachment.file_type.startsWith('image/') ? <Image size={12} /> : <FileText size={12} />}
                  <span>{attachment.filename}</span>
                </div>
              ))}
            </div>
          )}
          
          {/* Mission plan preview */}
          {message.message_type === 'mission_plan' && (
            <div className="mt-2 p-2 bg-blue-50 rounded border">
              <div className="flex items-center space-x-1 text-xs font-medium text-blue-800">
                <MapPin size={12} />
                <span>Mission Plan Generated</span>
              </div>
            </div>
          )}
          
          <div className="text-xs opacity-50 mt-1">
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">Mission Planning Chat</h3>
            {planningProgress && (
              <div className="flex items-center space-x-2 mt-1">
                <div className="text-sm text-gray-600">
                  Stage: {planningProgress.current_stage}
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-1.5">
                  <div 
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${planningProgress.progress_percentage}%` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-500">
                  {planningProgress.progress_percentage}%
                </span>
              </div>
            )}
          </div>
          
          {planningProgress?.current_stage === 'complete' && (
            <button
              onClick={generateMission}
              disabled={isLoading}
              className="btn btn-primary text-sm"
            >
              Generate Mission
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto p-4 custom-scrollbar"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <h4 className="font-medium mb-2">Start Mission Planning</h4>
              <p className="text-sm mb-4">
                Tell me about your search and rescue mission. I'll help you plan every detail.
              </p>
              <div className="text-xs space-y-1">
                <div className="flex items-center justify-center space-x-1">
                  <MapPin size={12} />
                  <span>Define search area</span>
                </div>
                <div className="flex items-center justify-center space-x-1">
                  <Clock size={12} />
                  <span>Set time constraints</span>
                </div>
                <div className="flex items-center justify-center space-x-1">
                  <AlertCircle size={12} />
                  <span>Specify requirements</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map(renderMessage)}
        
        {isLoading && (
          <div className="chat-message ai">
            <div className="chat-bubble ai">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />

        {/* Drag overlay */}
        {dragOver && (
          <div className="absolute inset-0 bg-blue-500 bg-opacity-20 border-2 border-dashed border-blue-500 rounded-lg flex items-center justify-center z-10">
            <div className="text-blue-700 font-medium">Drop files here to attach</div>
          </div>
        )}
      </div>

      {/* File uploads preview */}
      {fileUploads.length > 0 && (
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            {fileUploads.map(upload => (
              <div key={upload.id} className="relative group">
                {upload.preview ? (
                  <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100">
                    <img 
                      src={upload.preview} 
                      alt={upload.file.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center">
                    <FileText size={24} className="text-gray-400" />
                  </div>
                )}
                <button
                  onClick={() => removeFile(upload.id)}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} />
                </button>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-1 rounded-b-lg truncate">
                  {upload.file.name}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200">
        <div className="flex items-end space-x-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Attach files"
          >
            <Paperclip size={20} />
          </button>
          
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your search and rescue mission..."
              className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              disabled={isLoading}
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={(!inputValue.trim() && fileUploads.length === 0) || isLoading}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.txt,.kml,.gpx"
        />
      </div>
    </div>
  );
};