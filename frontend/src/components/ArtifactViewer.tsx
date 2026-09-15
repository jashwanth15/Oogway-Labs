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
  theme?: 'dark' | 'light';
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose, theme = 'light' }) => {
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
      
      // Helper to generate full PMF scorecard HTML
      window.generatePmfGauge = function(v, s, n) {
        const tot = v + s + n;
        if (tot <= 0) return '';
        const score = Math.round((v / tot) * 100);
        const isFit = score >= 40;
        return \`
          <div class="border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>📊 Rahul Vohra PMF Scorecard Result</span>
              </h3>
              <span class="text-xs px-2.5 py-1 rounded-full font-bold \${isFit ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'}">
                \${isFit ? '🎉 Product-Market Fit Achieved' : '⚠️ Below 40% Benchmark'}
              </span>
            </div>
            <div class="mt-3">
              <div class="flex justify-between text-xs mb-1 font-medium">
                <span class="text-slate-300">"Very Disappointed" Ratio</span>
                <span class="font-bold text-lg \${isFit ? 'text-emerald-400' : 'text-amber-400'}">\${score}%</span>
              </div>
              <div class="w-full bg-slate-800 rounded-full h-3.5 overflow-hidden border border-slate-700">
                <div class="h-3.5 rounded-full \${isFit ? 'bg-emerald-500' : 'bg-amber-500'} transition-all duration-500" style="width: \${Math.min(score, 100)}%"></div>
              </div>
              <div class="flex justify-between text-[11px] text-slate-400 mt-1.5">
                <span>0%</span>
                <span class="text-amber-400 font-semibold">▲ 40% Target (Superhuman Benchmark)</span>
                <span>100%</span>
              </div>
            </div>
          </div>
          <div class="space-y-2 text-xs text-slate-300">
            <p><strong>Total Survey Responses:</strong> \${tot} (Very: \${v}, Somewhat: \${s}, Not: \${n})</p>
            <div class="p-3 rounded-xl \${isFit ? 'bg-emerald-950/40 border border-emerald-800/40' : 'bg-amber-950/40 border border-amber-800/40'}">
              <p class="font-bold text-slate-100 mb-1">\${isFit ? '🚀 Growth Strategy (Post-PMF):' : '🧭 Roadmap Strategy (Pre-PMF):'}</p>
              <p class="leading-relaxed">\${isFit 
                ? 'Superhuman reached 58% and unlocked hyper-growth. Spend 50% of your sprint capacity doubling down on your core love (speed/shortcuts), and 50% fixing blockers for the Somewhat Disappointed cohort.' 
                : 'Focus solely on the high-expectation customers who answered "Somewhat Disappointed" and whose primary benefit matched what "Very Disappointed" users love. Discover what holds them back and build those features.'}</p>
            </div>
          </div>
        \`;
      };

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
        resultContainer.innerHTML = window.generatePmfGauge(very, somewhat, notD);
      } else {
        const entries = Object.entries(data);
        const textCorpus = entries.map(([k, v]) => \`\${k} \${v}\`).join(' ').toLowerCase();

        let frameworkContent = '';
        if (textCorpus.includes('disappoint') || textCorpus.includes('disappear') || textCorpus.includes('q1') || textCorpus.includes('benchmark') || textCorpus.includes('pmf')) {
          frameworkContent = \`
            <div class="p-4 rounded-xl bg-slate-950 border border-amber-500/40 text-xs text-slate-300 space-y-3">
              <div class="flex items-center justify-between">
                <span class="font-bold text-amber-400 text-sm flex items-center gap-1.5">
                  <span>🎯 Question 1 Evaluation: The Core PMF Benchmark Metric</span>
                </span>
                <span class="text-[11px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold">Sean Ellis 40% Rule</span>
              </div>
              <p class="leading-relaxed">
                <strong>Survey Question:</strong> <em>"How would you feel if you could no longer use [Product]?"</em><br/>
                <strong>Options:</strong> (1) Very disappointed, (2) Somewhat disappointed, (3) Not disappointed.
              </p>
              <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
                <p class="font-bold text-slate-100">Why this question matters according to Rahul Vohra:</p>
                <p class="text-slate-300 leading-relaxed">
                  This single question provides the quantitative threshold for Product-Market Fit. If <strong>≥ 40%</strong> of respondents answer "Very Disappointed", you have PMF (Superhuman scored 58% at launch). If &lt; 40%, marketing will only churn users.
                </p>
              </div>
              <div class="pt-2 border-t border-slate-800">
                <p class="text-xs font-semibold text-slate-200 mb-2">⚡ Interactive Benchmark Simulation (Click to view score):</p>
                <div class="flex flex-wrap gap-2">
                  <button type="button" onclick="document.getElementById('sim-gauge').innerHTML = window.generatePmfGauge(22, 45, 33)" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-semibold border border-slate-700 transition">
                    📉 Summer 2017: 22% (Pre-PMF)
                  </button>
                  <button type="button" onclick="document.getElementById('sim-gauge').innerHTML = window.generatePmfGauge(38, 32, 30)" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-semibold border border-slate-700 transition">
                    ⚖️ 38% (Near PMF)
                  </button>
                  <button type="button" onclick="document.getElementById('sim-gauge').innerHTML = window.generatePmfGauge(58, 28, 14)" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-semibold border border-slate-700 transition">
                    🚀 Superhuman Launch: 58% (Fit Achieved!)
                  </button>
                </div>
                <div id="sim-gauge" class="mt-3"></div>
              </div>
            </div>
          \`;
        } else if (textCorpus.includes('person') || textCorpus.includes('benefit most') || textCorpus.includes('who') || textCorpus.includes('target') || textCorpus.includes('icp') || textCorpus.includes('persona') || textCorpus.includes('customer') || textCorpus.includes('q2')) {
          frameworkContent = \`
            <div class="p-4 rounded-xl bg-slate-950 border border-sky-500/40 text-xs text-slate-300 space-y-3">
              <div class="flex items-center justify-between">
                <span class="font-bold text-sky-400 text-sm flex items-center gap-1.5">
                  <span>👤 Question 2 Evaluation: High-Expectation Customer (HXC)</span>
                </span>
                <span class="text-[11px] px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold">Persona Discovery</span>
              </div>
              <p class="leading-relaxed">
                <strong>Survey Question:</strong> <em>"What type of person do you think would benefit most from [Product]?"</em>
              </p>
              <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
                <p class="font-bold text-slate-100">Rahul Vohra's High-Expectation Customer (HXC):</p>
                <p class="text-slate-300 leading-relaxed">
                  Only look at responses from users who said <strong>"Very Disappointed"</strong> in Question 1. These users describe themselves vividly.
                </p>
                <div class="mt-2 text-sky-300 bg-sky-950/30 p-2.5 rounded border border-sky-800/40">
                  <strong>Superhuman's Insight:</strong> Their HXC was not generic email users, but executives, founders, and sales leaders managing 100+ emails/day where speed determined career success.
                </div>
              </div>
            </div>
          \`;
        } else if (textCorpus.includes('benefit') || textCorpus.includes('love') || textCorpus.includes('value') || textCorpus.includes('favorite') || textCorpus.includes('why') || textCorpus.includes('speed') || textCorpus.includes('q3')) {
          frameworkContent = \`
            <div class="p-4 rounded-xl bg-slate-950 border border-purple-500/40 text-xs text-slate-300 space-y-3">
              <div class="flex items-center justify-between">
                <span class="font-bold text-purple-400 text-sm flex items-center gap-1.5">
                  <span>💎 Question 3 Evaluation: Core Value Proposition (What to Protect)</span>
                </span>
                <span class="text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 font-semibold">The 50% Rule</span>
              </div>
              <p class="leading-relaxed">
                <strong>Survey Question:</strong> <em>"What is the main benefit you receive from [Product]?"</em>
              </p>
              <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                <p class="font-bold text-slate-100">Protecting Your Core Superpower:</p>
                <p class="text-slate-300 leading-relaxed">
                  Look at the unanimous response from "Very Disappointed" users. At Superhuman, it was <strong>Speed & Keyboard Shortcuts</strong>.
                </p>
                <div class="p-2.5 rounded bg-purple-950/30 border border-purple-800/40 text-purple-300">
                  <strong>Action:</strong> Allocate <strong>50%</strong> of all engineering resources solely to making this core value even faster and more reliable. Never trade core speed for extra features.
                </div>
              </div>
            </div>
          \`;
        } else if (textCorpus.includes('improve') || textCorpus.includes('missing') || textCorpus.includes('holding back') || textCorpus.includes('wish') || textCorpus.includes('better') || textCorpus.includes('fix') || textCorpus.includes('feature') || textCorpus.includes('q4')) {
          frameworkContent = \`
            <div class="p-4 rounded-xl bg-slate-950 border border-amber-500/40 text-xs text-slate-300 space-y-3">
              <div class="flex items-center justify-between">
                <span class="font-bold text-amber-400 text-sm flex items-center gap-1.5">
                  <span>🛠️ Question 4 Evaluation: Product Roadmap & The Disappointment Filter</span>
                </span>
                <span class="text-[11px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold">The Filter</span>
              </div>
              <p class="leading-relaxed">
                <strong>Survey Question:</strong> <em>"How can we improve [Product] for you?"</em>
              </p>
              <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                <p class="font-bold text-slate-100">Rahul Vohra's Critical Roadmap Filter:</p>
                <ol class="list-decimal list-inside space-y-1 text-slate-300 leading-relaxed">
                  <li><span class="text-red-400 font-semibold">Ignore "Not Disappointed" users:</span> Their suggestions are distractions.</li>
                  <li><span class="text-amber-400 font-semibold">Filter "Somewhat Disappointed":</span> Only keep those who cited speed as their main benefit in Q3.</li>
                  <li><span class="text-emerald-400 font-semibold">Dedicate other 50% of roadmap:</span> Build only what held this group back (Superhuman built mobile app, search, integrations).</li>
                </ol>
              </div>
            </div>
          \`;
        } else {
          frameworkContent = \`
            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-3">
              <p class="font-bold text-amber-400 flex items-center gap-1.5 text-sm">
                <span>💡 Rahul Vohra Feedback Segmentation Analysis:</span>
              </p>
              <p class="leading-relaxed">
                In Superhuman's survey engine, feedback is segmented strictly by user enthusiasm to prevent roadmaps from becoming bloated:
              </p>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
                <div class="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
                  <span class="text-emerald-400 font-bold block mb-1">Very Disappointed (Lovers)</span>
                  <p class="text-[11px] text-slate-300">Identify what they love in Q3. Spend 50% of roadmap doubling down on this.</p>
                </div>
                <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-800/40">
                  <span class="text-amber-400 font-bold block mb-1">Somewhat Disappointed (Opportunity)</span>
                  <p class="text-[11px] text-slate-300">Find users who love the same core benefit. Spend 50% fixing their blockers in Q4.</p>
                </div>
                <div class="p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <span class="text-slate-400 font-bold block mb-1">Not Disappointed (Distraction)</span>
                  <p class="text-[11px] text-slate-400">Politely disregard all suggestions. They will pull your product off course.</p>
                </div>
              </div>
            </div>
          \`;
        }

        const entriesHtml = entries.length > 0
          ? entries.map(([k, v]) => \`
            <div class="py-1.5 border-b border-slate-800 flex flex-col sm:flex-row sm:justify-between">
              <span class="text-slate-400 text-xs font-semibold capitalize">\${k.replace(/[-_\[\]]/g, ' ').trim()}:</span>
              <span class="text-slate-200 text-xs font-medium">\${v || '(no response entered)'}</span>
            </div>
          \`).join('')
          : '<p class="text-slate-300 text-xs">Response submitted!</p>';

        resultContainer.innerHTML = \`
          <div class="flex items-center gap-2 mb-3 text-emerald-400 font-bold text-sm">
            <span>✓ Survey Input Evaluated with Rahul Vohra Engine</span>
          </div>
          <div class="space-y-1 mb-4">
            \${entriesHtml}
          </div>
          \${frameworkContent}
        \`;
      }
      resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });
<\/script>
`;

    const injectedStyle = `
<meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;">
<script src="https://cdn.tailwindcss.com"><\/script>
<script>
  tailwind.config = {
    darkMode: 'class'
  }
<\/script>
<style>
  html.dark body { font-family: system-ui, -apple-system, sans-serif; background-color: #0b1120 !important; color: #f1f5f9 !important; padding: 1.5rem !important; }
  html:not(.dark) body { font-family: system-ui, -apple-system, sans-serif; background-color: #f8fafc !important; color: #0f172a !important; padding: 1.5rem !important; }
  
  html.dark input, html.dark textarea, html.dark select { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
  html:not(.dark) input, html:not(.dark) textarea, html:not(.dark) select { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
  
  input, textarea, select { border-radius: 0.5rem !important; padding: 0.5rem 0.75rem !important; width: 100% !important; margin-top: 0.25rem !important; margin-bottom: 0.75rem !important; outline: none !important; }
  input:focus, textarea:focus, select:focus { border-color: #f59e0b !important; ring: 2px #f59e0b !important; }
  
  html.dark label { color: #cbd5e1 !important; font-weight: 500 !important; font-size: 0.875rem !important; }
  html:not(.dark) label { color: #475569 !important; font-weight: 500 !important; font-size: 0.875rem !important; }
  
  button[type="submit"], input[type="submit"], .btn-primary { background: linear-gradient(135deg, #d97706, #f59e0b) !important; color: #020617 !important; font-weight: 700 !important; padding: 0.6rem 1.25rem !important; border-radius: 0.75rem !important; cursor: pointer !important; border: none !important; transition: all 0.2s !important; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2) !important; }
  button[type="submit"]:hover, input[type="submit"]:hover { filter: brightness(1.1) !important; transform: translateY(-1px) !important; }
</style>
<script>
  if ('${theme}' === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
</script>
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
