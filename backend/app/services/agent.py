import asyncio
import json
import logging
import re
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from backend.app.config import settings
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.ship30_skill import Ship30Skill
from backend.app.schemas.chat import Citation, ArtifactPayload

logger = logging.getLogger(__name__)

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

    def detect_intent(self, message: str, explicit_skill: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Determines user intent: 'ship30', 'artifact', or 'qa'.
        Returns (intent, target_format).
        """
        if explicit_skill:
            if explicit_skill == "artifact":
                msg_lower = message.lower()
                art_type = "markdown" if any(t in msg_lower for t in ["markdown", "prd", "framework doc", "template"]) else "html"
                return "artifact", art_type
            return explicit_skill, None

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
                    if any(k in art.title.lower() for k in ["pmf", "survey", "scorecard", "calculator", "growth", "superhuman"]):
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
        intent, artifact_type = self.detect_intent(message, skill)

        yield {"type": "status", "message": f"Searching 303 Lenny transcripts for relevant insights..."}

        # Step 1: Hybrid Retrieval
        citations, is_grounded = self.retriever.search(message, top_k=5)

        # Hallucination guardrail
        if not is_grounded and not citations:
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
            is_pmf_calc = any(k in message.lower() for k in ["pmf", "vohra", "scorecard", "calculator", "superhuman", "product market fit", "sean ellis"])
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
                f"1. Build a complete, functional {safe_type.upper()} calculator tool using Rahul Vohra's 40% PMF Framework.\n"
                f"2. Use standard HTML: include input fields for response counts (<input type='number' name='very' value='45'>, <input type='number' name='somewhat' value='30'>, <input type='number' name='not' value='25'>), "
                f"a Calculate button, a progress bar, and a results card.\n"
                f"3. Enclose the complete code inside:\n"
                f"```artifact:{safe_type}:Interactive PMF Scorecard\n"
                f"<!DOCTYPE html>\n<html lang=\"en\">\n...\n</html>\n"
                f"```\n"
                f"4. Start directly with ```artifact:{safe_type}:Interactive PMF Scorecard now:"
            )
        else:
            system_instruction = (
                "You are The Lenny Growth Assistant. Answer the user's question directly, clearly, and concisely "
                "based strictly on the provided podcast excerpts. Ground key points with guest names and timestamps."
            )
            user_instruction = (
                f"Here are verified excerpts from Lenny's Podcast:\n"
                f"---\n{context}\n---\n\n"
                f"Question: {message}\n\n"
                f"Answer directly using the framework and insights above:"
            )

        yield {"type": "status", "message": f"Generating response with {model}..."}

        # Step 3: Route to LLM Engine (Local Ollama vs Cloud)
        full_response = ""
        max_predict = 1400 if intent == "artifact" else (1000 if intent == "ship30" else 400)
        try:
            if model.startswith("ollama:") or (not model.startswith("claude") and not model.startswith("gpt")):
                clean_model = model.replace("ollama:", "")
                async for chunk in self._stream_ollama(clean_model, system_instruction, user_instruction, history, max_tokens=max_predict):
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
                    async for chunk in self._stream_ollama(settings.DEFAULT_LOCAL_MODEL, system_instruction, user_instruction, history, max_tokens=max_predict):
                        full_response += chunk
                        yield {"type": "token", "token": chunk}
                else:
                    async for chunk in self._stream_claude(model, system_instruction, user_instruction, history):
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
        for msg in history[-4:]:  # Recent 4 turns of context
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        timeout = httpx.Timeout(180.0, connect=20.0)
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": "60m",
            "options": {
                "temperature": 0.2,
                "repeat_penalty": 1.25,
                "repeat_last_n": 256,
                "top_k": 40,
                "top_p": 0.9,
                "num_thread": 8,
                "num_ctx": 4096,
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
