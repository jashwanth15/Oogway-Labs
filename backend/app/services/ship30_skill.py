import re
from typing import Dict, Any, List
from backend.app.schemas.chat import Citation

SHIP_30_WRITING_PRINCIPLES = """
You are a master digital writer trained in the Ship 30 for 30 methodology created by Nicolas Cole and Dickie Bush.
Your objective is to craft an authoritative, high-converting, deeply educational digital essay based STRICTLY on insights from Lenny's Podcast transcripts.

### Ship 30 for 30 Core Architecture & Rules:
1. TARGET LENGTH:
   - Must be approximately 1,250 words (aim for 1,100 to 1,350 words). Do not cut corners. Elaborate each section with deep tactical nuance from the transcripts.

2. THE HOOK (The 1-3-1 Opening Rhythm):
   - Line 1: A single, bold, pattern-interrupt sentence.
   - Lines 2-4: Three short sentences defining the stakes, common mistake, or counter-intuitive reality.
   - Line 5: A single punchy transition line launching the thesis.

3. THE RULE OF ONE:
   - One reader. One specific problem. One transformation.
   - Ground every single point in the provided transcript evidence (mentioning the practitioner, e.g. Elena Verna, Rahul Vohra, Brian Chesky, etc.).

4. MAXIMUM SKIMMABILITY & PACING:
   - Use compelling, outcome-oriented H2 subheaders that tell the entire story on their own.
   - Use the '1-3-1' rhythm throughout paragraphs: keep paragraphs to 1–3 sentences maximum. Never write walls of text.
   - Use bold lead-ins on bullet points (e.g. "**The 40% threshold:** ...").
   - Use numbered frameworks and bulleted checklists.

5. SECTIONS REQUIRED:
   - **Compelling Headline**: Clear, bold, curiosity + benefit.
   - **The 1-3-1 Hook**: Pacing that hooks the busy product executive.
   - **The Core Conflict / The Old Playbook**: Why standard advice fails.
   - **The Grounded Framework (3 to 5 Pillars)**: Detailed breakdown citing the guest's verbatim lessons and metrics.
   - **The 3-Step Execution Checklist**: What the PM should do starting Monday morning.
   - **The Micro-Summary / Parting Punchline**: A memorable closing takeaway.

6. CITATION INTEGRITY:
   - Every framework must attribute its source to the guest from Lenny's Podcast.
   - Do NOT invent facts or hallucinate guests.
"""


class Ship30Skill:
    """Dedicated skill encapsulating the Ship 30 for 30 digital writing engine."""

    @staticmethod
    def get_system_prompt() -> str:
        return SHIP_30_WRITING_PRINCIPLES

    @staticmethod
    def build_prompt(topic: str, context: str, guest_context: str = "") -> str:
        prompt = f"""
Write a complete, high-impact Ship 30 for 30 style essay on the following topic:

Topic / Goal: {topic}
Guest Context: {guest_context if guest_context else "Synthesize from the provided podcast evidence"}

### Knowledge Base Grounding Excerpts:
{context}

### Writing Instructions:
- Follow the 1-3-1 cadence and skimmable formatting rules.
- Aim for approximately 1,250 words. Be comprehensive, detailed, and tactical.
- Cite the podcast guest(s) by name and reference their specific frameworks or case studies.
- End with a tactical Monday-morning execution checklist.
"""
        return prompt.strip()

    @staticmethod
    def analyze_essay(text: str) -> Dict[str, Any]:
        """Analyzes an essay against Ship 30 for 30 quality criteria."""
        words = len(re.findall(r"\b\w+\b", text))
        headings = len(re.findall(r"^##\s+", text, re.MULTILINE))
        bullet_points = len(re.findall(r"^\s*[\-\*]\s+", text, re.MULTILINE))
        bold_elements = len(re.findall(r"\*\*[^*]+\*\*", text))

        return {
            "word_count": words,
            "heading_count": headings,
            "bullet_point_count": bullet_points,
            "bold_emphasis_count": bold_elements,
            "target_word_count": 1250,
            "is_near_target_length": 900 <= words <= 1600,
            "is_skimmable": headings >= 3 and bullet_points >= 4 and bold_elements >= 3
        }
