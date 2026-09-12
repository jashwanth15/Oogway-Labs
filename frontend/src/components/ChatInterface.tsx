import React, { useState, useRef, useEffect } from 'react';
import { Message, Citation, Artifact, ModelOption, HealthStatus } from '../types';
import { CitationBadge } from './CitationBadge';
import { ModelSelector } from './ModelSelector';
import { 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  LayoutTemplate, 
  PenTool, 
  Layers, 
  HelpCircle,
  Menu,
  FileCode,
  ArrowRight,
  ShieldCheck,
  Compass
} from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (text: string, skill?: string) => void;
  isStreaming: boolean;
  statusText: string | null;
  models: ModelOption[];
  selectedModel: string;
  onSelectModel: (m: string) => void;
  onOpenArtifact: (art: Artifact) => void;
  onToggleSidebar: () => void;
  health: HealthStatus | null;
}

const STARTER_PROMPTS = [
  {
    title: "Rahul Vohra on PMF",
    desc: "How did Superhuman measure product-market fit using the 40% rule?",
    prompt: "How did Superhuman measure product-market fit according to Rahul Vohra? Explain the survey engine and segmentation strategy.",
    icon: Compass,
    skill: "rag"
  },
  {
    title: "Elena Verna: B2B Growth Loops",
    desc: "What are the core mechanics of product-led sales and growth loops?",
    prompt: "Explain Elena Verna's B2B product-led growth loops and how retention fuels acquisition.",
    icon: Layers,
    skill: "rag"
  },
  {
    title: "Ship 30 for 30 Essay",
    desc: "Write a ~1,250-word atomic essay on retention curves",
    prompt: "Write a complete Ship 30 for 30 style essay on why retention curves lie and how top companies fix leaky funnels, based on Lenny's podcast episodes.",
    icon: PenTool,
    skill: "ship30"
  },
  {
    title: "Interactive Growth Artifact",
    desc: "Generate an interactive PMF Scorecard tool in HTML/CSS",
    prompt: "Build an interactive PMF survey calculator and scorecard in HTML/CSS with Tailwind styling based on Rahul Vohra's framework.",
    icon: LayoutTemplate,
    skill: "artifact"
  }
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isStreaming,
  statusText,
  models,
  selectedModel,
  onSelectModel,
  onOpenArtifact,
  onToggleSidebar,
  health
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, statusText]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Top Navbar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              The Lenny Growth Assistant
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
                <ShieldCheck className="w-3 h-3" />
                Grounded Knowledge Base
              </span>
            </h2>
          </div>
        </div>

        {/* Model Switcher & Status */}
        <div className="flex items-center gap-2">
          <ModelSelector
            models={models}
            selectedModel={selectedModel}
            onSelectModel={onSelectModel}
            isLoading={isStreaming}
          />
        </div>
      </header>

      {/* Main Chat Feed */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="max-w-3xl mx-auto py-8 text-center animate-in fade-in duration-300">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-500 to-emerald-400 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-brand-500/20">
              <Sparkles className="w-7 h-7 text-slate-950 font-bold" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-100 tracking-tight mb-2">
              What growth challenge are we solving today?
            </h2>
            <p className="text-sm text-slate-400 max-w-xl mx-auto mb-8 leading-relaxed">
              Synthesizing frameworks, benchmarks, and strategies directly from 303 episodes of Lenny's Podcast. Verified sources, zero hallucinations, and live artifact generation.
            </p>

            {/* Starter Prompt Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-2xl mx-auto">
              {STARTER_PROMPTS.map((p, i) => {
                const Icon = p.icon;
                return (
                  <button
                    key={i}
                    onClick={() => onSendMessage(p.prompt, p.skill)}
                    className="p-4 rounded-xl bg-slate-900/90 border border-slate-800/90 hover:border-brand-500/50 hover:bg-slate-900 transition-all duration-150 group text-left shadow-sm hover:shadow-md hover:shadow-brand-500/5"
                  >
                    <div className="flex items-center gap-2.5 mb-1.5 text-brand-400">
                      <Icon className="w-4 h-4" />
                      <span className="text-xs font-bold text-slate-200 group-hover:text-brand-300 transition-colors">
                        {p.title}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {p.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Chat Messages */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md shadow-brand-600/10">
                    <Bot className="w-4 h-4 text-slate-950 font-bold" />
                  </div>
                )}

                <div
                  className={`flex flex-col max-w-[88%] ${
                    m.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-brand-600 text-slate-950 font-medium shadow-md shadow-brand-600/20'
                        : 'bg-slate-900 border border-slate-800 text-slate-200 shadow-sm prose-dark w-full'
                    }`}
                  >
                    {m.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    ) : (
                      <div
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(marked.parse(m.content) as string)
                        }}
                      />
                    )}
                  </div>

                  {/* Grounded Citations Row */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap items-center gap-1">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
                        Sources:
                      </span>
                      {m.citations.map((c, idx) => (
                        <CitationBadge key={idx} citation={c} index={idx} />
                      ))}
                    </div>
                  )}

                  {/* Generated Artifacts Callout Banner */}
                  {m.artifacts && m.artifacts.length > 0 && (
                    <div className="mt-3 w-full space-y-2">
                      {m.artifacts.map((art, aIdx) => (
                        <div
                          key={aIdx}
                          className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-brand-500/30 hover:border-brand-500 transition-all cursor-pointer group shadow-sm"
                          onClick={() => onOpenArtifact(art)}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="p-2 rounded-lg bg-brand-500/10 text-brand-400 group-hover:scale-105 transition-transform">
                              <FileCode className="w-4 h-4" />
                            </div>
                            <div className="truncate">
                              <div className="text-[10px] font-mono uppercase text-brand-400 font-semibold">
                                Generated Artifact • {art.artifact_type}
                              </div>
                              <h4 className="text-xs font-bold text-slate-100 truncate">
                                {art.title}
                              </h4>
                            </div>
                          </div>
                          <button
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg bg-brand-600/90 text-slate-950 hover:bg-brand-500 transition-colors"
                          >
                            <span>Open</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center flex-shrink-0 mt-0.5 text-slate-300">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {/* Agent Live Status Indicator */}
            {statusText && (
              <div className="flex items-center gap-2.5 text-xs text-brand-400 animate-pulse py-1 pl-12 font-mono">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>{statusText}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Box Footer */}
      <footer className="p-4 bg-slate-950 border-t border-slate-800/80">
        <div className="max-w-3xl mx-auto">
          {/* Quick Skill Tags */}
          <div className="flex items-center gap-2 mb-2 overflow-x-auto text-[11px] pb-1">
            <span className="text-slate-400 font-medium">Quick Actions:</span>
            <button
              onClick={() => setInput("Write a Ship 30 for 30 essay on ")}
              className="px-2.5 py-0.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            >
              ✍️ Ship 30 Essay
            </button>
            <button
              onClick={() => setInput("Build an interactive HTML/CSS scorecard widget for ")}
              className="px-2.5 py-0.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            >
              🎨 HTML/CSS Artifact
            </button>
            <button
              onClick={() => setInput("How does [Guest Name] recommend calculating ")}
              className="px-2.5 py-0.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            >
              🔍 Grounded Q&A
            </button>
          </div>

          <form onSubmit={handleSubmit} className="relative flex items-end gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-2 focus-within:border-brand-500 transition-colors">
            <textarea
              ref={textareaRef}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything grounded in 300+ Lenny's Podcast transcripts... (Enter to send, Shift+Enter for newline)"
              className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 resize-none outline-none px-2 py-1 leading-relaxed"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className={`p-2 rounded-xl transition-all ${
                input.trim() && !isStreaming
                  ? 'bg-brand-600 hover:bg-brand-500 text-slate-950 font-bold shadow-md shadow-brand-600/20 active:scale-95'
                  : 'bg-slate-800 text-slate-400 cursor-not-allowed'
              }`}
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
            <span>Model: <strong className="text-slate-300">{selectedModel}</strong></span>
            <span>Grounding: 303 Podcast Transcripts • Anti-Hallucination Guardrails</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
