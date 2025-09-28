/**
 * Chat API Service
 *
 * Handles all chat-related API calls including:
 * - Chat message sending and receiving
 * - Conversation history management
 * - Real-time chat updates via WebSocket
 * - Message attachment handling
 */

import {
  ChatMessage,
  Conversation,
  ConversationParticipant,
  SendMessageRequest,
  CreateConversationRequest,
  UpdateConversationRequest,
  ChatTypingIndicator,
  ChatPresence,
  ChatNotification,
  MessageType,
  ConversationStatus,
  ConversationPriority,
  WebSocketMessage,
  WebSocketMessagePayload,
  ApiResponse,
  PaginationParams,
  PaginatedResponse,
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const API_TIMEOUT = 10000; // 10 seconds

// Error handling utility
class ChatServiceError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ChatServiceError';
  }
}

// Retry configuration
const RETRY_CONFIG = {
  maxAttempts: 3,
  delayMs: 1000,
  backoffMultiplier: 2,
};

// WebSocket Manager for real-time chat
class ChatWebSocketManager {
  private static instance: ChatWebSocketManager;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval?: NodeJS.Timeout;
  private isConnected = false;
  private messageHandlers: Map<string, (message: any) => void> = new Map();
  private connectionCallbacks: Array<(connected: boolean) => void> = [];
  private typingTimeouts: Map<string, NodeJS.Timeout> = new Map();

  static getInstance(): ChatWebSocketManager {
    if (!ChatWebSocketManager.instance) {
      ChatWebSocketManager.instance = new ChatWebSocketManager();
    }
    return ChatWebSocketManager.instance;
  }

  connect(userId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/chat?user_id=${userId}`);

      this.ws.onopen = () => {
        console.log('Chat WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.connectionCallbacks.forEach(callback => callback(true));
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('Chat WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        this.connectionCallbacks.forEach(callback => callback(false));

        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect(userId);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
        this.isConnected = false;
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopHeartbeat();
    this.isConnected = false;
    this.typingTimeouts.forEach(timeout => clearTimeout(timeout));
    this.typingTimeouts.clear();
  }

  sendMessage(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  onMessage(handler: (message: any) => void): string {
    const id = Math.random().toString(36).substr(2, 9);
    this.messageHandlers.set(id, handler);
    return id;
  }

  offMessage(handlerId: string): void {
    this.messageHandlers.delete(handlerId);
  }

  onConnectionChange(callback: (connected: boolean) => void): void {
    this.connectionCallbacks.push(callback);
  }

  removeConnectionChange(callback: (connected: boolean) => void): void {
    const index = this.connectionCallbacks.indexOf(callback);
    if (index > -1) {
      this.connectionCallbacks.splice(index, 1);
    }
  }

  setTyping(conversationId: string, userId: string, isTyping: boolean): void {
    const typingKey = `${conversationId}:${userId}`;

    if (isTyping) {
      // Clear existing timeout
      const existingTimeout = this.typingTimeouts.get(typingKey);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // Send typing indicator
      this.sendMessage({
        type: 'typing',
        payload: {
          conversation_id: conversationId,
          user_id: userId,
          is_typing: true,
        },
      });

      // Set new timeout to stop typing after 3 seconds
      const timeout = setTimeout(() => {
        this.setTyping(conversationId, userId, false);
      }, 3000);
      this.typingTimeouts.set(typingKey, timeout);
    } else {
      // Clear timeout and send stop typing
      const existingTimeout = this.typingTimeouts.get(typingKey);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
        this.typingTimeouts.delete(typingKey);
      }

      this.sendMessage({
        type: 'typing',
        payload: {
          conversation_id: conversationId,
          user_id: userId,
          is_typing: false,
        },
      });
    }
  }

  private handleWebSocketMessage(message: WebSocketMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendMessage({
          type: 'heartbeat',
          payload: { timestamp: new Date().toISOString() },
        });
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = undefined;
    }
  }

  private scheduleReconnect(userId: string): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect(userId);
    }, delay);
  }
}

// Generic API request wrapper with error handling and retry logic
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(url, {
      ...config,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ChatServiceError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code
      );
    }

    const data: ApiResponse<T> = await response.json();

    if (!data.success) {
      throw new ChatServiceError(data.error || 'API request failed');
    }

    return data.data as T;
  } catch (error) {
    if (error instanceof ChatServiceError) {
      throw error;
    }

    // Handle network errors and retries
    if (retryCount < RETRY_CONFIG.maxAttempts) {
      const delay = RETRY_CONFIG.delayMs * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount);
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiRequest<T>(endpoint, options, retryCount + 1);
    }

    // Final error after all retries
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ChatServiceError('Request timeout');
      }
      throw new ChatServiceError(error.message);
    }

    throw new ChatServiceError('Unknown error occurred');
  }
}

// Chat API Service Class
export class ChatService {
  private static wsManager = ChatWebSocketManager.getInstance();

  /**
   * Initialize chat service with WebSocket connection
   */
  static initialize(userId: string): void {
    this.wsManager.connect(userId);
  }

  /**
   * Disconnect from chat service
   */
  static disconnect(): void {
    this.wsManager.disconnect();
  }

  /**
   * Check if WebSocket is connected
   */
  static isConnected(): boolean {
    return this.wsManager['isConnected'];
  }

  /**
   * Subscribe to WebSocket messages
   */
  static onMessage(handler: (message: WebSocketMessage) => void): string {
    return this.wsManager.onMessage(handler);
  }

  /**
   * Unsubscribe from WebSocket messages
   */
  static offMessage(handlerId: string): void {
    this.wsManager.offMessage(handlerId);
  }

  /**
   * Subscribe to connection status changes
   */
  static onConnectionChange(callback: (connected: boolean) => void): void {
    this.wsManager.onConnectionChange(callback);
  }

  /**
   * Set typing indicator
   */
  static setTyping(conversationId: string, userId: string, isTyping: boolean): void {
    this.wsManager.setTyping(conversationId, userId, isTyping);
  }

  /**
   * Get all conversations for a user
   */
  static async getConversations(
    filters?: {
      status?: ConversationStatus;
      priority?: ConversationPriority;
      participant?: string;
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<Conversation>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/conversations${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<Conversation>>(endpoint);
  }

  /**
   * Get a single conversation by ID
   */
  static async getConversation(id: string): Promise<Conversation> {
    return apiRequest<Conversation>(`/conversations/${id}`);
  }

  /**
   * Create a new conversation
   */
  static async createConversation(
    conversationData: CreateConversationRequest
  ): Promise<Conversation> {
    return apiRequest<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify(conversationData),
    });
  }

  /**
   * Update an existing conversation
   */
  static async updateConversation(
    id: string,
    updates: UpdateConversationRequest
  ): Promise<Conversation> {
    return apiRequest<Conversation>(`/conversations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete a conversation
   */
  static async deleteConversation(id: string): Promise<void> {
    return apiRequest<void>(`/conversations/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Get messages for a conversation
   */
  static async getMessages(
    conversationId: string,
    filters?: {
      message_type?: MessageType;
      sender_id?: string;
      start_date?: string;
      end_date?: string;
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<ChatMessage>> {
    const params = new URLSearchParams();
    params.append('conversation_id', conversationId);

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/messages${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<ChatMessage>>(endpoint);
  }

  /**
   * Send a message
   */
  static async sendMessage(messageData: SendMessageRequest): Promise<ChatMessage> {
    // Handle file attachments
    if (messageData.attachments && messageData.attachments.length > 0) {
      const formData = new FormData();
      formData.append('conversation_id', messageData.conversation_id);
      formData.append('content', messageData.content);
      formData.append('message_type', messageData.message_type || 'text');

      if (messageData.reply_to) {
        formData.append('reply_to', messageData.reply_to);
      }

      if (messageData.metadata) {
        formData.append('metadata', JSON.stringify(messageData.metadata));
      }

      messageData.attachments.forEach((file, index) => {
        formData.append(`attachments[${index}]`, file);
      });

      const response = await fetch(`${API_BASE_URL}/messages`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ChatServiceError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData.code
        );
      }

      const data: ApiResponse<ChatMessage> = await response.json();

      if (!data.success) {
        throw new ChatServiceError(data.error || 'Failed to send message');
      }

      return data.data as ChatMessage;
    } else {
      // Send text-only message
      return apiRequest<ChatMessage>('/messages', {
        method: 'POST',
        body: JSON.stringify(messageData),
      });
    }
  }

  /**
   * Edit a message
   */
  static async editMessage(
    messageId: string,
    newContent: string
  ): Promise<ChatMessage> {
    return apiRequest<ChatMessage>(`/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify({ content: newContent }),
    });
  }

  /**
   * Delete a message
   */
  static async deleteMessage(messageId: string): Promise<void> {
    return apiRequest<void>(`/messages/${messageId}`, {
      method: 'DELETE',
    });
  }

  /**
   * React to a message
   */
  static async addReaction(
    messageId: string,
    emoji: string
  ): Promise<ChatMessage> {
    return apiRequest<ChatMessage>(`/messages/${messageId}/reactions`, {
      method: 'POST',
      body: JSON.stringify({ emoji }),
    });
  }

  /**
   * Remove a reaction from a message
   */
  static async removeReaction(
    messageId: string,
    emoji: string
  ): Promise<ChatMessage> {
    return apiRequest<ChatMessage>(`/messages/${messageId}/reactions/${emoji}`, {
      method: 'DELETE',
    });
  }

  /**
   * Add participant to conversation
   */
  static async addParticipant(
    conversationId: string,
    participant: { id: string; type: 'user' | 'ai' | 'drone' | 'system' }
  ): Promise<Conversation> {
    return apiRequest<Conversation>(`/conversations/${conversationId}/participants`, {
      method: 'POST',
      body: JSON.stringify(participant),
    });
  }

  /**
   * Remove participant from conversation
   */
  static async removeParticipant(
    conversationId: string,
    participantId: string
  ): Promise<Conversation> {
    return apiRequest<Conversation>(
      `/conversations/${conversationId}/participants/${participantId}`,
      {
        method: 'DELETE',
      }
    );
  }

  /**
   * Update participant role
   */
  static async updateParticipantRole(
    conversationId: string,
    participantId: string,
    role: 'owner' | 'admin' | 'member' | 'observer'
  ): Promise<ConversationParticipant> {
    return apiRequest<ConversationParticipant>(
      `/conversations/${conversationId}/participants/${participantId}/role`,
      {
        method: 'PUT',
        body: JSON.stringify({ role }),
      }
    );
  }

  /**
   * Get user notifications
   */
  static async getNotifications(
    filters?: {
      type?: 'message' | 'mention' | 'reaction' | 'system';
      read?: boolean;
    },
    pagination?: PaginationParams
  ): Promise<PaginatedResponse<ChatNotification>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    if (pagination) {
      Object.entries(pagination).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/notifications${queryString ? `?${queryString}` : ''}`;

    return apiRequest<PaginatedResponse<ChatNotification>>(endpoint);
  }

  /**
   * Mark notifications as read
   */
  static async markNotificationsRead(notificationIds: string[]): Promise<void> {
    return apiRequest<void>('/notifications/read', {
      method: 'PUT',
      body: JSON.stringify({ notification_ids: notificationIds }),
    });
  }

  /**
   * Get conversation statistics
   */
  static async getConversationStats(filters?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{
    total_conversations: number;
    active_conversations: number;
    total_messages: number;
    messages_by_type: Record<MessageType, number>;
    average_response_time: number;
    conversations_by_priority: Record<ConversationPriority, number>;
  }> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const queryString = params.toString();
    const endpoint = `/conversations/stats${queryString ? `?${queryString}` : ''}`;

    return apiRequest(endpoint);
  }
}

// Export error class and WebSocket manager for consumers
export { ChatServiceError, ChatWebSocketManager };