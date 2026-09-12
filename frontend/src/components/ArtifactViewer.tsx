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

  // Injects safe styling, Tailwind CDN, and client-side form handler into untrusted HTML for instant high-craft rendering
  const prepareSandboxedHtml = (rawHtml: string) => {
    const interceptorScript = `
<script>
  window.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('submit', (e) => {
      e.preventDefault();
      const form = e.target;
      let resultContainer = document.getElementById('result') || document.getElementById('scorecard') || document.getElementById('pmf-result');
      if (!resultContainer) {
        resultContainer = document.createElement('div');
        resultContainer.id = 'dynamic-submission-result';
        resultContainer.className = 'mt-6 p-5 rounded-2xl bg-slate-900 border border-slate-700 text-slate-100 shadow-2xl animate-fade-in';
        form.parentNode.insertBefore(resultContainer, form.nextSibling);
      }
      
      const formData = new FormData(form);
      const data = {};
      for (let [k, v] of formData.entries()) {
        data[k] = v;
      }
      
      // Check for PMF metrics or rating inputs
      const very = parseFloat(data['very'] || data['very_disappointed'] || data['veryDisappointed'] || 0);
      const somewhat = parseFloat(data['somewhat'] || data['somewhat_disappointed'] || 0);
      const notD = parseFloat(data['not'] || data['not_disappointed'] || 0);
      const total = very + somewhat + notD;
      
      if (total > 0) {
        const pmfScore = Math.round((very / total) * 100);
        const isFit = pmfScore >= 40;
        resultContainer.innerHTML = \`
          <div class="border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-slate-100">Rahul Vohra PMF Scorecard Result</h3>
              <span class="text-xs px-2.5 py-1 rounded-full font-bold \${isFit ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'}">
                \${isFit ? '🎉 Product-Market Fit Achieved' : '⚠️ Below 40% Benchmark'}
              </span>
            </div>
            <div class="mt-3">
              <div class="flex justify-between text-xs mb-1 font-medium">
                <span>Very Disappointed Score</span>
                <span class="font-bold text-lg \${isFit ? 'text-emerald-400' : 'text-amber-400'}">\${pmfScore}%</span>
              </div>
              <div class="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="h-3 rounded-full \${isFit ? 'bg-emerald-500' : 'bg-amber-500'}" style="width: \${Math.min(pmfScore, 100)}%"></div>
              </div>
              <div class="flex justify-between text-[11px] text-slate-400 mt-1">
                <span>0%</span>
                <span class="text-amber-400 font-semibold">40% Target (Superhuman Benchmark)</span>
                <span>100%</span>
              </div>
            </div>
          </div>
          <div class="space-y-2 text-xs text-slate-300">
            <p><strong>Total Respondents:</strong> \${total} (Very: \${very}, Somewhat: \${somewhat}, Not: \${notD})</p>
            <p><strong>Rahul Vohra's Strategy:</strong> \${isFit 
              ? 'Double down on the core features loved by "Very Disappointed" users and politely disregard feedback from "Not Disappointed" users.' 
              : 'Focus solely on the high-expectation customers who answered "Somewhat Disappointed" and analyze what is holding them back from answering "Very Disappointed".'}</p>
          </div>
        \`;
      } else {
        const entries = Object.entries(data);
        const entriesHtml = entries.length > 0
          ? entries.map(([k, v]) => \`
            <div class="py-1.5 border-b border-slate-800 flex flex-col sm:flex-row sm:justify-between">
              <span class="text-slate-400 text-xs font-semibold capitalize">\${k.replace(/[-_]/g, ' ')}:</span>
              <span class="text-slate-200 text-xs font-medium">\${v || '(no response entered)'}</span>
            </div>
          \`).join('')
          : '<p class="text-slate-300 text-xs">Response captured!</p>';
        
        resultContainer.innerHTML = \`
          <div class="flex items-center gap-2 mb-3 text-emerald-400 font-bold text-sm">
            <span>✓ Survey Response Submitted & Evaluated</span>
          </div>
          <div class="space-y-1 mb-4">
            \${entriesHtml}
          </div>
          <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-1.5">
            <p class="font-bold text-amber-400 flex items-center gap-1.5">
              <span>💡 Rahul Vohra Framework Evaluation:</span>
            </p>
            <p class="leading-relaxed">
              Superhuman evaluated customer feedback by grouping responses based on user enthusiasm. 
              Only build roadmap items that move "Somewhat Disappointed" users into "Very Disappointed", 
              while continuing to delight your highest-converting user segment.
            </p>
          </div>
        \`;
      }
      resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });
</script>
`;

    const injectedStyle = `
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; background-color: #0b1120 !important; color: #f1f5f9 !important; padding: 1.5rem !important; }
  input, textarea, select { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; border-radius: 0.5rem !important; padding: 0.5rem 0.75rem !important; width: 100% !important; margin-top: 0.25rem !important; margin-bottom: 0.75rem !important; outline: none !important; }
  input:focus, textarea:focus, select:focus { border-color: #f59e0b !important; ring: 2px #f59e0b !important; }
  label { color: #cbd5e1 !important; font-weight: 500 !important; font-size: 0.875rem !important; }
  button[type="submit"], input[type="submit"], .btn-primary { background: linear-gradient(135deg, #d97706, #f59e0b) !important; color: #020617 !important; font-weight: 700 !important; padding: 0.6rem 1.25rem !important; border-radius: 0.75rem !important; cursor: pointer !important; border: none !important; transition: all 0.2s !important; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2) !important; }
  button[type="submit"]:hover, input[type="submit"]:hover { filter: brightness(1.1) !important; transform: translateY(-1px) !important; }
</style>
`;

    if (rawHtml.includes('<!DOCTYPE html>') || rawHtml.includes('<html')) {
      if (rawHtml.includes('</head>')) {
        return rawHtml.replace('</head>', `${injectedStyle}${interceptorScript}</head>`);
      }
      return `${injectedStyle}${interceptorScript}${rawHtml}`;
    }

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  ${injectedStyle}
  ${interceptorScript}
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
                <span className="text-emerald-400">sandbox="allow-scripts allow-forms"</span>
              </div>
              <iframe
                title={artifact.title}
                srcDoc={prepareSandboxedHtml(artifact.content)}
                sandbox="allow-scripts allow-forms"
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
