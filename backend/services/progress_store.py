"""Persistent progress tracking via a local JSON file.

Stores which questions each user has been asked, keyed by email and
category.  Thread-safe writes with ``threading.Lock``.
"""

from __future__ import annotations

import json
import os
import threading

DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROGRESS_FILE: str = os.path.join(DATA_DIR, "progress.json")

KNOWN_CATEGORIES: set[str] = {"behavioral", "technical", "coding", "system-design"}


class ProgressStore:
    """Persistent progress tracking via a local JSON file.

    Schema::

        {
            "user@example.com": {
                "behavioral": ["qid1", "qid2", ...],
                "technical": ["qid3", ...],
                ...
            }
        }
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, dict[str, list[str]]] = self._load()

    def _load(self) -> dict[str, dict[str, list[str]]]:
        """Load progress from disk, migrating old format if needed."""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r") as f:
                    data = json.load(f)
                return self._maybe_migrate(data)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _maybe_migrate(self, data: dict) -> dict[str, dict[str, list[str]]]:
        """Migrate old format ``{category: [qids]}`` to ``{email: {category: [qids]}}``."""
        if not data:
            return data
        # If top-level keys are category names, it's old format
        if set(data.keys()).issubset(KNOWN_CATEGORIES):
            migrated: dict[str, dict[str, list[str]]] = {"default": data}
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(PROGRESS_FILE, "w") as f:
                json.dump(migrated, f, indent=2)
            return migrated
        return data

    def _save(self) -> None:
        """Flush current state to disk."""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PROGRESS_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def add_asked_question(self, user_email: str, category: str, question_id: str) -> None:
        """Persist a question as asked for the given user and category."""
        with self._lock:
            if user_email not in self._data:
                self._data[user_email] = {}
            if category not in self._data[user_email]:
                self._data[user_email][category] = []
            if question_id not in self._data[user_email][category]:
                self._data[user_email][category].append(question_id)
                self._save()

    def get_asked_questions(self, user_email: str, category: str) -> list[str]:
        """Return all persistently tracked question IDs for a user + category."""
        return list(self._data.get(user_email, {}).get(category, []))

    def get_all(self, user_email: str | None = None) -> dict:
        """Return progress data.  If *user_email* is given, return that user's data."""
        if user_email:
            return dict(self._data.get(user_email, {}))
        return dict(self._data)

    def reset(self, user_email: str, category: str | None = None) -> None:
        """Reset progress for a user's category, or all categories if *category* is ``None``."""
        with self._lock:
            if user_email in self._data:
                if category:
                    self._data[user_email].pop(category, None)
                else:
                    self._data[user_email] = {}
                self._save()


# Global instance
progress_store = ProgressStore()
