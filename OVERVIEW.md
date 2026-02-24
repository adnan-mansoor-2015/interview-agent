# Architecture Overview

```
Frontend (React :3000)            Backend (FastAPI :8000)
┌──────────────────────┐         ┌──────────────────────────────────────┐
│  CategorySelector    │         │  app.py (API routes)                 │
│  ChatInterface       │  HTTP   │       ↓                              │
│    ├─ MessageBubble  │ ──────→ │  orchestrator.py (state machine)     │
│    ├─ InputArea      │         │       ↓                              │
│    ├─ VoiceRecorder  │         │  ┌─────────────┬────────────────┐    │
│    └─ ImageUploader  │         │  │ question_    │ interview_     │    │
│                      │         │  │ curator.py   │ coach.py       │    │
│  services/api.js     │         │  ├─────────────┼────────────────┤    │
│  (fetch client)      │         │  │ evaluator.py │ session_       │    │
│                      │         │  │ (text+vision)│ store.py       │    │
└──────────────────────┘         │  └─────────────┴────────────────┘    │
                                 │       ↓                              │
                                 │  claude_client.py                    │
                                 │  (Gemini/Claude with model fallback) │
                                 └──────────────────────────────────────┘
                                          ↓
                                 Google Gemini API (primary)
                                 Anthropic Claude API (fallback provider)
```

## Session Lifecycle

```
1. User picks a category → Question Curator selects a question from CSV
2. User answers via text/voice/diagram → Coach asks short follow-ups
3. User clicks Evaluate → Evaluator scores with category-specific rubrics
4. User clicks Next → repeat
```

### Phase State Machine (Orchestrator)

```
question_needed → answering → ready_for_eval → evaluating → question_needed
```

---

## Backend — File by File

### `config.py` — Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `LLM_PROVIDER` | `"gemini"` | Primary provider (`"gemini"` or `"anthropic"`) |
| `GEMINI_TEXT_MODEL_CHAIN` | `[2.5-flash, 2.0-flash, 1.5-flash, 1.5-pro]` | Models tried in order on rate limits |
| `GEMINI_VISION_MODEL_CHAIN` | Same | Vision model fallback chain |
| `MAX_TOKENS` | `16384` | High for thinking models |
| `REDIS_URL` | `redis://localhost:6379` | Optional session persistence |

### `app.py` — FastAPI Routes

6 endpoints. Creates sessions, routes messages through the orchestrator, handles diagram uploads. Configures CORS for `localhost:3000`.

### `services/claude_client.py` — LLM Abstraction

Two classes with the same interface: `send_message()`, `send_message_with_image()`, `extract_text()`.

**GeminiClient:** On 429 RESOURCE_EXHAUSTED, automatically retries with the next model in the fallback chain. Handles thinking models (gemini-2.5-flash) where `.text` can be `None`.

**AnthropicClient:** Fallback provider wrapping the Anthropic SDK.

All agents import `claude_client` — they don't know which provider is active.

### `services/session_store.py` — Session Management

Stores session state (phase, conversation thread, evaluations, asked questions). Tries Redis, falls back to in-memory dict. Sessions expire after 24h.

### `agents/orchestrator.py` — Central Router

Routes messages based on session phase:

| Phase | Action |
|-------|--------|
| `question_needed` | → Question Curator |
| `answering` | → Interview Coach |
| `answering` + "evaluate" | → Evaluator |
| `ready_for_eval` | → Evaluator |

Formats questions and evaluations for display. Manages state transitions.

### `agents/question_curator.py` — Question Sourcing

| Category | Source | LLM? |
|----------|--------|------|
| Behavioral | `behavioral_questions.csv` (106 Qs) | No |
| Technical | `technical_topics.csv` (131 topics) → LLM generates question | Yes |
| Coding | `leetcode_questions.csv` (173 problems) | No |
| System Design | `system_design_questions.csv` (36 Qs) | No |

Deduplicates via MD5 hash of question text.

### `agents/interview_coach.py` — Follow-Up Coach

Sends the conversation to the LLM with a category-specific prompt. The LLM either asks a short follow-up (1-2 sentences, like a real interviewer) or responds `"COMPLETE"` when the answer is thorough enough.

### `agents/evaluator.py` — Answer Scorer

**Text evaluation:** Scores 0-10 with category-specific rubrics:
- Behavioral: STAR Coverage, Specificity, Impact, Authenticity
- Technical: Accuracy, Depth, Clarity, Practical Application
- System Design: Components, Scalability, Reliability, Data Consistency, Communication

**Vision evaluation:** Analyzes uploaded system design diagrams — identifies components, traces data flow, scores scalability/reliability.

### `prompts/` — System Prompts

| File | Used By |
|------|---------|
| `curator_prompts.py` | Question Curator (technical questions only) |
| `coach_prompts.py` | Interview Coach (all categories) |
| `evaluator_prompts.py` | Evaluator (text + diagram rubrics) |

Each prompt defines the agent's role, assessment criteria, output format, and tone.

### `data/` — CSV Question Banks

| File | Records | Key Columns |
|------|---------|-------------|
| `behavioral_questions.csv` | 106 | Question, Leadership_Principle, Company, Priority |
| `technical_topics.csv` | 131 | Category, Topic, Sub_Topic, Difficulty |
| `leetcode_questions.csv` | 173 | Title, Difficulty, Companies, URL, Optimal_Complexity |
| `system_design_questions.csv` | 36 | Question, Company, Scale_Requirements, Key_Components |

### `test_backend.py` — Structure Tests

Verifies all components load without API keys: config, session CRUD, prompt generation, route registration.

---

## Frontend — File by File

### `App.js` — Root

Two views: home (CategorySelector) and chat (ChatInterface). Tracks `currentView`, `sessionId`, `category`.

### `services/api.js` — API Client

Fetch wrapper for `http://localhost:8000/api`. Functions: `startSession()`, `sendMessage()`, `uploadImage()`, `getSession()`.

### `components/CategorySelector.js` — Home Screen

4 category cards (Behavioral, Technical, Coding, System Design). Optional focus area selection for behavioral (Amazon LP, Google) and technical (Cloud, OOP, DS&A, Prompt Engineering).

### `components/Chat/ChatInterface.js` — Chat View

Auto-starts session on mount. Displays messages, handles text/voice/image input. Shows "Evaluate" and "Next Question" buttons based on phase.

### `components/Chat/MessageBubble.js` — Messages

Role-based styling (user right/blue, assistant left/dark). Basic markdown rendering. Loading animation.

### `components/Chat/InputArea.js` — Text Input

Textarea with Enter-to-send, Shift+Enter for newlines.

### `components/Chat/VoiceRecorder.js` — Voice

Browser `SpeechRecognition` API. Records continuously, accumulates transcript, passes to parent.

### `components/Chat/ImageUploader.js` — Diagrams

File picker → preview → base64 encode → upload to backend. For system design category.

---

## Multi-Model Fallback

When a Gemini model returns 429 RESOURCE_EXHAUSTED, the client automatically tries the next model:

```
gemini-2.5-flash → gemini-2.0-flash → gemini-1.5-flash → gemini-1.5-pro
```

- Only retries on rate limits (not other errors)
- Logs every attempt at INFO level, failures at WARNING
- If all models exhausted, error propagates to agent-level handling
- Separate chains for text and vision calls
