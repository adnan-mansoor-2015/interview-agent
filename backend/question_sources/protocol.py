"""Question source protocol — the contract all question backends must satisfy.

To plug in a database, API, or any other data source:
  1. Create a class that satisfies ``QuestionSource``.
  2. Register it in ``agents/question_curator.py``'s ``_sources`` dict.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class QuestionSource(Protocol):
    """Protocol for category-specific question data sources."""

    def get_question(self, focus_areas: list[str], asked_questions: list[str]) -> dict:
        """Select and return a question dict, excluding *asked_questions*."""
        ...

    def get_structure(self) -> dict:
        """Return the hierarchy tree with question counts (for dropdown nav)."""
        ...

    def get_progress(self, asked_questions: set[str]) -> dict:
        """Compute coverage stats at every hierarchy level."""
        ...

    def get_detailed_progress(self, asked_questions: set[str]) -> dict:
        """Full hierarchy tree with per-item completion status."""
        ...
