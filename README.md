# AI-Powered Interview Prep Chat Agent

**Version:** 2.0
**Platform:** Claude Pro Subscription (Anthropic API)
**Approach:** Multi-Agent Orchestration with Prompt Engineering

---

## Overview

A conversational AI interview preparation system using **Claude's multi-agent capabilities** where users interact via **text, speech, or image inputs** in a chat-based interface. The system uses specialized Claude agents for question sourcing and answer evaluation, providing real-time feedback and follow-up questions in an iterative coaching flow.

---

## Core Architecture: Multi-Agent Pattern

### Agent Roles

| Agent | Responsibility | Tools/Capabilities |
|-------|---------------|-------------------|
| **Question Curator Agent** | Search and retrieve real FAANG interview questions from web sources | Web search, Reddit/Glassdoor scraping, question bank filtering |
| **Interview Coach Agent** | Conduct the interview, ask follow-ups, probe incomplete answers | Conversational flow, STAR method expertise, probing questions |
| **Evaluator Agent** | Critically assess answers with scores and detailed feedback | STAR analysis, technical accuracy, diagram critique (vision), rubric-based scoring |
| **Orchestrator Agent** | Route between agents, maintain session state, manage conversation flow | Session memory, agent coordination |

---

## Features

### 1. 💬 Behavioral (STAR Method)

**Question Sourcing:**
- Amazon Leadership Principles questions
- Google Leadership Principles (Googleyness) questions
- Sourced from Reddit, Glassdoor, Blind
- Unlimited questions with deduplication
- "Next Question" button for continuous practice

**Interaction:**
- **Text input:** Multi-line textarea
- **Speech input:** Browser-based voice recording (Web Speech API)
- **Interactive coaching:** Follow-up questions if answer is incomplete
- **STAR method guidance:** Situation, Task, Action, Result

**Evaluation:**
- Score: 0-10 with breakdown per STAR element
- Strengths and improvement areas
- Sample interviewer follow-ups
- Study recommendations

---

### 2. 💻 Technical Knowledge

**Question Sourcing:**
- Senior Backend Engineer focus areas:
  - Cloud Architecture (AWS, Azure, GCP)
  - Object-Oriented Programming
  - Data Structures & Algorithms
  - Prompt Engineering
- Real questions asked at Amazon and FAANG companies
- Sourced from Glassdoor, Blind, LeetCode Discuss

**Interaction:**
- Text or speech input
- Follow-up questions for incomplete answers
- Probing on: concepts, trade-offs, real-world examples, edge cases

**Evaluation:**
- Technical accuracy (factual correctness)
- Depth of knowledge
- Clarity of communication
- Practical application
- Study recommendations

---

### 3. 🧩 Problem Solving (Coding Challenges)

**Question Sourcing:**
- LeetCode problems tagged with FAANG companies
- HackerRank Interview Preparation Kit
- Bloomberg, Microsoft, Apple coding questions
- Difficulty filters: Easy, Medium, Hard

**Format:**
- Direct links to LeetCode/HackerRank (respects platform ToS)
- Focus areas highlighted (Hash Maps, Dynamic Programming, etc.)

**Optional Code Review:**
- Paste your solution for AI review
- Time/space complexity analysis
- Code quality feedback
- Optimization suggestions

---

### 4. 🏗️ System Design

**Question Sourcing:**
- Common FAANG questions (Design Instagram, Twitter, Uber, etc.)
- Sourced from System Design Primer, Glassdoor, Reddit
- Scale requirements specified (users, QPS, storage)

**Interaction:**
- **Upload diagram** as image (Excalidraw, Lucidchart, whiteboard photo)
- **AI vision analysis:** Claude identifies components, data flow, architecture patterns
- **Iterative refinement:** Upload revised diagrams based on feedback
- **Text explanations:** Describe your approach in chat

**Evaluation:**
- Component selection appropriateness
- Scalability assessment
- Reliability and fault tolerance
- Data consistency (CAP theorem)
- Diagram clarity
- Critical feedback on missing elements
- Improvement suggestions

---

## User Experience Flow

### Example: Behavioral Interview

```
👤 USER: Start behavioral interview - Amazon Leadership Principles

🤖 SYSTEM: Activating Question Curator Agent...

📋 Question 1/∞ — Leadership Principle: "Bias for Action"
"Tell me about a time you had to make a decision with incomplete information."

[🎤 Record Answer] [✍️ Type Answer] [⏭️ Next Question]

---

👤 USER: [Records 90-second answer via microphone]

🤖 COACH: Thanks for that response. I can see you faced a tight deadline.
I'd like to hear more about the SPECIFIC actions you took.
Can you walk through your decision-making process step-by-step?

---

👤 USER: [Provides more detail via text]

🤖 COACH: Excellent detail! One more thing - what was the measurable outcome?

---

👤 USER: [Adds result metrics]

[🎯 Evaluate My Answer] [⏭️ Move to Next Question]

---

👤 USER: [Clicks Evaluate]

🤖 EVALUATOR:
📊 Overall Score: 9/10 ✅

STAR Breakdown:
• Situation: 10/10 — Crystal clear context
• Task: 9/10 — Your ownership was evident
• Action: 8/10 — Good detail
• Result: 10/10 — Love the specific metrics (30% faster delivery)

💪 Strengths:
- Quantified impact beautifully
- Showed bias for action under uncertainty

[📝 Next Question] [🔄 Re-attempt]
```

---

## Technical Stack

### Frontend
- **Framework:** React (chat-based UI)
- **Speech Input:** Web Speech API (browser native)
- **Image Upload:** Drag-and-drop for diagrams
- **Styling:** Tailwind CSS (dark mode)

### Backend
- **Framework:** FastAPI (Python)
- **AI:** Anthropic Claude API
  - Text: `claude-sonnet-4-20250514`
  - Vision: `claude-3-5-sonnet-20241022` (for diagrams)
- **Web Search:** Brave Search API (for question sourcing)
- **Session Storage:** Redis (conversation history)

### Key Dependencies
```
anthropic>=0.39.0
fastapi>=0.104.0
redis>=5.0.0
python-dotenv>=1.0.0
```

---

## Project Structure

```
interview-agent/
├── backend/
│   ├── app.py                      # FastAPI entry point
│   ├── config.py                   # Environment configuration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Main agent coordinator
│   │   ├── question_curator.py     # Question sourcing agent
│   │   ├── interview_coach.py      # Follow-up question agent
│   │   └── evaluator.py            # Scoring and feedback agent
│   ├── prompts/
│   │   ├── curator_prompts.py      # Question curator system prompts
│   │   ├── coach_prompts.py        # Interview coach prompts
│   │   └── evaluator_prompts.py    # Evaluation rubrics
│   ├── routes/
│   │   ├── chat.py                 # Chat message endpoint
│   │   ├── session.py              # Session management
│   │   └── upload.py               # Image upload for diagrams
│   ├── services/
│   │   ├── claude_client.py        # Anthropic API wrapper
│   │   ├── search_service.py       # Web search integration
│   │   └── session_store.py        # Redis session management
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatContainer.jsx
│   │   │   │   ├── MessageBubble.jsx
│   │   │   │   └── InputArea.jsx
│   │   │   ├── CategorySelector.jsx
│   │   │   ├── VoiceRecorder.jsx
│   │   │   └── ImageUploader.jsx
│   │   ├── context/
│   │   │   └── ChatContext.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## Environment Setup

### Backend

1. **Install dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Required variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   BRAVE_SEARCH_API_KEY=xxxxx  # Optional: for web search
   REDIS_URL=redis://localhost:6379
   ```

3. **Start Redis:**
   ```bash
   docker run -d -p 6379:6379 redis:latest
   # Or: brew install redis && redis-server
   ```

4. **Run backend:**
   ```bash
   uvicorn app:app --reload --port 8000
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start dev server:**
   ```bash
   npm start
   # Runs on http://localhost:3000
   ```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/start` | Start new interview session |
| `POST` | `/api/chat/message` | Send message (text/speech transcript) |
| `POST` | `/api/chat/upload` | Upload diagram image |
| `GET` | `/api/session/{id}` | Get session history |
| `DELETE` | `/api/session/{id}` | Clear session |

---

## Session State Schema

```json
{
  "session_id": "uuid",
  "category": "behavioral | technical | coding | system-design",
  "focus_areas": ["Amazon LP", "Ownership"],
  "current_question": {
    "id": "hash123",
    "text": "Tell me about a time...",
    "source": "Reddit - r/cscareerquestions",
    "metadata": {}
  },
  "conversation_thread": [
    {"role": "assistant", "content": "Question..."},
    {"role": "user", "content": "Answer..."},
    {"role": "assistant", "content": "Follow-up..."}
  ],
  "phase": "question_needed | answering | ready_for_eval | evaluating",
  "asked_questions": ["hash123", "hash456"],
  "evaluations": [
    {
      "question_id": "hash123",
      "score": 9,
      "feedback": {}
    }
  ]
}
```

---

## Agent Prompt Engineering

### Question Curator Agent
- Searches Reddit, Glassdoor, Blind for verified questions
- Deduplicates against asked questions
- Returns question with source attribution

### Interview Coach Agent
- Assesses answer completeness (STAR elements, technical depth)
- Asks ONE targeted follow-up question
- Conversational and encouraging tone
- Signals "COMPLETE" when ready for evaluation

### Evaluator Agent
- Scores on 0-10 scale with rubric
- Provides strengths, improvements, follow-ups
- Benchmark: "strong hire" at FAANG
- Direct but constructive feedback

### Diagram Evaluator (Vision)
- Identifies components in uploaded diagrams
- Traces data flow and architecture patterns
- Critical evaluation of scalability, reliability
- Suggests specific improvements

---

## Success Metrics

- **Question Quality:** 90%+ from verified FAANG sources
- **Evaluation Accuracy:** ±1 point vs human interviewer
- **Follow-up Relevance:** 80%+ deemed helpful
- **Diagram Understanding:** 95%+ component identification accuracy
- **User Satisfaction:** 8/10+ "felt like real interview"

---

## Development Roadmap

### Phase 1: Core Chat (Week 1)
- [x] FastAPI backend with session management
- [ ] Chat interface with text input
- [ ] Orchestrator agent routing
- [ ] Question Curator agent integration

### Phase 2: Multi-Modal Input (Week 2)
- [ ] Voice recording (Web Speech API)
- [ ] Image upload for diagrams
- [ ] Vision agent integration

### Phase 3: Evaluation & Feedback (Week 3)
- [ ] Interview Coach agent
- [ ] Evaluator agent with rubrics
- [ ] Score display and feedback UI

### Phase 4: Polish (Week 4)
- [ ] Question deduplication
- [ ] Session persistence
- [ ] Performance optimization
- [ ] User testing

---

## License

MIT

---

## Support

For issues or questions, please open a GitHub issue or contact the development team.
