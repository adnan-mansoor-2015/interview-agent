"""Shared helpers used across all question source implementations."""

from __future__ import annotations

import csv
import hashlib
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_csv(filename: str) -> list[dict[str, str]]:
    """Load a CSV file from ``backend/data/`` and return a list of row dicts."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_question_id(text: str) -> str:
    """Deterministic, short hash used to de-duplicate questions across sessions."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def parse_llm_json(content: str) -> dict:
    """Extract and parse JSON from an LLM response that may be wrapped in markdown fences."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)
