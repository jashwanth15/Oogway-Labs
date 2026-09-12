# Product Requirements Document (PRD)
## Project: The Lenny Growth Assistant

---

## 1. Forward Deployment Discovery Brief

### 1.1 User and Problem
* **Primary User**: Product Managers (PMs), Heads of Growth, Startup Founders, and Growth Engineers.
* **The Problem / JTBD (Job-to-be-Done)**: 
  Lenny’s Podcast features 300+ in-depth interviews with the world’s elite product operators (Brian Chesky, Shreyas Doshi, Elena Verna, Rahul Vohra, Gustaf Alströmer, etc.). However:
  1. *Discovery friction*: Valuable frameworks, metrics, benchmarks, and tactical insights are buried inside hundreds of hours of conversational audio and unstructured transcripts.
  2. *Hallucination risk in generic AI*: Off-the-shelf LLMs hallucinate product advice or blend generic internet platitudes with real expert frameworks.
  3. *Actionability gap*: PMs do not just want Q&A; they need immediate, high-leverage artifacts (PRDs, growth loop diagrams, onboarding teardowns, executive memos) and published thought-leadership content (such as Ship 30 for 30 essays).
* **Pain Removed**: "The Lenny Growth Assistant" converts an unmanageable 300+ transcript archive into a real-time advisory engine that guarantees source attribution, generates structured growth artifacts natively previewed side-by-side, and transforms validated takeaways into 1,250-word Ship 30 for 30 essays.

### 1.2 Measurable Success Metrics
1. **Factual Grounding Rate (Target: 100%)**: Every empirical recommendation or guest quote must provide a direct citation (Episode Title, Guest, Timestamp/Context).
2. **Hallucination Rejection Rate (Target: 100%)**: If a question falls outside the corpus (e.g., questions on non-podcast topics or unmentioned companies), the system explicitly refuses to guess and signals lack of evidence.
3. **Artifact Velocity**: Production of a rendered, interactive artifact (e.g., Growth Model HTML canvas or PRD markdown) in under 5 seconds from completion of retrieval.
4. **Evaluator Time-to-Run (Target: < 3 minutes)**: Any engineer or client evaluator should run a single command (`docker-compose up` or `run.bat`) and immediately interact with a fully local Ollama-powered instance without entering paid API keys.

### 1.3 Key Assumptions
1. **Transcript Availability**: Transcripts are sourced from the open-source repository `ChatPRD/lennys-podcast-transcripts`, containing indexed topic guides and verbatim episode transcripts.
2. **Local Execution Feasibility**: Evaluators will run the mandatory demo locally using Ollama on consumer hardware. Hence, retrieval and embedding models must operate with low memory footprint and zero external network dependencies for offline operation.
3. **Untrusted Artifact Sandbox**: Generated HTML/CSS code from an LLM cannot be trusted unconditionally. It must be sandboxed to prevent cookie theft, XSS, or top-level navigation.

### 1.4 Scope Choices (What’s In vs. What’s Out)
* **In Scope**:
  * Hybrid retrieval engine (BM25 keyword search + dense semantic embedding matching) over Lenny's transcript library.
  * Session isolation and persistent chat history stored in PostgreSQL (with automatic SQLite fallback for zero-configuration testing).
  * Dual-engine LLM abstraction: Local LLM (Ollama: Mistral, Qwen, Llama) and Cloud LLM (Anthropic Claude / OpenAI) with dynamic UI toggling.
  * Dedicated **Ship 30 for 30 Content Skill**: Built specifically following Nicolas Cole and Dickie Bush’s framework (Hook, 1-3-1 rhythm, skimmability, bold anchors, ~1,250 words, grounded claims).
  * Native **Claude-style Artifact Viewer**: Split-panel preview beside the chat supporting rendered Markdown and sandboxed HTML/CSS snippets with code inspector and copy features.
  * Complete developer tooling: Automated test suite, health monitoring, Docker Compose configuration, structured logging.
* **Intentionally Excluded**:
  * *Live audio transcription*: We leverage the curated, high-accuracy transcripts from `ChatPRD/lennys-podcast-transcripts` rather than running Whisper on raw audio.
  * *User authentication / billing*: Focus is strictly on forward-deployment evaluation of agentic reasoning, RAG precision, and artifact UX.

### 1.5 Key Risks and Mitigation Strategies
| Risk | Severity | Mitigation Strategy |
|---|---|---|
| **Hallucination** | High | Strict RAG prompt constraints; minimum similarity threshold; explicit fallback prompt instructing the model to declare lack of evidence if context does not match. |
| **Local Model Latency** | Medium | Stream responses via Server-Sent Events (SSE) so users see tokens immediately; default to lightweight high-efficiency local models (`qwen2.5:0.5b` or `mistral`). |
| **Data Leakage & Untrusted HTML** | High | Artifacts rendered in an `<iframe>` configured with `sandbox="allow-scripts"` and omitting `allow-same-origin`, blocking access to parent cookies and storage. |
| **Database Dependency Failures** | Medium | Graceful fallback from PostgreSQL to SQLite if PostgreSQL is unreachable, accompanied by visible system health diagnostics. |

---

## 2. User Flows & System Capabilities

### 2.1 User Flows
1. **Flow 1: Grounded Advisory & Source Tracing**
   * User asks: *"How did Superhuman find product-market fit according to Rahul Vohra?"*
   * Assistant retrieves relevant segments from the Rahul Vohra episode.
   * Assistant streams the response explaining the PMF engine (the 40% 'very disappointed' metric, segmenting high-expectation customers).
   * Assistant renders clickable citation badges linked directly to the transcript.
2. **Flow 2: Ship 30 for 30 Essay Generation**
   * User requests: *"Write a Ship 30 for 30 essay on retention vs acquisition loops based on Elena Verna's episodes."*
   * The agent activates the dedicated `generate_ship30_essay` skill.
   * Generates a ~1,250-word structured piece with a magnetic hook, 1-3-1 pacing, bold highlights, actionable takeaways, and transcript citations.
   * Opens the essay automatically in the Artifact Viewer.
3. **Flow 3: Interactive Growth Artifact Generation**
   * User asks: *"Generate a visual PMF survey scorecard in HTML/CSS."*
   * Assistant crafts an interactive web widget.
   * The Artifact Viewer slides open alongside the chat, rendering the live interactive widget in a sandboxed viewport while providing a 'Code' toggle for the raw source.
4. **Flow 4: Model Toggle (Cloud ↔ Local Ollama)**
   * User switches model dropdown from "Local: Mistral (Ollama)" to "Cloud: Claude 3.5 Sonnet".
   * Session retains complete conversation context seamlessly.

---

## 3. Acceptance Criteria

* **AC-1 (Grounding)**: Answers reference guest names and episode contexts. Non-podcast questions return: *"I could not find information on this topic in Lenny's Podcast transcripts."*
* **AC-2 (Model Switch)**: Changing model provider in the UI switches subsequent inference without restarting the server or breaking conversation memory.
* **AC-3 (Ship 30 for 30 Skill)**: Output matches target word count (~1,250 words), contains scannable subheadings, bullet lists, bolded key phrases, and actionable takeaways.
* **AC-4 (Artifact Isolation)**: HTML/CSS artifacts render in an isolated sandboxed iframe without script injection to the host window.
* **AC-5 (Persistence)**: Chat sessions, messages, and artifacts persist across browser reloads in PostgreSQL / SQLite.
* **AC-6 (One-Command Startup)**: Running `docker-compose up` boots the entire application (API, DB, UI) with zero manual database migration steps.
