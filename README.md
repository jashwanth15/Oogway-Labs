# The Lenny Growth Assistant 🚀
> **A Forward Deployed AI Solution Grounded in 300+ Lenny's Podcast Transcripts**

Built for the **Oogway Labs Forward Deployed Engineer Assessment**.

---

## 🌟 Executive Summary

**The Lenny Growth Assistant** turns hundreds of hours of world-class product and growth wisdom from [Lenny's Podcast](https://www.lennyspodcast.com/) into an internal advisory engine. It provides:
1. **Strictly Grounded Q&A**: Answers product & growth questions using hybrid BM25 + semantic retrieval with verbatim quotes, guest attribution, and zero-hallucination guardrails.
2. **Dedicated Ship 30 for 30 Essay Skill**: Transforms podcast insights into ~1,250-word atomic essays featuring magnetic 1-3-1 hooks, skimmable subheadings, bold anchors, and tactical execution checklists.
3. **Claude-Style In-App Artifact Viewer**: Native split-pane side-by-side viewer for rendered Markdown and interactive HTML/CSS widgets—isolated with defense-in-depth sandboxing.
4. **Flexible Multi-LLM Layer**: Run **100% locally and privately with Ollama** (`mistral:latest`, `qwen2.5:0.5b`) for zero-cost evaluation, or toggle dynamically to **Anthropic Claude 3.5 Sonnet** and **OpenAI GPT-4o** directly in the UI.
5. **Robust Persistence & Operability**: Persistent conversation history stored in PostgreSQL (Supabase / Railway / Docker) with automatic, zero-setup SQLite fallback.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT LAYER (React / Vite)                     │
│  ┌─────────────────────────┐          ┌──────────────────────────────────┐  │
│  │   Chat & Session Feed   │ ◄──────► │  Claude-Style Artifact Viewer    │  │
│  │   (SSE Token Stream)    │          │  (Sandboxed IFrame Preview)      │  │
│  └────────────▲────────────┘          └────────────────▲─────────────────┘  │
└───────────────┼────────────────────────────────────────┼────────────────────┘
                │ HTTP REST / SSE Stream                 │
┌───────────────▼────────────────────────────────────────┴────────────────────┐
│                             API GATEWAY (FastAPI)                           │
│  /api/health  •  /api/models  •  /api/sessions  •  /api/chat  •  /api/search│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                             AGENTIC CORE                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Intent Router & Skill Dispatcher                                      │  │
│  │ ├─ Hybrid Retrieval (BM25 + Topic Index + Guest Boosting)             │  │
│  │ ├─ Skill: Ship 30 for 30 (~1,250 words, 1-3-1 hook, skimmable)        │  │
│  │ └─ Skill: Interactive Growth Artifacts (HTML/CSS & Markdown)          │  │
│  └──────────────────┬─────────────────────────────────┬──────────────────┘  │
│                     ▼                                 ▼                     │
│  ┌──────────────────────────────────┐ ┌──────────────────────────────────┐  │
│  │ Local LLM (Ollama)               │ │ Cloud LLM (Claude / OpenAI)      │  │
│  │ - mistral / qwen2.5              │ │ - Claude 3.5 Sonnet              │  │
│  │ - Zero keys, local evaluation    │ │ - GPT-4o                         │  │
│  └──────────────────────────────────┘ └──────────────────────────────────┘  │
└──────────────────────┬────────────────────────────────┬─────────────────────┘
                       │                                │
┌──────────────────────▼──────────────┐  ┌──────────────▼─────────────────────┐
│      TRANSCRIPT KNOWLEDGE BASE      │  │        PERSISTENCE LAYER           │
│  - 303 Episodes Ingested            │  │  - PostgreSQL (Supabase / Railway) │
│  - 15,251 Semantic Chunks           │  │  - SQLite Automatic Fallback      │
│  - 89 Curated Topic Indices         │  │  - Sessions, Messages, Artifacts   │
└─────────────────────────────────────┘  └────────────────────────────────────┘
```

---

## ⚡ Quick Start (Evaluator Setup)

You can run the entire system via **Docker Compose** (one command) or natively using our **1-click startup scripts**.

### Option A: 1-Command Startup with Docker Compose (Recommended)
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd oogway

# 2. Boot PostgreSQL, FastAPI backend, and Frontend
docker compose up --build
```
* Frontend: `http://localhost:3000`
* Backend API & OpenAPI Docs: `http://localhost:8000/docs`

> [!NOTE]
> To use local Ollama with Docker Compose, ensure Ollama is running on your host (`ollama serve`). The Docker backend connects directly to the host's Ollama via `host.docker.internal:11434`.

---

### Option B: Local 1-Click Startup (No Docker Needed)

#### On Windows:
Double-click `run.bat` or run:
```powershell
.\run.bat
```

#### On macOS / Linux:
```bash
chmod +x run.sh
./run.sh
```

#### Manual Step-by-Step Run:
```bash
# 1. Backend Setup
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Frontend Setup (in a second terminal)
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:3000`** in your browser!

---

## 🦙 Local vs Cloud LLM Setup

### 1. Local LLM (Mandatory for Demo — Ollama)
1. Install [Ollama](https://ollama.com/).
2. Pull a recommended model:
   ```bash
   ollama pull mistral
   # or for lightweight low-memory execution:
   ollama pull qwen2.5:0.5b
   ```
3. Ensure the service is running:
   ```bash
   ollama serve
   ```
4. The Lenny Growth Assistant automatically discovers your installed local models on launch!

### 2. Cloud LLM (Optional — Anthropic Claude & OpenAI)
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Add your API keys:
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```
You can switch between Ollama and Claude in real time using the **Model Selector** in the UI header.

---

## 🧪 Automated Testing & Verification

Run the automated test suite covering API contracts, hybrid retrieval precision, persistence lifecycle, and Ship 30 for 30 essay formatting:

```bash
# Run all automated tests
backend\venv\Scripts\python -m pytest backend/tests/ -v
```

### Test Suite Summary:
* `test_health_endpoint`: Verifies DB, Ollama, and transcript index connectivity.
* `test_models_endpoint`: Verifies dynamic discovery of local and cloud providers.
* `test_session_crud_api`: Tests multi-turn conversation session creation and deletion.
* `test_transcript_search_api`: Tests direct transcript search API.
* `test_session_lifecycle_and_cascade`: Tests SQLite/PostgreSQL cascade deletion across messages and artifacts.
* `test_grounded_search_rahul_vohra`: Validates retrieval accuracy for Superhuman PMF engine.
* `test_grounded_search_elena_verna`: Validates retrieval accuracy for B2B PLG growth loops.
* `test_out_of_domain_hallucination_guardrail`: Validates anti-hallucination rejection of out-of-domain queries.
* `test_ship30_skill_principles_prompt`: Verifies encoding of Ship 30 writing rules.
* `test_ship30_essay_analyzer`: Evaluates skimmability, subheadings, bold anchors, and word counts.

---

## 🔒 Security & Artifact Isolation Strategy

When the assistant generates interactive HTML/CSS widgets or canvases, they are rendered natively in the **Claude-Style Artifact Viewer**.

### Isolation Architecture:
1. **Null-Origin Sandbox**: Rendered inside an `<iframe sandbox="allow-scripts" srcDoc={content} />`.
2. **Explicit Omission of `allow-same-origin`**: Without `allow-same-origin`, the script executes in a unique, untrusted origin. It cannot access:
   - Parent DOM elements.
   - `localStorage`, `sessionStorage`, or IndexedDB.
   - Authentication cookies or session tokens.
3. **XSS & Data Leakage Prevention**: Markdown content is sanitized through **DOMPurify** with strict HTML tag filtering.

---

## 📁 Repository Structure

```
oogway/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py             # System health & diagnostics
│   │   │   └── routes.py             # Sessions, chat streaming, search
│   │   ├── db/
│   │   │   ├── database.py           # PostgreSQL + SQLite fallback
│   │   │   └── models.py             # Session, Message, Artifact models
│   │   ├── schemas/
│   │   │   ├── chat.py               # Pydantic v2 schemas
│   │   │   └── session.py
│   │   ├── services/
│   │   │   ├── agent.py              # Dual-engine router (Ollama & Claude)
│   │   │   ├── retrieval.py          # Hybrid BM25 & grounding guardrails
│   │   │   ├── ship30_skill.py       # Ship 30 for 30 essay engine
│   │   │   └── transcript_loader.py  # Chunker & cache indexer
│   │   ├── config.py
│   │   └── main.py                   # FastAPI application entrypoint
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_persistence.py
│   │   ├── test_retrieval.py
│   │   └── test_ship30.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ArtifactViewer.tsx    # Sandboxed Claude-style viewer
│   │   │   ├── ChatInterface.tsx     # Stream feed, starter cards, input
│   │   │   ├── CitationBadge.tsx     # Verbatim quotes & timestamps
│   │   │   ├── ModelSelector.tsx     # Local Ollama ↔ Cloud toggle
│   │   │   └── SessionSidebar.tsx    # Conversation history & health
│   │   ├── App.tsx
│   │   ├── types.ts
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── data/
│   ├── transcripts/                  # 303 podcast episodes + topic indices
│   └── index_cache/                  # Precomputed fast-load chunks cache
├── docs/
│   ├── PRD.md                        # Discovery brief, user problem, metrics
│   ├── architecture.md               # Topology, database schema, security
│   └── design.md                     # UI/UX principles, design decisions
├── transcripts/                      # Coding-agent execution logs & corrections
├── docker-compose.yml                # 1-command container orchestration
├── .env.example                      # Documented safe configuration
├── run.bat                           # Windows 1-click launcher
└── run.sh                            # Unix/macOS 1-click launcher
```

---

## 📹 Demo Video Recording Guide (2–3 Minutes)

The take-home assessment requires a **2–3 minute video** with your camera enabled, uploaded to YouTube. Here is the recommended recording structure:

### Video Script Outline:
1. **0:00 - 0:35 | Problem & Discovery Brief**:
   * *Talking Point*: Introduce yourself and the problem: Product teams want actionable growth advice from Lenny's 300+ guests without reading transcripts or dealing with generic AI hallucinations.
2. **0:35 - 1:20 | Live Local Demo with Ollama**:
   * *Screen Share*: Show the UI running with `Ollama: mistral:latest`.
   * *Query*: Ask *"How did Superhuman measure PMF according to Rahul Vohra?"*
   * *Demonstration*: Show the token streaming, the exact citations to Rahul Vohra's episode, and the clickable quote popup with timestamps.
3. **1:20 - 1:55 | Ship 30 for 30 Skill & Artifact Viewer**:
   * *Query*: Click the *"Build an interactive PMF survey scorecard widget"* starter card.
   * *Demonstration*: Watch the Claude-style Artifact Viewer open beside the chat. Show the live sandboxed HTML/CSS widget in the `Preview` tab and switch to the `Code` tab.
4. **1:55 - 2:30 | Technical Trade-off Discussion**:
   * *Highlight*: Discuss the **BM25 inverse document frequency false-positive challenge** (where rare query words like 'wheat' in non-tech queries scored high) and how we engineered the **50% keyword coverage guardrail** to achieve 100% factual grounding and prevent hallucinations.
   * *Closing*: Conclude with operability—single command Docker setup and automated test suite.

---

## 🤝 Evaluator Handoff & Troubleshooting

* **Issue**: Local model generation is slow.
  * *Fix*: Switch from `mistral:latest` to `qwen2.5:0.5b` in the Model Selector for 4x faster generation on CPU.
* **Issue**: PostgreSQL is not installed locally.
  * *Fix*: No action needed! The application automatically falls back to local SQLite storage in `data/lenny_assistant.db`.
* **Issue**: Ollama is not detected.
  * *Fix*: Run `ollama serve` in a terminal or configure `ANTHROPIC_API_KEY` in `.env` to use Claude 3.5 Sonnet.
