// Chat Types
export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_type: 'user' | 'ai' | 'drone' | 'system';
  content: string;
  message_type: MessageType;
  timestamp: string;
  edited_at?: string;
  attachments?: MessageAttachment[];
  metadata?: Record<string, any>;
  reactions?: MessageReaction[];
  reply_to?: string;
  thread_id?: string;
}

export interface Conversation {
  id: string;
  title?: string;
  participants: ConversationParticipant[];
  status: ConversationStatus;
  priority: ConversationPriority;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  archived_at?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ConversationParticipant {
  id: string;
  type: 'user' | 'ai' | 'drone' | 'system';
  name?: string;
  avatar?: string;
  joined_at: string;
  left_at?: string;
  role?: 'owner' | 'admin' | 'member' | 'observer';
}

export interface MessageAttachment {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  url: string;
  thumbnail_url?: string;
  uploaded_at: string;
}

export interface MessageReaction {
  emoji: string;
  user_id: string;
  timestamp: string;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  message_type?: MessageType;
  attachments?: File[];
  reply_to?: string;
  metadata?: Record<string, any>;
}

export interface CreateConversationRequest {
  title?: string;
  participants: Array<{
    id: string;
    type: 'user' | 'ai' | 'drone' | 'system';
  }>;
  initial_message?: string;
  priority?: ConversationPriority;
  tags?: string[];
}

export interface UpdateConversationRequest {
  title?: string;
  status?: ConversationStatus;
  priority?: ConversationPriority;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ChatTypingIndicator {
  conversation_id: string;
  user_id: string;
  user_name?: string;
  is_typing: boolean;
  timestamp: string;
}

export interface ChatPresence {
  user_id: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  last_seen: string;
  custom_status?: string;
}

export interface ChatNotification {
  id: string;
  user_id: string;
  type: 'message' | 'mention' | 'reaction' | 'system';
  title: string;
  message: string;
  conversation_id?: string;
  message_id?: string;
  read: boolean;
  created_at: string;
  action_url?: string;
}

export type MessageType =
  | 'text'
  | 'image'
  | 'video'
  | 'audio'
  | 'file'
  | 'location'
  | 'contact'
  | 'system'
  | 'command'
  | 'mission_update'
  | 'drone_status'
  | 'weather_alert'
  | 'emergency';

export type ConversationStatus =
  | 'active'
  | 'archived'
  | 'muted'
  | 'pinned'
  | 'deleted';

export type ConversationPriority =
  | 'low'
  | 'normal'
  | 'high'
  | 'urgent'
  | 'critical';

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'message' | 'typing' | 'presence' | 'notification' | 'error' | 'heartbeat';
  payload: any;
  timestamp: string;
}

export interface WebSocketMessagePayload {
  message?: ChatMessage;
  typing?: ChatTypingIndicator;
  presence?: ChatPresence;
  notification?: ChatNotification;
  error?: {
    code: string;
    message: string;
  };
  heartbeat?: {
    timestamp: string;
  };
}