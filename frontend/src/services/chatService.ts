/**
 * Chat service for SAR Mission Commander
 */
import { api, handleApiError } from './api';
import { ChatMessage, ChatSession } from './missionService';

/**
 * Chat API functions
 */
export const chatService = {
  /**
   * Get chat messages for a mission
   */
  async getMissionChat(missionId: string): Promise<ChatSession> {
    try {
      const response = await api.get(`/missions/${missionId}/chat`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Send a chat message for a mission
   */
  async sendMissionChatMessage(missionId: string, content: string, userId?: string): Promise<any> {
    try {
      const response = await api.post(`/missions/${missionId}/chat`, {
        content,
        message_type: 'text',
        user_id: userId || 'default_user'
      });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Get chat session info
   */
  async getChatSession(_sessionId: string): Promise<ChatSession> {
    try {
      // This would need a specific endpoint for getting session info
      // For now, we'll use the mission chat endpoint
      throw new Error('Not implemented - use getMissionChat instead');
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  /**
   * Format chat message for display
   */
  formatMessage(message: ChatMessage): {
    id: number;
    content: string;
    timestamp: string;
    isUser: boolean;
    isAI: boolean;
    isSystem: boolean;
    confidence?: number;
  } {
    return {
      id: message.id,
      content: message.content,
      timestamp: new Date(message.timestamp).toLocaleTimeString(),
      isUser: message.message_type === 'user_input',
      isAI: message.message_type === 'ai_response',
      isSystem: message.message_type === 'system',
      confidence: message.ai_confidence
    };
  },

  /**
   * Get conversation summary
   */
  getConversationSummary(messages: ChatMessage[]): {
    messageCount: number;
    lastActivity: string;
    currentStage: string;
  } {
    if (messages.length === 0) {
      return {
        messageCount: 0,
        lastActivity: 'No messages',
        currentStage: 'planning'
      };
    }

    const lastMessage = messages[messages.length - 1];
    const aiMessages = messages.filter(m => m.message_type === 'ai_response');

    return {
      messageCount: messages.length,
      lastActivity: new Date(lastMessage.timestamp).toLocaleString(),
      currentStage: aiMessages.length > 0 ? 'in_progress' : 'planning'
    };
  }
};

export default chatService;