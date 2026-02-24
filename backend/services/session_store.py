import json
import uuid
from typing import Optional, Dict, Any
import config

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SessionStore:
    def __init__(self):
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
                self.redis_client.ping()  # Test connection
                self.use_redis = True
            except:
                self.use_redis = False
                self.memory_store = {}
        else:
            self.use_redis = False
            self.memory_store = {}

    def create_session(self, category: str, focus_areas: list = None) -> str:
        """Create a new interview session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "category": category,
            "focus_areas": focus_areas or [],
            "current_question": None,
            "conversation_thread": [],
            "phase": "question_needed",  # question_needed | answering | ready_for_eval | evaluating
            "asked_questions": [],
            "evaluations": [],
        }

        if self.use_redis:
            self.redis_client.setex(
                f"session:{session_id}", config.SESSION_TTL, json.dumps(session_data)
            )
        else:
            self.memory_store[session_id] = session_data

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        if self.use_redis:
            data = self.redis_client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        else:
            return self.memory_store.get(session_id)

    def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session data."""
        if self.use_redis:
            self.redis_client.setex(
                f"session:{session_id}", config.SESSION_TTL, json.dumps(session_data)
            )
        else:
            self.memory_store[session_id] = session_data

    def delete_session(self, session_id: str):
        """Delete a session."""
        if self.use_redis:
            self.redis_client.delete(f"session:{session_id}")
        else:
            self.memory_store.pop(session_id, None)

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation thread."""
        session = self.get_session(session_id)
        if session:
            session["conversation_thread"].append({"role": role, "content": content})
            self.update_session(session_id, session)

    def set_phase(self, session_id: str, phase: str):
        """Update session phase."""
        session = self.get_session(session_id)
        if session:
            session["phase"] = phase
            self.update_session(session_id, session)

    def add_asked_question(self, session_id: str, question_id: str):
        """Track asked questions for deduplication."""
        session = self.get_session(session_id)
        if session:
            session["asked_questions"].append(question_id)
            self.update_session(session_id, session)


# Global session store instance
session_store = SessionStore()
