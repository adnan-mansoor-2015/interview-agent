# AI Interview Prep Agent

Conversational interview practice with 4 AI agents (Coach, Evaluator, Question Curator, Orchestrator). Supports behavioral, technical, coding, and system design categories.

Powered by Google Gemini with automatic multi-model fallback on rate limits.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
- Redis (optional — falls back to in-memory)

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env → set GEMINI_API_KEY=your_key

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
# → {"status":"healthy"}
```

## Usage

1. Open http://localhost:3000
2. Pick a category (Behavioral, Technical, Coding, System Design)
3. Answer the question via text or voice
4. The coach asks short follow-ups like a real interviewer
5. Click "Evaluate" for a scored breakdown with feedback
6. Click "Next Question" to continue

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/chat/start` | Start interview session |
| POST | `/api/chat/message` | Send answer / trigger eval |
| POST | `/api/chat/upload` | Upload diagram (system design) |
| GET | `/api/session/{id}` | Get session data |
| DELETE | `/api/session/{id}` | Delete session |
| GET | `/health` | Health check |

## Project Structure

```
backend/
├── app.py                  # FastAPI routes
├── config.py               # Models, API keys, fallback chains
├── agents/
│   ├── orchestrator.py     # Routes messages between agents
│   ├── question_curator.py # Picks questions from CSV banks
│   ├── interview_coach.py  # Asks follow-up questions
│   └── evaluator.py        # Scores answers (text + vision)
├── prompts/                # System prompts for each agent
├── services/
│   ├── claude_client.py    # LLM client (Gemini/Claude + fallback)
│   └── session_store.py    # Session management (Redis/in-memory)
└── data/                   # CSV question banks

frontend/
├── src/
│   ├── App.js              # Root component
│   ├── services/api.js     # Backend API client
│   └── components/
│       ├── CategorySelector.js
│       └── Chat/
│           ├── ChatInterface.js
│           ├── MessageBubble.js
│           ├── InputArea.js
│           ├── VoiceRecorder.js
│           └── ImageUploader.js
```

See [OVERVIEW.md](OVERVIEW.md) for detailed file-by-file documentation.

## License

MIT
