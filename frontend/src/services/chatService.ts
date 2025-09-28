// Chat API Service
// Handles chat message sending, receiving, and real-time updates via WebSocket

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

// TypeScript interfaces for chat requests/responses
export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name: string;
  sender_type: 'user' | 'ai' | 'drone' | 'system';
  message_type: 'text' | 'image' | 'video' | 'location' | 'command' | 'status';
  content: string;
  attachments?: ChatAttachment[];
  metadata?: Record<string, any>;
  timestamp: string;
  edited_at?: string;
  is_deleted: boolean;
  reply_to?: string;
  reactions?: MessageReaction[];
}

export interface ChatAttachment {
  id: string;
  type: 'image' | 'video' | 'document' | 'location' | 'audio';
  filename: string;
  url: string;
  size: number;
  mime_type: string;
  thumbnail_url?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface MessageReaction {
  emoji: string;
  user_id: string;
  user_name: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  participants: ConversationParticipant[];
  created_at: string;
  updated_at: string;
  last_message?: ChatMessage;
  unread_count: number;
  is_active: boolean;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  tags: string[];
  mission_id?: string;
}

export interface ConversationParticipant {
  id: string;
  name: string;
  type: 'user' | 'ai' | 'drone' | 'system';
  role: 'admin' | 'operator' | 'observer' | 'ai_assistant';
  joined_at: string;
  is_online: boolean;
}

export interface SendMessageRequest {
  conversation_id: string;
  message_type: 'text' | 'image' | 'video' | 'location' | 'command' | 'status';
  content: string;
  attachments?: File[];
  reply_to?: string;
  metadata?: Record<string, any>;
}

export interface CreateConversationRequest {
  title: string;
  participants: string[];
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  mission_id?: string;
  tags?: string[];
}

export interface ChatAnalytics {
  total_messages: number;
  active_conversations: number;
  average_response_time: number;
  message_types_distribution: Record<string, number>;
  participants_activity: {
    participant_id: string;
    participant_name: string;
    messages_sent: number;
    last_activity: string;
  }[];
}

// Real-time chat data management
class ChatDataManager {
  private listeners: Map<string, Set<(message: ChatMessage) => void>> = new Map();
  private conversationListeners: Map<string, Set<(conversation: Conversation) => void>> = new Map();
  private websocket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connectWebSocket() {
    if (this.websocket?.readyState === WebSocket.OPEN) return;

    this.websocket = new WebSocket(api.wsUrl + '/chat');

    this.websocket.onopen = () => {
      console.log('Chat WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'new_message' && data.message) {
          this.notifyMessageListeners(data.conversation_id, data.message);
        } else if (data.type === 'conversation_update' && data.conversation) {
          this.notifyConversationListeners(data.conversation.id, data.conversation);
        } else if (data.type === 'message_deleted' && data.message_id) {
          this.notifyMessageDeleted(data.conversation_id, data.message_id);
        } else if (data.type === 'message_edited' && data.message) {
          this.notifyMessageEdited(data.conversation_id, data.message);
        } else if (data.type === 'typing_indicator' && data.typing) {
          this.notifyTypingIndicator(data.conversation_id, data.typing);
        }
      } catch (error) {
        console.error('Error parsing chat WebSocket message:', error);
      }
    };

    this.websocket.onclose = () => {
      console.log('Chat WebSocket disconnected');
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        setTimeout(() => this.connectWebSocket(), delay);
      }
    };

    this.websocket.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
    };
  }

  subscribeToConversation(conversationId: string, callback: (message: ChatMessage) => void) {
    if (!this.listeners.has(conversationId)) {
      this.listeners.set(conversationId, new Set());
    }
    this.listeners.get(conversationId)!.add(callback);

    if (this.websocket?.readyState !== WebSocket.OPEN) {
      this.connectWebSocket();
    }

    return () => {
      this.listeners.get(conversationId)?.delete(callback);
    };
  }

  subscribeToConversationUpdates(conversationId: string, callback: (conversation: Conversation) => void) {
    if (!this.conversationListeners.has(conversationId)) {
      this.conversationListeners.set(conversationId, new Set());
    }
    this.conversationListeners.get(conversationId)!.add(callback);

    return () => {
      this.conversationListeners.get(conversationId)?.delete(callback);
    };
  }

  sendTypingIndicator(conversationId: string, isTyping: boolean) {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify({
        type: 'typing_indicator',
        conversation_id: conversationId,
        is_typing: isTyping,
        user_id: api.getUserId(),
        timestamp: new Date().toISOString()
      }));
    }
  }

  private notifyMessageListeners(conversationId: string, message: ChatMessage) {
    this.listeners.get(conversationId)?.forEach(callback => callback(message));
  }

  private notifyConversationListeners(conversationId: string, conversation: Conversation) {
    this.conversationListeners.get(conversationId)?.forEach(callback => callback(conversation));
  }

  private notifyMessageDeleted(conversationId: string, messageId: string) {
    // Handle message deletion in listeners
    this.listeners.get(conversationId)?.forEach(callback => {
      // Could emit a special message with deletion info
    });
  }

  private notifyMessageEdited(conversationId: string, message: ChatMessage) {
    this.listeners.get(conversationId)?.forEach(callback => callback(message));
  }

  private notifyTypingIndicator(conversationId: string, typing: any) {
    // Handle typing indicators in listeners if needed
  }
}

// API service class with error handling and retry logic
class ChatService {
  private queryClient: ReturnType<typeof useQueryClient>;
  private dataManager = new ChatDataManager();

  constructor() {
    // Query client will be injected when using hooks
  }

  setQueryClient(client: ReturnType<typeof useQueryClient>) {
    this.queryClient = client;
  }

  getDataManager() {
    return this.dataManager;
  }

  // Get conversations
  async getConversations(page = 1, limit = 20): Promise<{ conversations: Conversation[], total: number }> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      const response = await fetch(`${api.baseUrl}/chat/conversations?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch conversations: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        conversations: data.conversations,
        total: data.total
      };
    } catch (error) {
      console.error('Error fetching conversations:', error);
      throw error;
    }
  }

  // Get single conversation with messages
  async getConversation(id: string, page = 1, limit = 50): Promise<{ conversation: Conversation, messages: ChatMessage[] }> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      const response = await fetch(`${api.baseUrl}/chat/conversations/${id}?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch conversation: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching conversation:', error);
      throw error;
    }
  }

  // Create new conversation
  async createConversation(conversationData: CreateConversationRequest): Promise<Conversation> {
    try {
      const response = await fetch(`${api.baseUrl}/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify(conversationData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  }

  // Send message
  async sendMessage(messageData: SendMessageRequest): Promise<ChatMessage> {
    try {
      const formData = new FormData();
      formData.append('conversation_id', messageData.conversation_id);
      formData.append('message_type', messageData.message_type);
      formData.append('content', messageData.content);

      if (messageData.reply_to) {
        formData.append('reply_to', messageData.reply_to);
      }

      if (messageData.metadata) {
        formData.append('metadata', JSON.stringify(messageData.metadata));
      }

      if (messageData.attachments) {
        messageData.attachments.forEach((file, index) => {
          formData.append(`attachments`, file);
        });
      }

      const response = await fetch(`${api.baseUrl}/chat/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  // Edit message
  async editMessage(messageId: string, content: string): Promise<ChatMessage> {
    try {
      const response = await fetch(`${api.baseUrl}/chat/messages/${messageId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error(`Failed to edit message: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error editing message:', error);
      throw error;
    }
  }

  // Delete message
  async deleteMessage(messageId: string): Promise<void> {
    try {
      const response = await fetch(`${api.baseUrl}/chat/messages/${messageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete message: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting message:', error);
      throw error;
    }
  }

  // Add reaction to message
  async addReaction(messageId: string, emoji: string): Promise<ChatMessage> {
    try {
      const response = await fetch(`${api.baseUrl}/chat/messages/${messageId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ emoji }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add reaction: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error adding reaction:', error);
      throw error;
    }
  }

  // Get chat analytics
  async getChatAnalytics(timeRange?: string): Promise<ChatAnalytics> {
    try {
      const params = timeRange ? `?timeRange=${timeRange}` : '';
      const response = await fetch(`${api.baseUrl}/chat/analytics${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch chat analytics: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching chat analytics:', error);
      throw error;
    }
  }

  // Mark conversation as read
  async markConversationAsRead(conversationId: string): Promise<void> {
    try {
      const response = await fetch(`${api.baseUrl}/chat/conversations/${conversationId}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to mark conversation as read: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error marking conversation as read:', error);
      throw error;
    }
  }
}

// Export singleton instances
export const chatService = new ChatService();

// React Query hooks
export const useConversations = (page = 1, limit = 20) => {
  return useQuery({
    queryKey: ['conversations', page, limit],
    queryFn: () => chatService.getConversations(page, limit),
    staleTime: 30000, // 30 seconds
    retry: 3,
  });
};

export const useConversation = (id: string, page = 1, limit = 50) => {
  return useQuery({
    queryKey: ['conversation', id, page, limit],
    queryFn: () => chatService.getConversation(id, page, limit),
    enabled: !!id,
    staleTime: 15000, // 15 seconds
    retry: 3,
  });
};

export const useCreateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatService.createConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    retry: 2,
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatService.sendMessage,
    onSuccess: (message) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      queryClient.invalidateQueries({ queryKey: ['conversation', message.conversation_id] });
    },
    retry: 2,
  });
};

export const useEditMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ messageId, content }: { messageId: string; content: string }) =>
      chatService.editMessage(messageId, content),
    onSuccess: (message) => {
      queryClient.invalidateQueries({ queryKey: ['conversation', message.conversation_id] });
    },
    retry: 2,
  });
};

export const useDeleteMessage = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatService.deleteMessage,
    onSuccess: (_, messageId) => {
      // Invalidate all conversations since we don't know which one the message belongs to
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    retry: 2,
  });
};

export const useAddReaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ messageId, emoji }: { messageId: string; emoji: string }) =>
      chatService.addReaction(messageId, emoji),
    onSuccess: (message) => {
      queryClient.invalidateQueries({ queryKey: ['conversation', message.conversation_id] });
    },
    retry: 2,
  });
};

export const useChatAnalytics = (timeRange?: string) => {
  return useQuery({
    queryKey: ['chatAnalytics', timeRange],
    queryFn: () => chatService.getChatAnalytics(timeRange),
    staleTime: 60000, // 1 minute
    retry: 3,
  });
};

export const useMarkConversationAsRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatService.markConversationAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    retry: 2,
  });
};

// Real-time subscription hooks
export const useMessageSubscription = (conversationId: string) => {
  const queryClient = useQueryClient();

  return (callback: (message: ChatMessage) => void) => {
    return chatService.getDataManager().subscribeToConversation(conversationId, (message) => {
      // Update React Query cache
      queryClient.setQueryData(['conversation', conversationId], (oldData: any) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          messages: [...oldData.messages, message]
        };
      });
      callback(message);
    });
  };
};

export const useConversationSubscription = (conversationId: string) => {
  return (callback: (conversation: Conversation) => void) => {
    return chatService.getDataManager().subscribeToConversationUpdates(conversationId, callback);
  };
};

// Typing indicator hook
export const useTypingIndicator = (conversationId: string) => {
  const sendTyping = (isTyping: boolean) => {
    chatService.getDataManager().sendTypingIndicator(conversationId, isTyping);
  };

  return { sendTyping };
};