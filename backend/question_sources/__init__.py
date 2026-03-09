"""Question sources package — pluggable backends for interview question data.

Each source satisfies the ``QuestionSource`` protocol and handles one
interview category (behavioral, technical, coding, system-design).

To add a new data backend (e.g. PostgreSQL):
  1. Create a class satisfying ``QuestionSource`` in this package.
  2. Register it in ``agents/question_curator.py``'s ``_sources`` dict.
"""

from question_sources.behavioral import BehavioralCSVSource
from question_sources.coding import CodingCSVSource
from question_sources.protocol import QuestionSource
from question_sources.system_design import SystemDesignCSVSource
from question_sources.technical import TechnicalCSVSource

__all__ = [
    "QuestionSource",
    "BehavioralCSVSource",
    "TechnicalCSVSource",
    "CodingCSVSource",
    "SystemDesignCSVSource",
]
