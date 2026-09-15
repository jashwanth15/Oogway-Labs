import asyncio
import json
import re
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from backend.app.config import settings
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.ship30_skill import Ship30Skill
from backend.app.schemas.chat import Citation, ArtifactPayload
from backend.app.logger import setup_logger

logger = setup_logger(__name__)

SYSTEM_PROMPT = """
You are 'The Lenny Growth Assistant', an elite product and growth advisory agent powered exclusively by transcripts from Lenny's Podcast (300+ interviews with top founders, PMs, and growth leaders).

Your Core Mandates:
1. STRICT GROUNDING: Base your answers ONLY on the provided podcast excerpts. Citing guests (e.g. Elena Verna, Rahul Vohra, Brian Chesky, Shreyas Doshi) is mandatory.
2. CITATIONS: Attribute quotes, frameworks, and benchmarks to the respective guest and episode.
3. ZERO HALLUCINATION: If the provided excerpts do not contain enough information to answer the question, state clearly and politely:
   "I searched Lenny's podcast archives for this topic, but no matching discussion was found in the transcripts."
   Do NOT make up facts or extrapolate beyond what the guests discussed.
4. ACTIONABLE CLARITY: Format answers with clear markdown, bullet points, and bold emphasis for key takeaways.
5. ARTIFACTS: When the user asks for a reusable artifact, PRD, framework canvas, or interactive UI widget:
   - Provide the explanation in chat.
   - Output the complete code or markdown within an artifact block:
     ```artifact:html:Title Of Widget
     <html>...</html>
     ```
     or
     ```artifact:markdown:Title Of Document
     # ...
     ```
"""


class GrowthAgent:
    def __init__(self):
        self.retriever = HybridRetriever.get_instance()
        self.ship30_skill = Ship30Skill()
        self._cached_models: List[str] = ["qwen2.5:0.5b", "mistral:latest", "mymodel:latest"]

    async def check_ollama_status(self) -> Dict[str, Any]:
        """Checks if Ollama service is reachable and lists local models."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    if models:
                        self._cached_models = models
                    return {"available": True, "models": self._cached_models}
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
        return {"available": True, "models": self._cached_models}

    def get_pmf_scorecard_template(self) -> str:
        """Returns a high-craft standalone HTML5 artifact for Rahul Vohra's PMF framework."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rahul Vohra PMF Survey Calculator & Scorecard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background-color: #0b1120; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 1.5rem; }
    .tab-btn.active { background-color: #f59e0b; color: #0b1120; font-weight: 700; }
    .tab-btn:not(.active) { background-color: #1e293b; color: #94a3b8; }
    .tab-btn:not(.active):hover { background-color: #334155; color: #f8fafc; }
  </style>
</head>
<body class="min-h-screen">
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700/80 shadow-2xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 mb-2">
            <span>⚡ Superhuman Growth Engine</span>
          </div>
          <h1 class="text-2xl font-black text-slate-100 tracking-tight">Rahul Vohra's PMF Survey Calculator & Scorecard</h1>
          <p class="text-xs text-slate-400 mt-1">Measure Product-Market Fit quantitatively and reverse-engineer your product roadmap using Sean Ellis's 40% benchmark.</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700 font-mono text-amber-400">Target: ≥ 40%</span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-800">
        <button onclick="switchTab('calculator')" id="tab-calculator" class="tab-btn active px-4 py-2 rounded-xl text-xs transition">📊 1. Quantitative Scorecard</button>
        <button onclick="switchTab('survey')" id="tab-survey" class="tab-btn px-4 py-2 rounded-xl text-xs transition">🎯 2. The 4-Question Survey Engine</button>
        <button onclick="switchTab('roadmap')" id="tab-roadmap" class="tab-btn px-4 py-2 rounded-xl text-xs transition">🛠️ 3. The 50/50 Roadmap Rule</button>
      </div>
    </div>

    <!-- TAB 1: CALCULATOR -->
    <div id="content-calculator" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div class="md:col-span-5 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
          <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">Input Survey Responses</h2>
          <p class="text-xs text-slate-400">Enter respondent counts for Question #1: <em>"How would you feel if you could no longer use the product?"</em></p>
          <form id="pmfForm" onsubmit="event.preventDefault(); recalculate();" class="space-y-3">
            <div>
              <label class="block text-xs font-semibold text-emerald-400 mb-1">Very Disappointed (Core Lovers):</label>
              <input type="number" id="input-very" name="very" value="58" min="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 font-bold focus:border-amber-400 focus:outline-none" oninput="recalculate()" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-amber-400 mb-1">Somewhat Disappointed (Growth Opportunity):</label>
              <input type="number" id="input-somewhat" name="somewhat" value="28" min="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 font-bold focus:border-amber-400 focus:outline-none" oninput="recalculate()" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 mb-1">Not Disappointed (Disregard Feedback):</label>
              <input type="number" id="input-not" name="not" value="14" min="0" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 font-bold focus:border-amber-400 focus:outline-none" oninput="recalculate()" />
            </div>
            <div class="pt-2">
              <button type="submit" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-amber-500/10">Calculate PMF Score</button>
            </div>
          </form>

          <div class="pt-4 border-t border-slate-800/80">
            <span class="text-[11px] font-semibold text-slate-400 block mb-2">⚡ Superhuman Historical Case Studies:</span>
            <div class="flex flex-col gap-1.5">
              <button onclick="loadPreset(22, 45, 33)" class="text-left px-3 py-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-xs border border-slate-800 text-slate-300 transition flex items-center justify-between">
                <span>📉 Summer 2017: 22% PMF</span><span class="text-[10px] text-amber-400 font-mono">Pre-PMF</span>
              </button>
              <button onclick="loadPreset(38, 32, 30)" class="text-left px-3 py-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-xs border border-slate-800 text-slate-300 transition flex items-center justify-between">
                <span>⚖️ Mid-Cycle: 38% PMF</span><span class="text-[10px] text-amber-400 font-mono">Near-Fit</span>
              </button>
              <button onclick="loadPreset(58, 28, 14)" class="text-left px-3 py-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-xs border border-slate-800 text-slate-300 transition flex items-center justify-between">
                <span>🚀 Public Launch: 58% PMF</span><span class="text-[10px] text-emerald-400 font-mono">PMF Achieved!</span>
              </button>
            </div>
          </div>
        </div>

        <div class="md:col-span-7 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">PMF Scorecard Results</h2>
              <span id="badge-status" class="px-3 py-1 rounded-full text-xs font-bold border transition">Evaluating...</span>
            </div>

            <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800/80 mb-6">
              <div class="flex items-baseline justify-between mb-2">
                <span class="text-xs text-slate-400 font-medium">PMF Score ("Very Disappointed" Ratio):</span>
                <span id="metric-score" class="text-4xl font-black text-amber-400 tracking-tight">--%</span>
              </div>
              <div class="relative w-full bg-slate-800 rounded-full h-4 overflow-hidden border border-slate-700/60 my-3">
                <div id="meter-bar" class="h-4 rounded-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all duration-500" style="width: 0%"></div>
              </div>
              <div class="flex justify-between text-[11px] font-mono text-slate-400">
                <span>0%</span>
                <span class="text-amber-400 font-bold">▲ 40% Benchmark (Ellis / Superhuman Target)</span>
                <span>100%</span>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3 mb-6">
              <div class="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span class="text-[10px] text-slate-400 font-semibold block uppercase">Total Responses</span>
                <span id="metric-total" class="text-lg font-bold text-slate-100 font-mono">0</span>
              </div>
              <div class="p-3 rounded-xl bg-slate-950 border border-emerald-900/40 text-center">
                <span class="text-[10px] text-emerald-400 font-semibold block uppercase">Very Disappointed</span>
                <span id="metric-very-count" class="text-lg font-bold text-emerald-400 font-mono">0</span>
              </div>
              <div class="p-3 rounded-xl bg-slate-950 border border-amber-900/40 text-center">
                <span class="text-[10px] text-amber-400 font-semibold block uppercase">Somewhat</span>
                <span id="metric-somewhat-count" class="text-lg font-bold text-amber-400 font-mono">0</span>
              </div>
            </div>
          </div>

          <div id="strategy-box" class="p-4 rounded-xl border text-xs leading-relaxed transition"></div>
        </div>
      </div>
    </div>

    <!-- TAB 2: 4-QUESTION ENGINE -->
    <div id="content-survey" class="space-y-4 hidden">
      <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
        <div>
          <h2 class="text-lg font-bold text-slate-100">Rahul Vohra's 4-Question Survey Engine</h2>
          <p class="text-xs text-slate-400 mt-1">Superhuman doesn't just ask one question. They run this 4-step survey loop to isolate high-conviction roadmap items.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-5 rounded-xl bg-slate-950 border border-amber-500/30 space-y-2">
            <span class="text-xs font-bold text-amber-400 uppercase">Question #1: The Benchmark Gate</span>
            <p class="text-sm font-semibold text-slate-200">"How would you feel if you could no longer use [Product]?"</p>
            <p class="text-xs text-slate-400 leading-relaxed">Options: <em>Very disappointed</em>, <em>Somewhat disappointed</em>, <em>Not disappointed</em>.<br/><strong>Threshold:</strong> If ≥ 40% answer "Very Disappointed", you have PMF.</p>
          </div>
          <div class="p-5 rounded-xl bg-slate-950 border border-sky-500/30 space-y-2">
            <span class="text-xs font-bold text-sky-400 uppercase">Question #2: Persona Discovery</span>
            <p class="text-sm font-semibold text-slate-200">"What type of person do you think would benefit most from [Product]?"</p>
            <p class="text-xs text-slate-400 leading-relaxed"><strong>The Filter:</strong> Only read responses from "Very Disappointed" users. They describe your High-Expectation Customer (HXC) with vivid accuracy.</p>
          </div>
          <div class="p-5 rounded-xl bg-slate-950 border border-purple-500/30 space-y-2">
            <span class="text-xs font-bold text-purple-400 uppercase">Question #3: Core Superpower</span>
            <p class="text-sm font-semibold text-slate-200">"What is the main benefit you receive from [Product]?"</p>
            <p class="text-xs text-slate-400 leading-relaxed">Look for consensus among your lovers (at Superhuman: <em>Speed & Keyboard Shortcuts</em>). Dedicate 50% of roadmap to protecting this.</p>
          </div>
          <div class="p-5 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-2">
            <span class="text-xs font-bold text-emerald-400 uppercase">Question #4: Roadmap Engine</span>
            <p class="text-sm font-semibold text-slate-200">"How can we improve [Product] for you?"</p>
            <p class="text-xs text-slate-400 leading-relaxed"><strong>The Critical Filter:</strong> Ignore "Not Disappointed" users. Only listen to "Somewhat Disappointed" users who love the Q3 benefit. Build what holds them back!</p>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: ROADMAP RULE -->
    <div id="content-roadmap" class="space-y-4 hidden">
      <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
        <div>
          <h2 class="text-lg font-bold text-slate-100">The 50/50 Engineering Roadmap Rule</h2>
          <p class="text-xs text-slate-400 mt-1">Rahul Vohra's golden formula to balance retention defensibility with acquisition growth.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="p-5 rounded-2xl bg-gradient-to-br from-purple-950/40 to-slate-950 border border-purple-800/40 space-y-3">
            <span class="text-xl font-black text-purple-400">50% Capacity</span>
            <h3 class="text-sm font-bold text-slate-100">Double Down on What Users Love</h3>
            <p class="text-xs text-slate-300 leading-relaxed">Never take your core superpower for granted. For Superhuman, this was making email faster (sub-100ms interactions, offline sync, keyboard shortcuts).</p>
          </div>
          <div class="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/40 to-slate-950 border border-emerald-800/40 space-y-3">
            <span class="text-xl font-black text-emerald-400">50% Capacity</span>
            <h3 class="text-sm font-bold text-slate-100">Address "Somewhat Disappointed" Blockers</h3>
            <p class="text-xs text-slate-300 leading-relaxed">Convert on-the-fence users into evangelists. Superhuman built native mobile apps, calendar integrations, and search capabilities requested by users who loved speed.</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('tab-' + tabId);
      if (activeBtn) activeBtn.classList.add('active');
      document.getElementById('content-calculator').classList.toggle('hidden', tabId !== 'calculator');
      document.getElementById('content-survey').classList.toggle('hidden', tabId !== 'survey');
      document.getElementById('content-roadmap').classList.toggle('hidden', tabId !== 'roadmap');
    }

    function loadPreset(very, somewhat, notD) {
      document.getElementById('input-very').value = very;
      document.getElementById('input-somewhat').value = somewhat;
      document.getElementById('input-not').value = notD;
      recalculate();
    }

    function recalculate() {
      const very = Math.max(0, parseFloat(document.getElementById('input-very').value) || 0);
      const somewhat = Math.max(0, parseFloat(document.getElementById('input-somewhat').value) || 0);
      const notD = Math.max(0, parseFloat(document.getElementById('input-not').value) || 0);
      const total = very + somewhat + notD;
      const score = total > 0 ? Math.round((very / total) * 100) : 0;
      const isFit = score >= 40;

      document.getElementById('metric-score').innerText = score + '%';
      document.getElementById('metric-total').innerText = total;
      document.getElementById('metric-very-count').innerText = very;
      document.getElementById('metric-somewhat-count').innerText = somewhat;

      const bar = document.getElementById('meter-bar');
      bar.style.width = Math.min(score, 100) + '%';
      bar.className = isFit 
        ? 'h-4 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500'
        : 'h-4 rounded-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-500';

      const badge = document.getElementById('badge-status');
      badge.className = isFit 
        ? 'px-3 py-1 rounded-full text-xs font-bold border bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
        : 'px-3 py-1 rounded-full text-xs font-bold border bg-amber-500/20 text-amber-400 border-amber-500/40';
      badge.innerText = isFit ? '🎉 Product-Market Fit Achieved (≥40%)' : '⚠️ Pre-PMF (' + score + '% / 40% Target)';

      const strat = document.getElementById('strategy-box');
      strat.className = isFit 
        ? 'p-4 rounded-xl border text-xs leading-relaxed bg-emerald-950/30 border-emerald-800/40 text-emerald-200'
        : 'p-4 rounded-xl border text-xs leading-relaxed bg-amber-950/30 border-amber-800/40 text-amber-200';
      strat.innerHTML = isFit
        ? '<strong class="font-bold text-emerald-300 block mb-1 text-sm">🚀 Green Light to Scale (PMF Score: ' + score + '%):</strong>Your score exceeds the Sean Ellis 40% benchmark! You can safely invest in acquisition channels. Apply the 50/50 rule: allocate half your sprints to enhancing what your ' + very + ' core lovers adore, and half to removing blockers for the ' + somewhat + ' users on the fence.'
        : '<strong class="font-bold text-amber-300 block mb-1 text-sm">🧭 Focus on Retention, Do NOT Scale (PMF Score: ' + score + '%):</strong>Your score is below the 40% threshold. Investing in paid ads or sales now will leak users through your funnel. Isolate the ' + somewhat + ' "Somewhat Disappointed" users whose main benefit matches your lovers, find what is holding them back, and build only those features.';
    }

    window.addEventListener('DOMContentLoaded', () => { recalculate(); });
    setTimeout(recalculate, 100);
  </script>
</body>
</html>
"""

    def get_dhm_scorecard_template(self) -> str:
        """Returns standalone interactive HTML/Tailwind DHM Strategy Scorecard."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gibson Biddle DHM Product Strategy Scorecard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .tab-btn.active {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: #ffffff;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
    }
    .tab-btn:not(.active) {
      background: #0f172a;
      color: #94a3b8;
      border: 1px solid #1e293b;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 min-h-screen">
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <div class="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-700/80 shadow-2xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mb-2">
            <span>🏰 Gibson Biddle's Product Strategy Framework</span>
          </div>
          <h1 class="text-2xl font-black text-slate-100 tracking-tight">DHM Product Strategy Scorecard</h1>
          <p class="text-xs text-slate-400 mt-1">Evaluate product initiatives across <strong>Delight</strong>, <strong>Hard-to-copy advantage</strong>, and <strong>Margin-enhancement</strong> (former VP Product at Netflix & Chegg).</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700 font-mono text-indigo-400">Strategy = D + H + M</span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-800">
        <button onclick="switchTab('evaluator')" id="tab-evaluator" class="tab-btn active px-4 py-2 rounded-xl text-xs transition">🎯 1. Feature Evaluator</button>
        <button onclick="switchTab('moats')" id="tab-moats" class="tab-btn px-4 py-2 rounded-xl text-xs transition">🏰 2. The 4 Hard-to-Copy Moats</button>
        <button onclick="switchTab('netflix')" id="tab-netflix" class="tab-btn px-4 py-2 rounded-xl text-xs transition">🎬 3. Netflix Historical Case Studies</button>
      </div>
    </div>

    <!-- TAB 1: EVALUATOR -->
    <div id="content-evaluator" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
        <!-- Input Form -->
        <div class="md:col-span-6 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
          <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">Score an Initiative</h2>
          
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Feature / Initiative Name:</label>
            <input type="text" id="feature-name" value="Personalized Video Recommendations" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 focus:border-indigo-400 focus:outline-none" oninput="recalculate()" />
          </div>

          <!-- Delight -->
          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="text-xs font-semibold text-pink-400">1. Delight Customers (1 - 10):</label>
              <span id="label-delight" class="text-xs font-bold text-pink-300 font-mono">8 / 10</span>
            </div>
            <input type="range" id="input-delight" min="1" max="10" value="8" class="w-full accent-pink-500 cursor-pointer" oninput="recalculate()" />
            <span class="text-[11px] text-slate-400 block mt-0.5">Does it solve real customer problems and bring genuine joy/relief?</span>
          </div>

          <!-- Hard-to-Copy Moats -->
          <div>
            <label class="block text-xs font-semibold text-amber-400 mb-1.5">2. Hard-to-Copy Advantage (Select Applicable Moats):</label>
            <div class="space-y-1.5 text-xs text-slate-300">
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <input type="checkbox" id="moat-brand" class="accent-indigo-500 rounded" checked onchange="recalculate()" />
                <span><strong>Brand:</strong> Trusted reputation (Disney, Apple, Netflix)</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <input type="checkbox" id="moat-network" class="accent-indigo-500 rounded" onchange="recalculate()" />
                <span><strong>Network Effects:</strong> Product value grows as more users join</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <input type="checkbox" id="moat-scale" class="accent-indigo-500 rounded" checked onchange="recalculate()" />
                <span><strong>Economies of Scale:</strong> Lower unit costs with higher volume</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700">
                <input type="checkbox" id="moat-switch" class="accent-indigo-500 rounded" checked onchange="recalculate()" />
                <span><strong>Switching Costs / Proprietary Tech:</strong> Algorithms, data lock-in</span>
              </label>
            </div>
          </div>

          <!-- Margin-Enhancing -->
          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="text-xs font-semibold text-emerald-400">3. Margin-Enhancing (1 - 10):</label>
              <span id="label-margin" class="text-xs font-bold text-emerald-300 font-mono">8 / 10</span>
            </div>
            <input type="range" id="input-margin" min="1" max="10" value="8" class="w-full accent-emerald-500 cursor-pointer" oninput="recalculate()" />
            <span class="text-[11px] text-slate-400 block mt-0.5">Expands margins via pricing power, lower churn/retention, or lower operational costs.</span>
          </div>

          <!-- Presets -->
          <div class="pt-3 border-t border-slate-800/80">
            <span class="text-[11px] font-semibold text-slate-400 block mb-2">⚡ Historical Netflix Presets (Gibson Biddle):</span>
            <div class="grid grid-cols-2 gap-1.5">
              <button onclick="loadPreset('Personalized Recommendations', 8, [true, false, true, true], 8)" class="text-left p-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-[11px] border border-slate-800 text-slate-300 transition">
                🤖 Algorithmic Matching
              </button>
              <button onclick="loadPreset('Netflix Original Series', 9, [true, false, true, false], 9)" class="text-left p-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-[11px] border border-slate-800 text-slate-300 transition">
                🍿 Original Content
              </button>
              <button onclick="loadPreset('Next-Day DVD Delivery', 8, [false, false, true, false], 7)" class="text-left p-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-[11px] border border-slate-800 text-slate-300 transition">
                📦 Automated DVD Hubs
              </button>
              <button onclick="loadPreset('Netflix Friends (Social Feature)', 3, [false, true, false, false], 2)" class="text-left p-2 rounded-lg bg-slate-950 hover:bg-slate-800 text-[11px] border border-slate-800 text-slate-300 transition">
                ❌ 'Friends' Social Network
              </button>
            </div>
          </div>
        </div>

        <!-- Output Scorecard -->
        <div class="md:col-span-6 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl flex flex-col justify-between space-y-6">
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-bold text-slate-200 uppercase tracking-wider">Strategy Assessment</h2>
              <span id="badge-verdict" class="px-3 py-1 rounded-full text-xs font-bold border transition">Evaluating...</span>
            </div>

            <div class="space-y-4">
              <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
                <span class="text-xs font-medium text-slate-400 block mb-1">Composite DHM Viability Score</span>
                <div id="metric-score" class="text-4xl font-black text-indigo-400 font-mono tracking-tight">85 / 100</div>
              </div>

              <!-- Breakdown grid -->
              <div class="grid grid-cols-3 gap-2 text-center">
                <div class="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span class="text-[10px] uppercase font-bold text-pink-400 block">Delight</span>
                  <span id="score-delight" class="text-lg font-bold text-slate-100 font-mono">8/10</span>
                </div>
                <div class="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span class="text-[10px] uppercase font-bold text-amber-400 block">Moats</span>
                  <span id="score-moats" class="text-lg font-bold text-slate-100 font-mono">3 / 4</span>
                </div>
                <div class="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <span class="text-[10px] uppercase font-bold text-emerald-400 block">Margin</span>
                  <span id="score-margin" class="text-lg font-bold text-slate-100 font-mono">8/10</span>
                </div>
              </div>

              <!-- Recommendation Box -->
              <div id="verdict-box" class="p-4 rounded-xl border text-xs leading-relaxed">
                <!-- Injected via JavaScript -->
              </div>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/30 text-[11px] text-indigo-300 space-y-1">
            <strong class="text-indigo-200 block">💡 Gibson Biddle's Rule of Thumb:</strong>
            <p>Every product idea must aim to satisfy all three dimensions. If an initiative only Delights without Moats, competitors copy it in 6 months. If it only expands Margin without Delight, customers churn.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: MOATS -->
    <div id="content-moats" class="hidden space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div class="flex items-center gap-2 text-amber-400 font-bold text-sm">
            <span>🛡️ 1. Brand</span>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">Customer trust built through years of consistency and emotional resonance. Netflix built a trusted brand for cinema entertainment; Disney for families. Brand alone is hard to build but offers durable pricing power.</p>
        </div>
        <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div class="flex items-center gap-2 text-indigo-400 font-bold text-sm">
            <span>🌐 2. Network Effects</span>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">Each new user increases the value for other users (e.g. social networks, marketplaces like Uber or Airbnb). Note: Netflix discovered entertainment is mostly a personal experience, which is why social 'Friends' features failed.</p>
        </div>
        <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div class="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <span>📈 3. Economies of Scale</span>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">Spreading fixed costs over an enormous user base so unit costs drop below competitors. For example, Netflix amortizing a $150M blockbuster film across 250M global subscribers costs less than $1/subscriber, impossible for smaller entrants.</p>
        </div>
        <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2">
          <div class="flex items-center gap-2 text-cyan-400 font-bold text-sm">
            <span>🔒 4. Switching Costs / Proprietary Tech</span>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">Friction of leaving due to stored personalization, accumulated ratings, or unmatched algorithms. In Netflix's case, years of viewing history feeding personal recommendation models meant switching away lost all personalization.</p>
        </div>
      </div>
    </div>

    <!-- TAB 3: NETFLIX CASE STUDIES -->
    <div id="content-netflix" class="hidden space-y-4">
      <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <h3 class="text-sm font-bold text-slate-100 uppercase tracking-wider">How Netflix Used the DHM Model to Make Hard Decisions</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left text-slate-300 border-collapse">
            <thead class="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th class="p-3">Initiative</th>
                <th class="p-3">Delight</th>
                <th class="p-3">Hard to Copy</th>
                <th class="p-3">Margin Enhancing</th>
                <th class="p-3">Decision</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-sans">
              <tr>
                <td class="p-3 font-semibold text-slate-200">Personalized Recommendations</td>
                <td class="p-3 text-pink-400">High (easy discovery)</td>
                <td class="p-3 text-amber-400">High (10B+ ratings, ML algorithms)</td>
                <td class="p-3 text-emerald-400">High (spreads demand away from expensive new releases)</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">Doubled Down</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-200">Original Content (House of Cards)</td>
                <td class="p-3 text-pink-400">High (exclusive prestige TV)</td>
                <td class="p-3 text-amber-400">High (exclusive copyright, scale)</td>
                <td class="p-3 text-emerald-400">High (replaces costly 3rd party licensing fees)</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">Doubled Down</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-200">Next-Day DVD Delivery (100 Hubs)</td>
                <td class="p-3 text-pink-400">High (instant gratification)</td>
                <td class="p-3 text-amber-400">High (multi-million dollar automated hubs)</td>
                <td class="p-3 text-emerald-400">High (killed Blockbuster, dropped churn)</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">Doubled Down</span></td>
              </tr>
              <tr>
                <td class="p-3 font-semibold text-slate-200">Netflix Friends (Social Network)</td>
                <td class="p-3 text-slate-400">Low (people don't want friends seeing guilty pleasures)</td>
                <td class="p-3 text-slate-400">Medium (Network effect attempted)</td>
                <td class="p-3 text-slate-400">Low (no measurable impact on churn)</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">Killed Experiment</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tabId) {
      ['evaluator', 'moats', 'netflix'].forEach(t => {
        const btn = document.getElementById('tab-' + t);
        const content = document.getElementById('content-' + t);
        if (t === tabId) {
          btn.className = 'tab-btn active px-4 py-2 rounded-xl text-xs transition';
          content.classList.remove('hidden');
        } else {
          btn.className = 'tab-btn px-4 py-2 rounded-xl text-xs transition';
          content.classList.add('hidden');
        }
      });
    }

    function loadPreset(name, delight, moats, margin) {
      document.getElementById('feature-name').value = name;
      document.getElementById('input-delight').value = delight;
      document.getElementById('moat-brand').checked = moats[0];
      document.getElementById('moat-network').checked = moats[1];
      document.getElementById('moat-scale').checked = moats[2];
      document.getElementById('moat-switch').checked = moats[3];
      document.getElementById('input-margin').value = margin;
      recalculate();
    }

    function recalculate() {
      const delight = parseInt(document.getElementById('input-delight').value) || 1;
      const margin = parseInt(document.getElementById('input-margin').value) || 1;
      
      document.getElementById('label-delight').innerText = delight + ' / 10';
      document.getElementById('score-delight').innerText = delight + ' / 10';
      
      document.getElementById('label-margin').innerText = margin + ' / 10';
      document.getElementById('score-margin').innerText = margin + ' / 10';

      const moatsChecked = [
        document.getElementById('moat-brand').checked,
        document.getElementById('moat-network').checked,
        document.getElementById('moat-scale').checked,
        document.getElementById('moat-switch').checked
      ].filter(Boolean).length;

      document.getElementById('score-moats').innerText = moatsChecked + ' / 4';

      const delightScore = (delight / 10) * 40;
      const moatScore = (moatsChecked / 4) * 35;
      const marginScore = (margin / 10) * 25;
      const totalScore = Math.round(delightScore + moatScore + marginScore);

      document.getElementById('metric-score').innerText = totalScore + ' / 100';

      const badge = document.getElementById('badge-verdict');
      const box = document.getElementById('verdict-box');
      const fname = document.getElementById('feature-name').value || 'This Initiative';

      if (delight >= 7 && moatsChecked >= 2 && margin >= 6) {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold border bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
        badge.innerText = '🏆 Triple Threat (High D-H-M)';
        box.className = 'p-4 rounded-xl border text-xs leading-relaxed bg-emerald-950/30 border-emerald-800/40 text-emerald-200';
        box.innerHTML = '<strong class="font-bold text-emerald-300 block mb-1 text-sm">🚀 Green Light to Invest:</strong>"' + fname + '" hits all three pillars of Gibson Biddle\\\'s framework. It delivers strong customer delight, is protected by ' + moatsChecked + ' hard-to-copy moats, and expands margins. Prioritize for your strategic roadmap.';
      } else if (delight >= 7 && moatsChecked < 2) {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold border bg-amber-500/20 text-amber-400 border-amber-500/40';
        badge.innerText = '⚠️ Customer Pleaser (Fragile Moat)';
        box.className = 'p-4 rounded-xl border text-xs leading-relaxed bg-amber-950/30 border-amber-800/40 text-amber-200';
        box.innerHTML = '<strong class="font-bold text-amber-300 block mb-1 text-sm">⚠️ High Delight, but Easily Copied:</strong>"' + fname + '" delights customers, but has only ' + moatsChecked + ' defensible moat. Competitors will clone this quickly unless you attach it to network effects, proprietary tech, or brand affinity.';
      } else if (margin >= 7 && delight < 5) {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold border bg-rose-500/20 text-rose-400 border-rose-500/40';
        badge.innerText = '🚫 Margin Trap';
        box.className = 'p-4 rounded-xl border text-xs leading-relaxed bg-rose-950/30 border-rose-800/40 text-rose-200';
        box.innerHTML = '<strong class="font-bold text-rose-300 block mb-1 text-sm">🚫 Danger of Churn:</strong>"' + fname + '" increases profit/margins but provides poor delight (' + delight + '/10). Gibson Biddle warns against executing margin plays that don\\\'t give customers enough value in return.';
      } else {
        badge.className = 'px-3 py-1 rounded-full text-xs font-bold border bg-slate-800 text-slate-300 border-slate-700';
        badge.innerText = '🧭 Needs Refinement';
        box.className = 'p-4 rounded-xl border text-xs leading-relaxed bg-slate-950 border-slate-800 text-slate-300';
        box.innerHTML = '<strong class="font-bold text-slate-200 block mb-1 text-sm">🧭 Revisit Hypotheses:</strong>Score is ' + totalScore + '/100. Identify how you can either amplify delight or attach a defensible moat before committing engineering capacity.';
      }
    }

    window.addEventListener('DOMContentLoaded', recalculate);
    setTimeout(recalculate, 100);
  </script>
</body>
</html>
"""

    def get_lno_matrix_template(self) -> str:
        """Returns standalone interactive HTML/Tailwind Shreyas Doshi LNO Task Matrix & Energy Allocation Dashboard."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Shreyas Doshi LNO Framework Task Matrix & Energy Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .tab-btn.active {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: #ffffff;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
    }
    .tab-btn:not(.active) {
      background: #0f172a;
      color: #94a3b8;
      border: 1px solid #1e293b;
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 min-h-screen">
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <div class="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-700/80 shadow-2xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mb-2">
            <span>⚡ Shreyas Doshi's High-Agency Playbook</span>
          </div>
          <h1 class="text-2xl font-black text-slate-100 tracking-tight">LNO Task Matrix & Energy Dashboard</h1>
          <p class="text-xs text-slate-400 mt-1">Manage energy, not just time. Classify product work into <strong>Leverage (10x-100x)</strong>, <strong>Neutral (1x)</strong>, and <strong>Overhead (&lt;1x)</strong>.</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700 font-mono text-indigo-400">ROI = Return / Energy</span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex flex-wrap gap-2 mt-6 pt-4 border-t border-slate-800">
        <button onclick="switchTab('board')" id="tab-board" class="tab-btn active px-4 py-2 rounded-xl text-xs transition">📋 1. Interactive LNO Board</button>
        <button onclick="switchTab('philosophy')" id="tab-philosophy" class="tab-btn px-4 py-2 rounded-xl text-xs transition">🧠 2. The LNO Philosophy & Energy Traps</button>
        <button onclick="switchTab('presets')" id="tab-presets" class="tab-btn px-4 py-2 rounded-xl text-xs transition">⚡ 3. Real-World PM Role Presets</button>
      </div>
    </div>

    <!-- TAB 1: INTERACTIVE LNO BOARD -->
    <div id="content-board" class="space-y-6">
      <!-- Energy Allocation Summary & Progress Bar -->
      <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider">Weekly Energy & Time Allocation</h2>
            <p class="text-[11px] text-slate-400">Dynamic distribution calculated across active tasks</p>
          </div>
          <div class="flex items-center gap-4 text-xs font-mono">
            <span class="text-slate-400">Total Workload: <strong id="metric-total-hours" class="text-slate-100 font-bold">0 hrs/wk</strong></span>
            <span class="text-slate-400">Active Tasks: <strong id="metric-total-tasks" class="text-slate-100 font-bold">0</strong></span>
          </div>
        </div>

        <!-- 3 KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">🚀 Leverage (L)</span>
              <span id="metric-l-hours" class="text-xl font-black text-indigo-200">0 hrs</span>
              <span class="text-[10px] text-indigo-300/80 block mt-0.5">Target: 45% - 60%</span>
            </div>
            <span id="badge-l-pct" class="text-lg font-black text-indigo-400 font-mono">0%</span>
          </div>

          <div class="p-4 rounded-xl bg-sky-950/20 border border-sky-500/30 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider block">⚖️ Neutral (N)</span>
              <span id="metric-n-hours" class="text-xl font-black text-sky-200">0 hrs</span>
              <span class="text-[10px] text-sky-300/80 block mt-0.5">Target: 25% - 35%</span>
            </div>
            <span id="badge-n-pct" class="text-lg font-black text-sky-400 font-mono">0%</span>
          </div>

          <div class="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-bold text-rose-400 uppercase tracking-wider block">📦 Overhead (O)</span>
              <span id="metric-o-hours" class="text-xl font-black text-rose-200">0 hrs</span>
              <span class="text-[10px] text-rose-300/80 block mt-0.5">Target: &lt; 15%</span>
            </div>
            <span id="badge-o-pct" class="text-lg font-black text-rose-400 font-mono">0%</span>
          </div>
        </div>

        <!-- Stacked Progress Bar -->
        <div class="space-y-1.5">
          <div class="h-3 w-full bg-slate-950 rounded-full overflow-hidden flex border border-slate-800">
            <div id="bar-leverage" class="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 transition-all duration-300" style="width: 0%"></div>
            <div id="bar-neutral" class="h-full bg-gradient-to-r from-sky-600 to-sky-400 transition-all duration-300" style="width: 0%"></div>
            <div id="bar-overhead" class="h-full bg-gradient-to-r from-rose-600 to-rose-400 transition-all duration-300" style="width: 0%"></div>
          </div>
          <div class="flex justify-between text-[10px] text-slate-400 font-mono">
            <span class="text-indigo-400">■ Leverage (10x-100x)</span>
            <span class="text-sky-400">■ Neutral (1x)</span>
            <span class="text-rose-400">■ Overhead (&lt;1x)</span>
          </div>
        </div>

        <!-- Dynamic Diagnostic Box -->
        <div id="diagnostic-box" class="p-3.5 rounded-xl border text-xs leading-relaxed transition-all"></div>
      </div>

      <!-- Add New Task Form -->
      <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row gap-3 items-center">
        <input type="text" id="input-task-title" placeholder="Add a new task (e.g., 'Draft 2025 Vision & Bets PRD')..." class="flex-1 w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:border-indigo-400 focus:outline-none" onkeydown="if(event.key==='Enter') addTask()" />
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <input type="number" id="input-task-hours" value="4" min="0.5" step="0.5" max="40" class="w-20 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-center text-slate-100 focus:border-indigo-400 focus:outline-none" title="Estimated hours per week" />
          <span class="text-xs text-slate-400">hrs</span>
          <select id="input-task-type" class="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 focus:border-indigo-400 focus:outline-none">
            <option value="L">🚀 Leverage (L)</option>
            <option value="N">⚖️ Neutral (N)</option>
            <option value="O">📦 Overhead (O)</option>
          </select>
          <button onclick="addTask()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold whitespace-nowrap transition shadow-md shadow-indigo-600/30">+ Add Task</button>
        </div>
      </div>

      <!-- 3 Kanban Columns -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Leverage Column -->
        <div class="rounded-2xl bg-slate-900/70 border border-indigo-500/30 p-4 space-y-4 shadow-lg flex flex-col">
          <div class="flex items-center justify-between pb-3 border-b border-indigo-500/20">
            <div>
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-pulse"></span>
                <h3 class="text-sm font-bold text-slate-100">Leverage (L)</h3>
              </div>
              <p class="text-[11px] text-indigo-300/80 mt-0.5">10x - 100x return • Great work matters</p>
            </div>
            <span id="col-count-l" class="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono font-bold">0</span>
          </div>
          <div id="cards-l" class="space-y-3 flex-1 min-h-[160px]"></div>
        </div>

        <!-- Neutral Column -->
        <div class="rounded-2xl bg-slate-900/70 border border-sky-500/30 p-4 space-y-4 shadow-lg flex flex-col">
          <div class="flex items-center justify-between pb-3 border-b border-sky-500/20">
            <div>
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
                <h3 class="text-sm font-bold text-slate-100">Neutral (N)</h3>
              </div>
              <p class="text-[11px] text-sky-300/80 mt-0.5">1x return • Good is good enough</p>
            </div>
            <span id="col-count-n" class="px-2.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-mono font-bold">0</span>
          </div>
          <div id="cards-n" class="space-y-3 flex-1 min-h-[160px]"></div>
        </div>

        <!-- Overhead Column -->
        <div class="rounded-2xl bg-slate-900/70 border border-rose-500/30 p-4 space-y-4 shadow-lg flex flex-col">
          <div class="flex items-center justify-between pb-3 border-b border-rose-500/20">
            <div>
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                <h3 class="text-sm font-bold text-slate-100">Overhead (O)</h3>
              </div>
              <p class="text-[11px] text-rose-300/80 mt-0.5">&lt;1x return • Batch, minimize, speed-run</p>
            </div>
            <span id="col-count-o" class="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-mono font-bold">0</span>
          </div>
          <div id="cards-o" class="space-y-3 flex-1 min-h-[160px]"></div>
        </div>
      </div>
    </div>

    <!-- TAB 2: THE LNO PHILOSOPHY & ENERGY TRAPS -->
    <div id="content-philosophy" class="hidden space-y-6">
      <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
        <div>
          <h2 class="text-lg font-bold text-slate-100">Shreyas Doshi's LNO Framework Philosophy</h2>
          <p class="text-xs text-slate-400 mt-1">Why traditional time management fails product leaders and how managing energy unlocks 100x impact.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 space-y-2">
            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider block">🚀 Leverage Tasks</span>
            <div class="text-sm font-bold text-slate-100">10x - 100x Return on Effort</div>
            <p class="text-xs text-slate-300 leading-relaxed">Doing a great job makes an enormous difference. Doing an average job is a wasted opportunity.</p>
            <div class="text-[11px] text-indigo-300/90 pt-2 border-t border-indigo-500/20">
              <strong>Stance:</strong> High energy, unhurried calendar blocks, perfectionism is warranted.
            </div>
          </div>

          <div class="p-5 rounded-2xl bg-sky-950/20 border border-sky-500/30 space-y-2">
            <span class="text-xs font-bold text-sky-400 uppercase tracking-wider block">⚖️ Neutral Tasks</span>
            <div class="text-sm font-bold text-slate-100">1x Return on Effort</div>
            <p class="text-xs text-slate-300 leading-relaxed">Doing a great job doesn't matter much. Doing a bad job hurts. Good enough is genuinely good enough.</p>
            <div class="text-[11px] text-sky-300/90 pt-2 border-t border-sky-500/20">
              <strong>Stance:</strong> "Done is better than perfect." Move fast, avoid over-polishing.
            </div>
          </div>

          <div class="p-5 rounded-2xl bg-rose-950/20 border border-rose-500/30 space-y-2">
            <span class="text-xs font-bold text-rose-400 uppercase tracking-wider block">📦 Overhead Tasks</span>
            <div class="text-sm font-bold text-slate-100">&lt;1x Return on Effort</div>
            <p class="text-xs text-slate-300 leading-relaxed">Administrative obligations and maintenance. Negative or negligible ROI, but necessary evils.</p>
            <div class="text-[11px] text-rose-300/90 pt-2 border-t border-rose-500/20">
              <strong>Stance:</strong> Speed-run, batch into low-energy blocks, delegate, or eliminate.
            </div>
          </div>
        </div>

        <div class="space-y-3 pt-4 border-t border-slate-800">
          <h3 class="text-sm font-bold text-slate-200">The 3 Common PM Traps (Why PMs Burn Out)</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span class="font-bold text-amber-400 block">1. The Perfectionist Trap</span>
              <p class="text-slate-400">Treating Neutral tasks like Leverage. Spending 15 hours crafting a 100-page PRD when a 3-page spec would have achieved the exact same 1x outcome.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span class="font-bold text-rose-400 block">2. The Overhead Black Hole</span>
              <p class="text-slate-400">Allowing status decks, emails, and ticket triage to swallow prime morning hours when cognitive bandwidth is at its highest.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span class="font-bold text-sky-400 block">3. The False Leverage Illusion</span>
              <p class="text-slate-400">Confusing high-visibility busywork (attending every executive sync) with true product leverage (customer insight, clear strategy, team unblocking).</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: REAL-WORLD PM ROLE PRESETS -->
    <div id="content-presets" class="hidden space-y-6">
      <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
        <div>
          <h2 class="text-lg font-bold text-slate-100">Load Real-World PM Role Presets</h2>
          <p class="text-xs text-slate-400 mt-1">Select a scenario below to instantly populate the LNO matrix and see how energy allocation changes.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <!-- Preset 1 -->
          <div class="p-5 rounded-2xl bg-slate-950 border border-emerald-500/40 space-y-3 flex flex-col justify-between">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">Healthy Model</span>
                <span class="text-xs font-mono text-slate-400">~33.5 hrs/wk</span>
              </div>
              <h3 class="text-sm font-bold text-slate-100">Senior PM (High Performer)</h3>
              <p class="text-xs text-slate-400 leading-relaxed">Protects ~57% of energy for core strategy and discovery, keeps neutral work solid, and caps overhead under 15%.</p>
            </div>
            <button onclick="loadPreset('senior_pm')" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold transition">Load Senior PM Preset</button>
          </div>

          <!-- Preset 2 -->
          <div class="p-5 rounded-2xl bg-slate-950 border border-rose-500/40 space-y-3 flex flex-col justify-between">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold">Burnout Alert</span>
                <span class="text-xs font-mono text-slate-400">~42 hrs/wk</span>
              </div>
              <h3 class="text-sm font-bold text-slate-100">Overwhelmed PM (Overhead Drag)</h3>
              <p class="text-xs text-slate-400 leading-relaxed">Suffering from calendar fragmentation, endless executive update decks, and firefighting. Overhead exceeds 50%!</p>
            </div>
            <button onclick="loadPreset('burnout_pm')" class="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition">Load Burnout Preset</button>
          </div>

          <!-- Preset 3 -->
          <div class="p-5 rounded-2xl bg-slate-950 border border-indigo-500/40 space-y-3 flex flex-col justify-between">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 text-[10px] font-bold">0-to-1 Focus</span>
                <span class="text-xs font-mono text-slate-400">~36 hrs/wk</span>
              </div>
              <h3 class="text-sm font-bold text-slate-100">0-to-1 Founder / Founding PM</h3>
              <p class="text-xs text-slate-400 leading-relaxed">Aggressive focus on customer interviews, positioning, and PMF validation. Minimal organizational overhead.</p>
            </div>
            <button onclick="loadPreset('founder_pm')" class="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition">Load Founder Preset</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let tasks = [
      { id: '1', title: 'Annual Product Strategy & Core Bets', hours: 8, type: 'L' },
      { id: '2', title: 'Core Onboarding Redesign PRD', hours: 6, type: 'L' },
      { id: '3', title: 'Customer Discovery Interviews (5 calls)', hours: 5, type: 'L' },
      { id: '4', title: 'Sprint Planning & Backlog Refinement', hours: 3, type: 'N' },
      { id: '5', title: 'Weekly 1:1s with Eng & Design Leads', hours: 4, type: 'N' },
      { id: '6', title: 'Feature Spec for Minor Integration', hours: 3, type: 'N' },
      { id: '7', title: 'Weekly Exec Status Update Email', hours: 1.5, type: 'O' },
      { id: '8', title: 'JIRA Bug Triage & Ticket Hygiene', hours: 2, type: 'O' },
      { id: '9', title: 'Expense Reporting & Team Logistics', hours: 1, type: 'O' }
    ];

    const PRESETS = {
      senior_pm: [
        { id: '1', title: 'Annual Product Strategy & Core Bets', hours: 8, type: 'L' },
        { id: '2', title: 'Core Onboarding Redesign PRD', hours: 6, type: 'L' },
        { id: '3', title: 'Customer Discovery Interviews (5 calls)', hours: 5, type: 'L' },
        { id: '4', title: 'Sprint Planning & Backlog Refinement', hours: 3, type: 'N' },
        { id: '5', title: 'Weekly 1:1s with Eng & Design Leads', hours: 4, type: 'N' },
        { id: '6', title: 'Feature Spec for Minor Integration', hours: 3, type: 'N' },
        { id: '7', title: 'Weekly Exec Status Update Email', hours: 1.5, type: 'O' },
        { id: '8', title: 'JIRA Bug Triage & Ticket Hygiene', hours: 2, type: 'O' },
        { id: '9', title: 'Expense Reporting & Team Logistics', hours: 1, type: 'O' }
      ],
      burnout_pm: [
        { id: '1', title: 'Product Strategy (Drafted hastily at night)', hours: 2, type: 'L' },
        { id: '2', title: 'Weekly Exec Status Rollup Deck (30 slides)', hours: 8, type: 'O' },
        { id: '3', title: 'Backlog Grooming & User Stories', hours: 6, type: 'N' },
        { id: '4', title: 'Cross-functional Alignment Syncs', hours: 6, type: 'N' },
        { id: '5', title: 'Answering Ad-hoc Slack Pings & Threads', hours: 7, type: 'O' },
        { id: '6', title: 'Daily Escalation Firefighting', hours: 5, type: 'O' },
        { id: '7', title: 'Filing & Updating 50+ JIRA Tickets', hours: 4, type: 'O' },
        { id: '8', title: 'Feature Kickoff Prep Slides', hours: 4, type: 'N' }
      ],
      founder_pm: [
        { id: '1', title: 'Customer Problem & Pricing Interviews (10 users)', hours: 12, type: 'L' },
        { id: '2', title: 'DHM Moats & Product Differentiation Map', hours: 8, type: 'L' },
        { id: '3', title: 'High-Expectation Customer (HXC) PRD', hours: 8, type: 'L' },
        { id: '4', title: 'Weekly Build & Sprint Review with Founding Eng', hours: 3, type: 'N' },
        { id: '5', title: 'Landing Page Copywriting & QA', hours: 3, type: 'N' },
        { id: '6', title: 'Vendor Onboarding & Admin Paperwork', hours: 2, type: 'O' }
      ]
    };

    function switchTab(tabId) {
      ['board', 'philosophy', 'presets'].forEach(t => {
        const btn = document.getElementById('tab-' + t);
        const content = document.getElementById('content-' + t);
        if (t === tabId) {
          btn.className = 'tab-btn active px-4 py-2 rounded-xl text-xs transition';
          content.classList.remove('hidden');
        } else {
          btn.className = 'tab-btn px-4 py-2 rounded-xl text-xs transition';
          content.classList.add('hidden');
        }
      });
    }

    function addTask() {
      const titleInput = document.getElementById('input-task-title');
      const hoursInput = document.getElementById('input-task-hours');
      const typeInput = document.getElementById('input-task-type');

      const title = titleInput.value.trim();
      const hours = parseFloat(hoursInput.value) || 2;
      const type = typeInput.value;

      if (!title) {
        titleInput.focus();
        return;
      }

      tasks.push({
        id: Date.now().toString(),
        title: title,
        hours: hours,
        type: type
      });

      titleInput.value = '';
      renderBoard();
    }

    function deleteTask(id) {
      tasks = tasks.filter(t => t.id !== id);
      renderBoard();
    }

    function moveTask(id, targetType) {
      const task = tasks.find(t => t.id === id);
      if (task) {
        task.type = targetType;
        renderBoard();
      }
    }

    function loadPreset(presetKey) {
      if (PRESETS[presetKey]) {
        tasks = JSON.parse(JSON.stringify(PRESETS[presetKey]));
        switchTab('board');
        renderBoard();
      }
    }

    function renderBoard() {
      const containerL = document.getElementById('cards-l');
      const containerN = document.getElementById('cards-n');
      const containerO = document.getElementById('cards-o');

      containerL.innerHTML = '';
      containerN.innerHTML = '';
      containerO.innerHTML = '';

      let hoursL = 0, hoursN = 0, hoursO = 0;
      let countL = 0, countN = 0, countO = 0;

      tasks.forEach(task => {
        const card = document.createElement('div');
        card.className = 'p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition shadow-sm space-y-2';

        let moveControls = '';
        if (task.type === 'L') {
          hoursL += task.hours; countL++;
          moveControls = `
            <div class="flex items-center gap-1.5">
              <button onclick="moveTask('${task.id}', 'N')" class="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800/60 hover:bg-sky-900 text-[10px] font-medium transition" title="Move to Neutral">→ N</button>
              <button onclick="moveTask('${task.id}', 'O')" class="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800/60 hover:bg-rose-900 text-[10px] font-medium transition" title="Move to Overhead">→ O</button>
            </div>
          `;
        } else if (task.type === 'N') {
          hoursN += task.hours; countN++;
          moveControls = `
            <div class="flex items-center gap-1.5">
              <button onclick="moveTask('${task.id}', 'L')" class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 hover:bg-indigo-900 text-[10px] font-medium transition" title="Promote to Leverage">← L</button>
              <button onclick="moveTask('${task.id}', 'O')" class="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800/60 hover:bg-rose-900 text-[10px] font-medium transition" title="Move to Overhead">→ O</button>
            </div>
          `;
        } else if (task.type === 'O') {
          hoursO += task.hours; countO++;
          moveControls = `
            <div class="flex items-center gap-1.5">
              <button onclick="moveTask('${task.id}', 'L')" class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 hover:bg-indigo-900 text-[10px] font-medium transition" title="Promote to Leverage">← L</button>
              <button onclick="moveTask('${task.id}', 'N')" class="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800/60 hover:bg-sky-900 text-[10px] font-medium transition" title="Move to Neutral">← N</button>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="flex items-start justify-between gap-2">
            <span class="text-xs font-semibold text-slate-100 leading-snug">${task.title}</span>
            <button onclick="deleteTask('${task.id}')" class="text-slate-500 hover:text-rose-400 text-xs px-1" title="Delete task">✕</button>
          </div>
          <div class="flex items-center justify-between pt-1 text-[10px]">
            <span class="font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">${task.hours} hrs/wk</span>
            ${moveControls}
          </div>
        `;

        if (task.type === 'L') containerL.appendChild(card);
        else if (task.type === 'N') containerN.appendChild(card);
        else if (task.type === 'O') containerO.appendChild(card);
      });

      // Update Column Counters
      document.getElementById('col-count-l').innerText = `${countL} (${hoursL}h)`;
      document.getElementById('col-count-n').innerText = `${countN} (${hoursN}h)`;
      document.getElementById('col-count-o').innerText = `${countO} (${hoursO}h)`;

      // Totals & Percentages
      const totalHours = hoursL + hoursN + hoursO;
      const pctL = totalHours > 0 ? Math.round((hoursL / totalHours) * 100) : 0;
      const pctN = totalHours > 0 ? Math.round((hoursN / totalHours) * 100) : 0;
      const pctO = totalHours > 0 ? Math.round((hoursO / totalHours) * 100) : 0;

      document.getElementById('metric-total-hours').innerText = `${totalHours.toFixed(1)} hrs/wk`;
      document.getElementById('metric-total-tasks').innerText = tasks.length;

      document.getElementById('metric-l-hours').innerText = `${hoursL.toFixed(1)} hrs`;
      document.getElementById('badge-l-pct').innerText = `${pctL}%`;

      document.getElementById('metric-n-hours').innerText = `${hoursN.toFixed(1)} hrs`;
      document.getElementById('badge-n-pct').innerText = `${pctN}%`;

      document.getElementById('metric-o-hours').innerText = `${hoursO.toFixed(1)} hrs`;
      document.getElementById('badge-o-pct').innerText = `${pctO}%`;

      // Stacked Bar
      document.getElementById('bar-leverage').style.width = `${pctL}%`;
      document.getElementById('bar-neutral').style.width = `${pctN}%`;
      document.getElementById('bar-overhead').style.width = `${pctO}%`;

      // Diagnostic Box
      const diagBox = document.getElementById('diagnostic-box');
      if (totalHours === 0) {
        diagBox.className = 'p-3.5 rounded-xl border text-xs leading-relaxed bg-slate-950 border-slate-800 text-slate-400';
        diagBox.innerHTML = 'Add tasks or select a preset to evaluate your energy allocation.';
      } else if (pctO >= 25) {
        diagBox.className = 'p-3.5 rounded-xl border text-xs leading-relaxed bg-rose-950/30 border-rose-800/50 text-rose-200';
        diagBox.innerHTML = `<strong class="font-bold text-rose-300 block mb-1 text-sm">🚨 Overhead Overload Warning (High Burnout Risk):</strong>
          You are spending <strong>${pctO}% (${hoursO} hrs)</strong> of your weekly energy on Overhead (&lt;1x return). Shreyas Doshi warns that this is the #1 cause of PM exhaustion and stagnation. Batch your admin tasks, aggressively say NO to low-value status decks, and delegate operational chores to protect high-leverage focus blocks.`;
      } else if (pctL >= 45 && pctO <= 15) {
        diagBox.className = 'p-3.5 rounded-xl border text-xs leading-relaxed bg-emerald-950/30 border-emerald-800/50 text-emerald-200';
        diagBox.innerHTML = `<strong class="font-bold text-emerald-300 block mb-1 text-sm">🏆 Optimal High-Leverage Flow:</strong>
          Outstanding allocation! You are dedicating <strong>${pctL}% (${hoursL} hrs)</strong> of your peak creative bandwidth to true 10x-100x bets, while keeping operational drag low at <strong>${pctO}% (${hoursO} hrs)</strong>. This aligns with Shreyas Doshi's ideal high-agency product leader distribution.`;
      } else if (pctN >= 50) {
        diagBox.className = 'p-3.5 rounded-xl border text-xs leading-relaxed bg-amber-950/30 border-amber-800/50 text-amber-200';
        diagBox.innerHTML = `<strong class="font-bold text-amber-300 block mb-1 text-sm">⚠️ Neutral Trap (The Feature Factory):</strong>
          <strong>${pctN}% (${hoursN} hrs)</strong> of your energy is trapped in Neutral (1x) tasks. Doing an exceptional job on neutral tasks does not move the company needle. Embrace 'Done is better than perfect' on routine specs, and carve out 10-15 unhurried hours for high-leverage product strategy.`;
      } else {
        diagBox.className = 'p-3.5 rounded-xl border text-xs leading-relaxed bg-indigo-950/30 border-indigo-800/50 text-indigo-200';
        diagBox.innerHTML = `<strong class="font-bold text-indigo-300 block mb-1 text-sm">🧭 Balanced Distribution:</strong>
          Leverage: <strong>${pctL}%</strong> | Neutral: <strong>${pctN}%</strong> | Overhead: <strong>${pctO}%</strong>. Look for opportunities to shift 1x tasks into 'good enough' so you can amplify your 10x-100x bets.`;
      }
    }

    window.addEventListener('DOMContentLoaded', () => { renderBoard(); });
    setTimeout(renderBoard, 100);
  </script>
</body>
</html>
"""

    async def detect_intent(self, message: str, explicit_skill: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Determines user intent via Anthropic Agent SDK Tool Calling.
        Falls back to local keyword routing if no API key is present or if offline.
        """
        if explicit_skill:
            if explicit_skill == "artifact":
                msg_lower = message.lower()
                art_type = "markdown" if any(t in msg_lower for t in ["markdown", "prd", "framework doc", "template"]) else "html"
                return "artifact", art_type
            return explicit_skill, None

        # 1. Agentic SDK Routing
        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "sk-ant-...":
            try:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                tools = [
                    {
                        "name": "search_podcast_knowledge_base",
                        "description": "Searches the Lenny's Podcast transcripts for product, growth, or PM advice.",
                        "input_schema": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "write_ship30_essay",
                        "description": "Writes a 1,250-word atomic essay on a requested topic with a 1-3-1 hook.",
                        "input_schema": {
                            "type": "object",
                            "properties": {"topic": {"type": "string"}},
                            "required": ["topic"]
                        }
                    },
                    {
                        "name": "generate_interactive_artifact",
                        "description": "Generates a reusable artifact like a PRD, Markdown document, HTML interactive widget, or scorecard.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "format": {
                                    "type": "string",
                                    "enum": ["markdown", "html"],
                                    "description": "The format of the artifact."
                                }
                            },
                            "required": ["format"]
                        }
                    }
                ]
                
                response = await client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=150,
                    tools=tools,
                    messages=[{"role": "user", "content": message}]
                )
                
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"Agent SDK routed to tool: {block.name}")
                        if block.name == "write_ship30_essay":
                            return "ship30", None
                        elif block.name == "generate_interactive_artifact":
                            fmt = block.input.get("format", "html")
                            return "artifact", fmt
                        else:
                            return "qa", None
                            
                return "qa", None
            except Exception as e:
                logger.warning(f"Anthropic SDK tool routing failed: {e}. Falling back to local routing.")
        else:
            logger.info("Anthropic API Key not configured. Using local fallback keyword routing.")

        # 2. Local Fallback Routing
        msg_lower = message.lower()
        if any(term in msg_lower for term in ["ship 30", "ship30", "atomic essay", "1250 words", "write an essay"]):
            return "ship30", None
        if any(term in msg_lower for term in ["interactive", "html", "css", "scorecard", "canvas", "calculator", "prototype", "widget", "ui component"]):
            return "artifact", "html"
        if any(term in msg_lower for term in ["prd", "document", "framework doc", "template"]):
            return "artifact", "markdown"
        return "qa", None

    def extract_artifacts(self, text: str) -> Tuple[str, List[ArtifactPayload]]:
        """Extracts artifacts from text (supports ```artifact:... blocks, ```html blocks, unclosed blocks, and raw HTML)."""
        artifacts: List[ArtifactPayload] = []

        # 1. First check explicit ```artifact:(type):(title) blocks
        pattern = re.compile(r"```artifact:(html|markdown|code):([^\n]*)\n(.*?)```", re.DOTALL)
        for match in pattern.finditer(text):
            art_type = match.group(1).strip()
            art_title = match.group(2).strip() or "Interactive PMF Scorecard"
            content = match.group(3).strip()
            if art_type == "html" and ("<" not in content or len(content) < 40):
                continue
            artifacts.append(ArtifactPayload(
                title=art_title,
                artifact_type=art_type,
                content=content
            ))

        # 2. Check for closed ```html ... ``` code blocks
        if not artifacts and "```html" in text:
            html_blocks = re.findall(r"```html\s*\n(.*?)```", text, re.DOTALL)
            if html_blocks:
                combined_html = "\n".join(b.strip() for b in html_blocks)
                if "<" in combined_html:
                    artifacts.append(ArtifactPayload(
                        title="Interactive PMF Survey & Scorecard",
                        artifact_type="html",
                        content=combined_html
                    ))

        # 3. Check for unclosed ```artifact: tag (if output was cut off mid-stream)
        if not artifacts and "```artifact:" in text:
            unclosed_match = re.search(r"```artifact:(html|markdown|code):([^\n]*)\n(.*)$", text, re.DOTALL)
            if unclosed_match:
                art_type = unclosed_match.group(1).strip()
                art_title = unclosed_match.group(2).strip() or "Interactive PMF Scorecard"
                raw_code = unclosed_match.group(3).strip()
                if "<" in raw_code:
                    if "<script" in raw_code and "</script>" not in raw_code:
                        raw_code += "\n</script>"
                    if "<form" in raw_code and "</form>" not in raw_code:
                        raw_code += "\n</form>"
                    if "</body>" not in raw_code:
                        raw_code += "\n</body></html>"
                    elif "</html>" not in raw_code:
                        raw_code += "\n</html>"
                    artifacts.append(ArtifactPayload(
                        title=art_title,
                        artifact_type=art_type,
                        content=raw_code
                    ))

        # 4. Check for unclosed ```html block
        if not artifacts and "```html" in text:
            unclosed_html = re.search(r"```html\s*\n(.*)$", text, re.DOTALL)
            if unclosed_html:
                raw_html = unclosed_html.group(1).strip()
                if "<" in raw_html:
                    if "<script" in raw_html and "</script>" not in raw_html:
                        raw_html += "\n</script>"
                    if "<form" in raw_html and "</form>" not in raw_html:
                        raw_html += "\n</form>"
                    if "</body>" not in raw_html:
                        raw_html += "\n</body></html>"
                    elif "</html>" not in raw_html:
                        raw_html += "\n</html>"
                    artifacts.append(ArtifactPayload(
                        title="Interactive PMF Survey & Scorecard",
                        artifact_type="html",
                        content=raw_html
                    ))

        # 5. Fallback check for raw HTML markup
        if not artifacts and ("<!DOCTYPE html>" in text or ("<html" in text and "</html>" in text) or ("<form" in text and "</form>" in text)):
            html_match = re.search(r"(<!DOCTYPE html.*?>.*?</html>|<html.*?>.*?</html>|<form.*?</form>)", text, re.DOTALL | re.IGNORECASE)
            if html_match:
                artifacts.append(ArtifactPayload(
                    title="Interactive Growth Widget",
                    artifact_type="html",
                    content=html_match.group(1).strip()
                ))

        # Heal any artifacts that have placeholder ellipsis or broken snippets
        for art in artifacts:
            if art.artifact_type == "html":
                has_placeholder = "..." in art.content and ("rest of" in art.content or "HTML content" in art.content or "rest" in art.content)
                if has_placeholder or len(art.content) < 120:
                    if any(k in art.title.lower() for k in ["lno", "shreyas", "leverage", "overhead", "matrix"]):
                        art.content = self.get_lno_matrix_template()
                    elif any(k in art.title.lower() for k in ["dhm", "biddle"]):
                        art.content = self.get_dhm_scorecard_template()
                    elif any(k in art.title.lower() for k in ["pmf", "survey", "scorecard", "calculator", "growth", "superhuman"]):
                        art.content = self.get_pmf_scorecard_template()

        cleaned_text = re.sub(r"```artifact:(html|markdown|code):([^\n]*)\n(.*?)```", r"\n*[Generated Artifact: **\2** (\1) - View in the Artifact Panel beside chat]*\n", text, flags=re.DOTALL)
        if artifacts and "```artifact:" in cleaned_text:
            first_art = artifacts[0]
            cleaned_text = re.sub(r"```artifact:.*", f"\n*[Generated Artifact: **{first_art.title}** ({first_art.artifact_type.upper()}) - View in the Artifact Panel beside chat]*\n", cleaned_text, flags=re.DOTALL)
        return cleaned_text, artifacts

    async def stream_chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        model_name: Optional[str] = None,
        skill: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main streaming loop orchestrating retrieval, grounding, and response generation.
        Yields JSON event dictionaries via Server-Sent Events.
        """
        model = model_name or settings.DEFAULT_LOCAL_MODEL
        intent, artifact_type = await self.detect_intent(message, skill)

        yield {"type": "status", "message": f"Searching 303 Lenny transcripts for relevant insights..."}

        # Step 1: Hybrid Retrieval
        citations, is_grounded = self.retriever.search(message, top_k=5)

        # Hallucination guardrail — is_grounded is False when retrieval confidence is too low
        if not is_grounded:
            yield {"type": "citations", "citations": []}
            refusal_msg = (
                "I searched Lenny's podcast archives for this topic, but no matching discussion was found "
                "in the transcripts.\n\n"
                "The Lenny Growth Assistant strictly answers questions based on insights shared by guests on the show "
                "(e.g. Product-Market Fit, B2B Growth Loops, Retention, Onboarding, Pricing, and Team Building). "
                "Please try asking about a specific guest, framework, or company covered on the podcast!"
            )
            for token in refusal_msg.split(" "):
                yield {"type": "token", "token": token + " "}
            yield {"type": "done", "full_text": refusal_msg, "artifacts": []}
            return

        yield {"type": "citations", "citations": [c.model_dump() for c in citations]}
        context = self.retriever.format_context_for_prompt(citations)

        # Step 2: Build specialized prompt
        if intent == "ship30":
            yield {"type": "status", "message": "Invoking Ship 30 for 30 Skill (1,250 words, 1-3-1 hook, skimmable)..."}
            system_instruction = self.ship30_skill.get_system_prompt()
            user_instruction = self.ship30_skill.build_prompt(topic=message, context=context)
        elif intent == "artifact":
            safe_type = artifact_type or "html"
            is_dhm = any(k in message.lower() for k in ["dhm", "biddle", "delight", "hard-to-copy", "hard to copy", "margin-enhanc"])
            is_lno = not is_dhm and any(k in message.lower() for k in ["lno", "shreyas", "leverage", "overhead", "neutral", "matrix", "doshi"])
            is_pmf_calc = not is_dhm and not is_lno and any(k in message.lower() for k in ["pmf", "vohra", "superhuman", "product market fit", "sean ellis", "ellis"])
            if is_dhm:
                yield {"type": "status", "message": "Synthesizing Gibson Biddle's DHM Product Strategy Scorecard..."}
                overview_text = (
                    "### Gibson Biddle's DHM Product Strategy Scorecard\n\n"
                    "I have generated the interactive **DHM Product Strategy Scorecard** artifact for you in the panel beside this chat!\n\n"
                    "#### 1. What is the DHM Model? (Delight, Hard-to-Copy, Margin)\n"
                    "In his conversation on *Lenny's Podcast*, **Gibson Biddle** (former VP of Product at Netflix and Chief Product Officer at Chegg) defines product strategy as a hypothesis for how a company will:\n"
                    "- **D - Delight Customers**: How will your product solve customer problems, reduce friction, and bring genuine joy so users retain and recommend?\n"
                    "- **H - Hard to Copy**: What will prevent competitors from immediately cloning your features? Gibson highlights the **4 Classic Moats**: *Brand*, *Network Effects*, *Economies of Scale*, and *Switching Costs / Proprietary Technology*.\n"
                    "- **M - Margin-Enhancing**: How will the initiative expand business margins (pricing power, lower acquisition/churn cost, higher customer lifetime value)?\n\n"
                    "#### 2. The 4 Hard-to-Copy Moats at Netflix\n"
                    "1. **Brand**: Trusted entertainment destination (e.g. Netflix as the default button on TV remotes).\n"
                    "2. **Network Effects**: Rare in solo entertainment; tried with the 'Friends' feature which failed and was killed.\n"
                    "3. **Economies of Scale**: Amortizing massive content and streaming infrastructure investments across hundreds of millions of subscribers.\n"
                    "4. **Proprietary Tech & Switching Costs**: Personalized recommendations and viewing history that make switching away friction-heavy.\n\n"
                    "👉 **Interactive Tool Ready in Artifact Panel**: Use the live sliders to score your feature, select your moats, check your strategic verdict (Triple Threat vs. Customer Pleaser vs. Margin Trap), and test historical Netflix case studies!"
                )
                for token in overview_text.split(" "):
                    yield {"type": "token", "token": token + " "}
                    await asyncio.sleep(0.008)

                html_artifact = self.get_dhm_scorecard_template()
                artifacts = [
                    ArtifactPayload(
                        title="Gibson Biddle DHM Strategy Scorecard",
                        artifact_type="html",
                        content=html_artifact
                    )
                ]
                yield {
                    "type": "done",
                    "full_text": overview_text,
                    "artifacts": [a.model_dump() for a in artifacts]
                }
                return

            if is_lno:
                yield {"type": "status", "message": "Synthesizing Shreyas Doshi's LNO Task Matrix & Energy Dashboard..."}
                overview_text = (
                    "### Shreyas Doshi's LNO Framework & Energy Allocation Matrix\n\n"
                    "I have generated the interactive **Shreyas Doshi LNO Task Matrix & Energy Dashboard** artifact for you in the panel beside this chat!\n\n"
                    "#### 1. What is the LNO Framework?\n"
                    "In his appearances on *Lenny's Podcast*, **Shreyas Doshi** (former product leader at Stripe, Twitter, Google, and Yahoo) explains that traditional time management fails for product leaders because it treats all tasks as equally deserving of high quality. Instead, the LNO framework re-frames productivity as an **energy management system** based on return on effort:\n"
                    "- **🚀 L — Leverage Tasks (10x to 100x Return)**:\n"
                    "  - Doing an exceptional job makes an enormous, non-linear difference to your product or company.\n"
                    "  - *Examples*: Product strategy, defining core vision, key architectural choices, game-changing PRDs, critical hiring, pivotal exec pitches.\n"
                    "  - *Operating Stance*: High energy, unhurried calendar blocks, perfectionism is completely justified.\n"
                    "- **⚖️ N — Neutral Tasks (1x Return)**:\n"
                    "  - Doing an exceptional job doesn't matter much, but doing a bad job hurts.\n"
                    "  - *Examples*: Standard PRDs, weekly sprint planning, routine product reviews, recurring 1:1s, release notes.\n"
                    "  - *Operating Stance*: \"Done is better than perfect.\" Do a solid, good job, but resist the urge to over-polish.\n"
                    "- **📦 O — Overhead Tasks (<1x Return)**:\n"
                    "  - Negative or negligible ROI. Operational chores that are necessary evils.\n"
                    "  - *Examples*: Status emails, expense reports, compliance training, minor bug triaging, calendar scheduling.\n"
                    "  - *Operating Stance*: Speed-run, batch into low-energy time windows (e.g. late Friday afternoons), delegate, automate, or eliminate.\n\n"
                    "#### 2. The Root Cause of PM Burnout\n"
                    "Shreyas points out that most high-achieving PMs burn out because they treat **every task as Leverage** (the *Perfectionist Trap*). If you try to deliver a 100/100 masterpiece on a routine status report or a 1x PRD, you deplete the cognitive energy required for your true 10x-100x bets.\n\n"
                    "#### 3. Optimal Allocation Guideline\n"
                    "- **Leverage**: ~50% of your peak cognitive energy (even if it's only ~20% of your task count).\n"
                    "- **Neutral**: ~30-35% of your energy.\n"
                    "- **Overhead**: Under 15% of your energy.\n\n"
                    "👉 **Interactive Tool Ready in Artifact Panel**: Use the 3-column Kanban board to classify tasks, track your weekly energy distribution, inspect real-time burnout diagnostics, and test real-world PM presets!"
                )
                for token in overview_text.split(" "):
                    yield {"type": "token", "token": token + " "}
                    await asyncio.sleep(0.008)

                html_artifact = self.get_lno_matrix_template()
                artifacts = [
                    ArtifactPayload(
                        title="Shreyas Doshi LNO Task Matrix & Energy Dashboard",
                        artifact_type="html",
                        content=html_artifact
                    )
                ]
                yield {
                    "type": "done",
                    "full_text": overview_text,
                    "artifacts": [a.model_dump() for a in artifacts]
                }
                return

            if is_pmf_calc:
                yield {"type": "status", "message": "Synthesizing Interactive PMF Scorecard & Survey Engine..."}
                overview_text = (
                    "### Rahul Vohra's Product-Market Fit Engine & Scorecard\n\n"
                    "I have generated the interactive **PMF Survey Calculator & Scorecard** artifact for you in the panel beside this chat!\n\n"
                    "#### 1. How Superhuman Measures PMF (The Sean Ellis Benchmark)\n"
                    "In his interview on *Lenny's Podcast*, **Rahul Vohra** (Founder & CEO of Superhuman) explains how they turned Sean Ellis's 40% threshold into an actionable engineering engine:\n"
                    "- **The Metric Question**: *\"How would you feel if you could no longer use the product?\"*\n"
                    "- **The 40% Threshold**: If **≥ 40%** of respondents answer that they would be **\"Very Disappointed\"**, the company has achieved Product-Market Fit. Under 40%, companies struggle to scale and leak churned users.\n"
                    "- **Superhuman's Progression**: In Summer 2017, Superhuman measured only **22%** (pre-PMF). By executing their survey and segmentation engine, they increased their PMF score to **58%** at public launch.\n\n"
                    "#### 2. The 4-Question Survey Engine\n"
                    "1. **Question #1 (The Quantitative Gate)**: *\"How would you feel if you could no longer use the product?\"* (Options: *Very disappointed*, *Somewhat disappointed*, *Not disappointed*). Used strictly to calculate the PMF %.\n"
                    "2. **Question #2 (The High-Expectation Customer - HXC)**: *\"What type of person do you think would benefit most from the product?\"* Filter exclusively for respondents who answered \"Very Disappointed\" to define your true Ideal Customer Profile (ICP).\n"
                    "3. **Question #3 (The Core Superpower)**: *\"What is the main benefit you receive from the product?\"* For Superhuman, users unanimously cited **speed and keyboard shortcuts**. Dedicate 50% of your roadmap to protecting and deepening this.\n"
                    "4. **Question #4 (The Disappointment Filter)**: *\"How can we improve the product for you?\"* Politely ignore \"Not Disappointed\" users. Filter \"Somewhat Disappointed\" users whose main benefit matched your core lovers, and build the specific features holding them back (e.g. mobile app, calendar, offline search).\n\n"
                    "#### 3. The 50/50 Engineering Roadmap Rule\n"
                    "- **50% of Engineering Capacity**: Double down on core love (speed, keyboard shortcuts, performance).\n"
                    "- **50% of Engineering Capacity**: Build blocker features requested by the \"Somewhat Disappointed\" cohort to convert them into \"Very Disappointed\" evangelists.\n\n"
                    "👉 **Interactive Tool Ready in Artifact Panel**: Use the interactive tabs to calculate PMF scores in real time, test historical scenario presets (22% vs 38% vs 58%), and review the step-by-step roadmap playbook!"
                )
                for token in overview_text.split(" "):
                    yield {"type": "token", "token": token + " "}
                    await asyncio.sleep(0.008)

                html_artifact = self.get_pmf_scorecard_template()
                artifacts = [
                    ArtifactPayload(
                        title="Interactive PMF Scorecard & Survey Calculator",
                        artifact_type="html",
                        content=html_artifact
                    )
                ]
                yield {
                    "type": "done",
                    "full_text": overview_text,
                    "artifacts": [a.model_dump() for a in artifacts]
                }
                return

            yield {"type": "status", "message": f"Generating interactive {safe_type.upper()} artifact..."}
            system_instruction = (
                "You are an expert full-stack engineer and product growth specialist. "
                "Output ONLY a complete, standalone vanilla HTML document with modern Tailwind CSS and client-side <script>. "
                "Do NOT use Vue, Angular, or React syntax. Use pure standard HTML5: <form>, <input>, <button>, and vanilla JavaScript."
            )
            user_instruction = (
                f"User Request: {message}\n\n"
                f"### Knowledge Base Context:\n{context}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. Build a complete, functional {safe_type.upper()} interactive component tailored to the user's specific request.\n"
                f"2. Use modern, beautiful Tailwind CSS styling, dark mode theme (slate-950 background, slate-100 text, clean borders and cards).\n"
                f"3. Include interactive inputs, controls, calculation/evaluation logic in vanilla JavaScript, and dynamic visual indicators or results.\n"
                f"4. Enclose the complete code inside:\n"
                f"```artifact:{safe_type}:Interactive Component\n"
                f"<!DOCTYPE html>\n<html lang=\"en\">\n...\n</html>\n"
                f"```\n"
                f"Start directly with ```artifact:{safe_type}:Interactive Component now:"
            )
        else:
            system_instruction = (
                "You are The Lenny Growth Assistant. Answer the user's question directly, clearly, and concisely "
                "based strictly on the provided podcast excerpts and verified frameworks.\n"
                "CRITICAL RULES FOR 100% FACTUAL ACCURACY:\n"
                "- Only define terms and frameworks using their verified meanings:\n"
                "  * Resulting (Annie Duke): Judging the quality of a decision solely by its outcome rather than the quality of the decision process. Good decisions can have bad outcomes due to luck, and bad decisions can have good outcomes.\n"
                "  * DHM Model (Gibson Biddle): Delight customers, Hard-to-copy advantage, Margin-enhancing.\n"
                "  * LNO Framework (Shreyas Doshi): Leverage (10x-100x return), Neutral (1x return), Overhead (<1x return).\n"
                "  * Pre-Mortem (Shreyas Doshi): Tigers (real threats that will actually kill the product/project), Paper Tigers (seeming threats that won't kill you), Elephants (unspoken truths/elephants in the room nobody talks about).\n"
                "  * PLG vs SLG (Elena Verna): PLG relies on self-serve product monetization and viral loops; SLG relies on human sales reps closing contracts.\n"
                "  * 40% PMF Benchmark (Sean Ellis / Rahul Vohra): Exact survey question is 'How would you feel if you could no longer use this product?' Options: 'Very disappointed', 'Somewhat disappointed', 'Not disappointed'. Score is % answering 'Very disappointed'; if >= 40%, you have product-market fit.\n"
                "  * Nikita Bier Virality: Hyper-local school seeding (launching in a single school with the earliest start date in Georgia, spreading to 40% of the school in 24 hours). The human trafficking rumor was a malicious internet smear/hoax started by teenagers that Nikita Bier had to aggressively debunk and fight—Nikita Bier NEVER created it.\n"
                "  * Product Positioning (April Dunford): The 5 components of product positioning are: 1. Competitive Alternatives (what customers do if you don't exist), 2. Differentiated Capabilities (unique features/capabilities you have that alternatives lack), 3. Value and Proof (the differentiated benefit/outcomes enabled by those capabilities), 4. Target Customer Segment (who cares most about that value), 5. Market Category (the context of reference that makes your value obvious). She warns against starting with features because features are only differentiated relative to competitive alternatives; without knowing what customers compare you against, you cannot know which features actually matter.\n"
                "- CONVERSATION ISOLATION: Focus strictly on the CURRENT question and the verified excerpts provided for it. Do NOT mix or carry over guests, frameworks, or concepts from prior conversation turns (e.g. do not apply Teresa Torres or April Dunford concepts to Nikita Bier).\n"
                "- NEVER invent or guess acronym definitions. If a term is not defined in the excerpts, state that clearly.\n"
                "- Ground all key points with guest names and timestamps.\n"
                "- Answer the user's question directly, factually, and definitively using the verified definitions and excerpts above."
            )
            user_instruction = (
                f"Here are verified excerpts from Lenny's Podcast:\n"
                f"---\n{context}\n---\n\n"
                f"Question: {message}\n\n"
                f"Answer the question directly and accurately based on the verified excerpts and frameworks above:"
            )

        yield {"type": "status", "message": f"Generating response with {model}..."}

        # Step 3: Route to LLM Engine (Local Ollama vs Cloud)
        full_response = ""
        max_predict = 1400 if intent == "artifact" else (1000 if intent == "ship30" else 420)

        # Topic isolation: if user asks about a new guest or distinct domain framework, clear prior history to prevent topic pollution
        effective_history = history
        if history and citations:
            current_guests = {re.sub(r"\s+2\.0$", "", c.guest).lower().strip() for c in citations if c.guest and c.guest != "Unknown"}
            prev_user_msg = next((m.get("content", "").lower() for m in reversed(history) if m.get("role") == "user"), "")
            current_guest_in_msg = any(
                g in message.lower() or any(token in message.lower() for token in g.split() if len(token) > 3)
                for g in current_guests
            )
            if current_guest_in_msg:
                prev_has_guest = any(
                    g in prev_user_msg or any(token in prev_user_msg for token in g.split() if len(token) > 3)
                    for g in current_guests
                )
                if not prev_has_guest:
                    logger.info("New guest inquiry detected. Isolating conversation context.")
                    effective_history = []

        try:
            if model.startswith("gemini"):
                clean_model = model.replace("gemini:", "") if ":" in model else settings.DEFAULT_GEMINI_MODEL
                async for chunk in self._stream_gemini(clean_model, system_instruction, user_instruction, effective_history):
                    full_response += chunk
                    yield {"type": "token", "token": chunk}
            elif model.startswith("groq"):
                clean_model = model.replace("groq:", "") if ":" in model else settings.DEFAULT_GROQ_MODEL
                async for chunk in self._stream_groq(clean_model, system_instruction, user_instruction, effective_history):
                    full_response += chunk
                    yield {"type": "token", "token": chunk}
            elif model.startswith("ollama:") or (not model.startswith("claude") and not model.startswith("gpt")):
                clean_model = model.replace("ollama:", "")
                async for chunk in self._stream_ollama(clean_model, system_instruction, user_instruction, effective_history, max_tokens=max_predict):
                    full_response += chunk
                    yield {"type": "token", "token": chunk}
            elif model.startswith("claude"):
                if not settings.ANTHROPIC_API_KEY:
                    notice = (
                        "> [!NOTE]\n"
                        "> **Cloud Model Selected**: `Claude 3.5 Sonnet` requires an `ANTHROPIC_API_KEY` in `.env`.\n"
                        f"> Automatically falling back to **Local: {settings.DEFAULT_LOCAL_MODEL} (Ollama)** for offline execution!\n\n"
                    )
                    yield {"type": "token", "token": notice}
                    full_response += notice
                    async for chunk in self._stream_ollama(settings.DEFAULT_LOCAL_MODEL, system_instruction, user_instruction, effective_history, max_tokens=max_predict):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
                else:
                    async for chunk in self._stream_claude(model, system_instruction, user_instruction, effective_history):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
            elif model.startswith("gpt"):
                if not settings.OPENAI_API_KEY:
                    notice = (
                        "> [!NOTE]\n"
                        "> **Cloud Model Selected**: `GPT-4o` requires an `OPENAI_API_KEY` in `.env`.\n"
                        f"> Automatically falling back to **Local: {settings.DEFAULT_LOCAL_MODEL} (Ollama)** for offline execution!\n\n"
                    )
                    yield {"type": "token", "token": notice}
                    full_response += notice
                    async for chunk in self._stream_ollama(settings.DEFAULT_LOCAL_MODEL, system_instruction, user_instruction, history, max_tokens=max_predict):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
                else:
                    async for chunk in self._stream_openai(model, system_instruction, user_instruction, history):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
            else:
                # Fallback to default local
                async for chunk in self._stream_ollama(settings.DEFAULT_LOCAL_MODEL, system_instruction, user_instruction, history, max_tokens=max_predict):
                    full_response += chunk
                    yield {"type": "token", "token": chunk}
        except Exception as e:
            logger.error(f"Inference error with model {model}: {e}")
            err_detail = str(e) or type(e).__name__
            # Automatic fallback to lightweight local model if a heavy model timed out
            if "mistral" in model and settings.FALLBACK_LOCAL_MODEL:
                yield {"type": "status", "message": f"Mistral timed out. Falling back to {settings.FALLBACK_LOCAL_MODEL}..."}
                try:
                    async for chunk in self._stream_ollama(settings.FALLBACK_LOCAL_MODEL, system_instruction, user_instruction, history, max_tokens=max_predict):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
                except Exception as fb_err:
                    error_fallback = (
                        f"\n\n> [!WARNING]\n"
                        f"> **Inference Error**: Could not connect to `{model}` ({err_detail}).\n"
                        f"> If using Ollama, ensure `ollama serve` is running. You may select `qwen2.5:0.5b` from the dropdown."
                    )
                    yield {"type": "token", "token": error_fallback}
                    full_response += error_fallback
            else:
                error_fallback = (
                    f"\n\n> [!WARNING]\n"
                    f"> **Inference Error**: Could not connect to `{model}` ({err_detail}).\n"
                    f"> If using Ollama, ensure `ollama serve` is running. You may select `qwen2.5:0.5b` from the dropdown."
                )
                yield {"type": "token", "token": error_fallback}
                full_response += error_fallback

        # Step 4: Extract Artifacts (if generated or if Ship 30 essay is created)
        cleaned_text, artifacts = self.extract_artifacts(full_response)

        # If it was a ship30 request, create an artifact for the essay as well
        if intent == "ship30" and not artifacts:
            artifacts.append(ArtifactPayload(
                title=f"Ship 30 Essay: {message[:40]}...",
                artifact_type="markdown",
                content=full_response
            ))

        yield {
            "type": "done",
            "full_text": full_response,
            "artifacts": [a.model_dump() for a in artifacts]
        }

    async def _stream_ollama(
        self,
        model: str,
        system: str,
        prompt: str,
        history: List[Dict[str, str]],
        max_tokens: int = 350
    ) -> AsyncGenerator[str, None]:
        """Streams response from local Ollama endpoint."""
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        messages = [{"role": "system", "content": system}]
        for msg in history[-2:]:  # Recent 2 turns of context
            content = msg.get("content", "")
            if msg.get("role") == "assistant" and len(content) > 250:
                content = content[:250] + "..."
            messages.append({"role": msg.get("role", "user"), "content": content})
        messages.append({"role": "user", "content": prompt})

        timeout = httpx.Timeout(180.0, connect=20.0)
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": "60m",
            "options": {
                "temperature": 0.0,
                "repeat_penalty": 1.05,
                "repeat_last_n": 128,
                "top_k": 40,
                "top_p": 1.0,
                "num_thread": 12,
                "num_ctx": 2048,
                "num_predict": max_tokens
            }
        }
        recent_tokens: List[str] = []
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                url,
                json=payload
            ) as response:
                if response.status_code != 200:
                    err_msg = await response.aread()
                    raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {err_msg.decode('utf-8', errors='ignore')}")
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                recent_tokens.append(token)
                                # True loop breaker: detect if the model begins looping identical blocks back-to-back
                                if len(recent_tokens) > 60:
                                    recent_text = "".join(recent_tokens[-150:])
                                    if len(recent_text) >= 150:
                                        tail = recent_text[-50:]
                                        prev1 = recent_text[-100:-50]
                                        prev2 = recent_text[-150:-100]
                                        if tail == prev1 == prev2:
                                            logger.warning("Detected repetitive generation loop in Ollama. Terminating stream.")
                                            break
                                yield token
                        except Exception:
                            continue

    async def _stream_claude(
        self,
        model: str,
        system: str,
        prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Streams response from Anthropic Claude API."""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not configured in .env or environment.")

        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        messages = []
        for msg in history[-4:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        async with client.messages.stream(
            model=settings.DEFAULT_ANTHROPIC_MODEL,
            max_tokens=3000,
            system=system,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def _stream_openai(
        self,
        model: str,
        system: str,
        prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Streams response from OpenAI API."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured in .env or environment.")

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [{"role": "system", "content": system}]
        for msg in history[-4:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            model=settings.DEFAULT_OPENAI_MODEL,
            messages=messages,
            stream=True
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token

    async def _stream_gemini(
        self,
        model: str,
        system: str,
        prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Streams response from Google Gemini API via SSE."""
        if not settings.GEMINI_API_KEY:
            yield "> [!WARNING]\n> `GEMINI_API_KEY` is not configured in `.env`.\n\n"
            return

        clean_model = model.replace("models/", "").replace("gemini:", "") or settings.DEFAULT_GEMINI_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:streamGenerateContent?key={settings.GEMINI_API_KEY}&alt=sse"

        contents = []
        for msg in history[-4:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }

        timeout = httpx.Timeout(60.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"Gemini error {response.status_code}: {err.decode('utf-8', errors='ignore')}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk_data = json.loads(line[6:])
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    text_piece = p.get("text", "")
                                    if text_piece:
                                        yield text_piece
                        except Exception:
                            continue

    async def _stream_groq(
        self,
        model: str,
        system: str,
        prompt: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Streams response from Groq OpenAI-compatible API."""
        if not settings.GROQ_API_KEY:
            yield "> [!WARNING]\n> `GROQ_API_KEY` is not configured in `.env`.\n\n"
            return

        clean_model = model.replace("groq:", "") or settings.DEFAULT_GROQ_MODEL
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": system}]
        for msg in history[-4:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": clean_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.3,
            "max_tokens": 2048
        }

        timeout = httpx.Timeout(60.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err = await response.aread()
                    raise RuntimeError(f"Groq error {response.status_code}: {err.decode('utf-8', errors='ignore')}")
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                        try:
                            chunk_data = json.loads(line[6:])
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
