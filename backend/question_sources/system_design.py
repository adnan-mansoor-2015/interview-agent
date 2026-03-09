"""System design question source — FAANG architecture questions."""

from __future__ import annotations

import random

from question_sources.utils import generate_question_id, load_csv


class SystemDesignCSVSource:
    """Loads system design questions from ``system_design_questions.csv``.

    CSV columns: Question, Company, Key_Components, Scale_Requirements,
                 LP_Hints, Priority
    Hierarchy: flat (no natural subcategories)
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, str]] | None = None

    @property
    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            self._rows = load_csv("system_design_questions.csv")
        return self._rows

    # ------------------------------------------------------------------
    # QuestionSource interface
    # ------------------------------------------------------------------

    def get_question(self, focus_areas: list[str], asked_questions: list[str]) -> dict:
        pool = [
            q for q in self.rows
            if generate_question_id(q.get("Question", "")) not in asked_questions
        ]
        if not pool:
            pool = list(self.rows)

        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        question = random.choice(selection_pool)
        components_str = question.get("Key_Components", "")
        components = [c.strip() for c in components_str.split(",") if c.strip()]

        return {
            "question_id": generate_question_id(question.get("Question", "")),
            "question_text": question.get("Question", ""),
            "source": f"Asked at {question.get('Company', 'FAANG')}",
            "company": question.get("Company", ""),
            "scale_requirements": question.get("Scale_Requirements", ""),
            "key_components": components,
            "lp_hints": question.get("LP_Hints", ""),
            "metadata": {
                "difficulty": "senior",
                "commonly_asked": True,
                "priority": question.get("Priority", "1"),
            },
        }

    def get_structure(self) -> dict:
        return {"total": len(self.rows)}

    def get_progress(self, asked_questions: set[str]) -> dict:
        total = len(self.rows)
        covered = sum(
            1 for row in self.rows
            if generate_question_id(row.get("Question", "")) in asked_questions
        )
        return {
            "total": total,
            "covered": covered,
            "overall_percent": round(covered / total * 100) if total else 0,
            "levels": {},
        }

    def get_detailed_progress(self, asked_questions: set[str]) -> dict:
        items = []
        for row in self.rows:
            name = row.get("Question", "")
            items.append({
                "name": name,
                "company": row.get("Company", ""),
                "covered": generate_question_id(name) in asked_questions,
            })

        total = len(items)
        covered = sum(1 for i in items if i["covered"])
        return {
            "total": total,
            "covered": covered,
            "overall_percent": round(covered / total * 100) if total else 0,
            "levels": {},
            "items": items,
        }
