# AI-Powered Interview Prep Agent

A full-stack conversational interview practice system with **4 specialized AI agents** that coach, question, and evaluate your answers across behavioral, technical, coding, and system design categories. Powered by Google Gemini (with automatic multi-model fallback) and a React chat UI with voice and diagram upload support.

---

## Architecture Overview

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
                                 Anthropic Claude API (fallback)
```

---

## How It Works

### Session Lifecycle

```
1. User picks a category (behavioral/technical/coding/system-design)
2. Question Curator selects a question from CSV banks (or generates via LLM)
3. User answers via text, voice, or diagram upload
4. Interview Coach asks follow-up questions until answer is complete
5. Evaluator scores the answer with category-specific rubrics (0-10)
6. Repeat with next question
```

### Phase State Machine (managed by Orchestrator)

```
question_needed → answering → ready_for_eval → evaluating → question_needed
                     ↑                                            │
                     └────────── (next question) ─────────────────┘
```

---

## File-by-File Breakdown

### Root Files

| File | Purpose |
|------|---------|
| `.gitignore` | Excludes `node_modules/`, `venv/`, `.env`, `__pycache__/`, `build/`, `.DS_Store` |
| `README.md` | This file |
| `QUICKSTART.md` | Setup guide with cURL examples for manual API testing |
| `FINAL_GUIDE.md` | End-to-end usage guide with example flows |
| `BACKEND_TEST_RESULTS.md` | Test coverage report (all structure tests pass without API keys) |

---

### Backend

#### `backend/config.py` — Configuration Hub

Central configuration loaded from environment variables.

| Setting | Value | Purpose |
|---------|-------|---------|
| `LLM_PROVIDER` | `"gemini"` | Primary LLM provider (`"gemini"` or `"anthropic"`) |
| `GEMINI_TEXT_MODEL` | `"gemini-2.5-flash"` | Default text model |
| `GEMINI_VISION_MODEL` | `"gemini-2.5-flash"` | Default vision model |
| `GEMINI_TEXT_MODEL_CHAIN` | `[2.5-flash, 2.0-flash, 1.5-flash, 1.5-pro]` | Fallback chain on rate limits |
| `GEMINI_VISION_MODEL_CHAIN` | Same as text chain | Vision fallback chain |
| `MAX_TOKENS` | `16384` | Max output tokens (high for thinking models) |
| `REDIS_URL` | `redis://localhost:6379` | Session store (optional) |
| `SESSION_TTL` | `86400` (24h) | Session expiry |

---

#### `backend/app.py` — FastAPI Routes

The API entry point. Defines 6 endpoints:

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/api/chat/start` | POST | Creates a session, calls Orchestrator to get the first question. Input: `{category, focus_areas}`. Returns: `{session_id, response}` |
| `/api/chat/message` | POST | Sends user's answer to the Orchestrator. Input: `{session_id, message}`. Returns: follow-up question, "COMPLETE" signal, or scored evaluation |
| `/api/chat/upload` | POST | Uploads a diagram image for vision analysis. Input: `{session_id, image_base64, description}`. Returns: component analysis, scores, suggestions |
| `/api/session/{id}` | GET | Returns full session data (conversation thread, evaluations, phase) |
| `/api/session/{id}` | DELETE | Deletes a session |
| `/health` | GET | Returns `{"status": "healthy"}` |

Also configures CORS for `localhost:3000` (React dev server).

---

#### `backend/services/claude_client.py` — LLM Abstraction Layer

Provides a unified interface for all agents to call LLMs, regardless of provider.

**`GeminiClient` class** (primary):
- **`send_message(system_prompt, messages, model?, max_tokens?)`** — Text LLM call. Iterates through `GEMINI_TEXT_MODEL_CHAIN` on 429 errors. Builds conversation from message list, applies system prompt.
- **`send_message_with_image(system_prompt, text, image_base64, model?)`** — Vision LLM call. Same fallback logic using `GEMINI_VISION_MODEL_CHAIN`. Used for system design diagram analysis.
- **`extract_text(response)`** — Extracts text from Gemini response. Handles thinking models (gemini-2.5-flash) where `.text` may be `None` by falling back to `candidates[0].content.parts`.
- **`_is_rate_limit_error(exc)`** — Detects 429 / `RESOURCE_EXHAUSTED` from the google-genai SDK to trigger fallback.

**`AnthropicClient` class** (fallback):
- Same interface (`send_message`, `send_message_with_image`, `extract_text`) wrapping the Anthropic SDK.

**Client selection** at module level:
```python
if config.LLM_PROVIDER == "gemini":
    claude_client = GeminiClient()
else:
    claude_client = AnthropicClient()
```

All agents import `claude_client` — they never know which provider is active.

---

#### `backend/services/session_store.py` — Session Management

Stores interview state with automatic Redis/in-memory fallback.

**`SessionStore` class:**
- **`create_session(category, focus_areas)`** — Creates a new session with UUID. Initial phase: `"question_needed"`.
- **`get_session(session_id)`** / **`update_session(session_id, data)`** — CRUD operations.
- **`add_message(session_id, role, content)`** — Appends to `conversation_thread`.
- **`set_phase(session_id, phase)`** — Transitions the state machine.
- **`add_asked_question(session_id, question_id)`** — Tracks asked questions (MD5 hashes) for deduplication.

**Session schema:**
```python
{
    "session_id": "uuid",
    "category": "behavioral | technical | coding | system-design",
    "focus_areas": ["Amazon LP"],
    "current_question": {"question_id": "...", "question_text": "...", ...},
    "conversation_thread": [{"role": "user|assistant", "content": "..."}],
    "phase": "question_needed | answering | ready_for_eval | evaluating",
    "asked_questions": ["hash1", "hash2"],
    "evaluations": [{"question_id": "...", "evaluation": {...}}]
}
```

---

#### `backend/agents/orchestrator.py` — Central Router

The brain of the system. Routes messages to the right agent based on session phase.

**`process_message(session_id, user_message, image_base64?)`:**

| Current Phase | Action | Calls |
|---------------|--------|-------|
| `question_needed` | Get next question | → `QuestionCurator.get_question()` |
| `answering` | Process user's answer | → `InterviewCoach.process_answer()` |
| `answering` + "evaluate" keyword | Trigger evaluation | → `Evaluator.evaluate_answer()` |
| `ready_for_eval` | Score the answer | → `Evaluator.evaluate_answer()` |

**Key helper methods:**
- `_handle_new_question()` — Gets question, formats it for display, updates session.
- `_handle_evaluation()` — Scores answer, stores evaluation, formats results with emoji.
- `_format_question()` — Category-specific formatting (shows difficulty for coding, scale requirements for system design, LP for behavioral).
- `_format_evaluation()` — Renders scores, strengths, improvements, and follow-ups.

---

#### `backend/agents/question_curator.py` — Question Sourcing

Sources questions from CSV banks. Only uses LLM for technical category.

**`get_question(category, focus_areas, asked_questions)`:**

| Category | Source | LLM Used? |
|----------|--------|-----------|
| **Behavioral** | `behavioral_questions.csv` (106 questions — Amazon LP, Google) | No |
| **Technical** | `technical_topics.csv` (131 topics) → LLM generates targeted question | Yes (with CSV fallback) |
| **Coding** | `leetcode_questions.csv` (173 problems with company tags, difficulty) | No |
| **System Design** | `system_design_questions.csv` (36 questions with scale requirements) | No |

**Deduplication:** Generates MD5 hash of question text. Skips questions already in `asked_questions` set.

**Question data returned:**
```python
{
    "question_id": "a1b2c3d4e5f6",
    "question_text": "Tell me about a time you failed...",
    "focus_area": "Amazon LP - Ownership",
    "source": "behavioral_questions.csv",
    # + category-specific fields (difficulty, companies, url, key_components, etc.)
}
```

---

#### `backend/agents/interview_coach.py` — Follow-Up Coach

Conducts the interview by asking probing follow-up questions.

**`process_answer(category, question_data, conversation_thread)`:**
1. Gets category-specific system prompt (from `coach_prompts.py`)
2. Sends full conversation to LLM
3. LLM responds with either:
   - A follow-up question (answer is incomplete)
   - Exactly `"COMPLETE"` (answer is thorough enough for evaluation)

**Category-specific coaching:**
- **Behavioral:** Checks STAR coverage — probes for missing Situation/Task/Action/Result
- **Technical:** Checks for depth — probes for trade-offs, edge cases, real-world examples
- **System Design:** Checks architecture completeness — probes for scalability, failure handling, data consistency

---

#### `backend/agents/evaluator.py` — Answer Scorer

Scores answers using category-specific rubrics. Supports both text and vision.

**`evaluate_answer(category, question_data, conversation_thread)`:**
- Sends conversation to LLM with evaluator rubric prompt
- Parses JSON response with scores, strengths, improvements
- Returns structured evaluation

**`evaluate_diagram(question_data, user_description, image_base64)`:**
- Sends diagram image to LLM with vision capabilities
- Analyzes components, data flow, architecture patterns
- Returns: components identified, scalability/reliability scores, critical issues, suggestions

**Scoring rubrics by category:**

| Category | Dimensions (0-10 each) |
|----------|----------------------|
| **Behavioral** | STAR Coverage, Specificity, Impact, Authenticity |
| **Technical** | Technical Accuracy, Depth, Clarity, Practical Application |
| **System Design** | Component Selection, Scalability, Reliability, Data Consistency, Communication |
| **Diagram** | Components, Data Flow, Scalability Score, Reliability Score |

---

#### `backend/prompts/` — System Prompt Templates

Three files containing the system prompts that define each agent's behavior:

| File | Function | Used By |
|------|----------|---------|
| `curator_prompts.py` | `get_question_curator_prompt(category, focus_areas, asked_questions, topic_context?)` | Question Curator (technical only) |
| `coach_prompts.py` | `get_coach_prompt(category, question_data)` | Interview Coach |
| `evaluator_prompts.py` | `get_evaluator_prompt(category, question_data, conversation_thread)` + `get_diagram_evaluator_prompt(question_data, user_description)` | Evaluator |

Each prompt includes:
- Role definition (who the agent is)
- Category-specific rubric (what to assess)
- Output format (JSON schema expected)
- Tone guidelines (encouraging but critical)

---

#### `backend/data/` — Question Banks (CSV)

| File | Records | Key Columns |
|------|---------|-------------|
| `behavioral_questions.csv` | 106 | Question, Leadership_Principle, Company, Source, Priority |
| `technical_topics.csv` | 131 | Category, Topic, Sub_Topic, Key_Concepts, Difficulty |
| `leetcode_questions.csv` | 173 | Title, Difficulty, Companies, URL, Category, Optimal_Complexity |
| `system_design_questions.csv` | 36 | Question, Company, Scale_Requirements, Key_Components, Priority |

---

#### `backend/test_backend.py` — Structure Tests

Standalone test script that verifies all backend components load correctly **without needing API keys**.

Tests: config loading, session CRUD, prompt generation for all agents, FastAPI route registration.

---

### Frontend

#### `frontend/src/App.js` — Root Component

Manages navigation between two views:
- **Home** (`currentView === 'home'`): Shows `CategorySelector`
- **Chat** (`currentView === 'chat'`): Shows `ChatInterface`

State: `currentView`, `sessionId`, `category`

---

#### `frontend/src/services/api.js` — API Client

Fetch-based HTTP client pointing at `http://localhost:8000/api`.

| Function | Endpoint | Purpose |
|----------|----------|---------|
| `startSession(category, focusAreas)` | POST `/chat/start` | Begin interview |
| `sendMessage(sessionId, message)` | POST `/chat/message` | Send answer |
| `uploadImage(sessionId, imageBase64, description)` | POST `/chat/upload` | Upload diagram |
| `getSession(sessionId)` | GET `/session/{id}` | Fetch history |

---

#### `frontend/src/components/CategorySelector.js` — Home Screen

Displays 4 category cards in a grid:

| Category | Icon | Focus Options |
|----------|------|---------------|
| Behavioral (STAR) | `💬` | Amazon LP, Google Googleyness |
| Technical Knowledge | `💻` | Cloud Architecture, OOP, DS&A, Prompt Engineering |
| Problem Solving | `🧩` | (none — direct from LeetCode bank) |
| System Design | `🏗️` | (none — direct from question bank) |

User selects a category, optionally picks focus areas, then clicks "Start Interview".

---

#### `frontend/src/components/Chat/ChatInterface.js` — Chat View

The main interview interface. Key behaviors:

1. **On mount:** Calls `startSession()` API, displays first question
2. **Message loop:** User types/records answer → sends to backend → displays response
3. **Buttons:** "Evaluate My Answer" (green) and "Next Question" (orange) appear contextually based on session phase
4. **Voice:** Transcribed text populates the input area
5. **Image:** Base64-encoded diagram sent via `uploadImage()` API

---

#### `frontend/src/components/Chat/MessageBubble.js` — Message Display

Renders individual messages with role-based styling (user = right-aligned blue, assistant = left-aligned dark). Applies basic markdown formatting: `**bold**`, `• ` lists, `# ` headings. Shows a 3-dot animation during loading.

---

#### `frontend/src/components/Chat/InputArea.js` — Text Input

Multi-line textarea (3 rows). Enter sends, Shift+Enter adds newline. Disabled while waiting for API response.

---

#### `frontend/src/components/Chat/VoiceRecorder.js` — Voice Input

Uses browser-native `SpeechRecognition` API (Chrome/Edge). Toggle between "🎤 Record" and "⏹️ Stop". Accumulates transcription from interim results and passes final text to parent via `onTranscript` callback.

---

#### `frontend/src/components/Chat/ImageUploader.js` — Diagram Upload

Hidden file input triggered by "📸 Upload Diagram" button. Shows image preview + optional description field. Converts image to base64 via `FileReader` API and sends to backend.

---

#### Frontend CSS Files

| File | Styles |
|------|--------|
| `index.css` | Global dark theme (`#0f172a` bg, system fonts) |
| `App.css` | Root container (full viewport height) |
| `CategorySelector.css` | Card grid, gradient text, color-coded borders, hover effects |
| `ChatInterface.css` | Flexbox chat layout, action buttons (green evaluate, orange next) |
| `MessageBubble.css` | User/assistant bubble styles, loading animation |
| `InputArea.css` | Textarea and send button |
| `VoiceRecorder.css` | Record button with active state indicator |
| `ImageUploader.css` | Upload button, preview area, description input |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (free tier works)
- Redis (optional — falls back to in-memory)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set GEMINI_API_KEY=your_key_here

# Run
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
# Opens http://localhost:3000
```

---

## Multi-Model Fallback

The system automatically handles Gemini rate limits by trying models in order:

```
gemini-2.5-flash → gemini-2.0-flash → gemini-1.5-flash → gemini-1.5-pro
```

- **On 429 RESOURCE_EXHAUSTED:** Logs a warning and immediately tries the next model
- **On other errors:** Raises immediately (no masking of bugs)
- **All models exhausted:** Error propagates to agent-level error handling
- **Logging:** Every attempt and success is logged at INFO/WARNING level

---

## API Examples

```bash
# Start a behavioral interview
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{"category": "behavioral", "focus_areas": ["Amazon Leadership Principles"]}'

# Send an answer
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "In my previous role..."}'

# Trigger evaluation
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "evaluate"}'

# Health check
curl http://localhost:8000/health
```

---

## License

MIT
