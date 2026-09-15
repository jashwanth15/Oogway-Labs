import React, { useState, useEffect, useRef } from 'react';
import { SessionSidebar } from './components/SessionSidebar';
import { ChatInterface } from './components/ChatInterface';
import { ArtifactViewer } from './components/ArtifactViewer';
import { Message, Session, Artifact, ModelOption, HealthStatus, Citation } from './types';

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('ollama:lenny-growth:latest');
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('light');
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setStatusText(null);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  };

  // 1. Initial Load: Health, Models, and Sessions
  useEffect(() => {
    fetchHealth();
    fetchModels();
    fetchSessions();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (e) {
      console.error('Failed to fetch health:', e);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch('/api/models');
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
        if (data.default) {
          setSelectedModel((prev) => {
            if (!prev || prev === 'ollama:qwen2.5:0.5b') {
              return data.default;
            }
            return prev;
          });
        }
      }
    } catch (e) {
      console.error('Failed to fetch models:', e);
    }
  };

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/sessions');
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (e) {
      console.error('Failed to fetch sessions:', e);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setActiveSessionId(sessionId);
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(
          (data.messages || []).map((m: any) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            citations: m.citations,
            artifacts: m.artifacts,
            created_at: m.created_at
          }))
        );
        // If the session has artifacts, display the most recent one in the viewer
        if (data.artifacts && data.artifacts.length > 0) {
          setActiveArtifact(data.artifacts[data.artifacts.length - 1]);
        } else {
          setActiveArtifact(null);
        }
      }
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setActiveArtifact(null);
    setStatusText(null);
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if (res.ok) {
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          handleNewChat();
        }
      }
    } catch (e) {
      console.error('Failed to delete session:', e);
    }
  };

  // 2. Main Streaming Chat Handler (SSE)
  const handleSendMessage = async (text: string, skill?: string) => {
    const userMsgId = `usr_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    // Append user message immediately
    const userMessage: Message = {
      id: userMsgId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString()
    };

    // Placeholder for streaming assistant message
    const initialAssistantMessage: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      citations: [],
      artifacts: [],
      isStreaming: true,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsStreaming(true);
    setStatusText('Contacting Lenny Knowledge Base...');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          session_id: activeSessionId,
          message: text,
          model: selectedModel,
          skill: skill
        })
      });

      if (!res.ok || !res.body) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let currentSessionId = activeSessionId;
      let accumulatedContent = '';
      let accumulatedCitations: Citation[] = [];
      let accumulatedArtifacts: Artifact[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const jsonStr = trimmed.slice(6);
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'session_init') {
              currentSessionId = event.session_id;
              setActiveSessionId(currentSessionId);
            } else if (event.type === 'status') {
              setStatusText(event.message);
            } else if (event.type === 'citations') {
              accumulatedCitations = event.citations || [];
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, citations: accumulatedCitations } : m
                )
              );
            } else if (event.type === 'token') {
              accumulatedContent += event.token;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: accumulatedContent } : m
                )
              );
            } else if (event.type === 'artifact') {
              accumulatedArtifacts.push(event.artifact);
              setActiveArtifact(event.artifact);
            } else if (event.type === 'done') {
              const finalArtifacts = event.artifacts || accumulatedArtifacts;
              if (finalArtifacts.length > 0) {
                accumulatedArtifacts = finalArtifacts;
                setActiveArtifact(finalArtifacts[finalArtifacts.length - 1]);
              }
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        content: event.full_text || accumulatedContent,
                        artifacts: finalArtifacts,
                        isStreaming: false
                      }
                    : m
                )
              );
              setStatusText(null);
            } else if (event.type === 'error') {
              setStatusText(null);
              accumulatedContent += `\n\n> ⚠️ Error: ${event.message}`;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: accumulatedContent, isStreaming: false } : m
                )
              );
            }
          } catch (err) {
            console.error('Error parsing SSE event:', err);
          }
        }
      }

      // Refresh session list to reflect new title & updated timestamp
      fetchSessions();
    } catch (e: any) {
      if (e.name === 'AbortError') {
        console.log('Stream aborted by user.');
        return;
      }
      console.error('Chat error:', e);
      setStatusText(null);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: `> [!WARNING]\n> Connection error: ${e.message}. Please check that the backend is running.`,
                isStreaming: false
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
      setStatusText(null);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      {/* 1. Left Navigation Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        health={health}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* 2. Center Chat Feed Panel */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden border-r border-slate-800/80">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          onStopStreaming={handleStopStreaming}
          isStreaming={isStreaming}
          statusText={statusText}
          models={models}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          onOpenArtifact={(art) => setActiveArtifact(art)}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          health={health}
          theme={theme}
          onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        />
      </main>

      {/* 3. Right Split-Pane: Claude-style Artifact Viewer */}
      {activeArtifact && (
        <aside className="w-full sm:w-[480px] lg:w-[560px] xl:w-[640px] flex-shrink-0 h-full z-30 transition-all duration-300">
          <ArtifactViewer
            artifact={activeArtifact}
            onClose={() => setActiveArtifact(null)}
            theme={theme}
          />
        </aside>
      )}
    </div>
  );
};
