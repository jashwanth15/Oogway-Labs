import React from 'react';
import { Session, HealthStatus } from '../types';
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  Database, 
  Sparkles,
  Layers,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface SessionSidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  health: HealthStatus | null;
  isOpen: boolean;
  onToggle: () => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  health,
  isOpen,
  onToggle
}) => {
  return (
    <>
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 flex flex-col w-72 bg-slate-900 border-r border-slate-800 transform transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0 md:hidden'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div>
                <h1 className="text-base font-extrabold text-slate-100 tracking-tight">
                  Oogway Labs
                </h1>
                <p className="text-[11px] text-brand-500 font-bold uppercase tracking-wider">
                  FDE Growth Assistant
                </p>
              </div>
            </div>
            <button
              onClick={onToggle}
              className="p-1 rounded-md text-slate-400 hover:text-white md:hidden"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat CTA */}
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-slate-950 font-semibold text-xs shadow-md shadow-brand-600/20 transition-all duration-150 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>New Chat Session</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1 flex items-center justify-between">
            <span>Conversations</span>
            <span className="font-mono">{sessions.length}</span>
          </div>

          {sessions.length === 0 ? (
            <div className="text-center py-8 px-4 text-xs text-slate-400">
              <MessageSquare className="w-6 h-6 mx-auto mb-2 text-slate-400 opacity-60" />
              <p>No past conversations yet.</p>
              <p className="text-[11px] text-slate-400 mt-1">Start a chat to explore Lenny's transcripts!</p>
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-colors cursor-pointer ${
                  activeSessionId === s.id
                    ? 'bg-slate-800 text-white font-medium border border-slate-700/60'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
                onClick={() => onSelectSession(s.id)}
              >
                <div className="flex items-center gap-2 truncate pr-1">
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-brand-400" />
                  <span className="truncate">{s.title || 'Untitled Session'}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:text-red-400 hover:bg-slate-700/50 transition-all"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Knowledge Base Status Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-xs text-slate-400">
          <div className="flex items-center justify-between mb-1.5">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <Database className="w-3.5 h-3.5 text-brand-400" />
              Knowledge Base
            </span>
            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live Grounding
            </span>
          </div>

          <div className="text-[11px] space-y-0.5 text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Episodes:</span>
              <span className="text-slate-300 font-semibold">303 Episodes</span>
            </div>
            <div className="flex justify-between">
              <span>Chunks Indexed:</span>
              <span className="text-slate-300 font-semibold">
                {health?.knowledge_base?.total_chunks || '15,251'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>DB Mode:</span>
              <span className="text-slate-300 capitalize">
                {health?.database?.type || 'PostgreSQL'}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 md:hidden backdrop-blur-sm"
          onClick={onToggle}
        />
      )}
    </>
  );
};
