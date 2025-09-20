export interface ChatSession {
  id: string;
  name: string;
  status: 'active' | 'planning' | 'completed' | 'archived';
  created_at: string;
  updated_at: string;
  message_count: number;
  mission_id?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: string;
  message_type: 'text' | 'mission_plan' | 'file' | 'system';
  attachments?: ChatAttachment[];
  metadata?: Record<string, any>;
}

export interface ChatAttachment {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  url: string;
}

export interface PlanningProgress {
  session_id: string;
  current_stage: 'requirements' | 'area_selection' | 'drone_assignment' | 'review' | 'complete';
  progress_percentage: number;
  collected_requirements: {
    search_area?: any;
    priority?: string;
    drone_count?: number;
    time_limit?: number;
    weather_constraints?: any;
    special_requirements?: string[];
  };
  next_questions: string[];
}