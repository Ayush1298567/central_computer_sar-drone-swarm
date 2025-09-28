export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'drone' | 'mission';
  content: string;
  timestamp: number;
  user_id?: string;
  metadata?: {
    drone_id?: string;
    mission_id?: string;
    location?: { lat: number; lng: number };
    attachments?: ChatAttachment[];
  };
}

export interface ChatAttachment {
  id: string;
  type: 'image' | 'video' | 'document' | 'location';
  url: string;
  name: string;
  size: number;
}

export interface ChatSession {
  id: string;
  title: string;
  participants: string[];
  created_at: number;
  last_message_at: number;
  status: 'active' | 'archived' | 'deleted';
}

export interface ConversationalCommand {
  type: 'mission_create' | 'drone_command' | 'analysis_request' | 'status_query';
  parameters: Record<string, any>;
  context: {
    urgency: 'low' | 'medium' | 'high' | 'critical';
    location?: { lat: number; lng: number };
    mission_id?: string;
    drone_id?: string;
  };
}