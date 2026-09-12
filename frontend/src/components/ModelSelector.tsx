import React from 'react';
import { ModelOption } from '../types';
import { Cpu, Cloud, ChevronDown } from 'lucide-react';

interface ModelSelectorProps {
  models: ModelOption[];
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  isLoading?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onSelectModel,
  isLoading
}) => {
  const current = models.find((m) => m.id === selectedModel) || models[0];

  return (
    <div className="relative inline-flex items-center">
      {/* Visual Button Display */}
      <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-xs font-medium text-slate-200 shadow-sm transition-all pointer-events-none">
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

        <span className="font-mono text-xs text-slate-200">
          {current?.name || selectedModel}
        </span>

        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
      </div>

      {/* Invisible Full-Overlay Native Select (captures 100% of clicks across the entire badge) */}
      <select
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
        disabled={isLoading}
        aria-label="Select AI Model"
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id} className="bg-slate-900 text-slate-100 py-2">
            {m.is_local ? `⚡ ${m.name}` : `☁️ ${m.name}`}
          </option>
        ))}
      </select>
    </div>
  );
};
