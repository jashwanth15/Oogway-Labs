import React, { useState, useRef, useEffect } from 'react';
import { ModelOption } from '../types';
import { Cpu, Cloud, ChevronDown, Check } from 'lucide-react';

interface ModelSelectorProps {
  models: ModelOption[];
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  isLoading?: boolean;
}

const FALLBACK_MODELS: ModelOption[] = [
  { id: 'ollama:qwen2.5:0.5b', name: 'Local: qwen2.5:0.5b (Ollama)', provider: 'ollama', is_local: true, is_active: true },
  { id: 'ollama:mistral:latest', name: 'Local: mistral:latest (Ollama)', provider: 'ollama', is_local: true, is_active: false },
  { id: 'claude-3-5-sonnet', name: 'Cloud: Claude 3.5 Sonnet (Anthropic)', provider: 'anthropic', is_local: false, is_active: false },
  { id: 'gpt-4o', name: 'Cloud: GPT-4o (OpenAI)', provider: 'openai', is_local: false, is_active: false }
];

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onSelectModel,
  isLoading
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const displayModels = models && models.length > 0 ? models : FALLBACK_MODELS;
  const current = displayModels.find((m) => m.id === selectedModel) || displayModels[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <div className="relative inline-flex items-center text-left" ref={containerRef}>
      {/* Dropdown Toggle Button */}
      <button
        type="button"
        disabled={isLoading}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Select AI Model"
        className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border transition-all shadow-sm ${
          isOpen
            ? 'border-brand-500 ring-1 ring-brand-500/30 text-white'
            : 'border-slate-700/80 hover:border-slate-500 text-slate-200'
        } ${isLoading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        {current?.is_local ? (
          <div className="flex items-center gap-1.5 text-emerald-400">
            <Cpu className="w-3.5 h-3.5" />
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-sky-400">
            <Cloud className="w-3.5 h-3.5" />
          </div>
        )}

        <span className="font-mono text-xs truncate max-w-[150px] sm:max-w-[200px]">
          {current?.name || selectedModel}
        </span>

        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-brand-400' : ''
          }`}
        />
      </button>

      {/* Floating Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-72 sm:w-80 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 flex items-center justify-between">
            <span>Inference Engines</span>
            <span className="text-emerald-400 font-mono text-[10px]">Active</span>
          </div>

          <div className="py-1 space-y-1 max-h-72 overflow-y-auto">
            {displayModels.map((m) => {
              const isSelected = m.id === selectedModel;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    onSelectModel(m.id);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800 text-white font-medium border border-slate-700/90 shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    {m.is_local ? (
                      <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-400 flex-shrink-0">
                        <Cpu className="w-3.5 h-3.5" />
                      </div>
                    ) : (
                      <div className="p-1 rounded-md bg-sky-500/10 text-sky-400 flex-shrink-0">
                        <Cloud className="w-3.5 h-3.5" />
                      </div>
                    )}
                    <div className="truncate">
                      <div className="truncate font-mono text-xs text-slate-100">{m.name}</div>
                      <div className="text-[10px] text-slate-400">
                        {m.is_local ? 'Offline • Fast CPU inference' : 'Cloud • Requires API Key'}
                      </div>
                    </div>
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-brand-400 flex-shrink-0 ml-2" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
