"""Technical question source — CSV topics + LLM-generated questions."""

from __future__ import annotations

import logging
import random
from collections import defaultdict
from typing import Any

from question_sources.utils import generate_question_id, load_csv, parse_llm_json

logger = logging.getLogger(__name__)


def _get_depth(row: dict[str, str]) -> str:
    """Return the deepest granularity column from a technical CSV row."""
    return row.get("Sub-Sub-Topic / Granular Depth Point", row.get("Sub-Sub-Topic", ""))


class TechnicalCSVSource:
    """Loads topics from ``technical_topics.csv`` and optionally uses an LLM
    to generate interview questions from the selected topic.

    CSV columns: Priority, Category, Topic, Sub-Topic,
                 Sub-Sub-Topic / Granular Depth Point
    Hierarchy: Category → Topic → Sub-Topic (3 levels)

    Args:
        llm_client: An ``LLMProvider`` instance (optional).  When *None*,
            questions fall back to a simple CSV-derived format.
        prompt_fn: Callable that generates the system prompt for the LLM.
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        prompt_fn: Any | None = None,
    ) -> None:
        self._rows: list[dict[str, str]] | None = None
        self._llm = llm_client
        self._prompt_fn = prompt_fn

    def _init_llm(self) -> None:
        """Lazy-load LLM dependencies only when needed."""
        if self._llm is None:
            from services.claude_client import claude_client

            self._llm = claude_client
        if self._prompt_fn is None:
            from prompts.curator_prompts import get_question_curator_prompt

            self._prompt_fn = get_question_curator_prompt

    @property
    def rows(self) -> list[dict[str, str]]:
        if self._rows is None:
            self._rows = load_csv("technical_topics.csv")
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
                    f in q.get("Category", "").lower()
                    or f in q.get("Topic", "").lower()
                    or f in q.get("Sub-Topic", "").lower()
                    for f in focus_lower
                )
            ]
            if filtered:
                pool = filtered

        pool = [q for q in pool if generate_question_id(_get_depth(q)) not in asked_questions]
        if not pool:
            pool = list(self.rows)

        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        topic = random.choice(selection_pool)
        depth_point = _get_depth(topic)
        topic_id = generate_question_id(depth_point)
        focus_area = f"{topic.get('Topic', '')} - {topic.get('Sub-Topic', '')}"

        # Try LLM to generate a targeted question
        try:
            self._init_llm()
            topic_str = (
                f"Category: {topic.get('Category', '')}, "
                f"Topic: {topic.get('Topic', '')}, "
                f"Sub-Topic: {topic.get('Sub-Topic', '')}, "
                f"Depth: {depth_point}"
            )
            system_prompt = self._prompt_fn(
                "technical", focus_areas, asked_questions, topic_context=topic_str
            )
            response = self._llm.send_message(
                system_prompt=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Generate a senior-level technical interview question about: {topic_str}",
                }],
            )
            content = self._llm.extract_text(response)
            question_data = parse_llm_json(content)
            question_data["question_id"] = topic_id
            question_data.setdefault("focus_area", focus_area)
            question_data.setdefault("source", f"Senior Backend Engineer - {topic.get('Category', '')}")
            return question_data
        except Exception:
            logger.debug("LLM question generation failed — falling back to CSV", exc_info=True)
            return {
                "question_id": topic_id,
                "question_text": f"Tell me about {depth_point} — what do you know about how it works?",
                "source": f"Senior Backend Engineer - {topic.get('Category', '')}",
                "company": "FAANG",
                "focus_area": focus_area,
                "metadata": {"difficulty": "senior", "requires_diagram": False},
            }

    def get_structure(self) -> dict:
        tree: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for row in self.rows:
            tree[row.get("Category", "Other")][row.get("Topic", "Other")][row.get("Sub-Topic", "Other")] += 1

        result: dict = {}
        for cat in sorted(tree):
            cat_data: dict = {"children": {}, "total": 0}
            for topic in sorted(tree[cat]):
                topic_data: dict = {"children": {}, "total": 0}
                for sub in sorted(tree[cat][topic]):
                    count = tree[cat][topic][sub]
                    topic_data["children"][sub] = {"total": count}
                    topic_data["total"] += count
                cat_data["children"][topic] = topic_data
                cat_data["total"] += topic_data["total"]
            result[cat] = cat_data
        return result

    def get_progress(self, asked_questions: set[str]) -> dict:
        tree: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"total": 0, "covered": 0})))
        for row in self.rows:
            cat = row.get("Category", "Other")
            topic = row.get("Topic", "Other")
            sub = row.get("Sub-Topic", "Other")
            tree[cat][topic][sub]["total"] += 1
            if generate_question_id(_get_depth(row)) in asked_questions:
                tree[cat][topic][sub]["covered"] += 1

        total_all = covered_all = 0
        levels: dict = {}
        for cat in sorted(tree):
            cat_total = cat_covered = 0
            cat_children: dict = {}
            for topic in sorted(tree[cat]):
                topic_total = topic_covered = 0
                topic_children: dict = {}
                for sub in sorted(tree[cat][topic]):
                    s = tree[cat][topic][sub]
                    topic_children[sub] = {
                        "total": s["total"],
                        "covered": s["covered"],
                        "percent": round(s["covered"] / s["total"] * 100) if s["total"] else 0,
                    }
                    topic_total += s["total"]
                    topic_covered += s["covered"]
                cat_children[topic] = {
                    "total": topic_total,
                    "covered": topic_covered,
                    "percent": round(topic_covered / topic_total * 100) if topic_total else 0,
                    "children": topic_children,
                }
                cat_total += topic_total
                cat_covered += topic_covered
            levels[cat] = {
                "total": cat_total,
                "covered": cat_covered,
                "percent": round(cat_covered / cat_total * 100) if cat_total else 0,
                "children": cat_children,
            }
            total_all += cat_total
            covered_all += cat_covered

        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }

    def get_detailed_progress(self, asked_questions: set[str]) -> dict:
        tree: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for row in self.rows:
            cat = row.get("Category", "Other")
            topic = row.get("Topic", "Other")
            sub = row.get("Sub-Topic", "Other")
            name = _get_depth(row)
            tree[cat][topic][sub].append({
                "name": name,
                "covered": generate_question_id(name) in asked_questions,
            })

        total_all = covered_all = 0
        levels: dict = {}
        for cat in sorted(tree):
            cat_total = cat_covered = 0
            cat_children: dict = {}
            for topic in sorted(tree[cat]):
                topic_total = topic_covered = 0
                topic_children: dict = {}
                for sub in sorted(tree[cat][topic]):
                    items = tree[cat][topic][sub]
                    sub_covered = sum(1 for i in items if i["covered"])
                    topic_children[sub] = {
                        "total": len(items),
                        "covered": sub_covered,
                        "percent": round(sub_covered / len(items) * 100) if items else 0,
                        "items": items,
                    }
                    topic_total += len(items)
                    topic_covered += sub_covered
                cat_children[topic] = {
                    "total": topic_total,
                    "covered": topic_covered,
                    "percent": round(topic_covered / topic_total * 100) if topic_total else 0,
                    "children": topic_children,
                }
                cat_total += topic_total
                cat_covered += topic_covered
            levels[cat] = {
                "total": cat_total,
                "covered": cat_covered,
                "percent": round(cat_covered / cat_total * 100) if cat_total else 0,
                "children": cat_children,
            }
            total_all += cat_total
            covered_all += cat_covered

        return {
            "total": total_all,
            "covered": covered_all,
            "overall_percent": round(covered_all / total_all * 100) if total_all else 0,
            "levels": levels,
        }
