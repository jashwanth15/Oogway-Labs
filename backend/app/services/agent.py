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
        """Extracts ```artifact:type:Title blocks and returns cleaned text + artifacts."""
        artifacts: List[ArtifactPayload] = []
        pattern = re.compile(r"```artifact:(html|markdown|code):([^\n]+)\n(.*?)```", re.DOTALL)

        def replacer(match):
            art_type = match.group(1).strip()
            art_title = match.group(2).strip()
            content = match.group(3).strip()
            artifacts.append(ArtifactPayload(
                title=art_title,
                artifact_type=art_type,
                content=content
            ))
            return f"\n*[Generated Artifact: **{art_title}** ({art_type.upper()}) - View in the Artifact Panel beside chat]*\n"

        cleaned_text = pattern.sub(replacer, text)

        # Handle unclosed artifact tag (e.g. if tokens cut off before closing ```)
        if not artifacts and "```artifact:" in text:
            unclosed_match = re.search(r"```artifact:(html|markdown|code):([^\n]+)\n(.*)$", text, re.DOTALL)
            if unclosed_match:
                art_type = unclosed_match.group(1).strip()
                art_title = unclosed_match.group(2).strip()
                raw_code = unclosed_match.group(3).strip()
                if art_type == "html" and not raw_code.endswith("</html>"):
                    if "</body>" not in raw_code:
                        raw_code += "\n</body></html>"
                    elif "</html>" not in raw_code:
                        raw_code += "\n</html>"
                artifacts.append(ArtifactPayload(
                    title=art_title,
                    artifact_type=art_type,
                    content=raw_code
                ))
                cleaned_text = text[:unclosed_match.start()] + f"\n*[Generated Artifact: **{art_title}** ({art_type.upper()}) - View in the Artifact Panel beside chat]*\n"

        # Also handle standard ```html ... ``` code blocks
        if not artifacts and "```html" in text:
            html_match = re.search(r"```html\s*\n(.*?)```", text, re.DOTALL)
            if html_match:
                artifacts.append(ArtifactPayload(
                    title="Interactive HTML Artifact",
                    artifact_type="html",
                    content=html_match.group(1).strip()
                ))

        # Fallback check if full HTML was emitted without artifact block
        if not artifacts and "<!DOCTYPE html>" in text or ("<html" in text and "</html>" in text):
            html_match = re.search(r"(<!DOCTYPE html.*?>.*?</html>|<html.*?>.*?</html>)", text, re.DOTALL | re.IGNORECASE)
            if html_match:
                artifacts.append(ArtifactPayload(
                    title="Interactive Growth Widget",
                    artifact_type="html",
                    content=html_match.group(1).strip()
                ))

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
            yield {"type": "status", "message": f"Generating interactive {safe_type.upper()} artifact..."}
            system_instruction = SYSTEM_PROMPT
            user_instruction = (
                f"User Request: {message}\n\n"
                f"### Knowledge Base Context:\n{context}\n\n"
                f"CRITICAL REQUIREMENTS:\n"
                f"1. Ground your response in the podcast insights above (e.g. Rahul Vohra's 40% rule for PMF).\n"
                f"2. Provide a complete, production-ready {safe_type.upper()} artifact enclosed in:\n"
                f"```artifact:{safe_type}:Title of Artifact\n"
                f"(your complete code or markdown here)\n"
                f"```\n"
                f"3. For HTML artifacts, it MUST be fully interactive with client-side JavaScript. "
                f"Include an interactive script so clicking 'Submit' or 'Calculate' runs client-side calculations "
                f"(e.g. onsubmit=\"event.preventDefault(); calculate();\"), displays results, progress bars, and recommendations. "
                f"Never submit to external URLs or use action='...'.\n"
                f"4. Style with clean, modern Tailwind CSS."
            )
        else:
            system_instruction = SYSTEM_PROMPT
            user_instruction = (
                f"User Question: {message}\n\n"
                f"### Knowledge Base Context from Lenny's Transcripts:\n{context}\n\n"
                f"Answer the question clearly and concisely, grounding each point with citations to the guest and episode."
            )

        yield {"type": "status", "message": f"Generating response with {model}..."}

        # Step 3: Route to LLM Engine (Local Ollama vs Cloud)
        full_response = ""
        max_predict = 550 if intent == "artifact" else (700 if intent == "ship30" else 280)
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
                "temperature": 0.3,
                "repeat_penalty": 1.18,
                "repeat_last_n": 64,
                "top_k": 40,
                "top_p": 0.9,
                "num_thread": 8,
                "num_ctx": 1536,
                "num_predict": max_tokens
            }
        }
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
