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
    <div className="relative inline-block">
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-200 hover:border-slate-700 transition-colors">
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

        <select
          value={selectedModel}
          onChange={(e) => onSelectModel(e.target.value)}
          disabled={isLoading}
          aria-label="Select AI Model"
          className="bg-transparent text-slate-200 border-none outline-none cursor-pointer pr-4 font-mono text-xs focus:ring-0"
        >
          {models.map((m) => (
            <option key={m.id} value={m.id} className="bg-slate-900 text-slate-200 py-1">
              {m.is_local ? `⚡ ${m.name}` : `☁️ ${m.name}`}
            </option>
          ))}
        </select>
        <ChevronDown className="w-3 h-3 text-slate-400 pointer-events-none -ml-3" />
      </div>
    </div>
  );
};
