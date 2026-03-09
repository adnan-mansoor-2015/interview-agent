# Architecture Overview

```
Frontend (React :3000)                  Backend (FastAPI :8000)
┌──────────────────────────┐           ┌──────────────────────────────────────┐
│  LoginPage               │           │  app.py (API routes)                 │
│  CategorySelector        │           │       ↓                              │
│  ProgressView            │   HTTP    │  orchestrator.py (state machine)     │
│  ChatInterface           │ ───────→  │       ↓                              │
│    ├─ SearchableDropdown │           │  ┌─────────────┬────────────────┐    │
│    ├─ Breadcrumb         │           │  │ question_    │ interview_     │    │
│    ├─ MessageBubble      │           │  │ curator.py   │ coach.py       │    │
│    ├─ InputArea          │           │  │ (router)     │                │    │
│    ├─ VoiceRecorder      │           │  ├─────────────┼────────────────┤    │
│    └─ ImageUploader      │           │  │ evaluator.py │ session_       │    │
│                          │           │  │ (text+vision)│ store.py       │    │
│  services/api.js         │           │  └──────┬──────┴────────────────┘    │
│  (fetch client)          │           │         ↓                            │
└──────────────────────────┘           │  question_sources/                   │
                                       │    ├─ behavioral.py                  │
                                       │    ├─ technical.py (uses LLM)        │
                                       │    ├─ coding.py                      │
                                       │    └─ system_design.py               │
                                       │         ↓                            │
                                       │  services/llm/                       │
                                       │    ├─ gemini.py (auto-fallback)      │
                                       │    └─ anthropic.py                   │
                                       └──────────────────────────────────────┘
                                                ↓
                                       Google Gemini API (primary)
                                       Anthropic Claude API (fallback)
```

## Key Design Patterns

### LLMProvider Protocol (`services/llm/protocol.py`)

All LLM backends implement `send_message()`, `send_message_with_image()`, and `extract_text()`. Switch providers by setting `LLM_PROVIDER` in `.env`. The factory in `services/llm/__init__.py` returns the configured client. `claude_client.py` is a backward-compatible shim.

### QuestionSource Protocol (`question_sources/protocol.py`)

Each category implements `get_question()`, `get_structure()`, `get_progress()`, and `get_detailed_progress()`. The `QuestionCurator` is a thin router that delegates to the right source. To add a database-backed source, implement the protocol and register it in `question_curator.py._sources`.

### Session Lifecycle

```
1. User logs in with email → picks a category
2. Question Curator selects a question from CSV (or generates via LLM)
3. User answers via text/voice/diagram → Coach asks short follow-ups
4. User clicks Evaluate → Evaluator scores with category-specific rubrics
5. Progress is persisted per-user → User clicks Next → repeat
```

### Phase State Machine (Orchestrator)

```
question_needed → answering → ready_for_eval → evaluating → question_needed
```

## Multi-Model Fallback

When a Gemini model returns 429 RESOURCE_EXHAUSTED, the client automatically retries with the next model:

```
gemini-2.5-flash → gemini-2.0-flash → gemini-1.5-flash → gemini-1.5-pro
```

Separate chains for text and vision calls. Logs every attempt.
