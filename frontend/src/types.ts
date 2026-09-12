export interface Citation {
  episode_id: string;
  guest: string;
  title: string;
  youtube_url?: string;
  timestamp?: string;
  snippet: string;
  relevance_score?: number;
}

export interface Artifact {
  id?: string;
  title: string;
  artifact_type: 'markdown' | 'html' | 'code';
  content: string;
  created_at?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Citation[];
  artifacts?: Artifact[];
  created_at?: string;
  isStreaming?: boolean;
}

export interface Session {
  id: string;
  title: string;
  model_used: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ModelOption {
  id: string;
  name: string;
  provider: 'ollama' | 'anthropic' | 'openai';
  is_local: boolean;
  is_active: boolean;
}

export interface HealthStatus {
  status: string;
  database: {
    connected: boolean;
    type: string;
  };
  ollama: {
    available: boolean;
    models: string[];
  };
  knowledge_base: {
    ready: boolean;
    total_chunks: number;
  };
}
