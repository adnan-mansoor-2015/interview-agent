"""Coding question source — LeetCode / HackerRank problems."""

from __future__ import annotations

import random
from collections import defaultdict

from question_sources.utils import generate_question_id, load_csv

# Normalisation map: messy CSV category values → clean display groups.
CODING_CATEGORY_MAP: dict[str, str] = {
    "array": "Arrays & Hashing", "arrays": "Arrays & Hashing",
    "array / hashing": "Arrays & Hashing", "array / matrix": "Arrays & Hashing",
    "hashing": "Arrays & Hashing",
    "dynamic programming": "Dynamic Programming", "dp": "Dynamic Programming",
    "dynamic programming / binary search": "Dynamic Programming",
    "dynamic programming / string": "Dynamic Programming",
    "graph": "Graph", "graphs": "Graph",
    "graph / bfs": "Graph", "graph / dfs": "Graph",
    "graph / bfs-dp": "Graph", "graph / dfs-bfs": "Graph",
    "graph / dijkstra": "Graph", "graph / topological sort": "Graph",
    "graph / union find": "Graph",
    "graph / binary search / heap": "Graph",
    "tree": "Trees", "trees": "Trees",
    "tree / bfs": "Trees", "tree / dfs": "Trees",
    "tree / bfs-dfs": "Trees", "tree / design": "Trees",
    "linked list": "Linked List",
    "linked list / heap": "Linked List",
    "linked list / two pointers": "Linked List",
    "stack": "Stack", "stack / dp": "Stack",
    "stack / design": "Stack", "stack / sorting": "Stack",
    "binary search": "Binary Search",
    "binary search / design": "Binary Search",
    "backtracking": "Backtracking",
    "backtracking / dfs": "Backtracking",
    "backtracking / dp": "Backtracking",
    "two pointers": "Two Pointers",
    "two pointers / sorting": "Two Pointers",
    "two pointers / stack": "Two Pointers",
    "sliding window": "Sliding Window",
    "sliding window / string": "Sliding Window",
    "heap": "Heap", "heaps": "Heap",
    "heap / design": "Heap", "heap / hashing": "Heap",
    "heap / quickselect": "Heap", "heap / sorting": "Heap",
    "string": "String", "strings": "String",
    "string / dp": "String", "string / design": "String",
    "sorting": "Sorting", "sorting / greedy": "Sorting",
    "bit manipulation": "Bit Manipulation",
    "design": "Design", "advanced": "Design",
    "greedy": "Greedy", "greedy / dp": "Greedy", "greedy / heap": "Greedy",
    "trie": "Trie", "trie / dfs": "Trie", "trie / design": "Trie",
    "math": "Math & Other", "recursion": "Math & Other",
}


def _normalize(raw: str) -> str:
    return CODING_CATEGORY_MAP.get(raw.lower().strip(), "Math & Other")


class CodingCSVSource:
    """Loads coding problems from ``leetcode_questions.csv``.

    CSV columns: Question, Category, Difficulty, Company, Rank,
                 LeetCode_Link, IdealTimeComplexity, FollowUp
    Hierarchy: Normalised Category (1 level)
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, str]] | None = None

    @property
    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            self._rows = load_csv("leetcode_questions.csv")
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
                if any(f in q.get("Category", "").lower() for f in focus_lower)
            ]
            if filtered:
                pool = filtered

        pool = [q for q in pool if generate_question_id(q.get("Question", "")) not in asked_questions]
        if not pool:
            pool = list(self.rows)

        pool_sorted = sorted(pool, key=lambda q: int(q.get("Rank", 999)))
        top_pool = pool_sorted[: max(30, len(pool_sorted))]
        question = random.choice(top_pool)

        company_str = question.get("Company", "")
        companies = [c.strip() for c in company_str.split(",") if c.strip()]

        return {
            "question_id": generate_question_id(question.get("Question", "")),
            "question_title": question.get("Question", ""),
            "difficulty": question.get("Difficulty", "Medium"),
            "companies": companies,
            "leetcode_url": question.get("LeetCode_Link", ""),
            "hackerrank_url": None,
            "focus_areas": [question.get("Category", "")],
            "optimal_complexity": question.get("IdealTimeComplexity", ""),
            "follow_up": question.get("FollowUp", ""),
        }

    def get_structure(self) -> dict:
        counts: dict[str, int] = defaultdict(int)
        for row in self.rows:
            counts[_normalize(row.get("Category", ""))] += 1
        return {cat: {"total": count} for cat, count in sorted(counts.items())}

    def get_progress(self, asked_questions: set[str]) -> dict:
        cats: dict[str, dict] = defaultdict(lambda: {"total": 0, "covered": 0})
        for row in self.rows:
            norm = _normalize(row.get("Category", ""))
            cats[norm]["total"] += 1
            if generate_question_id(row.get("Question", "")) in asked_questions:
                cats[norm]["covered"] += 1

        total_all = sum(c["total"] for c in cats.values())
        covered_all = sum(c["covered"] for c in cats.values())
        levels = {
            cat: {
                "total": c["total"],
                "covered": c["covered"],
                "percent": round(c["covered"] / c["total"] * 100) if c["total"] else 0,
            }
            for cat, c in sorted(cats.items())
        }
        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }

    def get_detailed_progress(self, asked_questions: set[str]) -> dict:
        cats: dict[str, list] = defaultdict(list)
        for row in self.rows:
            norm = _normalize(row.get("Category", ""))
            name = row.get("Question", "")
            cats[norm].append({
                "name": name,
                "difficulty": row.get("Difficulty", "Medium"),
                "covered": generate_question_id(name) in asked_questions,
            })

        total_all = sum(len(v) for v in cats.values())
        covered_all = sum(1 for items in cats.values() for i in items if i["covered"])
        levels = {}
        for cat in sorted(cats):
            items = cats[cat]
            cat_covered = sum(1 for i in items if i["covered"])
            levels[cat] = {
                "total": len(items),
                "covered": cat_covered,
                "percent": round(cat_covered / len(items) * 100) if items else 0,
                "items": items,
            }
        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }
