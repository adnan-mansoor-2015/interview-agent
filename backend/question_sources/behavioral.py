"""Behavioral question source — Amazon / Google Leadership Principles."""

from __future__ import annotations

import random
from collections import defaultdict

from question_sources.utils import generate_question_id, load_csv


class BehavioralCSVSource:
    """Loads behavioral questions from ``behavioral_questions.csv``.

    CSV columns: Question, Company, Leadership_Principle, Priority, STAR_Focus
    Hierarchy: Company → Leadership Principle (2 levels)
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, str]] | None = None

    @property
    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            self._rows = load_csv("behavioral_questions.csv")
        return self._rows

    # ------------------------------------------------------------------
    # QuestionSource interface
    # ------------------------------------------------------------------

    def get_question(self, focus_areas: list[str], asked_questions: list[str]) -> dict:
        pool = list(self.rows)

        if focus_areas:
            focus_lower = [f.lower() for f in focus_areas]
            filtered = [
                q for q in pool
                if any(
                    f in q.get("Leadership_Principle", "").lower()
                    or f in q.get("Company", "").lower()
                    for f in focus_lower
                )
            ]
            if filtered:
                pool = filtered

        pool = [q for q in pool if generate_question_id(q.get("Question", "")) not in asked_questions]

        if not pool:
            pool = list(self.rows)

        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        question = random.choice(selection_pool)
        return {
            "question_id": generate_question_id(question.get("Question", "")),
            "question_text": question.get("Question", ""),
            "source": f"{question.get('Company', 'FAANG')} Leadership Principles",
            "company": question.get("Company", "Amazon"),
            "leadership_principle": question.get("Leadership_Principle", ""),
            "star_focus": question.get("STAR_Focus", ""),
            "metadata": {
                "difficulty": "medium",
                "commonly_asked": True,
                "priority": question.get("Priority", "1"),
            },
        }

    def get_structure(self) -> dict:
        tree: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for row in self.rows:
            tree[row.get("Company", "Other")][row.get("Leadership_Principle", "Other")] += 1

        result = {}
        for company in sorted(tree):
            company_data: dict = {"children": {}, "total": 0}
            for lp in sorted(tree[company]):
                company_data["children"][lp] = {"total": tree[company][lp]}
                company_data["total"] += tree[company][lp]
            result[company] = company_data
        return result

    def get_progress(self, asked_questions: set[str]) -> dict:
        tree: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"total": 0, "covered": 0}))
        for row in self.rows:
            company = row.get("Company", "Other")
            lp = row.get("Leadership_Principle", "Other")
            tree[company][lp]["total"] += 1
            if generate_question_id(row.get("Question", "")) in asked_questions:
                tree[company][lp]["covered"] += 1

        total_all = covered_all = 0
        levels: dict = {}
        for company in sorted(tree):
            comp_total = comp_covered = 0
            children: dict = {}
            for lp in sorted(tree[company]):
                s = tree[company][lp]
                children[lp] = {
                    "total": s["total"],
                    "covered": s["covered"],
                    "percent": round(s["covered"] / s["total"] * 100) if s["total"] else 0,
                }
                comp_total += s["total"]
                comp_covered += s["covered"]
            levels[company] = {
                "total": comp_total,
                "covered": comp_covered,
                "percent": round(comp_covered / comp_total * 100) if comp_total else 0,
                "children": children,
            }
            total_all += comp_total
            covered_all += comp_covered

        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }

    def get_detailed_progress(self, asked_questions: set[str]) -> dict:
        tree: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for row in self.rows:
            company = row.get("Company", "Other")
            lp = row.get("Leadership_Principle", "Other")
            name = row.get("Question", "")
            tree[company][lp].append({
                "name": name,
                "covered": generate_question_id(name) in asked_questions,
            })

        total_all = covered_all = 0
        levels: dict = {}
        for company in sorted(tree):
            comp_total = comp_covered = 0
            children: dict = {}
            for lp in sorted(tree[company]):
                items = tree[company][lp]
                lp_covered = sum(1 for i in items if i["covered"])
                children[lp] = {
                    "total": len(items),
                    "covered": lp_covered,
                    "percent": round(lp_covered / len(items) * 100) if items else 0,
                    "items": items,
                }
                comp_total += len(items)
                comp_covered += lp_covered
            levels[company] = {
                "total": comp_total,
                "covered": comp_covered,
                "percent": round(comp_covered / comp_total * 100) if comp_total else 0,
                "children": children,
            }
            total_all += comp_total
            covered_all += comp_covered

        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }
