"""Thin orchestrator — delegates to per-category QuestionSource implementations."""

from __future__ import annotations

from question_sources import (
    BehavioralCSVSource,
    CodingCSVSource,
    SystemDesignCSVSource,
    TechnicalCSVSource,
)
from question_sources.protocol import QuestionSource


class QuestionCurator:
    """Routes question operations to the appropriate category source.

    Each category (behavioral, technical, coding, system-design) is backed
    by a dedicated QuestionSource implementation.  To add a new source
    (e.g. database-backed), create a class satisfying the QuestionSource
    protocol and register it in ``_sources``.
    """

    def __init__(self) -> None:
        self._sources: dict[str, QuestionSource] = {
            "behavioral": BehavioralCSVSource(),
            "technical": TechnicalCSVSource(),
            "coding": CodingCSVSource(),
            "system-design": SystemDesignCSVSource(),
        }

    # ── Helpers ─────────────────────────────────────────────────────

    def _source(self, category: str) -> QuestionSource:
        """Look up the source for *category*, raising on unknown values."""
        src = self._sources.get(category)
        if src is None:
            raise ValueError(f"Unknown category: {category}")
        return src

    # ── Public API (mirrors the QuestionSource protocol) ────────────

    def get_question(
        self,
        category: str,
        focus_areas: list[str],
        asked_questions: list[str],
    ) -> dict:
        """Return a new question dict for *category*."""
        try:
            return self._source(category).get_question(focus_areas, asked_questions)
        except Exception as e:
            return {"error": f"Failed to generate question: {e}"}

    def get_category_structure(self, category: str) -> dict:
        """Return the hierarchical topic tree for *category*."""
        return self._source(category).get_structure()

    def get_progress(self, category: str, asked_questions: set[str]) -> dict:
        """Return a coverage summary for *category*."""
        return self._source(category).get_progress(asked_questions)

    def get_detailed_progress(self, category: str, asked_questions: set[str]) -> dict:
        """Return per-topic coverage details for *category*."""
        return self._source(category).get_detailed_progress(asked_questions)


# Global instance used by the orchestrator
question_curator = QuestionCurator()
