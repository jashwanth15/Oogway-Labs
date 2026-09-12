import React, { useState } from 'react';
import { Citation } from '../types';
import { Headphones, ExternalLink, Clock, ChevronDown, ChevronUp } from 'lucide-react';

interface CitationBadgeProps {
  citation: Citation;
  index: number;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, index }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block m-1">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-slate-800/90 text-slate-300 hover:text-white hover:bg-slate-700/90 border border-slate-700/80 transition-all duration-150"
      >
        <Headphones className="w-3.5 h-3.5 text-brand-500" />
        <span className="font-semibold text-brand-400">[{index + 1}]</span>
        <span className="truncate max-w-[140px]">{citation.guest}</span>
        {citation.timestamp && (
          <span className="text-[10px] text-slate-400 font-mono">
            {citation.timestamp}
          </span>
        )}
        {isOpen ? (
          <ChevronUp className="w-3 h-3 text-slate-400" />
        ) : (
          <ChevronDown className="w-3 h-3 text-slate-400" />
        )}
      </button>

      {isOpen && (
        <div className="absolute z-50 bottom-full mb-2 left-0 w-80 sm:w-96 p-4 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-700 shadow-2xl text-left animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-brand-400">
                Lenny's Podcast Transcript
              </div>
              <h4 className="text-sm font-bold text-slate-100 line-clamp-2 mt-0.5">
                {citation.title}
              </h4>
            </div>
            {citation.youtube_url && (
              <a
                href={citation.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
                title="Watch on YouTube"
              >
                <ExternalLink className="w-4 h-4 text-brand-400" />
              </a>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400 mb-3 pb-2 border-b border-slate-800 font-mono">
            <span>Guest: <strong className="text-slate-200">{citation.guest}</strong></span>
            {citation.timestamp && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-brand-400" />
                {citation.timestamp}
              </span>
            )}
            {citation.relevance_score && (
              <span className="ml-auto text-brand-400 font-medium">
                Match: {citation.relevance_score}
              </span>
            )}
          </div>

          <div className="text-xs text-slate-300 bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 italic font-serif leading-relaxed max-h-36 overflow-y-auto">
            "{citation.snippet}"
          </div>
        </div>
      )}
    </div>
  );
};
