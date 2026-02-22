# Quick Start Guide

## Backend Setup (Complete ✅)

The backend is fully implemented with:
- **4 specialized Claude agents** (Orchestrator, Question Curator, Interview Coach, Evaluator)
- **FastAPI REST API** with session management
- **Redis** for conversation history
- **Prompt engineering** for each agent role

### Start the Backend

1. **Install Redis:**
   ```bash
   # macOS
   brew install redis
   redis-server

   # Or Docker
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Set up environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Run the server:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```

4. **Test it:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

---

## API Endpoints

### Start Session
```bash
POST /api/chat/start
{
  "category": "behavioral",  # or technical, coding, system-design
  "focus_areas": ["Amazon LP", "Ownership"]
}
```

### Send Message
```bash
POST /api/chat/message
{
  "session_id": "uuid",
  "message": "I led a project where..."
}
```

### Upload Diagram (System Design)
```bash
POST /api/chat/upload
{
  "session_id": "uuid",
  "image_base64": "base64_encoded_image",
  "description": "This is my architecture for Instagram"
}
```

### Get Session History
```bash
GET /api/session/{session_id}
```

---

## How the Agents Work

### 1. Question Curator Agent
- **Prompt:** Searches for real FAANG questions from Reddit, Glassdoor, Blind
- **Output:** Question with source attribution, deduplicates against asked questions
- **For Coding:** Returns LeetCode/HackerRank links (respects ToS)

### 2. Interview Coach Agent
- **Prompt:** Assesses answer completeness (STAR for behavioral, depth for technical)
- **Output:** Follow-up question OR "COMPLETE" signal
- **Tone:** Conversational, probing, encouraging

### 3. Evaluator Agent
- **Prompt:** Scores 0-10 with rubric, compares to "strong hire" benchmark
- **Output:** Structured JSON with scores, strengths, improvements, follow-ups
- **Vision Mode:** For system design diagrams (identifies components, traces data flow)

### 4. Orchestrator Agent
- **Role:** Routes between agents based on session phase
- **States:** `question_needed` → `answering` → `ready_for_eval` → `evaluating` → `question_needed`

---

## Example Flow

```
User: Start behavioral interview
├─> Orchestrator → Question Curator
│   └─> Returns: "Tell me about a time you failed"
│
User: I was leading a project and missed a deadline...
├─> Orchestrator → Interview Coach
│   └─> Returns: "What specifically did YOU do?"
│
User: I personally worked overtime and...
├─> Interview Coach
│   └─> Returns: "COMPLETE"
│
User: [Clicks Evaluate]
├─> Orchestrator → Evaluator
│   └─> Returns: Score 8/10 with feedback
│
User: Next question
├─> Orchestrator → Question Curator
    └─> Returns: New question (deduplicated)
```

---

## Frontend (To Be Built)

The frontend needs:
1. **Chat Interface** — message bubbles, input area
2. **Voice Recording** — Web Speech API integration
3. **Image Upload** — Drag-drop for diagrams
4. **Category Selector** — 4 cards (Behavioral, Technical, Coding, System Design)
5. **API Integration** — Connect to FastAPI backend

Tech stack: React + Tailwind CSS

---

## Testing the Backend (Manual)

### Behavioral Interview Test
```bash
# 1. Start session
curl -X POST http://localhost:8000/api/chat/start \
  -H "Content-Type: application/json" \
  -d '{"category": "behavioral", "focus_areas": ["Amazon LP"]}'

# Save the session_id from response

# 2. Answer the question
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "I led a team through a tight deadline..."}'

# 3. Request evaluation
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "evaluate"}'
```

---

## Next Steps

1. Build React frontend
2. Add Web Speech API for voice input
3. Add image upload UI for diagrams
4. Test all 4 categories end-to-end
5. Deploy (optional: Vercel frontend + Railway backend)

---

## Architecture Summary

```
Frontend (React)
    ↓ HTTP
FastAPI Backend
    ├─> Redis (session storage)
    ├─> Anthropic API (Claude agents)
    └─> Multi-agent orchestration
        ├─ Question Curator (sourcing)
        ├─ Interview Coach (follow-ups)
        ├─ Evaluator (scoring)
        └─ Orchestrator (routing)
```

All logic is in **prompt engineering** — minimal custom code!
