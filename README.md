# AI Interview Prep Agent

Conversational interview practice powered by 4 AI agents: **Coach**, **Evaluator**, **Question Curator**, and **Orchestrator**. Covers behavioral, technical, coding, and system design categories with per-user progress tracking.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # set GEMINI_API_KEY (required)
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
# Opens http://localhost:3000
```

### Verify

```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | `"gemini"` or `"anthropic"` |
| `GEMINI_API_KEY` | — | Google AI Studio key ([get one free](https://aistudio.google.com/apikey)) |
| `ANTHROPIC_API_KEY` | — | Required only if `LLM_PROVIDER=anthropic` |
| `REDIS_URL` | `redis://localhost:6379` | Optional — falls back to in-memory |
| `ENVIRONMENT` | `development` | Set to `production` to disable debug |

## Architecture

```
frontend/ (React :3000)
├── App.js                              # Login → Home → Chat → Progress views
├── services/api.js                     # HTTP client
└── components/
    ├── LoginPage.js                    # Email login
    ├── CategorySelector.js             # Category cards
    ├── ProgressView.js                 # Collapsible progress tree
    ├── SearchableDropdown/             # Custom dropdown with search + badges
    ├── Breadcrumb/                     # Selection path trail
    └── Chat/
        ├── ChatInterface.js            # Main chat + dropdown navigation
        ├── MessageBubble.js            # Message rendering
        ├── InputArea.js                # Text input
        ├── VoiceRecorder.js            # Speech-to-text
        └── ImageUploader.js            # Diagram upload

backend/ (FastAPI :8000)
├── app.py                              # REST API routes
├── config.py                           # Env vars, model chains
├── agents/
│   ├── orchestrator.py                 # Phase-based message router
│   ├── question_curator.py             # Thin router → question_sources/
│   ├── interview_coach.py              # Follow-up questions
│   └── evaluator.py                    # Answer scoring (text + vision)
├── question_sources/                   # ← QuestionSource protocol
│   ├── protocol.py                     # QuestionSource Protocol definition
│   ├── utils.py                        # Shared helpers (CSV, JSON, hashing)
│   ├── behavioral.py                   # BehavioralCSVSource
│   ├── technical.py                    # TechnicalCSVSource (uses LLM)
│   ├── coding.py                       # CodingCSVSource
│   └── system_design.py               # SystemDesignCSVSource
├── services/
│   ├── llm/                            # ← LLMProvider protocol
│   │   ├── protocol.py                 # LLMProvider Protocol definition
│   │   ├── gemini.py                   # GeminiClient (auto-fallback)
│   │   ├── anthropic.py                # AnthropicClient
│   │   └── __init__.py                 # Factory: create_llm_client()
│   ├── claude_client.py                # Backward-compat shim
│   ├── session_store.py                # Redis / in-memory sessions
│   └── progress_store.py              # Per-user JSON progress
├── prompts/                            # System prompts per agent
└── data/                               # CSV question banks
```

## How to Extend

### Add an LLM Provider

1. Create `backend/services/llm/my_provider.py`
2. Implement the `LLMProvider` protocol: `send_message()`, `send_message_with_image()`, `extract_text()`
3. Register in `backend/services/llm/__init__.py`

### Add a Question Source

1. Create `backend/question_sources/my_source.py`
2. Implement the `QuestionSource` protocol: `get_question()`, `get_structure()`, `get_progress()`, `get_detailed_progress()`
3. Register in `backend/agents/question_curator.py` under `_sources`

### Add a New Category

1. Create a `QuestionSource` implementation (see above)
2. Add the category key to `question_curator.py._sources`
3. Add a card in `frontend/src/components/CategorySelector.js`
4. Add prompts in `backend/prompts/`

## CSV Data Formats

| File | Columns |
|------|---------|
| `behavioral_questions.csv` | Question, Company, Leadership_Principle, Priority, STAR_Focus |
| `technical_topics.csv` | Priority, Category, Topic, Sub-Topic, Sub-Sub-Topic / Granular Depth Point |
| `leetcode_questions.csv` | Title, Difficulty, Companies, URL, Optimal_Complexity, Category |
| `system_design_questions.csv` | Question, Company, Key_Components, Scale_Requirements, LP_Hints, Priority |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/chat/start` | Start interview session |
| POST | `/api/chat/message` | Send answer / trigger eval |
| POST | `/api/chat/upload` | Upload diagram (system design) |
| GET | `/api/session/{id}` | Get session data |
| DELETE | `/api/session/{id}` | Delete session |
| PUT | `/api/session/{id}/focus` | Update focus areas |
| GET | `/api/session/{id}/progress` | Session progress |
| GET | `/api/session/{id}/progress/detailed` | Detailed progress tree |
| GET | `/api/categories/{category}/structure` | Topic hierarchy |
| GET | `/api/progress/{category}` | Persistent progress |
| GET | `/api/progress/{category}/detailed` | Persistent detailed progress |
| DELETE | `/api/progress/{category}` | Reset category progress |
| DELETE | `/api/progress` | Reset all progress |
| GET | `/health` | Health check |

## License

MIT
