import React from 'react';
import { Citation } from '../types';
import { X, ExternalLink, Clock, User, Headphones, Check, Copy } from 'lucide-react';

interface VideoModalProps {
  citation: Citation;
  onClose: () => void;
}

export const VideoModal: React.FC<VideoModalProps> = ({ citation, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  const getEmbedUrl = (url?: string, timestamp?: string): string | null => {
    if (!url) return null;
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    if (!match) return null;
    const videoId = match[1];

    let startSec = 0;
    const tMatch = url.match(/[?&]t=(\d+)s?/);
    if (tMatch) {
      startSec = parseInt(tMatch[1], 10);
    } else if (timestamp) {
      const parts = timestamp.split(':').map(Number);
      if (parts.length === 3) startSec = parts[0] * 3600 + parts[1] * 60 + parts[2];
      else if (parts.length === 2) startSec = parts[0] * 60 + parts[1];
    }

    return `https://www.youtube-nocookie.com/embed/${videoId}?start=${startSec}&autoplay=1`;
  };

  const embedUrl = getEmbedUrl(citation.youtube_url, citation.timestamp);

  const handleCopySnippet = async () => {
    try {
      await navigator.clipboard.writeText(`"${citation.snippet}" — ${citation.guest} (${citation.timestamp})`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy snippet:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
      <div 
        className="w-full max-w-3xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-brand-500/10 text-brand-400">
              <Headphones className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>{citation.guest}</span>
                {citation.timestamp && (
                  <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                    {citation.timestamp}
                  </span>
                )}
              </h3>
              <p className="text-[11px] text-slate-400 truncate max-w-md">
                {citation.title}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {citation.youtube_url && (
              <a
                href={citation.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Open in YouTube"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Close modal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Video Player or Fallback */}
        <div className="relative aspect-video bg-black flex items-center justify-center">
          {embedUrl ? (
            <iframe
              src={embedUrl}
              title={citation.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              className="w-full h-full border-0"
            />
          ) : (
            <div className="text-center p-8 text-slate-400 space-y-2">
              <Headphones className="w-10 h-10 mx-auto text-slate-600 mb-2" />
              <p className="text-sm font-medium">Direct video stream unavailable for this episode.</p>
              {citation.youtube_url && (
                <a
                  href={citation.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 mt-2 rounded-xl bg-brand-600 text-slate-950 text-xs font-bold hover:bg-brand-500 transition-colors"
                >
                  <span>Open Video in New Tab</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          )}
        </div>

        {/* Verified Quote Transcript Excerpt */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>Verified Transcript Excerpt</span>
              {citation.relevance_score && (
                <span className="text-slate-500">• Match Score: {citation.relevance_score}</span>
              )}
            </span>
            <button
              onClick={handleCopySnippet}
              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied quote</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy quote</span>
                </>
              )}
            </button>
          </div>
          <blockquote className="text-xs text-slate-300 italic font-serif leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 max-h-28 overflow-y-auto">
            "{citation.snippet}"
          </blockquote>
        </div>
      </div>
    </div>
  );
};
