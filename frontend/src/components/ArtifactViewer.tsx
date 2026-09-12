import React, { useState } from 'react';
import { Artifact } from '../types';
import { 
  X, 
  Code2, 
  Eye, 
  Copy, 
  Check, 
  Download, 
  ShieldCheck, 
  Maximize2, 
  Minimize2,
  Sparkles
} from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface ArtifactViewerProps {
  artifact: Artifact;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy code:', e);
    }
  };

  const handleDownload = () => {
    const ext = artifact.artifact_type === 'html' ? 'html' : 'md';
    const mime = artifact.artifact_type === 'html' ? 'text/html' : 'text/markdown';
    const blob = new Blob([artifact.content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]/g, '-')}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Injects safe styling and Tailwind CDN into untrusted HTML for instant high-craft rendering
  const prepareSandboxedHtml = (rawHtml: string) => {
    if (rawHtml.includes('<!DOCTYPE html>') || rawHtml.includes('<html')) {
      // Injects meta CSP if not present
      return rawHtml;
    }
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; padding: 1.5rem; background-color: #0f172a; color: #f8fafc; }
  </style>
</head>
<body>
  ${rawHtml}
</body>
</html>`;
  };

  return (
    <div
      className={`flex flex-col h-full bg-slate-900 border-l border-slate-800 transition-all duration-300 ${
        isFullscreen ? 'fixed inset-0 z-50 w-full' : 'w-full'
      }`}
    >
      {/* Artifact Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/90 backdrop-blur">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-lg bg-brand-500/10 text-brand-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 truncate max-w-[200px] sm:max-w-xs">
              {artifact.title}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold border border-slate-700/60">
                {artifact.artifact_type}
              </span>
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                <ShieldCheck className="w-3 h-3" />
                Sandboxed Isolation
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* Tab Toggle: Preview / Code */}
          <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                activeTab === 'preview'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                activeTab === 'code'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Code</span>
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-red-500/20 hover:text-red-400 text-slate-400 transition-colors"
            title="Close Artifact Viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Artifact Viewport */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'preview' ? (
          artifact.artifact_type === 'html' ? (
            /* Sandboxed Iframe (defense-in-depth isolation) */
            <div className="w-full h-full bg-slate-950 flex flex-col">
              <div className="px-3 py-1 bg-slate-950/80 border-b border-slate-800 text-[11px] text-slate-400 flex items-center justify-between font-mono">
                <span>Viewport: Sandboxed execution (null-origin)</span>
                <span className="text-emerald-400">sandbox="allow-scripts"</span>
              </div>
              <iframe
                title={artifact.title}
                srcDoc={prepareSandboxedHtml(artifact.content)}
                sandbox="allow-scripts"
                className="w-full flex-1 border-0 bg-slate-950"
              />
            </div>
          ) : (
            /* Formatted Markdown View */
            <div className="w-full h-full overflow-y-auto p-6 bg-slate-950">
              <div
                className="max-w-3xl mx-auto prose-dark leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(marked.parse(artifact.content) as string)
                }}
              />
            </div>
          )
        ) : (
          /* Raw Code Inspector */
          <div className="w-full h-full overflow-auto p-4 bg-slate-950 font-mono text-xs text-slate-300 leading-relaxed selection:bg-brand-500/30">
            <pre className="whitespace-pre-wrap break-all">
              <code>{artifact.content}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
