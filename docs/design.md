# UI/UX Design System & Experience Architecture
## Project: The Lenny Growth Assistant

---

## 1. UI/UX Principles

The user interface for The Lenny Growth Assistant is designed according to modern, high-craft engineering standards (inspired by [Impeccable](https://impeccable.style/) and Claude Artifacts):

1. **Zero Prompt Burden**: Users should not need prompt engineering skills to extract value. The interface surfaces contextual starter prompts (e.g. *"Elena Verna's B2B Growth Loops"*, *"How Superhuman Measures PMF"*, *"Draft Ship 30 Essay on Retention"*).
2. **Confidence Through Grounding**: Every answer clearly presents clickable citation badges (Guest Name, Episode Title). Hovering or clicking a citation displays the exact verbatim snippet used from the transcript.
3. **Seamless Artifact Workspace**: Content and interactive tools shouldn't be trapped in a narrow vertical chat thread. When an artifact is produced (Markdown guide, Ship 30 essay, or HTML/CSS prototype), the workspace dynamically slides into a split-pane view with live preview and code inspector.
4. **Transparent Intelligence**: The system explicitly conveys what model is running (Local Ollama vs Cloud Claude), displays real-time tool execution states (e.g. *"Searching 300+ Lenny transcripts for 'Product-Market Fit'..."*), and degrades gracefully if an engine is offline.

---

## 2. Information Architecture & Layout

The desktop interface uses a flexible, multi-column workspace:

```
┌─────────────────┬───────────────────────────────────┬────────────────────────────────────┐
│  SESSION NAV    │           CONVERSATION            │          ARTIFACT VIEWER           │
│                 │                                   │                                    │
│ [ + New Chat ]  │  [ Model Selector: Ollama v ]     │  [ Preview ]  [ Code ]     [ X ]   │
│                 │                                   │  ┌──────────────────────────────┐  │
│ Recent Sessions │  Assistant:                       │  │                              │  │
│ • Superhuman    │  According to Rahul Vohra in...   │  │  Interactive Product         │  │
│   PMF Engine    │  [ Citation: Rahul Vohra #42 ]    │  │  Scorecard                   │  │
│ • Retention vs  │                                   │  │                              │  │
│   Acquisition   │  User:                            │  │  (Live Sandboxed Preview)    │  │
│ • B2B PLG Loop  │  Turn this into an interactive    │  │                              │  │
│                 │  canvas widget!                   │  │                              │  │
│                 │                                   │  │                              │  │
│ Knowledge Base: │  Assistant:                       │  │                              │  │
│ 300+ Episodes   │  I've created the artifact for    │  │                              │  │
│ Index: Ready    │  you on the right.                │  └──────────────────────────────┘  │
│                 │                                   │  [ Copy Code ]  [ Download ]       │
│ [ Settings ]    │  [ Message input...           > ] │                                    │
└─────────────────┴───────────────────────────────────┴────────────────────────────────────┘
```

### 2.1 Component Breakdown
1. **Left Sidebar (Navigation & Engine Health)**:
   * **New Chat CTA**: Fast session reset.
   * **Session History**: Chronological list of conversations with title truncation and delete buttons.
   * **Knowledge Base Health Pill**: Real-time status of the transcript index (e.g., `303 Episodes Indexed`).
   * **Model Indicator**: Active inference engine indicator with quick-switch settings.
2. **Center Panel (Conversational Interface)**:
   * **Model Toggle Bar**: Direct selector for `Ollama: mistral`, `Ollama: qwen2.5`, `Claude 3.5 Sonnet`, `OpenAI GPT-4o`.
   * **Message Bubbles**: Clean typography with Markdown styling, syntax-highlighted code blocks, and source citation pills.
   * **Agent Thinking / Tool Status**: Animated status indicator when searching transcripts or crafting Ship 30 essays.
   * **Input Box**: Auto-expanding textarea with quick-action prompt chips.
3. **Right Panel (Artifact Viewer)**:
   * **Tab Switcher**: Toggle between `Preview` (live rendered view) and `Code` (raw syntax).
   * **Action Toolbar**: One-click `Copy Code`, `Download (.html / .md)`, and `Fullscreen` expansion.
   * **Sandboxed Frame**: Secure execution container for generated HTML/CSS with Tailwind support.

---

## 3. Key Interaction States

| State | UI Behavior & Visual Feedback |
|---|---|
| **Empty State** | Displays welcome banner, "The Lenny Growth Assistant", knowledge base stats, and 4 suggested prompt cards covering PMF, Growth Loops, Pricing, and Ship 30 essays. |
| **Retrieving / Thinking** | Glowing badge with pulse animation: *"Searching 303 transcripts for 'retention curves'..."* |
| **Streaming Output** | Smooth token-by-token text streaming via SSE; citations appear as resolved pill chips at the end of responses. |
| **Artifact Generation** | Triggers split-pane animation; right panel expands smoothly to 50% width; shows loader until HTML/MD is mounted. |
| **Out-of-Scope Query** | Neutral warning card explaining that the topic was not found in Lenny's transcripts, suggesting related podcast topics. |
| **Error / Model Fallback** | Non-blocking toast notification: *"Local Ollama model unavailable. Would you like to switch to cloud model or retry?"* |

---

## 4. Responsive & Accessibility Design

### 4.1 Responsive Breakpoints
* **Desktop ($> 1280px$)**: Full 3-column experience with persistent sidebar, chat thread, and open artifact panel.
* **Laptop ($1024px - 1279px$)**: Sidebar collapses into an overlay drawer; Artifact Viewer and Chat split 50/50.
* **Tablet / Mobile ($< 1024px$)**: Single-column layout. When an artifact is opened, it slides up as a full-screen bottom sheet with a header toggle to jump back to chat.

### 4.2 Accessibility (WCAG 2.1 AA)
* **Contrast Ratios**: Minimum 4.5:1 text-to-background contrast in both light and dark modes (Tailwind slate-900 / white palette).
* **Keyboard Navigation**:
  * `Ctrl + N` / `Cmd + N`: Start new chat.
  * `Escape`: Close artifact viewer.
  * `Tab` order logically cycles through input -> send -> citations -> artifact tabs.
* **Screen Reader Tags**: ARIA landmarks (`role="main"`, `role="complementary"`, `aria-live="polite"` for streaming messages).

---

## 5. Design Decisions & Trade-offs

1. **Split-Screen vs. Modal for Artifacts**:
   * *Decision*: Split-screen side-by-side.
   * *Rationale*: Allows users to view conversation instructions and generated output simultaneously without losing context, mirroring the proven ergonomics of Claude Artifacts.
2. **Iframe vs. Shadow DOM for HTML Preview**:
   * *Decision*: Sandboxed `<iframe>` without `allow-same-origin`.
   * *Rationale*: Shadow DOM isolates CSS but does not isolate Javascript execution or protect `localStorage`/cookies against malicious or hallucinated scripts. The iframe provides true sandboxed isolation.
